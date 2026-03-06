"""Skybox separation module for sky and background plane detection.

This module provides automatic detection of sky and background planes for
proper depth assignment to avoid 3D artifacts in outdoor scenes.

Key features:
- Multiple sky detection methods (color, position, edge-based, combined)
- Proper depth assignment to sky regions
- Smooth boundary transitions
- Temporal consistency for video processing

Example usage:
    ```python
    from video2d3d.skybox import SkyDetector, SkyProcessor, SkyboxConfig

    # Create configuration
    config = SkyboxConfig(
        enabled=True,
        detection_method="combined",
        min_confidence=0.3,
    )

    # Detect sky
    detector = SkyDetector(config=config)
    result = detector.detect(image)

    # Process depth map
    processor = SkyProcessor(config=config)
    adjusted_depth = processor.process(depth_map, result)

    # Or use convenience function
    from video2d3d.skybox import process_sky_depth
    adjusted_depth = process_sky_depth(image, depth_map)
    ```
"""

from __future__ import annotations

# Import configuration classes
from video2d3d.skybox.config import (
    # Enums
    SkyDetectionMethod,
    SkyDepthMode,
    # Main configuration
    SkyboxConfig,
    # Sub-configurations
    ColorDetectionConfig,
    PositionDetectionConfig,
    EdgeDetectionConfig,
    SkyDepthConfig,
    # Constants
    _DEFAULT_SKY_HUE_MIN,
    _DEFAULT_SKY_HUE_MAX,
    _DEFAULT_SKY_SATURATION_MAX,
    _DEFAULT_SKY_VALUE_MIN,
    _DEFAULT_SKY_GRADIENT_THRESHOLD,
    _DEFAULT_SKY_REGION_RATIO,
    _DEFAULT_MIN_SKY_COVERAGE,
    _DEFAULT_MAX_SKY_COVERAGE,
    _DEFAULT_HORIZON_SEARCH_RATIO,
    _DEFAULT_EDGE_THRESHOLD,
    _DEFAULT_SKY_DEPTH_VALUE,
    _DEFAULT_BOUNDARY_BLEND_PIXELS,
    _DEFAULT_MIN_CONFIDENCE,
)

# Import detector classes
from video2d3d.skybox.detector import (
    # Classes
    SkyDetector,
    SkyDetectionResult,
    # Exceptions
    SkyDetectionError,
    # Functions
    create_sky_detector,
    detect_sky,
    # Constants
    _COLOR_WEIGHT,
    _POSITION_WEIGHT,
    _EDGE_WEIGHT,
    _BLUR_KERNEL_SIZE,
    _MORPHOLOGY_KERNEL_SIZE,
)

# Import processor classes
from video2d3d.skybox.processor import (
    # Classes
    SkyProcessor,
    # Exceptions
    SkyProcessingError,
    # Functions
    integrate_sky_depth,
    create_sky_depth_mask,
    blend_depth_at_boundary,
    create_sky_processor,
    process_sky_depth,
    # Constants
    _BOUNDARY_BLUR_KERNEL,
    _MIN_DEPTH_VALUE,
    _MAX_DEPTH_VALUE,
)


# Module-level logger
def _get_skybox_module_logger():
    """Get the skybox module logger."""
    from video2d3d.utils.logger import get_logger

    return get_logger("skybox")


logger = _get_skybox_module_logger()


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Configuration
    "SkyboxConfig",
    "ColorDetectionConfig",
    "PositionDetectionConfig",
    "EdgeDetectionConfig",
    "SkyDepthConfig",
    "SkyDetectionMethod",
    "SkyDepthMode",
    # Detection
    "SkyDetector",
    "SkyDetectionResult",
    "SkyDetectionError",
    "create_sky_detector",
    "detect_sky",
    # Processing
    "SkyProcessor",
    "SkyProcessingError",
    "integrate_sky_depth",
    "create_sky_depth_mask",
    "blend_depth_at_boundary",
    "create_sky_processor",
    "process_sky_depth",
    # Logger
    "logger",
    # Configuration constants
    "_DEFAULT_SKY_HUE_MIN",
    "_DEFAULT_SKY_HUE_MAX",
    "_DEFAULT_SKY_SATURATION_MAX",
    "_DEFAULT_SKY_VALUE_MIN",
    "_DEFAULT_SKY_GRADIENT_THRESHOLD",
    "_DEFAULT_SKY_REGION_RATIO",
    "_DEFAULT_MIN_SKY_COVERAGE",
    "_DEFAULT_MAX_SKY_COVERAGE",
    "_DEFAULT_HORIZON_SEARCH_RATIO",
    "_DEFAULT_EDGE_THRESHOLD",
    "_DEFAULT_SKY_DEPTH_VALUE",
    "_DEFAULT_BOUNDARY_BLEND_PIXELS",
    "_DEFAULT_MIN_CONFIDENCE",
    # Detection constants
    "_COLOR_WEIGHT",
    "_POSITION_WEIGHT",
    "_EDGE_WEIGHT",
    "_BLUR_KERNEL_SIZE",
    "_MORPHOLOGY_KERNEL_SIZE",
    # Processing constants
    "_BOUNDARY_BLUR_KERNEL",
    "_MIN_DEPTH_VALUE",
    "_MAX_DEPTH_VALUE",
]
