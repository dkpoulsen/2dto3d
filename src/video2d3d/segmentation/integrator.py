"""Integration module for combining segmentation with depth estimation.

This module provides functionality to integrate semantic segmentation masks
with depth estimation results for improved 3D object separation and depth
boundary refinement.

Key features:
- Edge-aware depth smoothing using segmentation boundaries
- Object-level depth consistency
- Boundary sharpening using segmentation edges
- Depth refinement at object boundaries
- 3D separation enhancement using object masks
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
_DEFAULT_SMOOTHING_STRENGTH: float = 0.5
_DEFAULT_BOUNDARY_SHARPNESS: float = 1.5
_DEFAULT_EDGE_DILATION: int = 3
_DEFAULT_MIN_OBJECT_DEPTH_VARIANCE: float = 0.01

# Edge detection constants (shared with main segmentation module)
_CANNY_LOW_THRESHOLD = 50
_CANNY_HIGH_THRESHOLD = 150

# Bilateral filter constants
_BILATERAL_FILTER_DIAMETER = -1  # Auto-compute from sigmaSpace
_BILATERAL_SIGMA_SPACE = 5.0
_EDGE_DILATION_KERNEL_SIZE = 5
_EDGE_DILATION_ITERATIONS = 2
_EDGE_STRENGTH_MULTIPLIER = 2.0


class BoundaryPreservationMethod(Enum):
    """Methods for preserving depth boundaries."""

    EDGE_WEIGHTED = "edge_weighted"  # Weight smoothing by edge strength
    MASK_GUIDED = "mask_guided"  # Use mask boundaries as hard constraints
    JOINT_BILATERAL = "joint_bilateral"  # Joint bilateral filtering
    NONE = "none"  # No boundary preservation


class DepthRefinementMethod(Enum):
    """Methods for refining depth using segmentation."""

    BOUNDARY_SHARPENING = "boundary_sharpening"  # Sharpen depth at boundaries
    OBJECT_SMOOTHING = "object_smoothing"  # Smooth within objects
    EDGE_AWARE_FILTER = "edge_aware_filter"  # Edge-aware filtering
    COMBINED = "combined"  # Combine multiple methods


@dataclass
class IntegrationConfig:
    """Configuration for depth-segmentation integration.

    Attributes:
        boundary_preservation: Method for preserving depth boundaries.
        depth_refinement: Method for refining depth using segmentation.
        smoothing_strength: Strength of smoothing (0.0 to 1.0).
        boundary_sharpness: Sharpness factor for boundaries (1.0 = no change).
        edge_dilation: Pixels to dilate edges for boundary region.
        min_object_depth_variance: Minimum variance to consider depth different.
        preserve_sharp_boundaries: Keep sharp boundaries at mask edges.
        smooth_within_objects: Apply smoothing within object regions.
        use_weighted_boundaries: Use soft weights at boundaries.
    """

    boundary_preservation: str = "edge_weighted"
    depth_refinement: str = "combined"
    smoothing_strength: float = _DEFAULT_SMOOTHING_STRENGTH
    boundary_sharpness: float = _DEFAULT_BOUNDARY_SHARPNESS
    edge_dilation: int = _DEFAULT_EDGE_DILATION
    min_object_depth_variance: float = _DEFAULT_MIN_OBJECT_DEPTH_VARIANCE
    preserve_sharp_boundaries: bool = True
    smooth_within_objects: bool = True
    use_weighted_boundaries: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 <= self.smoothing_strength <= 1.0:
            raise ValueError(f"smoothing_strength must be in [0, 1], got {self.smoothing_strength}")
        if self.boundary_sharpness <= 0:
            raise ValueError(f"boundary_sharpness must be positive, got {self.boundary_sharpness}")
        if self.edge_dilation < 0:
            raise ValueError(f"edge_dilation must be >= 0, got {self.edge_dilation}")

        valid_preservation = [m.value for m in BoundaryPreservationMethod]
        if self.boundary_preservation not in valid_preservation:
            raise ValueError(
                f"Invalid boundary_preservation '{self.boundary_preservation}'. "
                f"Valid options: {valid_preservation}"
            )

        valid_refinement = [m.value for m in DepthRefinementMethod]
        if self.depth_refinement not in valid_refinement:
            raise ValueError(
                f"Invalid depth_refinement '{self.depth_refinement}'. "
                f"Valid options: {valid_refinement}"
            )


class IntegrationError(Exception):
    """Exception raised for integration errors."""

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


def _get_integrator_logger() -> Logger:
    """Get the integrator logger."""
    return get_logger("segmentation.integrator")


class DepthSegmentationIntegrator:
    """Integrate segmentation masks with depth maps for improved 3D.

    This class provides methods to combine semantic segmentation results
    with depth estimation to:
    1. Preserve sharp depth boundaries at object edges
    2. Smooth depth within objects for consistency
    3. Enhance 3D separation by respecting object boundaries
    4. Reduce depth bleeding across object boundaries

    Example usage:
        ```python
        # Basic usage
        integrator = DepthSegmentationIntegrator()
        refined_depth = integrator.refine(depth_map, masks)

        # With configuration
        config = IntegrationConfig(
            boundary_preservation="edge_weighted",
            smoothing_strength=0.7,
        )
        integrator = DepthSegmentationIntegrator(config=config)
        refined_depth = integrator.refine(depth_map, masks)

        # Get boundary weights for visualization
        weights = integrator.compute_boundary_weights(masks)
        ```
    """

    def __init__(
        self,
        config: IntegrationConfig | None = None,
        *,
        smoothing_strength: float = _DEFAULT_SMOOTHING_STRENGTH,
        boundary_sharpness: float = _DEFAULT_BOUNDARY_SHARPNESS,
    ) -> None:
        """Initialize the integrator.

        Args:
            config: IntegrationConfig object. If provided, other args ignored.
            smoothing_strength: Strength of smoothing within objects.
            boundary_sharpness: Sharpness factor for boundaries.
        """
        if config is not None:
            self.config = config
        else:
            self.config = IntegrationConfig(
                smoothing_strength=smoothing_strength,
                boundary_sharpness=boundary_sharpness,
            )

        self._logger = _get_integrator_logger()
        self._logger.debug(
            f"DepthSegmentationIntegrator initialized: "
            f"smoothing={self.config.smoothing_strength}, "
            f"sharpness={self.config.boundary_sharpness}"
        )

    def refine(
        self,
        depth_map: np.ndarray,
        masks: list[dict[str, Any]],
        image: np.ndarray | None = None,
    ) -> np.ndarray:
        """Refine depth map using segmentation masks.

        Args:
            depth_map: Depth map (H, W) with values in [0, 1].
            masks: List of mask dictionaries from segmenter.
            image: Optional original image for edge detection.

        Returns:
            Refined depth map (H, W) with improved boundaries.
        """
        start_time = time.time()

        try:
            h, w = depth_map.shape
            refined = depth_map.astype(np.float32)

            # Compute boundary weights
            boundary_weights = self.compute_boundary_weights(masks, (h, w))

            # Apply based on refinement method
            method = self.config.depth_refinement

            if method == DepthRefinementMethod.BOUNDARY_SHARPENING.value:
                refined = self._apply_boundary_sharpening(refined, boundary_weights)
            elif method == DepthRefinementMethod.OBJECT_SMOOTHING.value:
                refined = self._apply_object_smoothing(refined, masks, boundary_weights)
            elif method == DepthRefinementMethod.EDGE_AWARE_FILTER.value:
                refined = self._apply_edge_aware_filter(refined, boundary_weights, image)
            else:  # COMBINED
                # Apply all methods in sequence
                refined = self._apply_object_smoothing(refined, masks, boundary_weights)
                refined = self._apply_boundary_sharpening(refined, boundary_weights)
                if image is not None:
                    refined = self._apply_edge_aware_filter(refined, boundary_weights, image)

            # Ensure output is in valid range
            refined = np.clip(refined, 0.0, 1.0).astype(np.float32)

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "depth_segmentation_integration",
                elapsed_ms,
                method=method,
                num_masks=len(masks),
            )

            return refined

        except Exception as e:
            log_exception("Depth refinement failed", exception=e)
            raise IntegrationError(
                f"Depth refinement failed: {e}",
                operation="refine",
                original_exception=e,
            ) from e

    def compute_boundary_weights(
        self,
        masks: list[dict[str, Any]],
        image_shape: tuple[int, int],
    ) -> np.ndarray:
        """Compute boundary weight map from masks.

        Higher weights indicate boundary regions that should be preserved.

        Args:
            masks: List of mask dictionaries.
            image_shape: Shape of the image (H, W).

        Returns:
            Weight map (H, W) with values >= 1.0 at boundaries.
        """
        h, w = image_shape[:2]
        weights = np.ones((h, w), dtype=np.float32)

        # Get dilation kernel
        kernel_size = self.config.edge_dilation * 2 + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (kernel_size, kernel_size),
        )

        for mask in masks:
            segmentation = mask["segmentation"].astype(np.uint8) * 255

            # Dilate to get boundary region
            dilated = cv2.dilate(segmentation, kernel, iterations=1)
            boundary = dilated - segmentation

            # Apply weighted boundaries if enabled
            if self.config.use_weighted_boundaries:
                # Distance transform for soft weights
                dist = cv2.distanceTransform(255 - boundary, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
                # Invert and normalize
                boundary_weights = 1.0 + (self.config.boundary_sharpness - 1.0) * (
                    1.0 - np.clip(dist / self.config.edge_dilation, 0, 1)
                )
                weights = np.maximum(weights, boundary_weights)
            else:
                # Hard weights
                weights[boundary > 0] = np.maximum(
                    weights[boundary > 0],
                    self.config.boundary_sharpness,
                )

        return weights

    def _apply_boundary_sharpening(
        self,
        depth_map: np.ndarray,
        boundary_weights: np.ndarray,
    ) -> np.ndarray:
        """Sharpen depth at boundaries using Laplacian edge enhancement.

        Args:
            depth_map: 2D depth map (H, W) with values in [0, 1].
            boundary_weights: 2D weight map (H, W) with values >= 1.0.

        Returns:
            Sharpened depth map.
        """
        if not self.config.preserve_sharp_boundaries:
            return depth_map

        # Compute Laplacian for edge enhancement
        laplacian = cv2.Laplacian(depth_map, cv2.CV_32F)

        # Scale by boundary weights (2D only - depth_map is expected to be 2D)
        sharpening = laplacian * (boundary_weights - 1.0)

        # Apply sharpening with damping factor
        sharpened = depth_map - 0.5 * sharpening

        return sharpened.astype(np.float32)

    def _apply_object_smoothing(
        self,
        depth_map: np.ndarray,
        masks: list[dict[str, Any]],
        boundary_weights: np.ndarray,
    ) -> np.ndarray:
        """Smooth depth within objects while preserving boundaries.

        Applies Gaussian blur within each object region, with blending
        weighted by distance from boundaries.

        Args:
            depth_map: 2D depth map (H, W) with values in [0, 1].
            masks: List of mask dictionaries from segmenter.
            boundary_weights: 2D weight map (H, W) with values >= 1.0.

        Returns:
            Smoothed depth map with preserved boundaries.
        """
        if not self.config.smooth_within_objects:
            return depth_map

        h, w = depth_map.shape
        smoothed = depth_map.copy()

        # Create combined mask for object indexing
        combined_mask = np.zeros((h, w), dtype=np.int32)
        for idx, mask in enumerate(masks, start=1):
            segmentation = mask["segmentation"]
            unassigned = combined_mask == 0
            combined_mask[unassigned & segmentation] = idx

        # Compute inverse boundary weights once (higher = closer to boundary = less smoothing)
        inv_weights = 1.0 / np.maximum(boundary_weights, 1.0)

        # Pre-compute Gaussian blur once for efficiency
        kernel_size = int(11 * self.config.smoothing_strength)
        if kernel_size % 2 == 0:
            kernel_size += 1

        if kernel_size >= 3:
            local_smoothed = cv2.GaussianBlur(depth_map, (kernel_size, kernel_size), 0)

            # Blend based on inverse boundary weights within each object
            blend = self.config.smoothing_strength * inv_weights
            for idx in range(1, len(masks) + 1):
                object_mask = combined_mask == idx
                if object_mask.any():
                    smoothed = np.where(
                        object_mask,
                        depth_map * (1 - blend) + local_smoothed * blend,
                        smoothed,
                    )

        return smoothed.astype(np.float32)

    def _apply_edge_aware_filter(
        self,
        depth_map: np.ndarray,
        boundary_weights: np.ndarray,
        image: np.ndarray | None,
    ) -> np.ndarray:
        """Apply edge-aware filtering using bilateral filter.

        Uses image edges to guide depth smoothing, preserving edges
        that correspond to strong image gradients.

        Args:
            depth_map: 2D depth map (H, W) with values in [0, 1].
            boundary_weights: 2D weight map (H, W) with values >= 1.0.
            image: Optional RGB image for edge detection.

        Returns:
            Edge-aware smoothed depth map.
        """
        if image is None:
            return depth_map

        # Convert image to grayscale for edge detection - handle both RGB and grayscale
        if image.ndim == 3 and image.shape[2] >= 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)
        elif image.ndim == 2:
            gray = image.astype(np.float32)
        else:
            # Fallback for unexpected formats
            gray = (
                image[:, :, 0].astype(np.float32) if image.ndim == 3 else image.astype(np.float32)
            )

        # Normalize grayscale
        gray = gray / 255.0

        # Compute edge strength using Canny with module constants
        edges = cv2.Canny(
            (gray * 255).astype(np.uint8),
            _CANNY_LOW_THRESHOLD,
            _CANNY_HIGH_THRESHOLD,
        )
        edge_strength = edges.astype(np.float32) / 255.0

        # Dilate edges to create edge regions
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (_EDGE_DILATION_KERNEL_SIZE, _EDGE_DILATION_KERNEL_SIZE),
        )
        edge_strength = cv2.dilate(edge_strength, kernel, iterations=_EDGE_DILATION_ITERATIONS)

        # Combine with boundary weights
        np.maximum(
            boundary_weights,
            1.0 + edge_strength * _EDGE_STRENGTH_MULTIPLIER,
        )

        # Apply bilateral filtering with module constants
        sigma_color = 0.1 * (1.0 - self.config.smoothing_strength)
        smoothed = cv2.bilateralFilter(
            depth_map,
            d=_BILATERAL_FILTER_DIAMETER,
            sigmaColor=sigma_color,
            sigmaSpace=_BILATERAL_SIGMA_SPACE,
        )

        # Blend based on edge strength (less smoothing where edges are strong)
        blend = 1.0 - edge_strength * self.config.smoothing_strength
        result = depth_map * (1 - blend) + smoothed * blend

        return result.astype(np.float32)

    def separate_objects_3d(
        self,
        depth_map: np.ndarray,
        masks: list[dict[str, Any]],
        separation_strength: float = 1.0,
    ) -> np.ndarray:
        """Enhance 3D separation between objects using segmentation.

        This method adjusts depth values to increase the perceived separation
        between different objects identified by segmentation.

        Args:
            depth_map: Depth map (H, W).
            masks: List of mask dictionaries.
            separation_strength: Strength of separation enhancement.

        Returns:
            Depth map with enhanced object separation.
        """
        h, w = depth_map.shape
        result = depth_map.copy()

        # Compute mean depth for each object
        object_depths = []
        for mask in masks:
            segmentation = mask["segmentation"]
            if segmentation.any():
                mean_depth = np.mean(depth_map[segmentation])
                object_depths.append((mean_depth, mask))

        if len(object_depths) < 2:
            return result

        # Sort by depth
        object_depths.sort(key=lambda x: x[0])

        # Enhance separation between adjacent depth layers
        for i in range(1, len(object_depths)):
            prev_depth, _ = object_depths[i - 1]
            curr_depth, curr_mask = object_depths[i]

            # Compute separation gap
            gap = curr_depth - prev_depth
            if gap < self.config.min_object_depth_variance:
                continue

            # Enhance depth for current object
            segmentation = curr_mask["segmentation"]
            enhancement = gap * separation_strength * 0.5
            result[segmentation] += enhancement

        return np.clip(result, 0, 1).astype(np.float32)

    def get_object_depth_layers(
        self,
        depth_map: np.ndarray,
        masks: list[dict[str, Any]],
    ) -> list[tuple[np.ndarray, float]]:
        """Get depth layers for each segmented object.

        Args:
            depth_map: Depth map (H, W).
            masks: List of mask dictionaries.

        Returns:
            List of (mask, mean_depth) tuples sorted by depth.
        """
        layers = []

        for mask in masks:
            segmentation = mask["segmentation"]
            if segmentation.any():
                mean_depth = np.mean(depth_map[segmentation])
                layers.append((segmentation.astype(np.uint8), mean_depth))

        layers.sort(key=lambda x: x[1])
        return layers


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_integrator(
    smoothing_strength: float = _DEFAULT_SMOOTHING_STRENGTH,
    boundary_sharpness: float = _DEFAULT_BOUNDARY_SHARPNESS,
    **kwargs: float | int | bool | str,
) -> DepthSegmentationIntegrator:
    """Create an integrator with the specified configuration.

    Args:
        smoothing_strength: Strength of smoothing within objects.
        boundary_sharpness: Sharpness factor for boundaries.
        **kwargs: Additional IntegrationConfig field values.

    Returns:
        Configured DepthSegmentationIntegrator instance.
    """
    config = IntegrationConfig(
        smoothing_strength=smoothing_strength,
        boundary_sharpness=boundary_sharpness,
        **kwargs,  # type: ignore[arg-type]
    )
    return DepthSegmentationIntegrator(config=config)


def refine_depth_with_segmentation(
    depth_map: np.ndarray,
    masks: list[dict[str, Any]],
    smoothing: float = _DEFAULT_SMOOTHING_STRENGTH,
    sharpen: float = _DEFAULT_BOUNDARY_SHARPNESS,
) -> np.ndarray:
    """Refine depth with segmentation (convenience function).

    Args:
        depth_map: Depth map (H, W).
        masks: List of mask dictionaries.
        smoothing: Smoothing strength.
        sharpen: Boundary sharpness.

    Returns:
        Refined depth map.
    """
    integrator = create_integrator(
        smoothing_strength=smoothing,
        boundary_sharpness=sharpen,
    )
    return integrator.refine(depth_map, masks)


__all__ = [
    # Classes
    "DepthSegmentationIntegrator",
    "IntegrationConfig",
    # Enums
    "BoundaryPreservationMethod",
    "DepthRefinementMethod",
    # Exceptions
    "IntegrationError",
    # Functions
    "create_integrator",
    "refine_depth_with_segmentation",
    # Constants
    "_DEFAULT_SMOOTHING_STRENGTH",
    "_DEFAULT_BOUNDARY_SHARPNESS",
    "_DEFAULT_EDGE_DILATION",
    "_CANNY_LOW_THRESHOLD",
    "_CANNY_HIGH_THRESHOLD",
]
