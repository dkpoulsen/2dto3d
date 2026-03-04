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

from video2d3d.utils.logger import (
    get_logger,
    log_exception,
    log_model_inference,
)


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
    def from_string(cls, name: str) -> "MiDaSModelType":
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
    cache_dir: Optional[Path] = None
    auto_download: bool = True
    output_resolution: Optional[int] = None
    use_fp16: bool = False
    optimize: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model type
        if isinstance(self.model_type, str):
            self.model_type = MiDaSModelType.from_string(self.model_type)

        # Auto-detect device
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

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


class ModelLoadError(DepthEstimationError):
    """Exception raised when model loading fails."""

    pass


class InferenceError(DepthEstimationError):
    """Exception raised when inference fails."""

    pass


def _get_depth_logger() -> "Logger":
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
        config: Optional[MiDaSConfig] = None,
        *,
        model_type: Union[str, MiDaSModelType] = "midas_small",
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
        self._model: Optional["nn.Module"] = None
        self._transform: Optional["Compose"] = None
        self._is_loaded: bool = False

        logger = _get_depth_logger()
        logger.info(
            f"DepthEstimator initialized: model={self.config.model_type.value}, "
            f"device={self.config.device}, resolution={self.config.effective_resolution}"
        )

    @property
    def model(self) -> Optional["nn.Module"]:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    @property
    def transform(self) -> Optional["Compose"]:
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

        # Normalize to [0, 1] range

        # Normalize to [0, 1] range
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
    ) -> np.ndarray:
        """Estimate depth from a single frame.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            temporal_smoothing: Apply temporal smoothing for video (not implemented).

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
            logger.warning("Temporal smoothing not yet implemented, using single frame")

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

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=1,
                inference_time_ms=elapsed_ms,
                resolution=self.config.effective_resolution,
            )

            logger.debug(f"Depth estimation completed in {elapsed_ms:.2f}ms")
            return depth_map

        except Exception as e:
            log_exception("Depth estimation failed", exception=e)
            raise InferenceError(
                f"Depth estimation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames.

        This method processes frames in batches for efficient GPU utilization.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            batch_size: Number of frames to process at once.

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

        logger.info(f"Processing batch of {len(frames)} frames with batch_size={batch_size}")
        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None or self._transform is None:
            raise InferenceError(
                "Model failed to load",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        depth_maps: list[np.ndarray] = []

        try:
            for i in range(0, len(frames), batch_size):
                batch = frames[i : i + batch_size]
                batch_start_time = time.time()

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
                    f"Processed batch {i // batch_size + 1}: "
                    f"{len(batch)} frames in {elapsed_ms:.2f}ms"
                )

            total_frames = len(frames)
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=batch_size,
                inference_time_ms=0,  # Total time varies
                total_frames=total_frames,
            )

            return depth_maps

        except Exception as e:
            log_exception("Batch depth estimation failed", exception=e, batch_size=batch_size)
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

    def __enter__(self) -> "DepthEstimator":
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
        logger = _get_depth_logger()
        if self._model is not None:
            del self._model
            self._model = None
        if self._transform is not None:
            del self._transform
            self._transform = None
        self._is_loaded = False

        # Clear GPU cache if using CUDA
        if self.config.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()

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


# Module-level logger for backward compatibility
logger = _get_depth_logger()

__all__ = [
    # Classes
    "DepthEstimator",
    "MiDaSConfig",
    "MiDaSModelType",
    # Exceptions
    "DepthEstimationError",
    "ModelLoadError",
    "InferenceError",
    # Functions
    "create_estimator",
    "estimate_depth_single",
    "_get_depth_logger",
]
