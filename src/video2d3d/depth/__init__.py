"""Depth estimation module.

This module provides depth estimation functionality using the MiDaS pre-trained
depth estimation model with PyTorch, including model loading from cache or download,
and single-frame depth prediction functionality.

Supported models:
- MiDaS v2.1 Small (fast, lower quality)
- MiDaS v3.0 Hybrid (balanced)
- DPT Large (best quality, slower)
- DPT Hybrid (good quality, medium speed)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import numpy as np
import torch
import torch.nn.functional as F

if TYPE_CHECKING:
    from loguru import Logger
    from torch import nn
    from torchvision.transforms import Compose

from video2d3d.utils.gpu import (
    GPUConfig,
    GPUError,
    OutOfMemoryError,
    clear_gpu_memory,
    compute_optimal_batch_size,
    get_memory_usage,
    select_device,
    setup_device,
    with_oom_retry,
)
from video2d3d.utils.logger import get_logger, log_exception, log_model_inference

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Default resolutions for different model types
_MIDAS_DEFAULT_RESOLUTION: int = 256
_DPT_DEFAULT_RESOLUTION: int = 384

# Default batch size for batch processing
_DEFAULT_BATCH_SIZE: int = 4


class MiDaSModelType(Enum):
    """Available MiDaS model variants."""

    MIDAS_V21_SMALL = "MiDaS_small"
    MIDAS_V21 = "MiDaS"
    DPT_LARGE = "DPT_Large"
    DPT_HYBRID = "DPT_Hybrid"

    @classmethod
    def from_string(cls, name: str) -> MiDaSModelType:
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive, supports various formats).

        Returns:
            MiDaSModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        # Normalize the name
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        # Map common names to enum values
        name_mapping = {
            "midas_small": cls.MIDAS_V21_SMALL,
            "midas_small_2.1": cls.MIDAS_V21_SMALL,
            "midas": cls.MIDAS_V21,
            "midas_2.1": cls.MIDAS_V21,
            "dpt_large": cls.DPT_LARGE,
            "dpt_large_384": cls.DPT_LARGE,
            "dpt_hybrid": cls.DPT_HYBRID,
            "dpt_hybrid_384": cls.DPT_HYBRID,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def hub_name(self) -> str:
        """Get the PyTorch Hub model name."""
        return self.value

    @property
    def default_resolution(self) -> int:
        """Get the default input resolution for this model."""
        # DPT models typically use 384, MiDaS small uses 256
        if self in (MiDaSModelType.DPT_LARGE, MiDaSModelType.DPT_HYBRID):
            return _DPT_DEFAULT_RESOLUTION
        return _MIDAS_DEFAULT_RESOLUTION

    @property
    def is_dpt(self) -> bool:
        """Check if this is a DPT (Dense Prediction Transformer) model."""
        return self in (MiDaSModelType.DPT_LARGE, MiDaSModelType.DPT_HYBRID)


@dataclass
class MiDaSConfig:
    """Configuration for MiDaS depth estimation.

    Attributes:
        model_type: Type of MiDaS model to use.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        cache_dir: Directory to cache downloaded models. None uses default.
        auto_download: Whether to automatically download models if not cached.
        output_resolution: Output depth map resolution. None uses model default.
        use_fp16: Use half-precision (FP16) inference for faster GPU inference.
        optimize: Use optimized inference mode (memory-efficient attention).
    """

    model_type: MiDaSModelType = MiDaSModelType.MIDAS_V21_SMALL
    device: str = "auto"
    cache_dir: Path | None = None
    auto_download: bool = True
    output_resolution: int | None = None
    use_fp16: bool = False
    optimize: bool = True

    # GPU acceleration settings
    gpu_config: GPUConfig | None = None
    auto_batch_size: bool = True
    min_batch_size: int = 1
    max_batch_size: int = 32
    memory_fraction: float = 0.8
    fallback_to_cpu: bool = True
    pinned_memory: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model type
        if isinstance(self.model_type, str):
            self.model_type = MiDaSModelType.from_string(self.model_type)

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(
                enabled=True,
                device=self.device,
                memory_fraction=self.memory_fraction,
                fallback_to_cpu=self.fallback_to_cpu,
                batch_size_auto=self.auto_batch_size,
                min_batch_size=self.min_batch_size,
                max_batch_size=self.max_batch_size,
                pinned_memory=self.pinned_memory,
                fp16_enabled=self.use_fp16,
            )

        # Auto-detect device using GPU utilities
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            self.device = selection.device
            self._device_selection = selection

        # Normalize cache_dir to Path
        if self.cache_dir is not None and isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)

    @property
    def effective_resolution(self) -> int:
        """Get the effective output resolution."""
        return self.output_resolution or self.model_type.default_resolution


class DepthEstimationError(Exception):
    """Exception raised for depth estimation errors."""

    def __init__(
        self,
        message: str,
        *,
        model_type: str | None = None,
        device: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            model_type: Model type that caused the error.
            device: Device being used.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.model_type = model_type
        self.device = device
        self.original_exception = original_exception


class ModelLoadError(DepthEstimationError):
    """Exception raised when model loading fails."""

    pass


class InferenceError(DepthEstimationError):
    """Exception raised when inference fails."""

    pass


def _get_depth_logger() -> Logger:
    """Get the depth module logger (lazy initialization)."""
    return get_logger("depth")


class DepthEstimator:
    """Estimate depth from 2D images using MiDaS models.

    This class provides a high-level interface for depth estimation using
    pre-trained MiDaS models from PyTorch Hub. It handles model loading,
    caching, preprocessing, and inference.

    Example usage:
        ```python
        # Basic usage
        estimator = DepthEstimator()
        depth_map = estimator.estimate_depth(image)

        # With custom configuration
        config = MiDaSConfig(model_type=MiDaSModelType.DPT_LARGE, device="cuda")
        estimator = DepthEstimator(config=config)
        depth_map = estimator.estimate_depth(image)

        # Context manager for automatic cleanup
        with DepthEstimator() as estimator:
            depth_map = estimator.estimate_depth(image)
        ```

    Attributes:
        config: MiDaS configuration.
        model: Loaded MiDaS model (None until load_model is called).
        transform: Preprocessing transform pipeline.
    """

    # PyTorch Hub repository for MiDaS
    HUB_REPO = "intel-isl/MiDaS"

    def __init__(
        self,
        config: MiDaSConfig | None = None,
        *,
        model_type: str | MiDaSModelType = "midas_small",
        device: str = "auto",
    ) -> None:
        """Initialize the depth estimator.

        Args:
            config: MiDaSConfig object. If provided, model_type and device are ignored.
            model_type: Type of MiDaS model (ignored if config is provided).
            device: Device for inference (ignored if config is provided).
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            if isinstance(model_type, str):
                model_type = MiDaSModelType.from_string(model_type)
            self.config = MiDaSConfig(model_type=model_type, device=device)

        # Model components (lazy loaded)
        self._model: nn.Module | None = None
        self._transform: Compose | None = None
        self._is_loaded: bool = False

        # Temporal smoothing (lazy initialized)
        self._temporal_smoother: TemporalSmoother | None = None
        self._temporal_config: TemporalSmoothingConfig | None = None

        logger = _get_depth_logger()
        logger.info(
            f"DepthEstimator initialized: model={self.config.model_type.value}, "
            f"device={self.config.device}, resolution={self.config.effective_resolution}"
        )

    @property
    def model(self) -> nn.Module | None:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    @property
    def transform(self) -> Compose | None:
        """Get the preprocessing transform (loads model if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._transform

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    def _get_torch_hub_dir(self) -> Path:
        """Get the PyTorch Hub directory for model caching."""
        if self.config.cache_dir is not None:
            hub_dir = self.config.cache_dir
        else:
            # Use default torch hub directory
            hub_dir = Path(torch.hub.get_dir())

        # Ensure directory exists
        hub_dir.mkdir(parents=True, exist_ok=True)
        # Point torch hub at the resolved directory
        torch.hub.set_dir(str(hub_dir))
        return hub_dir

    def load_model(self) -> None:
        """Load the MiDaS model from cache or download.

        This method loads both the model and the appropriate preprocessing
        transforms from PyTorch Hub. Models are cached locally for offline use.

        Raises:
            ModelLoadError: If model loading fails.
        """
        logger = _get_depth_logger()
        logger.info(f"Loading MiDaS model: {self.config.model_type.value}")

        try:
            start_time = time.time()

            # Set torch hub directory for caching
            hub_dir = self._get_torch_hub_dir()
            torch.hub.set_dir(str(hub_dir))
            logger.debug(f"Using torch hub directory: {hub_dir}")

            # Download/load the model
            if self.config.auto_download:
                logger.debug("Downloading/loading model from PyTorch Hub...")
                self._model = torch.hub.load(
                    self.HUB_REPO,
                    self.config.model_type.hub_name,
                    pretrained=True,
                    trust_repo=True,
                )
            else:
                # Try to load from local cache only
                self._model = torch.hub.load(
                    self.HUB_REPO,
                    self.config.model_type.hub_name,
                    pretrained=True,
                    skip_validation=True,
                    trust_repo=True,
                )

            # Load the appropriate transforms for this model
            self._transform = torch.hub.load(
                self.HUB_REPO,
                "transforms",
                trust_repo=True,
            )

            # Select the correct transform based on model type
            if self.config.model_type.is_dpt:
                self._transform = self._transform.dpt_transform
            else:
                self._transform = self._transform.small_transform

            # Move model to device and set to evaluation mode
            self._model = self._model.to(self.config.device)
            self._model.eval()

            # Apply optimizations if enabled
            if self.config.optimize and self.config.device == "cuda":
                self._model = self._model.half() if self.config.use_fp16 else self._model
                # Enable cudnn benchmark for consistent input sizes
                torch.backends.cudnn.benchmark = True

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Model loaded successfully in {elapsed_ms:.0f}ms: "
                f"{self.config.model_type.value} on {self.config.device}"
            )

            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=0,  # Loading, not inference
                inference_time_ms=elapsed_ms,
                operation="model_load",
            )

        except Exception as e:
            log_exception(
                "Failed to load MiDaS model",
                exception=e,
                model_type=self.config.model_type.value,
                device=self.config.device,
                hub_dir=str(self._get_torch_hub_dir()),
            )
            raise ModelLoadError(
                f"Failed to load MiDaS model '{self.config.model_type.value}': {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess an image for depth estimation.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Preprocessed image tensor ready for model input.

        Raises:
            InferenceError: If the model is not loaded or preprocessing fails.
        """
        if self._transform is None:
            raise InferenceError(
                "Model not loaded. Call load_model() first.",
                model_type=self.config.model_type.value if self.config else None,
                device=self.config.device if self.config else None,
            )

        # Apply MiDaS transforms
        input_tensor = self._transform(image)

        # Add batch dimension if needed
        if input_tensor.dim() == 3:
            input_tensor = input_tensor.unsqueeze(0)

        # Move to device
        input_tensor = input_tensor.to(self.config.device)

        # Apply FP16 if enabled
        if self.config.use_fp16 and self.config.device == "cuda":
            input_tensor = input_tensor.half()

        return input_tensor

    def _postprocess_depth(
        self,
        output: torch.Tensor,
        original_shape: tuple[int, int],
    ) -> np.ndarray:
        """Post-process model output to depth map.

        Args:
            output: Raw model output tensor.
            original_shape: Original image shape (H, W).

        Returns:
            Depth map as numpy array normalized to [0, 1].
        """
        # Remove batch dimension
        if output.dim() == 4:
            output = output.squeeze(0)

        # Convert to numpy
        depth_map = output.squeeze().cpu().numpy()

        # Interpolate to original size using module-level F import
        depth_tensor = torch.from_numpy(depth_map).unsqueeze(0).unsqueeze(0)
        depth_tensor = F.interpolate(
            depth_tensor,
            size=original_shape,
            mode="bicubic",
            align_corners=False,
        )
        depth_map: np.ndarray = depth_tensor.squeeze().numpy()

        depth_min = depth_map.min()
        depth_max = depth_map.max()
        if depth_max - depth_min > 0:
            depth_map = (depth_map - depth_min) / (depth_max - depth_min)
        else:
            depth_map = np.zeros_like(depth_map)

        return depth_map.astype(np.float32)

    def estimate_depth(
        self,
        frame: np.ndarray,
        temporal_smoothing: bool = False,
        temporal_config: TemporalSmoothingConfig | None = None,
    ) -> np.ndarray:
        """Estimate depth from a single frame.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            temporal_smoothing: Apply temporal smoothing for video sequences.
            temporal_config: Configuration for temporal smoothing. If not provided,
                           uses default configuration.

        Returns:
            Depth map as numpy array (H, W) with float32 values in [0, 1] range.
            Higher values indicate closer objects.

        Raises:
            InferenceError: If inference fails or input is invalid.
        """
        logger = _get_depth_logger()

        # Input validation
        if not isinstance(frame, np.ndarray):
            raise InferenceError(
                f"Input must be a numpy array, got {type(frame).__name__}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
        if frame.ndim != 3:
            raise InferenceError(
                f"Input must be 3D array (H, W, C), got {frame.ndim}D",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
        if frame.shape[2] != 3:
            raise InferenceError(
                f"Input must have 3 channels (RGB), got {frame.shape[2]}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        if temporal_smoothing:
            # Initialize temporal smoother if needed
            if self._temporal_smoother is None or (
                temporal_config is not None and temporal_config != self._temporal_config
            ):
                if temporal_config is not None:
                    self._temporal_config = temporal_config
                else:
                    self._temporal_config = TemporalSmoothingConfig()
                self._temporal_smoother = TemporalSmoother(config=self._temporal_config)
                logger.info("Temporal smoothing enabled")

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None or self._transform is None:
            raise InferenceError(
                "Model failed to load",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        logger.debug(f"Estimating depth for frame: shape={frame.shape}, dtype={frame.dtype}")
        start_time = time.time()

        try:
            original_shape = (frame.shape[0], frame.shape[1])

            # Preprocess
            input_tensor = self._preprocess_image(frame)

            # Inference
            with torch.no_grad():
                prediction = self._model(input_tensor)

            # Postprocess
            depth_map = self._postprocess_depth(prediction, original_shape)

            # Apply temporal smoothing if enabled
            if temporal_smoothing and self._temporal_smoother is not None:
                depth_map = self._temporal_smoother.smooth(depth_map, frame)
                logger.debug("Applied temporal smoothing to depth map")

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=1,
                inference_time_ms=elapsed_ms,
                resolution=self.config.effective_resolution,
            )

            logger.debug(f"Depth estimation completed in {elapsed_ms:.2f}ms")
            return depth_map

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str and self.config.fallback_to_cpu:
                logger.warning("GPU out of memory, falling back to CPU")
                self._fallback_to_cpu()
                return self.estimate_depth(frame)
            raise InferenceError(
                f"Depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e
        except Exception as e:
            log_exception("Depth estimation failed", exception=e)
            raise InferenceError(
                f"Depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _fallback_to_cpu(self) -> None:
        """Fall back to CPU processing when GPU fails.

        This method moves the model to CPU and updates the config.
        It's safe to call multiple times - subsequent calls are no-ops.
        """
        logger = _get_depth_logger()

        # Check if already on CPU
        if self.config.device == "cpu":
            logger.debug("Already on CPU, skipping fallback")
            return

        logger.warning("Falling back to CPU processing")

        # Move model to CPU
        if self._model is not None:
            self._model = self._model.to("cpu")
            self.config.device = "cpu"

            # Clear GPU memory
            clear_gpu_memory()

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames with GPU memory management.

        This method processes frames in batches for efficient GPU utilization.
        It automatically adjusts batch size based on available GPU memory and
        handles out-of-memory errors with retry logic.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            batch_size: Initial number of frames to process at once. Will be
                       adjusted automatically if auto_batch_size is enabled.

        Returns:
            List of depth maps as numpy arrays (H, W) with float32 values in [0, 1].

        Raises:
            InferenceError: If inference fails or input is invalid.
        """
        logger = _get_depth_logger()

        # Input validation
        if not frames:
            raise InferenceError(
                "Input frames list cannot be empty",
                model_type=None,
                device=None,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None or self._transform is None:
            raise InferenceError(
                "Model failed to load",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        # Get frame dimensions for memory calculation
        first_frame = frames[0]
        image_height, image_width = first_frame.shape[0], first_frame.shape[1]

        # Compute optimal batch size if auto-adjustment is enabled
        effective_batch_size = batch_size
        if self.config.auto_batch_size and self.config.gpu_config is not None:
            effective_batch_size = compute_optimal_batch_size(
                config=self.config.gpu_config,
                image_height=image_height,
                image_width=image_width,
                use_fp16=self.config.use_fp16,
            )
            logger.info(
                f"Auto-adjusted batch size: {effective_batch_size} " f"(requested: {batch_size})"
            )
        else:
            effective_batch_size = min(
                max(batch_size, self.config.min_batch_size),
                self.config.max_batch_size,
            )

        logger.info(
            f"Processing batch of {len(frames)} frames with batch_size={effective_batch_size}"
        )

        depth_maps: list[np.ndarray] = []
        current_batch_size = effective_batch_size

        try:
            i = 0
            while i < len(frames):
                batch = frames[i : i + current_batch_size]
                batch_start_time = time.time()

                try:
                    # Preprocess all frames in batch
                    original_shapes = [(f.shape[0], f.shape[1]) for f in batch]
                    input_tensors = [self._preprocess_image(f) for f in batch]
                    batch_tensor = torch.cat(input_tensors, dim=0)

                    # Inference
                    with torch.no_grad():
                        predictions = self._model(batch_tensor)

                    # Postprocess each frame
                    for _, (pred, shape) in enumerate(zip(predictions, original_shapes)):
                        depth_map = self._postprocess_depth(pred.unsqueeze(0), shape)
                        depth_maps.append(depth_map)

                    elapsed_ms = (time.time() - batch_start_time) * 1000
                    logger.debug(
                        f"Processed batch {i // effective_batch_size + 1}: "
                        f"{len(batch)} frames in {elapsed_ms:.2f}ms"
                    )

                    # Move to next batch
                    i += current_batch_size

                    # Reset batch size after successful processing (in case of previous OOM)
                    if current_batch_size < effective_batch_size:
                        current_batch_size = min(current_batch_size * 2, effective_batch_size)

                except RuntimeError as e:
                    error_str = str(e).lower()
                    if "out of memory" in error_str:
                        # Handle OOM by reducing batch size
                        logger.warning(
                            f"GPU OOM with batch_size={current_batch_size}, "
                            f"reducing to {current_batch_size // 2}"
                        )

                        # Clear GPU memory
                        clear_gpu_memory(self.config.device)

                        # Reduce batch size
                        new_batch_size = max(current_batch_size // 2, 1)
                        if new_batch_size < current_batch_size:
                            current_batch_size = new_batch_size
                            continue  # Retry same batch with smaller size

                        # If we can't reduce further, try CPU fallback
                        if self.config.fallback_to_cpu:
                            self._fallback_to_cpu()
                            # Reset batch size for CPU and continue in same loop
                            # This avoids recursive call and potential stack overflow
                            current_batch_size = min(batch_size, 4)
                            continue  # Retry same batch on CPU

                        raise InferenceError(
                            "GPU out of memory and CPU fallback disabled",
                            model_type=self.config.model_type.value,
                            device=self.config.device,
                            original_exception=e,
                        ) from e
                    raise

            total_frames = len(frames)
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=effective_batch_size,
                inference_time_ms=0,  # Total time varies
                total_frames=total_frames,
            )

            return depth_maps

        except Exception as e:
            log_exception(
                "Batch depth estimation failed", exception=e, batch_size=effective_batch_size
            )
            raise InferenceError(
                f"Batch depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame (callable interface).

        Args:
            frame: Input image as numpy array.

        Returns:
            Depth map as numpy array.
        """
        return self.estimate_depth(frame)

    def __enter__(self) -> DepthEstimator:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,  # types.TracebackType not available for runtime annotation
    ) -> None:
        """Context manager exit - cleanup resources.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Traceback object if an exception was raised.
        """
        self.close()

    def reset_temporal(self) -> None:
        """Reset temporal smoothing state for a new video sequence.

        This should be called when starting a new video or when
        temporal consistency should be reset.
        """
        if self._temporal_smoother is not None:
            self._temporal_smoother.reset()
            self._get_depth_logger().debug("Temporal smoothing state reset")

    def close(self) -> None:
        """Release model resources."""
        logger = _get_depth_logger()
        if self._model is not None:
            del self._model
            self._model = None
        if self._transform is not None:
            del self._transform
            self._transform = None
        self._is_loaded = False

        # Clear temporal smoothing state
        if self._temporal_smoother is not None:
            self._temporal_smoother.reset()
            self._temporal_smoother = None
            self._temporal_config = None

        # Clear GPU cache if using CUDA
        if self.config.device.startswith("cuda") or self.config.device == "auto":
            clear_gpu_memory(self.config.device)
        logger.debug("DepthEstimator resources released")


# Module-level convenience functions
def create_estimator(
    model_type: str = "midas_small",
    device: str = "auto",
    **kwargs: Any,
) -> DepthEstimator:
    """Create a depth estimator with the specified configuration.

    Args:
        model_type: Model type string (midas_small, dpt_large, dpt_hybrid, etc.).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        **kwargs: Additional MiDaSConfig field values.

    Returns:
        Configured DepthEstimator instance.
    """
    config = MiDaSConfig(
        model_type=MiDaSModelType.from_string(model_type),
        device=device,
        **kwargs,
    )
    return DepthEstimator(config=config)


def estimate_depth_single(
    image: np.ndarray,
    model_type: str = "midas_small",
    device: str = "auto",
) -> np.ndarray:
    """Estimate depth from a single image (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        model_type: Model type string.
        device: Device for inference.

    Returns:
        Depth map as numpy array.
    """
    with create_estimator(model_type=model_type, device=device) as estimator:
        return estimator.estimate_depth(image)


# Import AdaBins (AdaDepth) components
from video2d3d.depth.adadepth import (
    AdaBinsConfig,
    AdaBinsEstimator,
    AdaBinsInferenceError,
    AdaBinsLoadError,
    AdaBinsModelType,
    create_adabins_estimator,
    estimate_depth_adabins,
)

# Import ensemble components
from video2d3d.depth.ensemble import (
    EnsembleConfig,
    EnsembleError,
    EnsembleMethod,
    EnsemblePredictor,
    WeightStrategy,
    create_ensemble_predictor,
    estimate_depth_ensemble,
)

# Import model selector components
from video2d3d.depth.model_selector import (
    DepthModelConfig,
    DepthModelSelector,
)
from video2d3d.depth.model_selector import DepthModelType as UnifiedDepthModelType
from video2d3d.depth.model_selector import ModelInferenceError as SelectorInferenceError
from video2d3d.depth.model_selector import ModelLoadError as SelectorLoadError
from video2d3d.depth.model_selector import (
    SceneType,
    create_model_selector,
    estimate_depth_auto,
)

# Import depth processor components
from video2d3d.depth.processor import (
    _DEFAULT_GUIDED_FILTER_EPS,
    _DEFAULT_GUIDED_FILTER_RADIUS,
    ColorMapType,
    DepthMapProcessor,
    DepthProcessingError,
    DepthProcessorConfig,
    EdgeAwareFilterType,
    HoleFillingMethod,
    NormalizationMethod,
    create_processor,
    process_depth_map,
)

# Import temporal smoothing components
from video2d3d.depth.temporal import (  # Motion-compensated smoothing
    MotionCompensatedConfig,
    MotionCompensatedSmoother,
    TemporalSmoother,
    TemporalSmoothingConfig,
    TemporalSmoothingError,
    TemporalSmoothingMethod,
    TemporalState,
    create_motion_compensated_smoother,
    create_temporal_smoother,
    smooth_depth_motion_compensated,
    smooth_depth_temporal,
)

# Import ZoeDepth components
from video2d3d.depth.zoedepth import (
    DepthMode,
    ZoeDepthConfig,
    ZoeDepthEstimator,
    ZoeDepthInferenceError,
    ZoeDepthLoadError,
    ZoeDepthModelVariant,
    create_zoedepth_estimator,
    estimate_depth_zoedepth,
)

logger = _get_depth_logger()

__all__ = [
    # Classes
    "DepthEstimator",
    "MiDaSConfig",
    "MiDaSModelType",
    "DepthMapProcessor",
    "DepthProcessorConfig",
    "TemporalSmoother",
    "TemporalSmoothingConfig",
    "TemporalState",
    # Motion-compensated smoothing
    "MotionCompensatedSmoother",
    "MotionCompensatedConfig",
    # AdaBins classes
    "AdaBinsEstimator",
    "AdaBinsConfig",
    "AdaBinsModelType",
    # ZoeDepth classes
    "ZoeDepthEstimator",
    "ZoeDepthConfig",
    "ZoeDepthModelVariant",
    "DepthMode",
    # Model selector classes
    "DepthModelSelector",
    "DepthModelConfig",
    "UnifiedDepthModelType",
    "SceneType",
    # Ensemble classes
    "EnsemblePredictor",
    "EnsembleConfig",
    # Enums
    "NormalizationMethod",
    "EdgeAwareFilterType",
    "TemporalSmoothingMethod",
    # Ensemble enums
    "EnsembleMethod",
    "WeightStrategy",
    # Exceptions
    "DepthEstimationError",
    "ModelLoadError",
    "InferenceError",
    "DepthProcessingError",
    "TemporalSmoothingError",
    # AdaBins exceptions
    "AdaBinsLoadError",
    "AdaBinsInferenceError",
    # ZoeDepth exceptions
    "ZoeDepthLoadError",
    "ZoeDepthInferenceError",
    # Selector exceptions
    "SelectorLoadError",
    "SelectorInferenceError",
    # Ensemble exceptions
    "EnsembleError",
    # Functions
    "create_estimator",
    "estimate_depth_single",
    "create_processor",
    "process_depth_map",
    "create_temporal_smoother",
    "smooth_depth_temporal",
    # Motion-compensated functions
    "create_motion_compensated_smoother",
    "smooth_depth_motion_compensated",
    "_get_depth_logger",
    # AdaBins functions
    "create_adabins_estimator",
    "estimate_depth_adabins",
    # ZoeDepth functions
    "create_zoedepth_estimator",
    "estimate_depth_zoedepth",
    # Model selector functions
    "create_model_selector",
    "estimate_depth_auto",
    # Ensemble functions
    "create_ensemble_predictor",
    "estimate_depth_ensemble",
    # Constants
    "_DEFAULT_GUIDED_FILTER_RADIUS",
    "_DEFAULT_GUIDED_FILTER_EPS",
]
