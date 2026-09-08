"""Segmentation mask post-processing and refinement module.

This module provides post-processing functionality for segmentation masks:
- Mask refinement and cleanup
- Boundary smoothing
- Hole filling for incomplete masks
- Mask merging and filtering
- Edge extraction for depth refinement

The processor is designed to prepare segmentation masks for integration
with depth estimation for improved 3D object separation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger, log_exception, log_performance

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default values
_DEFAULT_MIN_AREA: int = 100
_DEFAULT_MAX_AREA: int = 10000000  # 10M pixels
_DEFAULT_MORPHOLOGY_KERNEL_SIZE: int = 5
_DEFAULT_EDGE_DILATION_ITERATIONS: int = 2
_DEFAULT_BOUNDARY_WIDTH: int = 3
_DEFAULT_GAUSSIAN_KERNEL_SIZE: int = 5
_VALID_HOLE_FILLING_METHODS: tuple[str, ...] = ("morphology", "flood_fill")


class MaskRefinementMethod(Enum):
    """Available mask refinement methods."""

    MORPHOLOGY = "morphology"  # Morphological operations (opening/closing)
    CONTOUR = "contour"  # Contour-based refinement
    WATERSHED = "watershed"  # Watershed-based separation
    NONE = "none"  # No refinement


class BoundaryType(Enum):
    """Types of boundaries to extract."""

    INNER = "inner"  # Inner boundary (erosion-based)
    OUTER = "outer"  # Outer boundary (dilation-based)
    BOTH = "both"  # Both inner and outer


@dataclass
class SegmentationProcessorConfig:
    """Configuration for segmentation mask processing.

    Attributes:
        min_mask_area: Minimum area for valid masks (smaller removed).
        max_mask_area: Maximum area for valid masks (larger removed).
        enable_hole_filling: Fill holes inside masks.
        hole_filling_method: Method for hole filling.
        enable_morphology: Apply morphological operations.
        morphology_kernel_size: Kernel size for morphology.
        enable_boundary_extraction: Extract mask boundaries.
        boundary_width: Width of boundary region in pixels.
        enable_smoothing: Smooth mask boundaries.
        smoothing_iterations: Number of smoothing iterations.
        merge_overlapping: Merge overlapping masks.
        overlap_threshold: IoU threshold for merging.
    """

    min_mask_area: int = _DEFAULT_MIN_AREA
    max_mask_area: int = _DEFAULT_MAX_AREA
    enable_hole_filling: bool = True
    hole_filling_method: str = "morphology"
    enable_morphology: bool = True
    morphology_kernel_size: int = _DEFAULT_MORPHOLOGY_KERNEL_SIZE
    enable_boundary_extraction: bool = True
    boundary_width: int = _DEFAULT_BOUNDARY_WIDTH
    enable_smoothing: bool = True
    smoothing_iterations: int = 2
    merge_overlapping: bool = False
    overlap_threshold: float = 0.5

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.min_mask_area < 0:
            raise ValueError(f"min_mask_area must be >= 0, got {self.min_mask_area}")
        if self.max_mask_area <= self.min_mask_area:
            raise ValueError(
                f"max_mask_area ({self.max_mask_area}) must be > min_mask_area ({self.min_mask_area})"
            )
        if self.morphology_kernel_size < 1:
            raise ValueError(
                f"morphology_kernel_size must be >= 1, got {self.morphology_kernel_size}"
            )
        if self.boundary_width < 1:
            raise ValueError(f"boundary_width must be >= 1, got {self.boundary_width}")
        if not 0.0 <= self.overlap_threshold <= 1.0:
            raise ValueError(f"overlap_threshold must be in [0, 1], got {self.overlap_threshold}")
        if self.hole_filling_method not in _VALID_HOLE_FILLING_METHODS:
            raise ValueError(
                f"hole_filling_method must be one of {_VALID_HOLE_FILLING_METHODS}, "
                f"got {self.hole_filling_method!r}"
            )


class SegmentationProcessorError(Exception):
    """Exception raised for segmentation processing errors."""

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.operation = operation
        self.original_exception = original_exception


def _get_processor_logger() -> Logger:
    """Get the segmentation processor logger."""
    return get_logger("segmentation.processor")


class SegmentationProcessor:
    """Process and refine segmentation masks.

    This class provides a pipeline for refining raw segmentation masks
    to prepare them for integration with depth estimation.

    Example usage:
        ```python
        # Basic usage
        processor = SegmentationProcessor()
        refined_masks = processor.process(masks, image_shape)

        # With configuration
        config = SegmentationProcessorConfig(
            enable_hole_filling=True,
            enable_boundary_extraction=True,
        )
        processor = SegmentationProcessor(config=config)
        refined_masks = processor.process(masks, image_shape)

        # Extract boundaries for depth refinement
        boundaries = processor.extract_boundaries(refined_masks, image_shape)
        ```
    """

    def __init__(
        self,
        config: SegmentationProcessorConfig | None = None,
        *,
        min_mask_area: int = _DEFAULT_MIN_AREA,
        enable_hole_filling: bool = True,
        enable_boundary_extraction: bool = True,
    ) -> None:
        """Initialize the segmentation processor.

        Args:
            config: SegmentationProcessorConfig object. If provided, other args ignored.
            min_mask_area: Minimum area for valid masks.
            enable_hole_filling: Fill holes inside masks.
            enable_boundary_extraction: Extract mask boundaries.
        """
        if config is not None:
            self.config = config
        else:
            self.config = SegmentationProcessorConfig(
                min_mask_area=min_mask_area,
                enable_hole_filling=enable_hole_filling,
                enable_boundary_extraction=enable_boundary_extraction,
            )

        self._logger = _get_processor_logger()
        self._logger.debug(
            f"SegmentationProcessor initialized: "
            f"min_area={self.config.min_mask_area}, "
            f"hole_fill={self.config.enable_hole_filling}"
        )

    def process(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
    ) -> list[dict[str, Any]]:
        """Process masks through the refinement pipeline.

        The pipeline applies operations in the following order:
        1. Filter by area
        2. Hole filling
        3. Morphological refinement
        4. Smoothing
        5. Boundary extraction

        Args:
            masks: List of mask dictionaries from segmenter.
            image_shape: Shape of the original image (H, W).

        Returns:
            Refined list of mask dictionaries.
        """
        start_time = time.time()

        try:
            # Step 1: Filter by area
            filtered_masks = self._filter_by_area(masks)

            # Step 2: Fill holes
            if self.config.enable_hole_filling:
                filtered_masks = [self._fill_holes(m) for m in filtered_masks]

            # Step 3: Morphological refinement
            if self.config.enable_morphology:
                filtered_masks = [self._apply_morphology(m) for m in filtered_masks]

            # Step 4: Smooth boundaries
            if self.config.enable_smoothing:
                filtered_masks = [
                    self._smooth_boundaries(m, i) for i, m in enumerate(filtered_masks)
                ]

            # Step 5: Extract boundaries
            if self.config.enable_boundary_extraction:
                filtered_masks = [self._extract_boundaries(m) for m in filtered_masks]

            # Step 6: Merge overlapping if enabled
            if self.config.merge_overlapping:
                filtered_masks = self._merge_overlapping_masks(filtered_masks)

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "segmentation_processing",
                elapsed_ms,
                num_masks=len(filtered_masks),
                hole_filling=self.config.enable_hole_filling,
                morphology=self.config.enable_morphology,
            )

            return filtered_masks

        except Exception as e:
            log_exception("Mask processing failed", exception=e)
            raise SegmentationProcessorError(
                f"Mask processing failed: {e}",
                operation="process",
                original_exception=e,
            ) from e

    def _filter_by_area(self, masks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter masks by area."""
        return [
            m
            for m in masks
            if self.config.min_mask_area <= m.get("area", 0) <= self.config.max_mask_area
        ]

    def _fill_holes(self, mask: dict[str, Any]) -> dict[str, Any]:
        """Fill holes inside a mask."""
        segmentation = mask["segmentation"].astype(np.uint8)

        if self.config.hole_filling_method == "morphology":
            # Use morphological closing
            kernel = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (self.config.morphology_kernel_size, self.config.morphology_kernel_size),
            )
            filled = cv2.morphologyEx(segmentation, cv2.MORPH_CLOSE, kernel)
        else:
            # Use flood fill
            filled = segmentation.copy()
            h, w = filled.shape
            # Flood fill from corners to find background
            cv2.floodFill(filled, None, (0, 0), 255)
            # Invert filled areas (holes become foreground)
            filled = cv2.bitwise_not(filled)
            # Combine with original
            filled = cv2.bitwise_or(segmentation * 255, filled)

        # Update mask
        result = mask.copy()
        result["segmentation"] = filled.astype(bool)
        result["area"] = int(np.sum(filled > 0))
        return result

    def _apply_morphology(self, mask: dict[str, Any]) -> dict[str, Any]:
        """Apply morphological operations for refinement."""
        segmentation = mask["segmentation"].astype(np.uint8) * 255

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.config.morphology_kernel_size, self.config.morphology_kernel_size),
        )

        # Opening to remove noise
        opened = cv2.morphologyEx(segmentation, cv2.MORPH_OPEN, kernel)
        # Closing to fill small gaps
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

        result = mask.copy()
        result["segmentation"] = closed.astype(bool)
        return result

    def _smooth_boundaries(
        self,
        mask: dict[str, Any],
        mask_idx: int,
    ) -> dict[str, Any]:
        """Smooth mask boundaries using Gaussian blur.

        Args:
            mask: Mask dictionary with 'segmentation' key.
            mask_idx: Index of mask (unused, for potential future use).

        Returns:
            Updated mask dictionary with smoothed segmentation.
        """
        segmentation = mask["segmentation"].astype(np.float32)

        for _ in range(self.config.smoothing_iterations):
            blurred = cv2.GaussianBlur(
                segmentation,
                (_DEFAULT_GAUSSIAN_KERNEL_SIZE, _DEFAULT_GAUSSIAN_KERNEL_SIZE),
                0,
            )
            segmentation = blurred

        # Re-threshold to get binary mask
        smoothed = (segmentation > 0.5).astype(np.uint8)

        result = mask.copy()
        result["segmentation"] = smoothed.astype(bool)
        return result

    def _extract_boundaries(self, mask: dict[str, Any]) -> dict[str, Any]:
        segmentation = mask["segmentation"].astype(np.uint8) * 255

        # Dilate and subtract to get boundary
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.config.boundary_width * 2 + 1, self.config.boundary_width * 2 + 1),
        )

        dilated = cv2.dilate(segmentation, kernel, iterations=_DEFAULT_EDGE_DILATION_ITERATIONS)
        boundary = dilated - segmentation

        result = mask.copy()
        result["boundary"] = boundary.astype(bool)
        return result

    def _merge_overlapping_masks(
        self,
        masks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge masks with high overlap."""
        if len(masks) <= 1:
            return masks

        merged = []
        used = set()

        for i, mask1 in enumerate(masks):
            if i in used:
                continue

            seg1 = mask1["segmentation"]
            merged_mask = mask1.copy()
            merged_seg = seg1.copy()

            for j, mask2 in enumerate(masks[i + 1 :], start=i + 1):
                if j in used:
                    continue

                seg2 = mask2["segmentation"]

                # Compute IoU
                intersection = np.sum(seg1 & seg2)
                union = np.sum(seg1 | seg2)
                iou = intersection / max(union, 1)

                if iou >= self.config.overlap_threshold:
                    # Merge masks
                    merged_seg = merged_seg | seg2
                    used.add(j)

            merged_mask["segmentation"] = merged_seg
            merged_mask["area"] = int(np.sum(merged_seg))
            merged.append(merged_mask)
            used.add(i)

        return merged

    def _get_morphology_kernel(self):
        """Build the morphological kernel from the configured size."""
        return cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (self.config.morphology_kernel_size, self.config.morphology_kernel_size),
        )

    def extract_boundaries(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
        boundary_type: BoundaryType = BoundaryType.BOTH,
    ) -> np.ndarray:
        """Extract all boundaries from masks into a single map.

        Args:
            masks: List of mask dictionaries.
            image_shape: Shape of the image (H, W).
            boundary_type: Type of boundaries to extract.

        Returns:
            Binary boundary map (H, W) where True indicates boundaries.
        """
        h, w = image_shape[:2]
        boundaries = np.zeros((h, w), dtype=np.uint8)

        kernel_size = self.config.boundary_width * 2 + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )

        for mask in masks:
            segmentation = mask["segmentation"].astype(np.uint8) * 255

            if boundary_type in (BoundaryType.INNER, BoundaryType.BOTH):
                # Inner boundary: erode and subtract
                eroded = cv2.erode(segmentation, kernel, iterations=1)
                inner = segmentation - eroded
                boundaries = cv2.bitwise_or(boundaries, inner)

            if boundary_type in (BoundaryType.OUTER, BoundaryType.BOTH):
                # Outer boundary: dilate and subtract
                dilated = cv2.dilate(segmentation, kernel, iterations=1)
                outer = dilated - segmentation
                boundaries = cv2.bitwise_or(boundaries, outer)

        return boundaries.astype(bool)

    def create_weight_map(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
        boundary_weight: float = 2.0,
    ) -> np.ndarray:
        """Create a weight map emphasizing boundaries.

        This is useful for depth refinement where boundaries should be
        preserved more strongly than interior regions.

        Args:
            masks: List of mask dictionaries.
            image_shape: Shape of the image (H, W).
            boundary_weight: Weight multiplier for boundary regions.

        Returns:
            Weight map (H, W) with values >= 1.0.
        """
        h, w = image_shape[:2]
        weight_map = np.ones((h, w), dtype=np.float32)

        boundaries = self.extract_boundaries(masks, image_shape)
        weight_map[boundaries] = boundary_weight

        return weight_map


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_segmentation_processor(
    min_mask_area: int = _DEFAULT_MIN_AREA,
    enable_hole_filling: bool = True,
    enable_boundary_extraction: bool = True,
    **kwargs: int | bool | float | str,
) -> SegmentationProcessor:
    """Create a segmentation processor with the specified configuration.

    Args:
        min_mask_area: Minimum area for valid masks.
        enable_hole_filling: Fill holes inside masks.
        enable_boundary_extraction: Extract mask boundaries.
        **kwargs: Additional SegmentationProcessorConfig field values.

    Returns:
        Configured SegmentationProcessor instance.
    """
    config = SegmentationProcessorConfig(
        min_mask_area=min_mask_area,
        enable_hole_filling=enable_hole_filling,
        enable_boundary_extraction=enable_boundary_extraction,
        **kwargs,  # type: ignore[arg-type]
    )
    return SegmentationProcessor(config=config)


def process_segmentation_masks(
    masks: list[dict[str, Any]],
    image_shape: tuple[int, int],
    *,
    min_area: int = _DEFAULT_MIN_AREA,
    fill_holes: bool = True,
    extract_boundaries: bool = True,
) -> list[dict[str, Any]]:
    """Process masks with default settings (convenience function).

    Args:
        masks: List of mask dictionaries.
        image_shape: Shape of the image (H, W).
        min_area: Minimum mask area.
        fill_holes: Fill holes inside masks.
        extract_boundaries: Extract boundary information.

    Returns:
        Refined list of mask dictionaries.
    """
    processor = create_segmentation_processor(
        min_mask_area=min_area,
        enable_hole_filling=fill_holes,
        enable_boundary_extraction=extract_boundaries,
    )
    return processor.process(masks, image_shape)


__all__ = [
    # Classes
    "SegmentationProcessor",
    "SegmentationProcessorConfig",
    # Enums
    "MaskRefinementMethod",
    "BoundaryType",
    # Exceptions
    "SegmentationProcessorError",
    # Functions
    "create_segmentation_processor",
    "process_segmentation_masks",
    # Constants
    "_DEFAULT_MIN_AREA",
    "_DEFAULT_MAX_AREA",
    "_DEFAULT_MORPHOLOGY_KERNEL_SIZE",
    "_DEFAULT_BOUNDARY_WIDTH",
    "_DEFAULT_GAUSSIAN_KERNEL_SIZE",
    "_VALID_HOLE_FILLING_METHODS",
]
