"""Configuration for sky/background plane detection and processing.

This module provides configuration dataclasses for the skybox separation
feature, which detects sky and background planes for proper depth assignment
to avoid 3D artifacts in outdoor scenes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SkyDetectionMethod(Enum):
    """Available sky detection methods."""

    COLOR = "color"  # Color-based detection (blue sky gradients)
    POSITION = "position"  # Position-based detection (upper regions)
    EDGE = "edge"  # Edge-based detection (horizon line)
    COMBINED = "combined"  # Combine multiple methods (default)


class SkyDepthMode(Enum):
    """How to assign depth to detected sky regions."""

    MAXIMUM = "maximum"  # Assign maximum depth (far plane)
    GRADIENT = "gradient"  # Apply gradient from top to horizon
    INVERSE_GRADIENT = "inverse_gradient"  # Brighter sky = farther


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Color-based detection defaults
_DEFAULT_SKY_HUE_MIN: float = 195.0  # Min hue for blue sky (in degrees, 0-360)
_DEFAULT_SKY_HUE_MAX: float = 255.0  # Max hue for blue sky
_DEFAULT_SKY_SATURATION_MAX: float = 0.6  # Max saturation for sky (low = washed out)
_DEFAULT_SKY_VALUE_MIN: float = 0.4  # Min brightness value
_DEFAULT_SKY_GRADIENT_THRESHOLD: float = 0.15  # Threshold for vertical gradient

# Position-based detection defaults
_DEFAULT_SKY_REGION_RATIO: float = 0.5  # Top 50% of image considered sky candidate
_DEFAULT_MIN_SKY_COVERAGE: float = 0.05  # Minimum 5% of image for valid sky
_DEFAULT_MAX_SKY_COVERAGE: float = 0.7  # Maximum 70% of image for sky

# Edge-based detection defaults
_DEFAULT_HORIZON_SEARCH_RATIO: float = 0.3  # Search bottom 30% for horizon
_DEFAULT_EDGE_THRESHOLD: float = 50.0  # Canny edge threshold

# Depth assignment defaults
_DEFAULT_SKY_DEPTH_VALUE: float = 1.0  # Maximum depth for sky (normalized)
_DEFAULT_BOUNDARY_BLEND_PIXELS: int = 10  # Pixels for smooth transition
_DEFAULT_MIN_CONFIDENCE: float = 0.3  # Minimum confidence for valid detection


# ---------------------------------------------------------------------------
# Configuration Classes
# ---------------------------------------------------------------------------


@dataclass
class ColorDetectionConfig:
    """Configuration for color-based sky detection.

    Attributes:
        hue_min: Minimum hue value for sky (0-360 degrees).
        hue_max: Maximum hue value for sky (0-360 degrees).
        saturation_max: Maximum saturation for sky (0-1).
        value_min: Minimum brightness value (0-1).
        gradient_threshold: Threshold for detecting vertical gradient.
        enable_cloudy_sky: Also detect cloudy/overcast sky (low saturation, high brightness).
    """

    hue_min: float = _DEFAULT_SKY_HUE_MIN
    hue_max: float = _DEFAULT_SKY_HUE_MAX
    saturation_max: float = _DEFAULT_SKY_SATURATION_MAX
    value_min: float = _DEFAULT_SKY_VALUE_MIN
    gradient_threshold: float = _DEFAULT_SKY_GRADIENT_THRESHOLD
    enable_cloudy_sky: bool = True

    def __post_init__(self) -> None:
        """Validate color detection configuration."""
        if not 0 <= self.hue_min <= 360:
            raise ValueError(f"hue_min must be in [0, 360], got {self.hue_min}")
        if not 0 <= self.hue_max <= 360:
            raise ValueError(f"hue_max must be in [0, 360], got {self.hue_max}")
        if not 0 <= self.saturation_max <= 1:
            raise ValueError(f"saturation_max must be in [0, 1], got {self.saturation_max}")
        if not 0 <= self.value_min <= 1:
            raise ValueError(f"value_min must be in [0, 1], got {self.value_min}")
        if not 0 <= self.gradient_threshold <= 1:
            raise ValueError(f"gradient_threshold must be in [0, 1], got {self.gradient_threshold}")


@dataclass
class PositionDetectionConfig:
    """Configuration for position-based sky detection.

    Attributes:
        sky_region_ratio: Ratio of image height from top to consider as sky region.
        min_sky_coverage: Minimum ratio of image that must be sky for valid detection.
        max_sky_coverage: Maximum ratio of image that can be classified as sky.
        prefer_top_weight: Weight multiplier for pixels closer to top edge.
    """

    sky_region_ratio: float = _DEFAULT_SKY_REGION_RATIO
    min_sky_coverage: float = _DEFAULT_MIN_SKY_COVERAGE
    max_sky_coverage: float = _DEFAULT_MAX_SKY_COVERAGE
    prefer_top_weight: float = 2.0

    def __post_init__(self) -> None:
        """Validate position detection configuration."""
        if not 0 <= self.sky_region_ratio <= 1:
            raise ValueError(f"sky_region_ratio must be in [0, 1], got {self.sky_region_ratio}")
        if not 0 <= self.min_sky_coverage <= 1:
            raise ValueError(f"min_sky_coverage must be in [0, 1], got {self.min_sky_coverage}")
        if not 0 <= self.max_sky_coverage <= 1:
            raise ValueError(f"max_sky_coverage must be in [0, 1], got {self.max_sky_coverage}")
        if self.min_sky_coverage > self.max_sky_coverage:
            raise ValueError(
                f"min_sky_coverage ({self.min_sky_coverage}) cannot exceed "
                f"max_sky_coverage ({self.max_sky_coverage})"
            )
        if self.prefer_top_weight < 1.0:
            raise ValueError(f"prefer_top_weight must be >= 1.0, got {self.prefer_top_weight}")


@dataclass
class EdgeDetectionConfig:
    """Configuration for edge-based horizon detection.

    Attributes:
        horizon_search_ratio: Ratio of image to search for horizon line.
        edge_threshold: Canny edge detection threshold.
        min_edge_pixels: Minimum edge pixels for valid horizon line.
        use_hough_transform: Use Hough line transform for horizon detection.
    """

    horizon_search_ratio: float = _DEFAULT_HORIZON_SEARCH_RATIO
    edge_threshold: float = _DEFAULT_EDGE_THRESHOLD
    min_edge_pixels: int = 100
    use_hough_transform: bool = False

    def __post_init__(self) -> None:
        """Validate edge detection configuration."""
        if not 0 <= self.horizon_search_ratio <= 1:
            raise ValueError(
                f"horizon_search_ratio must be in [0, 1], got {self.horizon_search_ratio}"
            )
        if self.edge_threshold <= 0:
            raise ValueError(f"edge_threshold must be positive, got {self.edge_threshold}")
        if self.min_edge_pixels < 0:
            raise ValueError(f"min_edge_pixels must be >= 0, got {self.min_edge_pixels}")


@dataclass
class SkyDepthConfig:
    """Configuration for depth assignment to sky regions.

    Attributes:
        depth_mode: How to assign depth to sky regions.
        sky_depth_value: Base depth value for sky (0-1, higher = farther).
        boundary_blend_pixels: Number of pixels for smooth transition at boundaries.
        apply_depth_gradient: Apply gradient from top to horizon in sky.
        gradient_strength: Strength of the depth gradient (0-1).
    """

    depth_mode: str = "maximum"
    sky_depth_value: float = _DEFAULT_SKY_DEPTH_VALUE
    boundary_blend_pixels: int = _DEFAULT_BOUNDARY_BLEND_PIXELS
    apply_depth_gradient: bool = True
    gradient_strength: float = 0.2

    def __post_init__(self) -> None:
        """Validate depth configuration."""
        valid_modes = [m.value for m in SkyDepthMode]
        if self.depth_mode not in valid_modes:
            raise ValueError(
                f"Invalid depth_mode '{self.depth_mode}'. Valid options: {valid_modes}"
            )
        if not 0 <= self.sky_depth_value <= 1:
            raise ValueError(f"sky_depth_value must be in [0, 1], got {self.sky_depth_value}")
        if self.boundary_blend_pixels < 0:
            raise ValueError(
                f"boundary_blend_pixels must be >= 0, got {self.boundary_blend_pixels}"
            )
        if not 0 <= self.gradient_strength <= 1:
            raise ValueError(f"gradient_strength must be in [0, 1], got {self.gradient_strength}")


@dataclass
class SkyboxConfig:
    """Main configuration for sky/background plane detection.

    This configuration controls the sky detection and depth assignment
    process to avoid 3D artifacts in outdoor scenes.

    Attributes:
        enabled: Whether sky detection is enabled.
        detection_method: Primary method for sky detection.
        min_confidence: Minimum confidence threshold for valid sky detection.
        color_config: Configuration for color-based detection.
        position_config: Configuration for position-based detection.
        edge_config: Configuration for edge-based detection.
        depth_config: Configuration for depth assignment.
        temporal_consistency: Enable temporal smoothing across frames.
        smoothing_frames: Number of frames for temporal smoothing.
    """

    enabled: bool = True
    detection_method: str = "combined"
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE
    color_config: Optional[ColorDetectionConfig] = None
    position_config: Optional[PositionDetectionConfig] = None
    edge_config: Optional[EdgeDetectionConfig] = None
    depth_config: Optional[SkyDepthConfig] = None
    temporal_consistency: bool = True
    smoothing_frames: int = 5

    def __post_init__(self) -> None:
        """Initialize sub-configurations if not provided."""
        valid_methods = [m.value for m in SkyDetectionMethod]
        if self.detection_method not in valid_methods:
            raise ValueError(
                f"Invalid detection_method '{self.detection_method}'. Valid options: {valid_methods}"
            )
        if not 0 <= self.min_confidence <= 1:
            raise ValueError(f"min_confidence must be in [0, 1], got {self.min_confidence}")
        if self.smoothing_frames < 1:
            raise ValueError(f"smoothing_frames must be >= 1, got {self.smoothing_frames}")

        # Initialize sub-configs with defaults if not provided
        if self.color_config is None:
            self.color_config = ColorDetectionConfig()
        if self.position_config is None:
            self.position_config = PositionDetectionConfig()
        if self.edge_config is None:
            self.edge_config = EdgeDetectionConfig()
        if self.depth_config is None:
            self.depth_config = SkyDepthConfig()

    @classmethod
    def from_dict(cls, config_dict: dict) -> SkyboxConfig:
        """Create configuration from dictionary.

        Args:
            config_dict: Dictionary with configuration values.

        Returns:
            SkyboxConfig instance.
        """
        # Extract sub-configs
        color_dict = config_dict.pop("color_config", None)
        position_dict = config_dict.pop("position_config", None)
        edge_dict = config_dict.pop("edge_config", None)
        depth_dict = config_dict.pop("depth_config", None)

        # Create sub-config instances
        color_config = ColorDetectionConfig(**color_dict) if color_dict else None
        position_config = PositionDetectionConfig(**position_dict) if position_dict else None
        edge_config = EdgeDetectionConfig(**edge_dict) if edge_dict else None
        depth_config = SkyDepthConfig(**depth_dict) if depth_dict else None

        return cls(
            color_config=color_config,
            position_config=position_config,
            edge_config=edge_config,
            depth_config=depth_config,
            **config_dict,
        )


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Enums
    "SkyDetectionMethod",
    "SkyDepthMode",
    # Configuration classes
    "SkyboxConfig",
    "ColorDetectionConfig",
    "PositionDetectionConfig",
    "EdgeDetectionConfig",
    "SkyDepthConfig",
    # Constants
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
]
