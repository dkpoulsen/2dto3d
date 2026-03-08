"""ZoeDepth metric depth estimation module.

This module provides depth estimation using the ZoeDepth architecture,
which combines MiDaS with domain-specific bin centers for metric depth estimation.

ZoeDepth is particularly effective for:
- Metric (absolute) depth estimation with real-world units
- Both indoor and outdoor scenes
- Domain adaptation between different depth ranges

Reference:
    "ZoeDepth: Zero-shot Transfer by Combining Relative and Metric Depth"
    https://arxiv.org/abs/2302.12288

Example usage:
    ```python
    from video2d3d.depth.zoedepth import ZoeDepthEstimator, ZoeDepthConfig

    # Basic usage
    config = ZoeDepthConfig(device="cuda")
    estimator = ZoeDepthEstimator(config=config)
    depth_map = estimator.estimate_depth(image)

    # Metric depth mode (absolute depth in meters)
    config = ZoeDepthConfig(depth_mode="metric")
    estimator = ZoeDepthEstimator(config=config)
    depth_map = estimator.estimate_depth(image)

    # Context manager for automatic cleanup
    with ZoeDepthEstimator() as estimator:
        depth_map = estimator.estimate_depth(image)
    ```
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
import torch.nn.functional as F

if TYPE_CHECKING:
    from loguru import Logger
    from torch import nn

from video2d3d.utils.gpu import (
    GPUConfig,
    clear_gpu_memory,
    compute_optimal_batch_size,
    select_device,
)
from video2d3d.utils.logger import get_logger, log_exception, log_model_inference

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default resolution for ZoeDepth models
_ZOEDEPTH_DEFAULT_RESOLUTION: int = 384

# Default batch size for batch processing
_DEFAULT_BATCH_SIZE: int = 4

# PyTorch Hub repository for ZoeDepth
_ZOEDEPTH_HUB_REPO = "isl-org/ZoeDepth"


class ZoeDepthModelVariant(Enum):
    """Available ZoeDepth model variants."""

    ZOE_N = "ZoeD_N"  # NYU-trained, indoor/relative depth
    ZOE_K = "ZoeD_K"  # KITTI-trained, outdoor/metric depth
    ZOE_NK = "ZoeD_NK"  # Combined, supports both relative and metric

    @classmethod
    def from_string(cls, name: str) -> ZoeDepthModelVariant:
        """Get model variant from string name.

        Args:
            name: Model name (case-insensitive, supports various formats).

        Returns:
            ZoeDepthModelVariant enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        # Normalize the name
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        # Map common names to enum values
        name_mapping = {
            "zoed_n": cls.ZOE_N,
            "zoedepth_n": cls.ZOE_N,
            "zoe_n": cls.ZOE_N,
            "n": cls.ZOE_N,
            "nyu": cls.ZOE_N,
            "indoor": cls.ZOE_N,
            "zoed_k": cls.ZOE_K,
            "zoedepth_k": cls.ZOE_K,
            "zoe_k": cls.ZOE_K,
            "k": cls.ZOE_K,
            "kitti": cls.ZOE_K,
            "outdoor": cls.ZOE_K,
            "zoed_nk": cls.ZOE_NK,
            "zoedepth_nk": cls.ZOE_NK,
            "zoe_nk": cls.ZOE_NK,
            "nk": cls.ZOE_NK,
            "combined": cls.ZOE_NK,
            "zoedepth": cls.ZOE_NK,  # Default to NK variant
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown ZoeDepth model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def hub_name(self) -> str:
        """Get the PyTorch Hub model name."""
        return self.value

    @property
    def default_resolution(self) -> int:
        """Get the default input resolution for this model."""
        return _ZOEDEPTH_DEFAULT_RESOLUTION

    @property
    def max_depth(self) -> float:
        """Get the maximum depth value for this model variant."""
        if self == ZoeDepthModelVariant.ZOE_N:
            return 10.0  # NYU max depth
        elif self == ZoeDepthModelVariant.ZOE_K:
            return 80.0  # KITTI max depth
        else:  # ZOE_NK
            return 80.0  # KITTI max for combined model

    @property
    def supports_metric(self) -> bool:
        """Check if this variant supports metric depth."""
        return True  # All ZoeDepth variants support metric depth

    @property
    def default_domain(self) -> str:
        """Get the default domain for this variant."""
        if self == ZoeDepthModelVariant.ZOE_N:
            return "indoor"
        elif self == ZoeDepthModelVariant.ZOE_K:
            return "outdoor"
        else:
            return "combined"


class DepthMode(Enum):
    """Depth estimation mode for ZoeDepth."""

    RELATIVE = "relative"  # Relative depth (normalized 0-1)
    METRIC = "metric"  # Metric depth (absolute values in meters)


@dataclass
class ZoeDepthConfig:
    """Configuration for ZoeDepth depth estimation.

    Attributes:
        model_variant: Variant of ZoeDepth model to use.
        depth_mode: Depth estimation mode ('relative' or 'metric').
        device: Device for inference ('cuda', 'cpu', or 'auto').
        cache_dir: Directory to cache downloaded models. None uses default.
        auto_download: Whether to automatically download models if not cached.
        output_resolution: Output depth map resolution. None uses model default.
        use_fp16: Use half-precision (FP16) inference for faster GPU inference.
        optimize: Use optimized inference mode (memory-efficient attention).
        domain: Domain hint for ZoeDepth_NK ('indoor', 'outdoor', or 'auto').
    """

    model_variant: ZoeDepthModelVariant = ZoeDepthModelVariant.ZOE_NK
    depth_mode: str = "relative"  # 'relative' or 'metric'
    device: str = "auto"
    cache_dir: Path | None = None
    auto_download: bool = True
    output_resolution: int | None = None
    use_fp16: bool = False
    optimize: bool = True
    domain: str = "auto"  # 'indoor', 'outdoor', or 'auto'

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
        # Handle string model variant
        if isinstance(self.model_variant, str):
            self.model_variant = ZoeDepthModelVariant.from_string(self.model_variant)

        # Validate depth mode
        valid_modes = [m.value for m in DepthMode]
        if self.depth_mode not in valid_modes:
            raise ValueError(
                f"Invalid depth_mode '{self.depth_mode}'. Valid options: {valid_modes}"
            )

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
        return self.output_resolution or self.model_variant.default_resolution

    @property
    def is_metric_mode(self) -> bool:
        """Check if metric depth mode is enabled."""
        return self.depth_mode == DepthMode.METRIC.value


class ZoeDepthLoadError(Exception):
    """Exception raised when ZoeDepth model loading fails."""

    def __init__(
        self,
        message: str,
        *,
        model_variant: str | None = None,
        device: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            model_variant: Model variant that caused the error.
            device: Device being used.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.model_variant = model_variant
        self.device = device
        self.original_exception = original_exception


class ZoeDepthInferenceError(Exception):
    """Exception raised when ZoeDepth inference fails."""

    def __init__(
        self,
        message: str,
        *,
        model_variant: str | None = None,
        device: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            model_variant: Model variant that caused the error.
            device: Device being used.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.model_variant = model_variant
        self.device = device
        self.original_exception = original_exception


def _get_zoedepth_logger() -> Logger:
    """Get the ZoeDepth module logger (lazy initialization)."""
    return get_logger("depth.zoedepth")


class ZoeDepthEstimator:
    """Estimate depth from 2D images using ZoeDepth models.

    This class provides a high-level interface for depth estimation using
    pre-trained ZoeDepth models. It handles model loading, caching,
    preprocessing, and inference.

    ZoeDepth supports both relative and metric (absolute) depth estimation,
    making it unique compared to other depth models like MiDaS.

    Example usage:
        ```python
        # Basic usage
        estimator = ZoeDepthEstimator()
        depth_map = estimator.estimate_depth(image)

        # Metric depth mode (absolute depth in meters)
        config = ZoeDepthConfig(
            model_variant=ZoeDepthModelVariant.ZOE_NK,
            depth_mode="metric"
        )
        estimator = ZoeDepthEstimator(config=config)
        depth_map = estimator.estimate_depth(image)

        # Context manager for automatic cleanup
        with ZoeDepthEstimator() as estimator:
            depth_map = estimator.estimate_depth(image)
        ```

    Attributes:
        config: ZoeDepth configuration.
        model: Loaded ZoeDepth model (None until load_model is called).
    """

    # PyTorch Hub repository for ZoeDepth
    HUB_REPO = _ZOEDEPTH_HUB_REPO

    def __init__(
        self,
        config: ZoeDepthConfig | None = None,
        *,
        model_variant: str | ZoeDepthModelVariant = "zoedepth_nk",
        device: str = "auto",
        depth_mode: str = "relative",
    ) -> None:
        """Initialize the ZoeDepth depth estimator.

        Args:
            config: ZoeDepthConfig object. If provided, model_variant, device,
                   and depth_mode are ignored.
            model_variant: Variant of ZoeDepth model (ignored if config is provided).
            device: Device for inference (ignored if config is provided).
            depth_mode: Depth estimation mode (ignored if config is provided).
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            if isinstance(model_variant, str):
                model_variant = ZoeDepthModelVariant.from_string(model_variant)
            self.config = ZoeDepthConfig(
                model_variant=model_variant,
                device=device,
                depth_mode=depth_mode,
            )

        # Model components (lazy loaded)
        self._model: nn.Module | None = None
        self._transform: Any | None = None  # torchvision.transforms.Compose
        self._is_loaded: bool = False

        logger = _get_zoedepth_logger()
        logger.info(
            f"ZoeDepthEstimator initialized: model={self.config.model_variant.value}, "
            f"device={self.config.device}, mode={self.config.depth_mode}, "
            f"resolution={self.config.effective_resolution}"
        )

    @property
    def model(self) -> nn.Module | None:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    @property
    def transform(self) -> Any | None:
        """Get the preprocessing transform (creates if not already created)."""
        if self._transform is None:
            self._create_transform()
        return self._transform

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

    def _create_transform(self) -> None:
        """Create the preprocessing transform pipeline.

        This creates a cached transform pipeline for efficient preprocessing.
        Called lazily when transform property is first accessed.
        """
        try:
            from torchvision import transforms

            self._transform = transforms.Compose(
                [
                    transforms.ToPILImage(),
                    transforms.Resize(
                        (self.config.effective_resolution, self.config.effective_resolution)
                    ),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225],
                    ),
                ]
            )
        except Exception as e:
            logger = _get_zoedepth_logger()
            logger.warning(f"Failed to create transform pipeline: {e}")
            raise

    def load_model(self) -> None:
        """Load the ZoeDepth model from cache or download.

        This method loads the ZoeDepth model from PyTorch Hub.
        Models are cached locally for offline use.

        Raises:
            ZoeDepthLoadError: If model loading fails.
        """
        logger = _get_zoedepth_logger()
        logger.info(f"Loading ZoeDepth model: {self.config.model_variant.value}")

        try:
            start_time = time.time()

            # Set torch hub directory for caching
            hub_dir = self._get_torch_hub_dir()
            torch.hub.set_dir(str(hub_dir))
            logger.debug(f"Using torch hub directory: {hub_dir}")

            # Download/load the model from PyTorch Hub
            if self.config.auto_download:
                logger.debug("Downloading/loading model from PyTorch Hub...")
                self._model = torch.hub.load(
                    self.HUB_REPO,
                    self.config.model_variant.hub_name,
                    pretrained=True,
                    trust_repo=True,
                )
            else:
                # Try to load from local cache only
                self._model = torch.hub.load(
                    self.HUB_REPO,
                    self.config.model_variant.hub_name,
                    pretrained=True,
                    skip_validation=True,
                    trust_repo=True,
                )

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
                f"ZoeDepth model loaded successfully in {elapsed_ms:.0f}ms: "
                f"{self.config.model_variant.value} on {self.config.device}"
            )

            log_model_inference(
                model_name=f"zoedepth_{self.config.model_variant.value}",
                batch_size=0,  # Loading, not inference
                inference_time_ms=elapsed_ms,
                operation="model_load",
            )

        except Exception as e:
            log_exception(
                "Failed to load ZoeDepth model",
                exception=e,
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                hub_dir=str(self._get_torch_hub_dir()),
            )
            raise ZoeDepthLoadError(
                f"Failed to load ZoeDepth model '{self.config.model_variant.value}': {e}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """Preprocess an image for depth estimation.

        Uses a cached transform pipeline for efficiency.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Preprocessed image tensor ready for model input.

        Raises:
            ZoeDepthInferenceError: If preprocessing fails.
        """
        try:
            # Get cached transform (creates on first call)
            if self._transform is None:
                self._create_transform()

            # Apply transforms
            input_tensor = self._transform(image)

            # Add batch dimension
            input_tensor = input_tensor.unsqueeze(0)

            # Move to device
            input_tensor = input_tensor.to(self.config.device)

            # Apply FP16 if enabled
            if self.config.use_fp16 and self.config.device.startswith("cuda"):
                input_tensor = input_tensor.half()

            return input_tensor

        except Exception as e:
            raise ZoeDepthInferenceError(
                f"Preprocessing failed: {e}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _postprocess_depth(
        self,
        output: torch.Tensor,
        original_shape: tuple[int, int],
        depth_mode: str | None = None,
    ) -> np.ndarray:
        """Post-process model output to depth map.

        Args:
            output: Raw model output tensor.
            original_shape: Original image shape (H, W).
            depth_mode: Depth mode to use ('relative' or 'metric').
                       If None, uses config setting.

        Returns:
            Depth map as numpy array. If metric mode, values are in meters.
            If relative mode, values are normalized to [0, 1].
        """
        # Determine effective depth mode (thread-safe: doesn't modify config)
        effective_mode = depth_mode if depth_mode is not None else self.config.depth_mode
        is_metric = effective_mode == DepthMode.METRIC.value

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

        # Apply depth mode processing
        if is_metric:
            # Keep metric values (already in meters from ZoeDepth)
            # Clamp to reasonable range based on model variant
            depth_map = np.clip(depth_map, 0, self.config.model_variant.max_depth)
        else:
            # Normalize to [0, 1] range for relative depth
            depth_min = depth_map.min()
            depth_max = depth_map.max()
            if depth_max - depth_min > 1e-8:
                depth_map = (depth_map - depth_min) / (depth_max - depth_min)
            else:
                depth_map = np.zeros_like(depth_map)

        return depth_map.astype(np.float32)

    def estimate_depth(
        self,
        frame: np.ndarray,
        depth_mode: str | None = None,
    ) -> np.ndarray:
        """Estimate depth from a single frame.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            depth_mode: Override depth mode ('relative' or 'metric').
                       If None, uses config setting.

        Returns:
            Depth map as numpy array (H, W) with float32 values.
            - In relative mode: values in [0, 1] range (higher = closer)
            - In metric mode: values in meters (absolute depth)

        Raises:
            ZoeDepthInferenceError: If inference fails or input is invalid.
        """
        logger = _get_zoedepth_logger()

        # Determine effective depth mode

        # Input validation
        if not isinstance(frame, np.ndarray):
            raise ZoeDepthInferenceError(
                f"Input must be a numpy array, got {type(frame).__name__}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
            )
        if frame.ndim != 3:
            raise ZoeDepthInferenceError(
                f"Input must be 3D array (H, W, C), got {frame.ndim}D",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
            )
        if frame.shape[2] != 3:
            raise ZoeDepthInferenceError(
                f"Input must have 3 channels (RGB), got {frame.shape[2]}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise ZoeDepthInferenceError(
                "Model failed to load",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
            )

        logger.debug(f"Estimating depth for frame: shape={frame.shape}, dtype={frame.dtype}")
        start_time = time.time()

        try:
            original_shape = (frame.shape[0], frame.shape[1])

            # Preprocess
            input_tensor = self._preprocess_image(frame)

            # Inference - ZoeDepth has a specific infer method
            with torch.no_grad():
                # ZoeDepth returns metric depth by default
                if hasattr(self._model, "infer"):
                    # Use the infer method for ZoeDepth
                    prediction = self._model.infer(input_tensor)
                else:
                    # Fallback to forward pass
                    prediction = self._model(input_tensor)

            # Postprocess (pass depth_mode for thread-safety)
            depth_map = self._postprocess_depth(prediction, original_shape, depth_mode=depth_mode)

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=f"zoedepth_{self.config.model_variant.value}",
                batch_size=1,
                inference_time_ms=elapsed_ms,
                resolution=self.config.effective_resolution,
            )

            logger.debug(f"ZoeDepth depth estimation completed in {elapsed_ms:.2f}ms")
            return depth_map

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str and self.config.fallback_to_cpu:
                logger.warning("GPU out of memory, falling back to CPU")
                self._fallback_to_cpu()
                return self.estimate_depth(frame, depth_mode=depth_mode)
            raise ZoeDepthInferenceError(
                f"ZoeDepth depth estimation failed: {e}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                original_exception=e,
            ) from e
        except Exception as e:
            log_exception("ZoeDepth depth estimation failed", exception=e)
            raise ZoeDepthInferenceError(
                f"ZoeDepth depth estimation failed: {e}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def estimate_depth_batch(
        self,
        frames: list[np.ndarray],
        batch_size: int = 4,
        depth_mode: str | None = None,
    ) -> list[np.ndarray]:
        """Estimate depth for a batch of frames with GPU memory management.

        This method processes frames in batches for efficient GPU utilization.
        It automatically adjusts batch size based on available GPU memory and
        handles out-of-memory errors with retry logic.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            batch_size: Initial number of frames to process at once. Will be
                       adjusted automatically if auto_batch_size is enabled.
            depth_mode: Override depth mode ('relative' or 'metric').

        Returns:
            List of depth maps as numpy arrays (H, W) with float32 values.

        Raises:
            ZoeDepthInferenceError: If inference fails or input is invalid.
        """
        logger = _get_zoedepth_logger()

        # Input validation
        if not frames:
            raise ZoeDepthInferenceError(
                "Input frames list cannot be empty",
                model_variant=None,
                device=None,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._model is None:
            raise ZoeDepthInferenceError(
                "Model failed to load",
                model_variant=self.config.model_variant.value,
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
                        if hasattr(self._model, "infer"):
                            predictions = self._model.infer(batch_tensor)
                        else:
                            predictions = self._model(batch_tensor)

                    # Postprocess each frame
                    for _idx, (pred, shape) in enumerate(zip(predictions, original_shapes)):
                        depth_map = self._postprocess_depth(
                            pred.unsqueeze(0), shape, depth_mode=depth_mode
                        )
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

                        raise ZoeDepthInferenceError(
                            "GPU out of memory and CPU fallback disabled",
                            model_variant=self.config.model_variant.value,
                            device=self.config.device,
                            original_exception=e,
                        ) from e
                    raise

            total_frames = len(frames)
            log_model_inference(
                model_name=f"zoedepth_{self.config.model_variant.value}",
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
            raise ZoeDepthInferenceError(
                f"Batch depth estimation failed: {e}",
                model_variant=self.config.model_variant.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def estimate_metric_depth(self, frame: np.ndarray) -> np.ndarray:
        """Estimate metric (absolute) depth from a single frame.

        This is a convenience method that forces metric depth mode.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Depth map as numpy array (H, W) with values in meters.
        """
        return self.estimate_depth(frame, depth_mode="metric")

    def estimate_relative_depth(self, frame: np.ndarray) -> np.ndarray:
        """Estimate relative depth from a single frame.

        This is a convenience method that forces relative depth mode.

        Args:
            frame: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            Depth map as numpy array (H, W) with values in [0, 1].
        """
        return self.estimate_depth(frame, depth_mode="relative")

    def _fallback_to_cpu(self) -> None:
        """Fall back to CPU processing when GPU fails."""
        logger = _get_zoedepth_logger()

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

    def __enter__(self) -> ZoeDepthEstimator:
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
        logger = _get_zoedepth_logger()
        if self._model is not None:
            del self._model
            self._model = None
        if self._transform is not None:
            del self._transform
            self._transform = None
        self._is_loaded = False

        if self.config.device.startswith("cuda") or self.config.device == "auto":
            clear_gpu_memory(self.config.device)
        logger.debug("ZoeDepthEstimator resources released")


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_zoedepth_estimator(
    model_variant: str = "zoedepth_nk",
    device: str = "auto",
    depth_mode: str = "relative",
    **kwargs: Any,
) -> ZoeDepthEstimator:
    """Create a ZoeDepth depth estimator with the specified configuration.

    Args:
        model_variant: Model variant string (zoedepth_n, zoedepth_k, zoedepth_nk).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        depth_mode: Depth estimation mode ('relative' or 'metric').
        **kwargs: Additional ZoeDepthConfig field values.

    Returns:
        Configured ZoeDepthEstimator instance.
    """
    config = ZoeDepthConfig(
        model_variant=model_variant,
        device=device,
        depth_mode=depth_mode,
        **kwargs,
    )
    return ZoeDepthEstimator(config=config)


def estimate_depth_zoedepth(
    image: np.ndarray,
    model_variant: str = "zoedepth_nk",
    device: str = "auto",
    depth_mode: str = "relative",
) -> np.ndarray:
    """Estimate depth from a single image using ZoeDepth (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        model_variant: Model variant string.
        device: Device for inference.
        depth_mode: Depth estimation mode ('relative' or 'metric').

    Returns:
        Depth map as numpy array.
    """
    with create_zoedepth_estimator(
        model_variant=model_variant,
        device=device,
        depth_mode=depth_mode,
    ) as estimator:
        return estimator.estimate_depth(image)


# Module-level exports
__all__ = [
    # Classes
    "ZoeDepthEstimator",
    "ZoeDepthConfig",
    "ZoeDepthModelVariant",
    "DepthMode",
    # Exceptions
    "ZoeDepthLoadError",
    "ZoeDepthInferenceError",
    # Functions
    "create_zoedepth_estimator",
    "estimate_depth_zoedepth",
    # Constants
    "_ZOEDEPTH_DEFAULT_RESOLUTION",
    "_DEFAULT_BATCH_SIZE",
    "_ZOEDEPTH_HUB_REPO",
]
