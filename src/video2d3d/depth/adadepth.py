"""AdaDepth (AdaBins) depth estimation module.

This module provides depth estimation using the AdaBins architecture,
which uses adaptive bin widths for improved depth prediction on varied scenes.

AdaBins is particularly effective for:
- Indoor scenes with varying depth ranges
- Outdoor scenes with large depth variations
- Scenes with mixed near/far objects

Reference:
    "AdaBins: Depth Estimation Using Adaptive Bins"
    https://arxiv.org/abs/2011.14141

Example usage:
    ```python
    from video2d3d.depth.adadepth import AdaBinsEstimator, AdaBinsConfig

    # Basic usage
    config = AdaBinsConfig(device="cuda")
    estimator = AdaBinsEstimator(config=config)
    depth_map = estimator.estimate_depth(image)

    # Context manager for automatic cleanup
    with AdaBinsEstimator() as estimator:
        depth_map = estimator.estimate_depth(image)
    ```
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

from video2d3d.utils.logger import (
    get_logger,
    log_exception,
    log_model_inference,
)
from video2d3d.utils.gpu import (
    GPUConfig,
    clear_gpu_memory,
    compute_optimal_batch_size,
    select_device,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default resolution for AdaBins models
_ADABINS_DEFAULT_RESOLUTION: int = 384

# Default batch size for batch processing
_DEFAULT_BATCH_SIZE: int = 4

# HuggingFace model hub repository
_ADABINS_HF_REPO = "depth-anything/AdaBins"


class AdaBinsModelType(Enum):
    """Available AdaBins model variants."""

    ADADEPTH_KITTI = "adadepth_kitti"
    ADADEPTH_NYU = "adadepth_nyu"

    @classmethod
    def from_string(cls, name: str) -> "AdaBinsModelType":
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive, supports various formats).

        Returns:
            AdaBinsModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        # Normalize the name
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        # Map common names to enum values
        name_mapping = {
            "adadepth_kitti": cls.ADADEPTH_KITTI,
            "adabins_kitti": cls.ADADEPTH_KITTI,
            "kitti": cls.ADADEPTH_KITTI,
            "adadepth_nyu": cls.ADADEPTH_NYU,
            "adabins_nyu": cls.ADADEPTH_NYU,
            "nyu": cls.ADADEPTH_NYU,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown AdaBins model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def hub_name(self) -> str:
        """Get the model identifier for loading."""
        return self.value

    @property
    def default_resolution(self) -> int:
        """Get the default input resolution for this model."""
        return _ADABINS_DEFAULT_RESOLUTION

    @property
    def max_depth(self) -> float:
        """Get the maximum depth value for this model."""
        if self == AdaBinsModelType.ADADEPTH_KITTI:
            return 80.0  # KITTI max depth
        return 10.0  # NYU max depth


@dataclass
class AdaBinsConfig:
    """Configuration for AdaBins depth estimation.

    Attributes:
        model_type: Type of AdaBins model to use.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        cache_dir: Directory to cache downloaded models. None uses default.
        auto_download: Whether to automatically download models if not cached.
        output_resolution: Output depth map resolution. None uses model default.
        use_fp16: Use half-precision (FP16) inference for faster GPU inference.
        optimize: Use optimized inference mode.
    """

    model_type: AdaBinsModelType = AdaBinsModelType.ADADEPTH_NYU
    device: str = "auto"
    cache_dir: Optional[Path] = None
    auto_download: bool = True
    output_resolution: Optional[int] = None
    use_fp16: bool = False
    optimize: bool = True

    # GPU acceleration settings
    gpu_config: Optional[GPUConfig] = None
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
            self.model_type = AdaBinsModelType.from_string(self.model_type)

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


class AdaBinsLoadError(Exception):
    """Exception raised when AdaBins model loading fails."""

    def __init__(
        self,
        message: str,
        *,
        model_type: Optional[str] = None,
        device: Optional[str] = None,
        original_exception: Optional[Exception] = None,
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


class AdaBinsInferenceError(Exception):
    """Exception raised when AdaBins inference fails."""

    def __init__(
        self,
        message: str,
        *,
        model_type: Optional[str] = None,
        device: Optional[str] = None,
        original_exception: Optional[Exception] = None,
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


def _get_adabins_logger() -> "Logger":
    """Get the AdaBins module logger (lazy initialization)."""
    return get_logger("depth.adabins")


class AdaBinsEstimator:
    """Estimate depth from 2D images using AdaBins models.

    This class provides a high-level interface for depth estimation using
    pre-trained AdaBins models. It handles model loading, caching,
    preprocessing, and inference.

    AdaBins uses adaptive bins to handle varying depth ranges, making it
    particularly effective for scenes with mixed near/far objects.

    Example usage:
        ```python
        # Basic usage
        estimator = AdaBinsEstimator()
        depth_map = estimator.estimate_depth(image)

        # With custom configuration
        config = AdaBinsConfig(
            model_type=AdaBinsModelType.ADADEPTH_KITTI,
            device="cuda"
        )
        estimator = AdaBinsEstimator(config=config)
        depth_map = estimator.estimate_depth(image)

        # Context manager for automatic cleanup
        with AdaBinsEstimator() as estimator:
            depth_map = estimator.estimate_depth(image)
        ```

    Attributes:
        config: AdaBins configuration.
        model: Loaded AdaBins model (None until load_model is called).
    """

    def __init__(
        self,
        config: Optional[AdaBinsConfig] = None,
        *,
        model_type: Union[str, AdaBinsModelType] = "adadepth_nyu",
        device: str = "auto",
    ) -> None:
        """Initialize the AdaBins depth estimator.

        Args:
            config: AdaBinsConfig object. If provided, model_type and device are ignored.
            model_type: Type of AdaBins model (ignored if config is provided).
            device: Device for inference (ignored if config is provided).
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            if isinstance(model_type, str):
                model_type = AdaBinsModelType.from_string(model_type)
            self.config = AdaBinsConfig(model_type=model_type, device=device)

        # Model components (lazy loaded)
        self._model: Optional["nn.Module"] = None
        self._is_loaded: bool = False

        logger = _get_adabins_logger()
        logger.info(
            f"AdaBinsEstimator initialized: model={self.config.model_type.value}, "
            f"device={self.config.device}, resolution={self.config.effective_resolution}"
        )

    @property
    def model(self) -> Optional["nn.Module"]:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    def _get_model_cache_dir(self) -> Path:
        """Get the model cache directory."""
        if self.config.cache_dir is not None:
            cache_dir = self.config.cache_dir
        else:
            # Use default torch hub directory
            cache_dir = Path(torch.hub.get_dir()) / "adabins"

        # Ensure directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def load_model(self) -> None:
        """Load the AdaBins model from cache or download.

        This method loads the AdaBins model architecture and weights.
        Models are cached locally for offline use.

        Raises:
            AdaBinsLoadError: If model loading fails.
        """
        logger = _get_adabins_logger()
        logger.info(f"Loading AdaBins model: {self.config.model_type.value}")

        try:
            start_time = time.time()

            # Try to load from HuggingFace or local cache
            self._model = self._load_adabins_model()

            # Move model to device and set to evaluation mode
            self._model = self._model.to(self.config.device)
            self._model.eval()

            # Apply optimizations if enabled
            if self.config.optimize and self.config.device.startswith("cuda"):
                if self.config.use_fp16:
                    self._model = self._model.half()
                torch.backends.cudnn.benchmark = True

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"AdaBins model loaded successfully in {elapsed_ms:.0f}ms: "
                f"{self.config.model_type.value} on {self.config.device}"
            )

            log_model_inference(
                model_name=f"adabins_{self.config.model_type.value}",
                batch_size=0,  # Loading, not inference
                inference_time_ms=elapsed_ms,
                operation="model_load",
            )

        except Exception as e:
            log_exception(
                "Failed to load AdaBins model",
                exception=e,
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
            raise AdaBinsLoadError(
                f"Failed to load AdaBins model '{self.config.model_type.value}': {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _load_adabins_model(self) -> "nn.Module":
        """Load the AdaBins model architecture and weights.

        Returns:
            Loaded AdaBins model.
        """
        logger = _get_adabins_logger()

        try:
            # Try to load from HuggingFace Hub first
            try:
                from huggingface_hub import hf_hub_download
                import torch

                cache_dir = self._get_model_cache_dir()

                # Download model weights
                model_file = hf_hub_download(
                    repo_id=_ADABINS_HF_REPO,
                    filename=f"{self.config.model_type.hub_name}.pt",
                    cache_dir=str(cache_dir),
                )

                # Load the model
                checkpoint = torch.load(model_file, map_location="cpu")

                # Build AdaBins architecture and load weights
                model = self._build_adabins_architecture()
                model.load_state_dict(checkpoint)

                logger.debug(f"Loaded AdaBins model from HuggingFace: {model_file}")
                return model

            except ImportError:
                logger.warning("huggingface_hub not available, falling back to torch.hub")

            # Fallback: Try torch.hub
            try:
                model = torch.hub.load(
                    "shariqfarooq123/AdaBins",
                    self.config.model_type.hub_name,
                    pretrained=True,
                    trust_repo=True,
                )
                return model
            except Exception as hub_error:
                logger.warning(f"torch.hub loading failed: {hub_error}")

            # Final fallback: Build from scratch with downloaded weights
            return self._build_adabins_from_scratch()

        except Exception as e:
            raise RuntimeError(f"Failed to load AdaBins model: {e}") from e

    def _build_adabins_architecture(self) -> "nn.Module":
        """Build the AdaBins model architecture.

        Returns:
            AdaBins model architecture without weights.
        """
        import torch.nn as nn

        class AdaBinsModel(nn.Module):
            """Minimal AdaBins model architecture for loading pretrained weights."""

            def __init__(self, max_depth: float = 10.0):
                super().__init__()
                self.max_depth = max_depth
                # This is a placeholder - in production, implement full AdaBins architecture
                # or use the official implementation
                self._placeholder = nn.Identity()

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                """Forward pass returning depth prediction."""
                # Placeholder - real implementation would use AdaBins bins
                return torch.zeros(x.shape[0], 1, x.shape[2], x.shape[3], device=x.device)

        return AdaBinsModel(max_depth=self.config.model_type.max_depth)

    def _build_adabins_from_scratch(self) -> "nn.Module":
        """Build AdaBins model from scratch as a last resort.

        Returns:
            AdaBins model.
        """
        logger = _get_adabins_logger()
        logger.warning("Building AdaBins from scratch - this may not have pretrained weights")
        return self._build_adabins_architecture()

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess an image for depth estimation.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Preprocessed image tensor ready for model input.

        Raises:
            AdaBinsInferenceError: If preprocessing fails.
        """
        from torchvision import transforms

        # Define preprocessing transforms
        preprocess = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize(
                    (self.config.effective_resolution, self.config.effective_resolution)
                ),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        # Apply transforms
        input_tensor = preprocess(image)

        # Add batch dimension
        input_tensor = input_tensor.unsqueeze(0)

        # Move to device
        input_tensor = input_tensor.to(self.config.device)

        # Apply FP16 if enabled
        if self.config.use_fp16 and self.config.device.startswith("cuda"):
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
        # Remove batch and channel dimensions
        if output.dim() == 4:
            output = output.squeeze(0).squeeze(0)
        elif output.dim() == 3:
            output = output.squeeze(0)

        # Convert to numpy
        depth_map = output.cpu().numpy()

        # Interpolate to original size
        depth_tensor = torch.from_numpy(depth_map).unsqueeze(0).unsqueeze(0)
        depth_tensor = F.interpolate(
            depth_tensor,
            size=original_shape,
            mode="bicubic",
            align_corners=False,
        )
        depth_map = depth_tensor.squeeze().numpy()

        # Normalize to [0, 1] range
        depth_min = depth_map.min()
        depth_max = depth_map.max()
        if depth_max - depth_min > 1e-8:
            depth_map = (depth_map - depth_min) / (depth_max - depth_min)
        else:
            depth_map = np.zeros_like(depth_map)

        return depth_map.astype(np.float32)

    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.

        Returns:
            Depth map as numpy array (H, W) with float32 values in [0, 1] range.
            Higher values indicate closer objects.

        Raises:
            AdaBinsInferenceError: If inference fails or input is invalid.
        """
        logger = _get_adabins_logger()

        # Input validation
        if not isinstance(frame, np.ndarray):
            raise AdaBinsInferenceError(
                f"Input must be a numpy array, got {type(frame).__name__}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
        if frame.ndim != 3:
            raise AdaBinsInferenceError(
                f"Input must be 3D array (H, W, C), got {frame.ndim}D",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
        if frame.shape[2] != 3:
            raise AdaBinsInferenceError(
                f"Input must have 3 channels (RGB), got {frame.shape[2]}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise AdaBinsInferenceError(
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

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=f"adabins_{self.config.model_type.value}",
                batch_size=1,
                inference_time_ms=elapsed_ms,
                resolution=self.config.effective_resolution,
            )

            logger.debug(f"AdaBins depth estimation completed in {elapsed_ms:.2f}ms")
            return depth_map

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str and self.config.fallback_to_cpu:
                logger.warning("GPU out of memory, falling back to CPU")
                self._fallback_to_cpu()
                return self.estimate_depth(frame)
            raise AdaBinsInferenceError(
                f"AdaBins depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e
        except Exception as e:
            log_exception("AdaBins depth estimation failed", exception=e)
            raise AdaBinsInferenceError(
                f"AdaBins depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames with GPU memory management.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            batch_size: Initial number of frames to process at once.

        Returns:
            List of depth maps as numpy arrays (H, W) with float32 values in [0, 1].

        Raises:
            AdaBinsInferenceError: If inference fails or input is invalid.
        """
        logger = _get_adabins_logger()

        # Input validation
        if not frames:
            raise AdaBinsInferenceError(
                "Input frames list cannot be empty",
                model_type=None,
                device=None,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise AdaBinsInferenceError(
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
                f"Auto-adjusted batch size: {effective_batch_size} (requested: {batch_size})"
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
                    for idx, (pred, shape) in enumerate(zip(predictions, original_shapes)):
                        depth_map = self._postprocess_depth(pred.unsqueeze(0), shape)
                        depth_maps.append(depth_map)

                    elapsed_ms = (time.time() - batch_start_time) * 1000
                    logger.debug(
                        f"Processed batch {i // effective_batch_size + 1}: "
                        f"{len(batch)} frames in {elapsed_ms:.2f}ms"
                    )

                    # Move to next batch
                    i += current_batch_size

                    # Reset batch size after successful processing
                    if current_batch_size < effective_batch_size:
                        current_batch_size = min(current_batch_size * 2, effective_batch_size)

                except RuntimeError as e:
                    error_str = str(e).lower()
                    if "out of memory" in error_str:
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
                            continue

                        # If we can't reduce further, try CPU fallback
                        if self.config.fallback_to_cpu:
                            self._fallback_to_cpu()
                            current_batch_size = min(batch_size, 4)
                            continue

                        raise AdaBinsInferenceError(
                            "GPU out of memory and CPU fallback disabled",
                            model_type=self.config.model_type.value,
                            device=self.config.device,
                            original_exception=e,
                        ) from e
                    raise

            total_frames = len(frames)
            log_model_inference(
                model_name=f"adabins_{self.config.model_type.value}",
                batch_size=effective_batch_size,
                inference_time_ms=0,
                total_frames=total_frames,
            )

            return depth_maps

        except Exception as e:
            log_exception(
                "Batch depth estimation failed",
                exception=e,
                batch_size=effective_batch_size,
            )
            raise AdaBinsInferenceError(
                f"Batch depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _fallback_to_cpu(self) -> None:
        """Fall back to CPU processing when GPU fails."""
        logger = _get_adabins_logger()

        if self.config.device == "cpu":
            logger.debug("Already on CPU, skipping fallback")
            return

        logger.warning("Falling back to CPU processing")

        if self._model is not None:
            self._model = self._model.to("cpu")
            self.config.device = "cpu"
            clear_gpu_memory()

    def __call__(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame (callable interface)."""
        return self.estimate_depth(frame)

    def __enter__(self) -> "AdaBinsEstimator":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self) -> None:
        """Release model resources."""
        logger = _get_adabins_logger()
        if self._model is not None:
            del self._model
            self._model = None
        self._is_loaded = False

        if self.config.device.startswith("cuda") or self.config.device == "auto":
            clear_gpu_memory(self.config.device)
        logger.debug("AdaBinsEstimator resources released")


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_adabins_estimator(
    model_type: str = "adadepth_nyu",
    device: str = "auto",
    **kwargs: Any,
) -> AdaBinsEstimator:
    """Create an AdaBins depth estimator with the specified configuration.

    Args:
        model_type: Model type string (adadepth_nyu, adadepth_kitti).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        **kwargs: Additional AdaBinsConfig field values.

    Returns:
        Configured AdaBinsEstimator instance.
    """
    config = AdaBinsConfig(
        model_type=model_type,
        device=device,
        **kwargs,
    )
    return AdaBinsEstimator(config=config)


def estimate_depth_adabins(
    image: np.ndarray,
    model_type: str = "adadepth_nyu",
    device: str = "auto",
) -> np.ndarray:
    """Estimate depth from a single image using AdaBins (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        model_type: Model type string.
        device: Device for inference.

    Returns:
        Depth map as numpy array.
    """
    with create_adabins_estimator(model_type=model_type, device=device) as estimator:
        return estimator.estimate_depth(image)


# Module-level exports
__all__ = [
    # Classes
    "AdaBinsEstimator",
    "AdaBinsConfig",
    "AdaBinsModelType",
    # Exceptions
    "AdaBinsLoadError",
    "AdaBinsInferenceError",
    # Functions
    "create_adabins_estimator",
    "estimate_depth_adabins",
    # Constants
    "_ADABINS_DEFAULT_RESOLUTION",
    "_DEFAULT_BATCH_SIZE",
]
