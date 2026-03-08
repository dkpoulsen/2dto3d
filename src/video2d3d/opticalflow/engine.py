"""Optical flow calculation using deep learning models (RAFT, PWC-Net).

This module provides optical flow estimation using state-of-the-art deep learning
models for accurate motion estimation in video processing pipelines.

Supported models:
- RAFT (Recurrent All-Pairs Field Transforms) - High accuracy
- PWC-Net (Pyramid, Warping, and Cost volume) - Fast inference
- Farneback (OpenCV) - CPU fallback

The optical flow engine computes dense motion fields between video frames,
which can be used for:
- Motion-compensated depth smoothing
- Video frame interpolation
- Motion analysis and tracking
- Temporal consistency in video processing

Example usage:
    ```python
    from video2d3d.opticalflow import OpticalFlowEngine, OpticalFlowConfig

    # Basic usage with RAFT
    config = OpticalFlowConfig(model_type="raft_large")
    engine = OpticalFlowEngine(config=config)
    flow = engine.compute_flow(frame1, frame2)

    # With GPU acceleration
    config = OpticalFlowConfig(model_type="raft_small", device="cuda")
    engine = OpticalFlowEngine(config=config)
    flow = engine.compute_flow(frame1, frame2)

    # Batch processing
    flows = engine.compute_flow_batch(frames[:-1], frames[1:])
    ```
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger
    from torch import nn

from video2d3d.utils.gpu import GPUConfig, clear_gpu_memory, select_device
from video2d3d.utils.logger import get_logger, log_exception, log_model_inference

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default input resolution for optical flow models
_DEFAULT_RAFT_RESOLUTION: int = 384
_DEFAULT_PWC_RESOLUTION: int = 384

# Default Farneback parameters (fallback)
_DEFAULT_FARNEBACK_PYR_SCALE: float = 0.5
_DEFAULT_FARNEBACK_LEVELS: int = 3
_DEFAULT_FARNEBACK_WINDOW: int = 15
_DEFAULT_FARNEBACK_ITERATIONS: int = 3
_DEFAULT_FARNEBACK_POLY_N: int = 5
_DEFAULT_FARNEBACK_POLY_SIGMA: float = 1.2


class OpticalFlowModelType(Enum):
    """Available optical flow model types."""

    RAFT_LARGE = "raft_large"  # RAFT with large backbone (most accurate)
    RAFT_SMALL = "raft_small"  # RAFT with small backbone (faster)
    RAFT_Sintel = "raft_sintel"  # RAFT fine-tuned on Sintel
    RAFT_Kitti = "raft_kitti"  # RAFT fine-tuned on KITTI
    PWC_NET = "pwc_net"  # PWC-Net (fast)
    FARNEBACK = "farneback"  # OpenCV Farneback (CPU fallback)

    @classmethod
    def from_string(cls, name: str) -> OpticalFlowModelType:
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive, supports various formats).

        Returns:
            OpticalFlowModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        name_mapping = {
            "raft_large": cls.RAFT_LARGE,
            "raft": cls.RAFT_LARGE,
            "raft_small": cls.RAFT_SMALL,
            "raft_sintel": cls.RAFT_Sintel,
            "sintel": cls.RAFT_Sintel,
            "raft_kitti": cls.RAFT_Kitti,
            "kitti": cls.RAFT_Kitti,
            "pwc_net": cls.PWC_NET,
            "pwcnet": cls.PWC_NET,
            "pwc": cls.PWC_NET,
            "farneback": cls.FARNEBACK,
            "opencv": cls.FARNEBACK,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def is_raft(self) -> bool:
        """Check if this is a RAFT model."""
        return self in (
            OpticalFlowModelType.RAFT_LARGE,
            OpticalFlowModelType.RAFT_SMALL,
            OpticalFlowModelType.RAFT_Sintel,
            OpticalFlowModelType.RAFT_Kitti,
        )

    @property
    def is_pwc(self) -> bool:
        """Check if this is a PWC-Net model."""
        return self == OpticalFlowModelType.PWC_NET

    @property
    def is_deep_learning(self) -> bool:
        """Check if this is a deep learning model (requires GPU/PyTorch)."""
        return self.is_raft or self.is_pwc

    @property
    def default_resolution(self) -> int:
        """Get the default input resolution for this model."""
        if self.is_raft:
            return _DEFAULT_RAFT_RESOLUTION
        elif self.is_pwc:
            return _DEFAULT_PWC_RESOLUTION
        return 0  # Farneback works at native resolution


class OpticalFlowError(Exception):
    """Exception raised for optical flow errors."""

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


class ModelLoadError(OpticalFlowError):
    """Exception raised when model loading fails."""

    pass


class InferenceError(OpticalFlowError):
    """Exception raised when inference fails."""

    pass


def _get_opticalflow_logger() -> Logger:
    """Get the optical flow module logger (lazy initialization)."""
    return get_logger("opticalflow")


@dataclass
class OpticalFlowConfig:
    """Configuration for optical flow estimation.

    Attributes:
        model_type: Type of optical flow model to use.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        cache_dir: Directory to cache downloaded models. None uses default.
        auto_download: Whether to automatically download models if not cached.
        input_resolution: Input resolution for deep learning models.
        use_fp16: Use half-precision (FP16) inference for faster GPU inference.
        farneback_pyr_scale: Pyramid scale for Farneback (0.5 means half size per level).
        farneback_levels: Number of pyramid levels for Farneback.
        farneback_window: Window size for Farneback.
        farneback_iterations: Number of iterations for Farneback.
        gpu_config: GPU configuration for acceleration.
    """

    model_type: OpticalFlowModelType = OpticalFlowModelType.RAFT_SMALL
    device: str = "auto"
    cache_dir: Path | None = None
    auto_download: bool = True
    input_resolution: int | None = None
    use_fp16: bool = False

    # Farneback parameters
    farneback_pyr_scale: float = _DEFAULT_FARNEBACK_PYR_SCALE
    farneback_levels: int = _DEFAULT_FARNEBACK_LEVELS
    farneback_window: int = _DEFAULT_FARNEBACK_WINDOW
    farneback_iterations: int = _DEFAULT_FARNEBACK_ITERATIONS

    # GPU settings
    gpu_config: GPUConfig | None = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model type
        if isinstance(self.model_type, str):
            self.model_type = OpticalFlowModelType.from_string(self.model_type)

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(
                enabled=True,
                device=self.device,
                fp16_enabled=self.use_fp16,
            )

        # Auto-detect device using GPU utilities
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            self.device = selection.device

        # Normalize cache_dir to Path
        if self.cache_dir is not None and isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)

        # Validate Farneback parameters
        if self.farneback_pyr_scale <= 0 or self.farneback_pyr_scale >= 1:
            raise ValueError(
                f"farneback_pyr_scale must be in (0, 1), got {self.farneback_pyr_scale}"
            )
        if self.farneback_levels < 1:
            raise ValueError(f"farneback_levels must be >= 1, got {self.farneback_levels}")
        if self.farneback_window < 1:
            raise ValueError(f"farneback_window must be >= 1, got {self.farneback_window}")
        if self.farneback_iterations < 1:
            raise ValueError(f"farneback_iterations must be >= 1, got {self.farneback_iterations}")

    @property
    def effective_resolution(self) -> int:
        """Get the effective input resolution."""
        return self.input_resolution or self.model_type.default_resolution

    def __repr__(self) -> str:
        """Return string representation of the configuration."""
        return (
            f"OpticalFlowConfig(model_type={self.model_type.value!r}, "
            f"device={self.device!r}, input_resolution={self.input_resolution!r}, "
            f"use_fp16={self.use_fp16!r})"
        )


class OpticalFlowEngine:
    """Optical flow estimation using deep learning models.

    This class provides a high-level interface for computing optical flow
    using state-of-the-art deep learning models (RAFT, PWC-Net) or
    traditional methods (Farneback) as fallback.

    Example usage:
        ```python
        # Basic usage
        engine = OpticalFlowEngine()
        flow = engine.compute_flow(frame1, frame2)

        # With configuration
        config = OpticalFlowConfig(model_type="raft_small", device="cuda")
        engine = OpticalFlowEngine(config=config)
        flow = engine.compute_flow(frame1, frame2)

        # Context manager for automatic cleanup
        with OpticalFlowEngine() as engine:
            flow = engine.compute_flow(frame1, frame2)
        ```

    Attributes:
        config: OpticalFlowConfig configuration.
    """

    def __init__(
        self,
        config: OpticalFlowConfig | None = None,
        *,
        model_type: str | OpticalFlowModelType = "raft_small",
        device: str = "auto",
    ) -> None:
        """Initialize the optical flow engine.

        Args:
            config: OpticalFlowConfig object. If provided, model_type and device are ignored.
            model_type: Type of optical flow model (ignored if config is provided).
            device: Device for inference (ignored if config is provided).
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            if isinstance(model_type, str):
                model_type = OpticalFlowModelType.from_string(model_type)
            self.config = OpticalFlowConfig(model_type=model_type, device=device)

        # Model components (lazy loaded)
        self._model: nn.Module | None = None
        self._is_loaded: bool = False

        logger = _get_opticalflow_logger()
        logger.info(
            f"OpticalFlowEngine initialized: model={self.config.model_type.value}, "
            f"device={self.config.device}"
        )

    @property
    def model(self) -> nn.Module | None:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded and self.config.model_type.is_deep_learning:
            self.load_model()
        return self._model

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    def __repr__(self) -> str:
        """Return string representation of the engine."""
        return (
            f"OpticalFlowEngine(model_type={self.config.model_type.value!r}, "
            f"device={self.config.device!r}, is_loaded={self._is_loaded!r})"
        )
        """Get the PyTorch Hub directory for model caching."""
        if self.config.cache_dir is not None:
            hub_dir = self.config.cache_dir
        else:
            import torch

            hub_dir = Path(torch.hub.get_dir())

        # Ensure directory exists
        hub_dir.mkdir(parents=True, exist_ok=True)
        return hub_dir

    def load_model(self) -> None:
        """Load the optical flow model.

        This method loads the deep learning model for optical flow estimation.
        For Farneback, no model loading is required.

        Raises:
            ModelLoadError: If model loading fails.
        """
        logger = _get_opticalflow_logger()

        # Farneback doesn't require model loading
        if not self.config.model_type.is_deep_learning:
            self._is_loaded = True
            logger.info("Using Farneback optical flow (no model loading required)")
            return

        logger.info(f"Loading optical flow model: {self.config.model_type.value}")

        try:
            start_time = time.time()

            if self.config.model_type.is_raft:
                self._load_raft_model()
            elif self.config.model_type.is_pwc:
                self._load_pwc_model()

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Model loaded successfully in {elapsed_ms:.0f}ms: "
                f"{self.config.model_type.value} on {self.config.device}"
            )

            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=0,
                inference_time_ms=elapsed_ms,
                operation="model_load",
            )

        except Exception as e:
            log_exception(
                "Failed to load optical flow model",
                exception=e,
                model_type=self.config.model_type.value,
                device=self.config.device,
            )
            raise ModelLoadError(
                f"Failed to load optical flow model '{self.config.model_type.value}': {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _load_raft_model(self) -> None:
        """Load the RAFT model from torchvision."""
        import torch

        logger = _get_opticalflow_logger()

        try:
            # Try to use torchvision's RAFT implementation first
            from torchvision.models.optical_flow import raft_large, raft_small

            if self.config.model_type == OpticalFlowModelType.RAFT_SMALL:
                self._model = raft_small(pretrained=True, progress=False)
                logger.debug("Loaded RAFT small model from torchvision")
            else:
                self._model = raft_large(pretrained=True, progress=False)
                logger.debug("Loaded RAFT large model from torchvision")

        except ImportError:
            # Fallback to torch.hub if torchvision doesn't have RAFT
            logger.warning("torchvision RAFT not available, falling back to torch.hub")

            hub_dir = self._get_torch_hub_dir()
            torch.hub.set_dir(str(hub_dir))

            # Map model type to RAFT model name in torch.hub
            # Note: torch.hub RAFT only supports 'raft_small' and 'raft_large'
            raft_model_name = (
                "raft_small"
                if self.config.model_type == OpticalFlowModelType.RAFT_SMALL
                else "raft_large"
            )

            self._model = torch.hub.load(
                "princeton-vl/RAFT", raft_model_name, pretrained=True, trust_repo=True
            )
        # Move model to device
        self._model = self._model.to(self.config.device)
        self._model.eval()

        # Apply FP16 if enabled
        if self.config.use_fp16 and self.config.device == "cuda":
            self._model = self._model.half()
            torch.backends.cudnn.benchmark = True

    def _load_pwc_model(self) -> None:
        """Load the PWC-Net model."""

        logger = _get_opticalflow_logger()
        logger.warning("PWC-Net loading not fully implemented, using fallback")

        # PWC-Net requires custom implementation or external library
        # For now, fall back to Farneback
        self._model = None
        self.config.model_type = OpticalFlowModelType.FARNEBACK

    def _preprocess_frames(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> tuple[Any, Any]:
        """Preprocess frames for optical flow computation.

        Args:
            frame1: First frame as numpy array (H, W, C) in RGB format.
            frame2: Second frame as numpy array (H, W, C) in RGB format.

        Returns:
            Tuple of preprocessed tensors.
        """
        import torch

        if self.config.model_type.is_raft:
            # RAFT expects (B, 2, C, H, W) or separate (B, C, H, W) tensors
            from torchvision.transforms.functional import resize

            # Convert to tensor and normalize
            t1 = torch.from_numpy(frame1).permute(2, 0, 1).float() / 255.0
            t2 = torch.from_numpy(frame2).permute(2, 0, 1).float() / 255.0

            # Add batch dimension
            t1 = t1.unsqueeze(0)
            t2 = t2.unsqueeze(0)

            # Resize if needed
            if self.config.effective_resolution > 0:
                h, w = frame1.shape[:2]
                scale = self.config.effective_resolution / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                t1 = resize(t1, [new_h, new_w], antialias=True)
                t2 = resize(t2, [new_h, new_w], antialias=True)

            # Move to device
            t1 = t1.to(self.config.device)
            t2 = t2.to(self.config.device)

            # Apply FP16 if enabled
            if self.config.use_fp16 and self.config.device == "cuda":
                t1 = t1.half()
                t2 = t2.half()

            return t1, t2

        return frame1, frame2

    def _postprocess_flow(
        self,
        flow: Any,
        original_shape: tuple[int, int],
    ) -> np.ndarray:
        """Post-process model output to optical flow field.

        Args:
            flow: Raw model output (tensor or numpy array).
            original_shape: Original frame shape (H, W).

        Returns:
            Optical flow as numpy array (H, W, 2).
        """
        import torch
        import torch.nn.functional as F

        if isinstance(flow, torch.Tensor):
            # Remove batch dimension if present
            if flow.dim() == 4:
                flow = flow.squeeze(0)

            # Convert to numpy
            flow = flow.permute(1, 2, 0).cpu().numpy()

        # Resize to original shape if needed
        h, w = original_shape
        if flow.shape[0] != h or flow.shape[1] != w:
            flow_tensor = torch.from_numpy(flow).permute(2, 0, 1).unsqueeze(0)
            flow_tensor = F.interpolate(
                flow_tensor,
                size=(h, w),
                mode="bilinear",
                align_corners=False,
            )
            # Scale flow values by the resize factor
            scale_h = h / flow.shape[0]
            scale_w = w / flow.shape[1]
            flow_tensor[:, 0] *= scale_w
            flow_tensor[:, 1] *= scale_h
            flow = flow_tensor.squeeze(0).permute(1, 2, 0).numpy()

        return flow.astype(np.float32)

    def compute_flow(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> np.ndarray:
        """Compute optical flow between two frames.

        Args:
            frame1: First frame as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            frame2: Second frame as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.

        Returns:
            Optical flow as numpy array (H, W, 2) with float32 values.
            flow[..., 0] is horizontal displacement, flow[..., 1] is vertical.
            Positive values indicate motion from frame1 to frame2.

        Raises:
            InferenceError: If inference fails or input is invalid.
        """
        logger = _get_opticalflow_logger()

        # Input validation
        if not isinstance(frame1, np.ndarray) or not isinstance(frame2, np.ndarray):
            raise InferenceError(
                f"Inputs must be numpy arrays, got {type(frame1).__name__} and {type(frame2).__name__}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        if frame1.ndim != 3 or frame2.ndim != 3:
            raise InferenceError(
                f"Inputs must be 3D arrays (H, W, C), got {frame1.ndim}D and {frame2.ndim}D",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        if frame1.shape != frame2.shape:
            raise InferenceError(
                f"Frames must have the same shape, got {frame1.shape} and {frame2.shape}",
                model_type=self.config.model_type.value,
                device=self.config.device,
            )

        original_shape = (frame1.shape[0], frame1.shape[1])

        # Ensure model is loaded
        if not self._is_loaded and self.config.model_type.is_deep_learning:
            self.load_model()

        logger.debug(f"Computing optical flow for frames: shape={frame1.shape}")
        start_time = time.time()

        try:
            if self.config.model_type.is_deep_learning:
                flow = self._compute_dl_flow(frame1, frame2, original_shape)
            else:
                flow = self._compute_farneback_flow(frame1, frame2)

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=1,
                inference_time_ms=elapsed_ms,
            )

            logger.debug(f"Optical flow computed in {elapsed_ms:.2f}ms")
            return flow

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str and self.config.device.startswith("cuda"):
                logger.warning("GPU out of memory, falling back to Farneback")
                clear_gpu_memory(self.config.device)
                self.config.model_type = OpticalFlowModelType.FARNEBACK
                return self._compute_farneback_flow(frame1, frame2)

            raise InferenceError(
                f"Optical flow computation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

        except Exception as e:
            log_exception("Optical flow computation failed", exception=e)
            raise InferenceError(
                f"Optical flow computation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.device,
                original_exception=e,
            ) from e

    def _compute_dl_flow(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
        original_shape: tuple[int, int],
    ) -> np.ndarray:
        """Compute optical flow using deep learning model."""
        import torch

        # Preprocess
        t1, t2 = self._preprocess_frames(frame1, frame2)

        # Inference
        with torch.no_grad():
            if self.config.model_type.is_raft:
                # RAFT returns list of flow predictions, take the last (most refined)
                flow_predictions = self._model(t1, t2)
                flow = flow_predictions[-1]
            else:
                flow = self._model(t1, t2)

        # Postprocess
        return self._postprocess_flow(flow, original_shape)

    def _compute_farneback_flow(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> np.ndarray:
        """Compute optical flow using Farneback algorithm (CPU fallback)."""
        # Convert to grayscale
        prev_gray = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
        curr_gray = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)

        # Compute optical flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray,
            curr_gray,
            None,
            pyr_scale=self.config.farneback_pyr_scale,
            levels=self.config.farneback_levels,
            winsize=self.config.farneback_window,
            iterations=self.config.farneback_iterations,
            poly_n=_DEFAULT_FARNEBACK_POLY_N,
            poly_sigma=_DEFAULT_FARNEBACK_POLY_SIGMA,
            flags=0,
        )

        return flow.astype(np.float32)

    def compute_flow_batch(
        self,
        frames1: list[np.ndarray],
        frames2: list[np.ndarray],
        batch_size: int = 4,
    ) -> list[np.ndarray]:
        """Compute optical flow for batches of frame pairs.

        Args:
            frames1: List of first frames in each pair.
            frames2: List of second frames in each pair.
            batch_size: Number of pairs to process at once (for GPU efficiency).

        Returns:
            List of optical flow arrays.

        Raises:
            ValueError: If frame lists have different lengths.
            InferenceError: If inference fails.
        """
        logger = _get_opticalflow_logger()

        if len(frames1) != len(frames2):
            raise ValueError(
                f"Frame lists must have the same length, got {len(frames1)} and {len(frames2)}"
            )

        if not frames1:
            return []

        # Ensure model is loaded
        if not self._is_loaded and self.config.model_type.is_deep_learning:
            self.load_model()

        logger.info(f"Computing optical flow for {len(frames1)} frame pairs")

        flows: list[np.ndarray] = []

        # Process in batches for deep learning models
        if self.config.model_type.is_deep_learning:
            for i in range(0, len(frames1), batch_size):
                batch_f1 = frames1[i : i + batch_size]
                batch_f2 = frames2[i : i + batch_size]

                for f1, f2 in zip(batch_f1, batch_f2):
                    flow = self.compute_flow(f1, f2)
                    flows.append(flow)
        else:
            # Farneback processes one pair at a time
            for f1, f2 in zip(frames1, frames2):
                flow = self.compute_flow(f1, f2)
                flows.append(flow)

        return flows

    def visualize_flow(
        self,
        flow: np.ndarray,
        frame: np.ndarray | None = None,
    ) -> np.ndarray:
        """Visualize optical flow as a color-coded image.

        Args:
            flow: Optical flow array (H, W, 2).
            frame: Optional reference frame to overlay flow on.

        Returns:
            RGB visualization of the optical flow.

        Raises:
            ValueError: If flow array has invalid shape.
        """
        # Input validation
        if not isinstance(flow, np.ndarray):
            raise ValueError(f"flow must be a numpy array, got {type(flow).__name__}")
        if flow.ndim != 3 or flow.shape[2] != 2:
            raise ValueError(f"flow must have shape (H, W, 2), got {flow.shape}")
        if frame is not None and frame.shape[:2] != flow.shape[:2]:
            raise ValueError(
                f"frame shape {frame.shape[:2]} doesn't match flow shape {flow.shape[:2]}"
            )

        # Compute magnitude and angle
        magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])

        # Normalize magnitude for visualization
        magnitude = magnitude / magnitude.max() if magnitude.max() > 0 else np.zeros_like(magnitude)

        # Create HSV image
        hsv = np.zeros((flow.shape[0], flow.shape[1], 3), dtype=np.uint8)
        hsv[..., 0] = angle * 180 / np.pi / 2  # Hue = direction
        hsv[..., 1] = 255  # Saturation = full
        hsv[..., 2] = (magnitude * 255).astype(np.uint8)  # Value = magnitude

        # Convert to RGB
        flow_vis = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # Overlay on frame if provided
        if frame is not None:
            alpha = 0.5
            flow_vis = cv2.addWeighted(frame, alpha, flow_vis, 1 - alpha, 0)

        return flow_vis

    def __call__(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
    ) -> np.ndarray:
        """Compute optical flow (callable interface).

        Args:
            frame1: First frame.
            frame2: Second frame.

        Returns:
            Optical flow array.
        """
        return self.compute_flow(frame1, frame2)

    def __enter__(self) -> OpticalFlowEngine:
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
        logger = _get_opticalflow_logger()
        if self._model is not None:
            del self._model
            self._model = None
        self._is_loaded = False

        # Clear GPU cache if using CUDA
        if self.config.device.startswith("cuda"):
            clear_gpu_memory(self.config.device)

        logger.debug("OpticalFlowEngine resources released")


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_opticalflow_engine(
    model_type: str = "raft_small",
    device: str = "auto",
    **kwargs: Any,
) -> OpticalFlowEngine:
    """Create an optical flow engine with the specified configuration.

    Args:
        model_type: Model type string (raft_large, raft_small, farneback, etc.).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        **kwargs: Additional OpticalFlowConfig field values.

    Returns:
        Configured OpticalFlowEngine instance.
    """
    config = OpticalFlowConfig(
        model_type=OpticalFlowModelType.from_string(model_type),
        device=device,
        **kwargs,
    )
    return OpticalFlowEngine(config=config)


def compute_optical_flow(
    frame1: np.ndarray,
    frame2: np.ndarray,
    model_type: str = "raft_small",
    device: str = "auto",
) -> np.ndarray:
    """Compute optical flow between two frames (convenience function).

    Args:
        frame1: First frame as numpy array (H, W, C) in RGB format.
        frame2: Second frame as numpy array (H, W, C) in RGB format.
        model_type: Model type string.
        device: Device for inference.

    Returns:
        Optical flow as numpy array.
    """
    with create_opticalflow_engine(model_type=model_type, device=device) as engine:
        return engine.compute_flow(frame1, frame2)


__all__ = [
    # Classes
    "OpticalFlowEngine",
    "OpticalFlowConfig",
    "OpticalFlowModelType",
    # Exceptions
    "OpticalFlowError",
    "ModelLoadError",
    "InferenceError",
    # Functions
    "create_opticalflow_engine",
    "compute_optical_flow",
    # Constants
    "_DEFAULT_RAFT_RESOLUTION",
    "_DEFAULT_PWC_RESOLUTION",
    "_DEFAULT_FARNEBACK_PYR_SCALE",
    "_DEFAULT_FARNEBACK_LEVELS",
    "_DEFAULT_FARNEBACK_WINDOW",
    "_DEFAULT_FARNEBACK_ITERATIONS",
]
