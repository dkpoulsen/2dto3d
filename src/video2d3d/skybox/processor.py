"""Sky depth processing module for proper depth assignment.

This module provides the SkyProcessor class that modifies depth maps to
properly handle sky and background planes, avoiding 3D artifacts in
outdoor scenes.

Key features:
- Assign maximum depth to sky regions
- Apply gradient depth in sky for realism
- Smooth transitions at sky boundaries
- Integration with existing depth processing pipeline
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.skybox.config import (
    SkyboxConfig,
    SkyDepthConfig,
    SkyDepthMode,
)
from video2d3d.skybox.detector import SkyDetectionResult, SkyDetector
from video2d3d.utils.logger import get_logger, log_exception, log_performance

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Gaussian blur kernel size for boundary smoothing
_BOUNDARY_BLUR_KERNEL: int = 15

# Minimum depth value for depth map normalization
_MIN_DEPTH_VALUE: float = 0.0
_MAX_DEPTH_VALUE: float = 1.0


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SkyProcessingError(Exception):
    """Exception raised for sky processing errors."""

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

    def __str__(self) -> str:
        """Return a detailed error message with context."""
        parts = [super().__str__()]
        if self.operation:
            parts.append(f"Operation: {self.operation}")
        if self.original_exception:
            parts.append(
                f"Caused by: {type(self.original_exception).__name__}: {self.original_exception}"
            )
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_processor_logger() -> Logger:
    """Get the sky processor logger."""
    return get_logger("skybox.processor")


# ---------------------------------------------------------------------------
# Sky Processor
# ---------------------------------------------------------------------------


class SkyProcessor:
    """Process depth maps for proper sky/background depth assignment.

    This class takes a depth map and sky detection result, then modifies
    the depth values in sky regions to avoid 3D artifacts.

    Example usage:
        ```python
        # Basic usage
        detector = SkyDetector()
        result = detector.detect(image)
        processor = SkyProcessor()
        adjusted_depth = processor.process(depth_map, result)

        # With custom configuration
        config = SkyboxConfig(depth_config=SkyDepthConfig(depth_mode="gradient"))
        processor = SkyProcessor(config=config)
        adjusted_depth = processor.process(depth_map, result)

        # One-shot processing
        adjusted_depth = process_sky_depth(image, depth_map)
        ```
    """

    def __init__(
        self,
        config: SkyboxConfig | None = None,
    ) -> None:
        """Initialize the sky processor.

        Args:
            config: SkyboxConfig object. If None, uses defaults.
        """
        self.config = config or SkyboxConfig()
        self._logger = _get_processor_logger()
        self._logger.debug(
            f"SkyProcessor initialized: depth_mode={self.config.depth_config.depth_mode}"
        )

    def process(
        self,
        depth_map: np.ndarray,
        sky_result: SkyDetectionResult,
        image: np.ndarray | None = None,
    ) -> np.ndarray:
        """Process depth map to handle sky regions properly.

        Args:
            depth_map: Input depth map (H, W) with values in [0, 1].
            sky_result: SkyDetectionResult from SkyDetector.
            image: Optional original image for advanced processing.

        Returns:
            Adjusted depth map with proper sky depth values.

        Raises:
            SkyProcessingError: If processing fails.
        """
        start_time = time.time()

        try:
            # Validate inputs
            if not isinstance(depth_map, np.ndarray):
                raise SkyProcessingError(
                    f"depth_map must be numpy array, got {type(depth_map).__name__}",
                    operation="process",
                )
            if depth_map.ndim != 2:
                raise SkyProcessingError(
                    f"depth_map must be 2D, got {depth_map.ndim}D",
                    operation="process",
                )

            # Check confidence threshold
            if sky_result.confidence < self.config.min_confidence:
                self._logger.debug(
                    f"Sky detection confidence {sky_result.confidence:.2f} below "
                    f"threshold {self.config.min_confidence}, skipping processing"
                )
                return depth_map.copy()

            # Create output depth map
            result = depth_map.astype(np.float32).copy()

            # Get depth configuration
            depth_config = self.config.depth_config or SkyDepthConfig()

            # Create sky depth map based on mode
            sky_depth = self._create_sky_depth_map(
                depth_map.shape,
                sky_result,
                depth_config,
            )

            # Apply sky depth with boundary blending
            result = self._apply_sky_depth(
                result,
                sky_depth,
                sky_result.sky_mask,
                depth_config,
            )

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "sky_depth_processing",
                elapsed_ms,
                depth_mode=depth_config.depth_mode,
                sky_coverage=sky_result.sky_coverage,
            )

            return result

        except SkyProcessingError:
            raise
        except Exception as e:
            log_exception("Sky depth processing failed", exception=e)
            raise SkyProcessingError(
                f"Sky depth processing failed: {e}",
                operation="process",
                original_exception=e,
            ) from e

    def _create_sky_depth_map(
        self,
        shape: tuple[int, int],
        sky_result: SkyDetectionResult,
        config: SkyDepthConfig,
    ) -> np.ndarray:
        """Create depth map for sky region.

        Args:
            shape: Shape of output depth map (H, W).
            sky_result: Sky detection result.
            config: Depth configuration.

        Returns:
            Depth map for sky region.
        """
        h, w = shape
        sky_depth = np.full((h, w), config.sky_depth_value, dtype=np.float32)

        if config.depth_mode == SkyDepthMode.MAXIMUM.value:
            # Simply use maximum depth
            pass

        elif config.depth_mode == SkyDepthMode.GRADIENT.value:
            # Apply gradient from top to horizon
            if sky_result.horizon_y is not None and sky_result.horizon_y > 0:
                # Create vertical gradient
                y_coords = np.arange(h).reshape(-1, 1)

                # Normalize to [0, 1] where 0 = top, 1 = horizon
                normalized_y = np.clip(y_coords / sky_result.horizon_y, 0, 1)

                # Apply gradient (top = max depth, horizon = slightly less)
                gradient_depth = config.sky_depth_value * (
                    1 - config.gradient_strength * normalized_y
                )

                # Only apply in sky region
                sky_depth = np.where(sky_result.sky_mask, gradient_depth, sky_depth)

        elif config.depth_mode == SkyDepthMode.INVERSE_GRADIENT.value:
            # Gradient where brighter sky = farther
            if sky_result.horizon_y is not None and sky_result.horizon_y > 0:
                y_coords = np.arange(h).reshape(-1, 1)

                # Inverse: horizon = max depth, top = slightly less
                normalized_y = np.clip(y_coords / sky_result.horizon_y, 0, 1)

                gradient_depth = config.sky_depth_value * (
                    config.gradient_strength + (1 - config.gradient_strength) * normalized_y
                )

                sky_depth = np.where(sky_result.sky_mask, gradient_depth, sky_depth)

        return sky_depth

    def _apply_sky_depth(
        self,
        depth_map: np.ndarray,
        sky_depth: np.ndarray,
        sky_mask: np.ndarray,
        config: SkyDepthConfig,
    ) -> np.ndarray:
        """Apply sky depth with smooth boundary blending.

        Args:
            depth_map: Original depth map.
            sky_depth: Depth values for sky region.
            sky_mask: Binary sky mask.
            config: Depth configuration.

        Returns:
            Blended depth map.
        """
        result = depth_map.copy()

        if config.boundary_blend_pixels <= 0:
            # No blending, hard transition
            result[sky_mask] = sky_depth[sky_mask]
            return result

        # Create blend weights for smooth transition
        # Create distance-based blend weights
        # Distance transform from sky boundary for smooth blending
        dist_in_sky = cv2.distanceTransform(
            sky_mask.astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE
        )

        # Normalize distances
        blend_distance = config.boundary_blend_pixels
        blend_weight = np.clip(dist_in_sky / blend_distance, 0, 1)

        # Apply sky depth with blending
        result = np.where(
            blend_weight > 0,
            result * (1 - blend_weight) + sky_depth * blend_weight,
            result,
        )

        return result.astype(np.float32)

    def process_depth_map(
        self,
        depth_map: np.ndarray,
        image: np.ndarray,
    ) -> np.ndarray:
        """Process depth map with automatic sky detection.

        Convenience method that detects sky and processes depth in one call.

        Args:
            depth_map: Input depth map (H, W).
            image: Original RGB image for sky detection.

        Returns:
            Processed depth map.
        """
        # Detect sky
        detector = SkyDetector(config=self.config)
        sky_result = detector.detect(image)

        # Process depth
        return self.process(depth_map, sky_result, image)


# ---------------------------------------------------------------------------
# Integration Functions
# ---------------------------------------------------------------------------


def integrate_sky_depth(
    depth_map: np.ndarray,
    image: np.ndarray,
    config: SkyboxConfig | None = None,
) -> tuple[np.ndarray, SkyDetectionResult]:
    """Integrate sky detection with depth processing.

    Detects sky in image and adjusts depth map accordingly.

    Args:
        depth_map: Input depth map (H, W).
        image: Original RGB image.
        config: Optional skybox configuration.

    Returns:
        Tuple of (adjusted_depth_map, sky_detection_result).
    """
    config = config or SkyboxConfig()

    # Detect sky
    detector = SkyDetector(config=config)
    sky_result = detector.detect(image)

    # Process depth
    processor = SkyProcessor(config=config)
    adjusted_depth = processor.process(depth_map, sky_result, image)

    return adjusted_depth, sky_result


def create_sky_depth_mask(
    sky_mask: np.ndarray,
    horizon_y: int | None = None,
    max_depth: float = 1.0,
    gradient_strength: float = 0.2,
) -> np.ndarray:
    """Create a depth mask for sky region.

    Utility function to create a depth mask from a sky mask.

    Args:
        sky_mask: Binary sky mask (H, W).
        horizon_y: Y-coordinate of horizon, or None for flat depth.
        max_depth: Maximum depth value for sky.
        gradient_strength: Strength of gradient from top to horizon.

    Returns:
        Depth mask for sky region.
    """
    h, w = sky_mask.shape
    depth_mask = np.full((h, w), max_depth, dtype=np.float32)

    if horizon_y is not None and horizon_y > 0 and gradient_strength > 0:
        y_coords = np.arange(h).reshape(-1, 1)
        normalized_y = np.clip(y_coords / horizon_y, 0, 1)
        gradient_depth = max_depth * (1 - gradient_strength * normalized_y)
        depth_mask = np.where(sky_mask, gradient_depth, max_depth).astype(np.float32)

    return depth_mask


def blend_depth_at_boundary(
    depth_map: np.ndarray,
    sky_mask: np.ndarray,
    sky_depth: float = 1.0,
    blend_pixels: int = 10,
) -> np.ndarray:
    """Blend depth values at sky boundary for smooth transition.

    Args:
        depth_map: Input depth map (H, W).
        sky_mask: Binary sky mask (H, W).
        sky_depth: Depth value to assign to sky.
        blend_pixels: Width of blend region in pixels.

    Returns:
        Blended depth map.
    """
    h, w = depth_map.shape

    # Create sky depth map
    sky_depth_map = np.full((h, w), sky_depth, dtype=np.float32)

    # Distance transform for blend weights
    dist = cv2.distanceTransform((~sky_mask).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # Normalize to create blend weights
    blend_weight = np.clip(1 - dist / blend_pixels, 0, 1)

    # Blend
    result = depth_map * (1 - blend_weight) + sky_depth_map * blend_weight

    return result.astype(np.float32)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_sky_processor(**kwargs: Any) -> SkyProcessor:
    """Create a sky processor with the specified configuration.

    Args:
        **kwargs: Configuration values for SkyboxConfig.

    Returns:
        Configured SkyProcessor instance.
    """
    config = SkyboxConfig(**kwargs)
    return SkyProcessor(config=config)


def process_sky_depth(
    image: np.ndarray,
    depth_map: np.ndarray,
    method: str = "combined",
) -> np.ndarray:
    """Process depth map for sky with default settings.

    Args:
        image: Input RGB image.
        depth_map: Input depth map (H, W).
        method: Detection method ('color', 'position', 'edge', 'combined').

    Returns:
        Processed depth map.
    """
    config = SkyboxConfig(detection_method=method)
    processor = SkyProcessor(config=config)
    return processor.process_depth_map(depth_map, image)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "SkyProcessor",
    # Exceptions
    "SkyProcessingError",
    # Integration functions
    "integrate_sky_depth",
    "create_sky_depth_mask",
    "blend_depth_at_boundary",
    # Convenience functions
    "create_sky_processor",
    "process_sky_depth",
    # Constants
    "_BOUNDARY_BLUR_KERNEL",
    "_MIN_DEPTH_VALUE",
    "_MAX_DEPTH_VALUE",
]
