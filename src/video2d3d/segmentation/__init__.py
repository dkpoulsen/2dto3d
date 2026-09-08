"""Semantic segmentation module for object boundary detection.

This module provides semantic segmentation functionality using the Segment
Anything Model (SAM) from Meta AI, optimized for depth estimation improvement
and 3D object separation.

Supported models:
- SAM ViT-H (highest quality, slower)
- SAM ViT-L (balanced)
- SAM ViT-B (fastest, lower quality)
- MobileSAM (mobile-optimized)

Key features:
- Automatic object boundary detection
- Integration with depth estimation for improved 3D separation
- Edge-aware segmentation for depth map refinement
- Support for both automatic and prompt-based segmentation
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.gpu import GPUConfig, clear_gpu_memory, select_device
from video2d3d.utils.logger import get_logger, log_exception, log_model_inference

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default model checkpoint URLs
_SAM_CHECKPOINT_URLS = {
    "vit_h": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth",
    "vit_l": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth",
    "vit_b": "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth",
}

# Default input sizes for different model variants
_SAM_DEFAULT_INPUT_SIZE = 1024


class SAMModelType(Enum):
    """Available SAM model variants."""

    VIT_H = "vit_h"  # ViT-Huge (highest quality)
    VIT_L = "vit_l"  # ViT-Large (balanced)
    VIT_B = "vit_b"  # ViT-Base (fastest)

    @classmethod
    def from_string(cls, name: str) -> SAMModelType:
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive).

        Returns:
            SAMModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        name_mapping = {
            "vit_h": cls.VIT_H,
            "vit_huge": cls.VIT_H,
            "sam_vit_h": cls.VIT_H,
            "vit_l": cls.VIT_L,
            "vit_large": cls.VIT_L,
            "sam_vit_l": cls.VIT_L,
            "vit_b": cls.VIT_B,
            "vit_base": cls.VIT_B,
            "sam_vit_b": cls.VIT_B,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown SAM model name '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def checkpoint_url(self) -> str:
        """Get the checkpoint download URL for this model."""
        return _SAM_CHECKPOINT_URLS[self.value]

    @property
    def checkpoint_filename(self) -> str:
        """Get the checkpoint filename for this model."""
        return f"sam_{self.value}.pth"


class SegmentationMode(Enum):
    """Available segmentation modes."""

    AUTOMATIC = "automatic"  # Full automatic segmentation
    EDGE_AWARE = "edge_aware"  # Edge-focused segmentation for depth boundaries
    OBJECT_CENTRIC = "object_centric"  # Focus on distinct objects


@dataclass
class SAMConfig:
    """Configuration for SAM segmentation.

    Attributes:
        model_type: Type of SAM model to use.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        checkpoint_path: Path to model checkpoint. None uses default cache.
        auto_download: Whether to automatically download models if not cached.
        input_size: Input image size for the model.
        points_per_side: Number of points per side for automatic grid sampling.
        pred_iou_thresh: IoU threshold for filtering masks.
        stability_score_thresh: Stability score threshold for mask filtering.
        min_mask_region_area: Minimum area for valid mask regions.
        use_fp16: Use half-precision for faster inference.
    """

    model_type: SAMModelType = SAMModelType.VIT_B
    device: str = "auto"
    resolved_device: str = "auto"
    checkpoint_path: Path | None = None
    auto_download: bool = True
    input_size: int = _SAM_DEFAULT_INPUT_SIZE
    points_per_side: int = 32
    pred_iou_thresh: float = 0.88
    stability_score_thresh: float = 0.95
    min_mask_region_area: int = 100
    use_fp16: bool = False

    # GPU acceleration settings
    gpu_config: GPUConfig | None = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model type
        if isinstance(self.model_type, str):
            self.model_type = SAMModelType.from_string(self.model_type)

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(
                enabled=True,
                device=self.device,
                fp16_enabled=self.use_fp16,
            )

        # Auto-detect device (store the resolved value separately so the
        # original 'auto' setting is preserved for introspection)
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            object.__setattr__(self, "resolved_device", selection.device)

        # Normalize checkpoint_path to Path
        if self.checkpoint_path is not None and isinstance(self.checkpoint_path, str):
            self.checkpoint_path = Path(self.checkpoint_path)


class SegmentationError(Exception):
    """Exception raised for segmentation errors."""

    def __init__(
        self,
        message: str,
        *,
        model_type: str | None = None,
        device: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.model_type = model_type
        self.device = device
        self.original_exception = original_exception


class ModelLoadError(SegmentationError):
    """Exception raised when model loading fails."""

    pass


class InferenceError(SegmentationError):
    """Exception raised when inference fails."""

    pass


def _get_segmentation_logger() -> Logger:
    """Get the segmentation module logger (lazy initialization)."""
    return get_logger("segmentation")


class SemanticSegmenter:
    """Semantic segmentation using SAM for object boundary detection.

    This class provides a high-level interface for semantic segmentation using
    the Segment Anything Model (SAM). It handles model loading, caching,
    preprocessing, and inference.

    The primary use case is to identify object boundaries that can be used
    to improve depth estimation and 3D separation.

    Example usage:
        ```python
        # Basic usage
        segmenter = SemanticSegmenter()
        masks = segmenter.segment(image)

        # With custom configuration
        config = SAMConfig(model_type=SAMModelType.VIT_B, device="cuda")
        segmenter = SemanticSegmenter(config=config)
        masks = segmenter.segment(image)

        # Get edges for depth refinement
        edges = segmenter.extract_boundaries(masks)
        ```
    """

    def __init__(
        self,
        config: SAMConfig | None = None,
        *,
        model_type: str | SAMModelType = "vit_b",
        device: str = "auto",
    ) -> None:
        """Initialize the semantic segmenter.

        Args:
            config: SAMConfig object. If provided, model_type and device are ignored.
            model_type: Type of SAM model (ignored if config is provided).
            device: Device for inference (ignored if config is provided).
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            if isinstance(model_type, str):
                model_type = SAMModelType.from_string(model_type)
            self.config = SAMConfig(model_type=model_type, device=device)

        # Model components (lazy loaded)
        self._sam: Any | None = None  # sam.SamPredictor or sam.SamAutomaticMaskGenerator
        self._mask_generator: Any | None = None
        self._is_loaded: bool = False

        logger = _get_segmentation_logger()
        logger.info(
            f"SemanticSegmenter initialized: model={self.config.model_type.value}, "
            f"device={self.config.resolved_device}"
        )

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    def _get_checkpoint_path(self) -> Path:
        """Get the checkpoint path, downloading if necessary."""
        if self.config.checkpoint_path is not None:
            return self.config.checkpoint_path

        # Use default cache directory
        cache_dir = Path.home() / ".cache" / "video2d3d" / "sam"
        cache_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_path = cache_dir / self.config.model_type.checkpoint_filename

        if not checkpoint_path.exists() and self.config.auto_download:
            self._download_checkpoint(checkpoint_path)

        return checkpoint_path

    def _download_checkpoint(self, checkpoint_path: Path) -> None:
        """Download the model checkpoint."""
        import urllib.request

        logger = _get_segmentation_logger()
        url = self.config.model_type.checkpoint_url

        logger.info(f"Downloading SAM checkpoint: {url}")

        try:
            urllib.request.urlretrieve(url, checkpoint_path)
            logger.info(f"Checkpoint saved to: {checkpoint_path}")
        except Exception as e:
            log_exception("Failed to download checkpoint", exception=e, url=url)
            raise ModelLoadError(
                f"Failed to download SAM checkpoint: {e}",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
                original_exception=e,
            ) from e

    def load_model(self) -> None:
        """Load the SAM model from cache or download.

        This method loads both the SAM model and creates the automatic mask
        generator for inference.

        Raises:
            ModelLoadError: If model loading fails.
        """
        logger = _get_segmentation_logger()
        logger.info(f"Loading SAM model: {self.config.model_type.value}")

        try:
            import torch
            from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

            start_time = time.time()

            # Get checkpoint path
            checkpoint_path = self._get_checkpoint_path()

            # Load SAM model
            self._sam = sam_model_registry[self.config.model_type.value](
                checkpoint=str(checkpoint_path)
            )

            # Move to device
            self._sam.to(device=self.config.resolved_device)

            # Apply FP16 if enabled
            if self.config.use_fp16 and self.config.resolved_device == "cuda":
                self._sam = self._sam.half()

            # Create mask generator
            self._mask_generator = SamAutomaticMaskGenerator(
                model=self._sam,
                points_per_side=self.config.points_per_side,
                pred_iou_thresh=self.config.pred_iou_thresh,
                stability_score_thresh=self.config.stability_score_thresh,
                min_mask_region_area=self.config.min_mask_region_area,
            )

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"SAM model loaded successfully in {elapsed_ms:.0f}ms: "
                f"{self.config.model_type.value} on {self.config.resolved_device}"
            )

            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=0,
                inference_time_ms=elapsed_ms,
                operation="model_load",
            )

        except ImportError as e:
            log_exception(
                "segment_anything package not installed. Install with: pip install segment-anything",
                exception=e,
            )
            raise ModelLoadError(
                "segment_anything package not installed. Install with: pip install segment-anything",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
                original_exception=e,
            ) from e
        except Exception as e:
            log_exception(
                "Failed to load SAM model",
                exception=e,
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
            )
            raise ModelLoadError(
                f"Failed to load SAM model '{self.config.model_type.value}': {e}",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
                original_exception=e,
            ) from e

    def segment(
        self,
        image: np.ndarray,
        mode: SegmentationMode = SegmentationMode.AUTOMATIC,
    ) -> list[dict[str, Any]]:
        """Segment an image and return masks for detected objects.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            mode: Segmentation mode to use.

        Returns:
            List of mask dictionaries, each containing:
                - 'segmentation': Binary mask (H, W) bool array
                - 'area': Area of the mask in pixels
                - 'bbox': Bounding box [x, y, w, h]
                - 'predicted_iou': Predicted IoU score
                - 'stability_score': Stability score

        Raises:
            InferenceError: If inference fails or input is invalid.
        """
        logger = _get_segmentation_logger()

        # Input validation
        if not isinstance(image, np.ndarray):
            raise InferenceError(
                f"Input must be a numpy array, got {type(image).__name__}",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
            )
        if image.ndim != 3:
            raise InferenceError(
                f"Input must be 3D array (H, W, C), got {image.ndim}D",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
            )

        # Ensure model is loaded
        if not self._is_loaded:
            self.load_model()

        if self._mask_generator is None:
            raise InferenceError(
                "Model failed to load",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
            )

        logger.debug(f"Segmenting image: shape={image.shape}, dtype={image.dtype}")
        start_time = time.time()

        try:
            # Convert RGB to BGR if needed (SAM expects RGB)
            rgb_image = image if image.shape[2] == 3 else image[:, :, :3]

            # Generate masks
            masks = self._mask_generator.generate(rgb_image)

            # Filter and sort masks based on mode
            if mode == SegmentationMode.EDGE_AWARE:
                masks = self._filter_edge_masks(masks, rgb_image)
            elif mode == SegmentationMode.OBJECT_CENTRIC:
                masks = self._filter_object_masks(masks)

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=self.config.model_type.value,
                batch_size=1,
                inference_time_ms=elapsed_ms,
                num_masks=len(masks),
            )

            logger.debug(f"Segmentation completed in {elapsed_ms:.2f}ms, found {len(masks)} masks")
            return masks

        except RuntimeError as e:
            error_str = str(e).lower()
            if "out of memory" in error_str:
                logger.warning("GPU out of memory, falling back to CPU")
                self._fallback_to_cpu()
                return self.segment(image, mode)
            raise InferenceError(
                f"Segmentation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
                original_exception=e,
            ) from e
        except Exception as e:
            log_exception("Segmentation failed", exception=e)
            raise InferenceError(
                f"Segmentation failed: {e}",
                model_type=self.config.model_type.value,
                device=self.config.resolved_device,
                original_exception=e,
            ) from e

    def _filter_edge_masks(
        self,
        masks: list[dict[str, Any]],
        image: np.ndarray,
    ) -> list[dict[str, Any]]:
        """Filter masks to focus on edge-relevant regions.

        This mode prioritizes masks that likely represent depth boundaries
        by scoring them based on overlap with detected image edges.

        Args:
            masks: List of mask dictionaries to filter.
            image: Input image (RGB or grayscale).

        Returns:
            Filtered list of masks sorted by edge overlap score.
        """
        import cv2

        # Compute image edges - handle both RGB and grayscale
        if image.ndim == 3 and image.shape[2] >= 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        elif image.ndim == 2:
            gray = image
        else:
            # Fallback: use first channel
            gray = image[:, :, 0] if image.ndim == 3 else image

        edges = cv2.Canny(gray, _CANNY_LOW_THRESHOLD, _CANNY_HIGH_THRESHOLD)

        # Score masks by edge overlap
        scored_masks = []
        for mask in masks:
            segmentation = mask["segmentation"]
            edge_overlap = np.sum(edges & segmentation)
            score = edge_overlap / max(mask["area"], 1)
            scored_masks.append((score, mask))

        # Sort by edge overlap score and return top masks
        scored_masks.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored_masks[:_MAX_EDGE_MASKS]]

    def _filter_object_masks(self, masks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter masks to focus on distinct objects.

        Keeps only masks with high quality scores and sorts by area.

        Args:
            masks: List of mask dictionaries to filter.

        Returns:
            Filtered list of masks sorted by area (largest first).
        """
        # Filter by stability score and predicted IoU
        filtered = [
            m
            for m in masks
            if m.get("stability_score", 0) > _HIGH_QUALITY_THRESHOLD
            and m.get("predicted_iou", 0) > _HIGH_QUALITY_THRESHOLD
        ]
        # Sort by area (larger objects first)
        filtered.sort(key=lambda m: m["area"], reverse=True)
        return filtered[:_MAX_OBJECT_MASKS]
        # Filter by stability score and predicted IoU
        filtered = [
            m
            for m in masks
            if m.get("stability_score", 0) > 0.9 and m.get("predicted_iou", 0) > 0.9
        ]
        # Sort by area (larger objects first)
        filtered.sort(key=lambda m: m["area"], reverse=True)
        return filtered[:30]  # Return top 30

    def extract_boundaries(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
    ) -> np.ndarray:
        """Extract object boundaries from segmentation masks.

        Args:
            masks: List of mask dictionaries from segment().
            image_shape: Shape of the original image (H, W).

        Returns:
            Binary boundary map (H, W) where True indicates boundaries.
        """
        import cv2

        h, w = image_shape[:2]
        boundaries = np.zeros((h, w), dtype=np.uint8)

        for mask in masks:
            # Convert boolean mask to 0/255 uint8 as required by findContours
            segmentation = mask["segmentation"].astype(np.uint8) * 255

            # Find contours
            contours, _ = cv2.findContours(segmentation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw contours
            cv2.drawContours(boundaries, contours, -1, 255, 1)

        return boundaries.astype(bool)

    def create_combined_mask(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
    ) -> np.ndarray:
        """Create a combined segmentation mask.

        Args:
            masks: List of mask dictionaries from segment().
            image_shape: Shape of the original image (H, W).

        Returns:
            Integer mask (H, W) where each value represents a different object.
        """
        h, w = image_shape[:2]
        combined = np.zeros((h, w), dtype=np.int32)

        for idx, mask in enumerate(masks, start=1):
            segmentation = mask["segmentation"]
            # Only assign if not already assigned
            unassigned = combined == 0
            combined[unassigned & segmentation] = idx

        return combined

    def _fallback_to_cpu(self) -> None:
        """Fall back to CPU processing when GPU fails."""
        logger = _get_segmentation_logger()

        if self.config.resolved_device == "cpu":
            logger.debug("Already on CPU, skipping fallback")
            return

        logger.warning("Falling back to CPU processing")

        if self._sam is not None:
            self._sam.to(device="cpu")
            self.config.resolved_device = "cpu"
            clear_gpu_memory()

    def close(self) -> None:
        """Release model resources."""
        logger = _get_segmentation_logger()
        if self._sam is not None:
            del self._sam
            self._sam = None
        if self._mask_generator is not None:
            del self._mask_generator
            self._mask_generator = None
        self._is_loaded = False

        # Clear GPU cache if using CUDA
        if self.config.resolved_device.startswith("cuda") or self.config.resolved_device == "auto":
            clear_gpu_memory(self.config.resolved_device)
        logger.debug("SemanticSegmenter resources released")

    def __enter__(self) -> SemanticSegmenter:
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


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_segmenter(
    model_type: str = "vit_b",
    device: str = "auto",
    **kwargs: Any,
) -> SemanticSegmenter:
    """Create a semantic segmenter with the specified configuration.

    Args:
        model_type: Model type string (vit_b, vit_l, vit_h).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        **kwargs: Additional SAMConfig field values.

    Returns:
        Configured SemanticSegmenter instance.
    """
    config = SAMConfig(
        model_type=SAMModelType.from_string(model_type),
        device=device,
        **kwargs,
    )
    return SemanticSegmenter(config=config)


def segment_image(
    image: np.ndarray,
    model_type: str = "vit_b",
    device: str = "auto",
) -> list[dict[str, Any]]:
    """Segment a single image (convenience function).

    Args:
        image: Input image as numpy array (H, W, C) in RGB format.
        model_type: Model type string.
        device: Device for inference.

    Returns:
        List of mask dictionaries.
    """
    with create_segmenter(model_type=model_type, device=device) as segmenter:
        return segmenter.segment(image)


from video2d3d.segmentation.integrator import (
    BoundaryPreservationMethod,
    DepthSegmentationIntegrator,
    IntegrationConfig,
    create_integrator,
    refine_depth_with_segmentation,
)

# Import processor and integrator components
from video2d3d.segmentation.processor import (
    MaskRefinementMethod,
    SegmentationProcessor,
    SegmentationProcessorConfig,
    create_segmentation_processor,
    process_segmentation_masks,
)

# Module-level logger for backward compatibility
logger = _get_segmentation_logger()


__all__ = [
    # Classes
    "SemanticSegmenter",
    "SAMConfig",
    "SAMModelType",
    "SegmentationMode",
    "SegmentationProcessor",
    "SegmentationProcessorConfig",
    "DepthSegmentationIntegrator",
    "IntegrationConfig",
    # Enums
    "MaskRefinementMethod",
    "BoundaryPreservationMethod",
    # Exceptions
    "SegmentationError",
    "ModelLoadError",
    "InferenceError",
    # Functions
    "create_segmenter",
    "segment_image",
    "create_segmentation_processor",
    "process_segmentation_masks",
    "create_integrator",
    "refine_depth_with_segmentation",
    "_get_segmentation_logger",
    # Constants (for advanced configuration)
    "_SAM_DEFAULT_INPUT_SIZE",
    "_CANNY_LOW_THRESHOLD",
    "_CANNY_HIGH_THRESHOLD",
    "_MAX_EDGE_MASKS",
    "_MAX_OBJECT_MASKS",
    "_HIGH_QUALITY_THRESHOLD",
]
