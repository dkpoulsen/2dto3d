"""Sky detection module for identifying sky and background planes.

This module provides the SkyDetector class that uses multiple detection methods
to identify sky regions in images for proper depth assignment in 3D conversion.

Detection methods:
- Color-based: Detects blue/cyan sky regions using HSV color space
- Position-based: Assumes sky is in upper portion of image
- Edge-based: Detects horizon line using edge detection
- Combined: Combines all methods for robust detection
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.skybox.config import (
    ColorDetectionConfig,
    EdgeDetectionConfig,
    PositionDetectionConfig,
    SkyboxConfig,
    SkyDetectionMethod,
)
from video2d3d.utils.logger import get_logger, log_exception, log_performance

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Gaussian kernel sizes (must be odd)
_BLUR_KERNEL_SIZE: int = 5
_MORPHOLOGY_KERNEL_SIZE: int = 5

# Edge detection constants
_CANNY_LOW_THRESHOLD: int = 50
_CANNY_HIGH_THRESHOLD: int = 150
_HOUGH_THRESHOLD: int = 100
_HOUGH_MIN_LINE_LENGTH: int = 100
_HOUGH_MAX_LINE_GAP: int = 10

# Confidence weights for combined detection
_COLOR_WEIGHT: float = 0.4
_POSITION_WEIGHT: float = 0.3
_EDGE_WEIGHT: float = 0.3


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class SkyDetectionError(Exception):
    """Exception raised for sky detection errors."""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize the error."""
        super().__init__(message)
        self.operation = operation
        self.original_exception = original_exception


# ---------------------------------------------------------------------------
# Result Classes
# ---------------------------------------------------------------------------


@dataclass
class SkyDetectionResult:
    """Result of sky detection.

    Attributes:
        sky_mask: Binary mask where True indicates sky pixels.
        confidence: Overall confidence of detection (0-1).
        horizon_y: Y-coordinate of detected horizon line (or None).
        sky_coverage: Ratio of image classified as sky.
        method_results: Per-method confidence scores.
    """

    sky_mask: np.ndarray
    confidence: float
    horizon_y: Optional[int]
    sky_coverage: float
    method_results: dict[str, float]


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_skybox_logger() -> Logger:
    """Get the skybox module logger."""
    return get_logger("skybox.detector")


# ---------------------------------------------------------------------------
# Sky Detector
# ---------------------------------------------------------------------------


class SkyDetector:
    """Detect sky and background planes in images.

    This class uses multiple detection methods to identify sky regions:
    1. Color-based: HSV color space analysis for blue/cyan sky
    2. Position-based: Upper region analysis with position weighting
    3. Edge-based: Horizon line detection using edge analysis
    4. Combined: Weighted combination of all methods

    Example usage:
        ```python
        # Basic usage
        detector = SkyDetector()
        result = detector.detect(image)

        # With configuration
        config = SkyboxConfig(detection_method="combined")
        detector = SkyDetector(config=config)
        result = detector.detect(image)

        # Check results
        if result.confidence > 0.5:
            sky_depth = create_sky_depth_map(result.sky_mask)
        ```
    """

    def __init__(
        self,
        config: Optional[SkyboxConfig] = None,
    ) -> None:
        """Initialize the sky detector.

        Args:
            config: SkyboxConfig object. If None, uses defaults.
        """
        self.config = config or SkyboxConfig()
        self._logger = _get_skybox_logger()
        self._logger.debug(
            f"SkyDetector initialized: method={self.config.detection_method}, "
            f"min_confidence={self.config.min_confidence}"
        )

        # Cache for temporal consistency
        self._previous_mask: Optional[np.ndarray] = None
        self._frame_count: int = 0

    def detect(self, image: np.ndarray) -> SkyDetectionResult:
        """Detect sky regions in an image.

        Args:
            image: Input image as numpy array (H, W, C) in RGB format.

        Returns:
            SkyDetectionResult containing sky mask and metadata.

        Raises:
            SkyDetectionError: If detection fails.
        """
        start_time = time.time()

        try:
            # Validate input
            if not isinstance(image, np.ndarray):
                raise SkyDetectionError(
                    f"Input must be numpy array, got {type(image).__name__}",
                    operation="detect",
                )
            if image.ndim != 3:
                raise SkyDetectionError(
                    f"Input must be 3D array (H, W, C), got {image.ndim}D",
                    operation="detect",
                )

            h, w = image.shape[:2]

            # Run detection based on method
            method = self.config.detection_method

            if method == SkyDetectionMethod.COLOR.value:
                sky_mask, confidence, method_results = self._detect_color(image)
                horizon_y = None
            elif method == SkyDetectionMethod.POSITION.value:
                sky_mask, confidence, method_results = self._detect_position(image)
                horizon_y = self._find_horizon_simple(sky_mask)
            elif method == SkyDetectionMethod.EDGE.value:
                sky_mask, horizon_y, confidence, method_results = self._detect_edge(image)
            else:  # COMBINED
                sky_mask, confidence, horizon_y, method_results = self._detect_combined(image)

            # Calculate sky coverage
            sky_coverage = np.sum(sky_mask) / (h * w)

            # Apply temporal consistency if enabled
            if self.config.temporal_consistency and self._previous_mask is not None:
                sky_mask = self._apply_temporal_smoothing(sky_mask)

            # Store for temporal consistency
            if self.config.temporal_consistency:
                self._previous_mask = sky_mask.copy()
            self._frame_count += 1

            # Create result
            result = SkyDetectionResult(
                sky_mask=sky_mask,
                confidence=confidence,
                horizon_y=horizon_y,
                sky_coverage=sky_coverage,
                method_results=method_results,
            )

            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "sky_detection",
                elapsed_ms,
                method=method,
                confidence=confidence,
                sky_coverage=sky_coverage,
            )

            return result

        except SkyDetectionError:
            raise
        except Exception as e:
            log_exception("Sky detection failed", exception=e)
            raise SkyDetectionError(
                f"Sky detection failed: {e}",
                operation="detect",
                original_exception=e,
            ) from e

    def _detect_color(self, image: np.ndarray) -> tuple[np.ndarray, float, dict[str, float]]:
        """Detect sky using color analysis in HSV space.

        Args:
            image: Input RGB image.

        Returns:
            Tuple of (sky_mask, confidence, method_results).
        """
        config = self.config.color_config or ColorDetectionConfig()
        h, w = image.shape[:2]

        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Convert hue from 0-180 (OpenCV) to 0-360 degrees
        hue = hsv[:, :, 0].astype(np.float32) * 2
        saturation = hsv[:, :, 1].astype(np.float32) / 255.0
        value = hsv[:, :, 2].astype(np.float32) / 255.0

        # Create sky mask based on color
        # Blue sky: hue in range, low saturation, high value
        blue_mask = (
            (hue >= config.hue_min)
            & (hue <= config.hue_max)
            & (saturation <= config.saturation_max)
            & (value >= config.value_min)
        )

        # Cloudy sky: very low saturation, high brightness
        cloudy_mask = (saturation <= 0.15) & (value >= 0.7) & config.enable_cloudy_sky

        # Combine masks
        sky_mask = blue_mask | cloudy_mask

        # Apply morphological cleanup
        sky_mask = self._cleanup_mask(sky_mask)

        # Calculate confidence based on gradient and coverage
        confidence = self._calculate_color_confidence(sky_mask, hsv, config.gradient_threshold)

        method_results = {
            "color_blue_coverage": np.sum(blue_mask) / (h * w),
            "color_cloudy_coverage": (
                np.sum(cloudy_mask) / (h * w) if config.enable_cloudy_sky else 0
            ),
            "color_total_confidence": confidence,
        }

        return sky_mask, confidence, method_results

    def _detect_position(self, image: np.ndarray) -> tuple[np.ndarray, float, dict[str, float]]:
        """Detect sky based on position (upper regions).

        Args:
            image: Input RGB image.

        Returns:
            Tuple of (sky_mask, confidence, method_results).
        """
        config = self.config.position_config or PositionDetectionConfig()
        h, w = image.shape[:2]

        # Calculate sky region boundary
        sky_region_y = int(h * config.sky_region_ratio)

        # Create position-based mask
        sky_mask = np.zeros((h, w), dtype=bool)
        sky_mask[:sky_region_y, :] = True

        # Apply position weights (higher weight for top pixels)
        y_coords = np.arange(h).reshape(-1, 1)
        weights = np.exp(-y_coords / (h * 0.3))

        # Calculate weighted coverage
        weighted_coverage = np.sum(sky_mask) / (h * w)

        # Confidence based on whether coverage is in expected range
        if config.min_sky_coverage <= weighted_coverage <= config.max_sky_coverage:
            confidence = 0.7  # Reasonable confidence for position-only detection
        else:
            confidence = 0.3  # Low confidence if coverage is unusual

        method_results = {
            "position_sky_region_ratio": config.sky_region_ratio,
            "position_coverage": weighted_coverage,
        }

        return sky_mask, confidence, method_results

    def _detect_edge(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, Optional[int], float, dict[str, float]]:
        """Detect sky using edge-based horizon detection.

        Args:
            image: Input RGB image.

        Returns:
            Tuple of (sky_mask, horizon_y, confidence, method_results).
        """
        config = self.config.edge_config or EdgeDetectionConfig()
        h, w = image.shape[:2]

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Apply blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (_BLUR_KERNEL_SIZE, _BLUR_KERNEL_SIZE), 0)

        # Detect edges
        edges = cv2.Canny(
            blurred,
            int(config.edge_threshold * 0.5),
            config.edge_threshold,
        )

        # Find horizon line
        horizon_y = self._find_horizon_hough(edges, config)

        if horizon_y is None:
            # Fallback: use simple edge density analysis
            horizon_y = self._find_horizon_density(edges, config)

        # Create sky mask
        sky_mask = np.zeros((h, w), dtype=bool)
        if horizon_y is not None and horizon_y > 0:
            sky_mask[:horizon_y, :] = True
            confidence = 0.6
        else:
            # No horizon found, assume no sky
            confidence = 0.2

        method_results = {
            "edge_horizon_y": horizon_y if horizon_y else -1,
            "edge_total_edges": np.sum(edges > 0),
        }

        return sky_mask, horizon_y, confidence, method_results

    def _detect_combined(
        self, image: np.ndarray
    ) -> tuple[np.ndarray, float, Optional[int], dict[str, float]]:
        """Detect sky using combined methods.

        Combines color, position, and edge detection with weighted voting.

        Args:
            image: Input RGB image.

        Returns:
            Tuple of (sky_mask, confidence, horizon_y, method_results).
        """
        h, w = image.shape[:2]

        # Run all detection methods
        color_mask, color_conf, color_results = self._detect_color(image)
        position_mask, position_conf, position_results = self._detect_position(image)
        edge_mask, horizon_y, edge_conf, edge_results = self._detect_edge(image)

        # Combine masks with weights
        combined_mask = np.zeros((h, w), dtype=np.float32)

        # Weight color detection highest
        combined_mask += color_mask.astype(np.float32) * _COLOR_WEIGHT * color_conf

        # Position provides prior
        combined_mask += position_mask.astype(np.float32) * _POSITION_WEIGHT * position_conf

        # Edge detection provides hard boundary
        combined_mask += edge_mask.astype(np.float32) * _EDGE_WEIGHT * edge_conf

        # Threshold combined mask
        threshold = self.config.min_confidence
        sky_mask = combined_mask >= threshold

        # Cleanup
        sky_mask = self._cleanup_mask(sky_mask)

        # Calculate overall confidence
        confidence = float(
            color_conf * _COLOR_WEIGHT + position_conf * _POSITION_WEIGHT + edge_conf * _EDGE_WEIGHT
        )

        # Update horizon from edge detection if confident
        if edge_conf > 0.5 and horizon_y is not None:
            final_horizon = horizon_y
        else:
            final_horizon = self._find_horizon_simple(sky_mask)

        # Combine method results
        method_results = {
            **{f"color_{k}": v for k, v in color_results.items()},
            **{f"position_{k}": v for k, v in position_results.items()},
            **{f"edge_{k}": v for k, v in edge_results.items()},
            "combined_final_confidence": confidence,
        }

        return sky_mask, confidence, final_horizon, method_results

    def _cleanup_mask(self, mask: np.ndarray) -> np.ndarray:
        """Clean up sky mask using morphological operations.

        Args:
            mask: Binary sky mask.

        Returns:
            Cleaned mask.
        """
        # Convert to uint8
        mask_uint8 = mask.astype(np.uint8) * 255

        # Morphological operations
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (_MORPHOLOGY_KERNEL_SIZE, _MORPHOLOGY_KERNEL_SIZE),
        )

        # Close small holes
        closed = cv2.morphologyEx(mask_uint8, cv2.MORPH_CLOSE, kernel)

        # Open to remove small noise
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

        return opened > 0

    def _calculate_color_confidence(
        self,
        sky_mask: np.ndarray,
        hsv: np.ndarray,
        gradient_threshold: float,
    ) -> float:
        """Calculate confidence score for color-based detection.

        Higher confidence if:
        - Sky region has vertical brightness gradient
        - Sky coverage is reasonable
        - Sky is connected region at top

        Args:
            sky_mask: Detected sky mask.
            hsv: HSV image.
            gradient_threshold: Threshold for gradient detection.

        Returns:
            Confidence score (0-1).
        """
        h, w = sky_mask.shape
        config = self.config.position_config or PositionDetectionConfig()

        # Check sky coverage
        coverage = np.sum(sky_mask) / (h * w)
        coverage_score = (
            1.0 if config.min_sky_coverage <= coverage <= config.max_sky_coverage else 0.5
        )

        # Check for vertical gradient in brightness
        value = hsv[:, :, 2].astype(np.float32) / 255.0
        sky_value = value.copy()
        sky_value[~sky_mask] = 0

        # Calculate gradient in sky region
        top_brightness = np.mean(sky_value[: h // 4, :])
        bottom_brightness = np.mean(sky_value[h // 4 : h // 2, :])

        gradient_score = 1.0 if top_brightness > bottom_brightness + gradient_threshold else 0.5

        # Check if sky is connected at top
        top_row_coverage = np.sum(sky_mask[0, :]) / w
        top_score = top_row_coverage

        # Combined confidence
        confidence = coverage_score * 0.4 + gradient_score * 0.3 + top_score * 0.3

        return float(min(confidence, 1.0))

    def _find_horizon_hough(self, edges: np.ndarray, config: EdgeDetectionConfig) -> Optional[int]:
        """Find horizon line using Hough transform.

        Args:
            edges: Edge image from Canny detector.
            config: Edge detection configuration.

        Returns:
            Y-coordinate of horizon, or None if not found.
        """
        if not config.use_hough_transform:
            return None

        h, w = edges.shape

        # Search in lower portion of image for horizon
        search_region = edges[int(h * (1 - config.horizon_search_ratio)) :, :]

        # Hough line detection
        lines = cv2.HoughLinesP(
            search_region,
            rho=1,
            theta=np.pi / 180,
            threshold=_HOUGH_THRESHOLD,
            minLineLength=_HOUGH_MIN_LINE_LENGTH,
            maxLineGap=_HOUGH_MAX_LINE_GAP,
        )

        if lines is None:
            return None

        # Find most horizontal line
        best_y = None
        best_length = 0

        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Check if line is approximately horizontal
            angle = abs(np.arctan2(abs(y2 - y1), abs(x2 - x1)))
            if angle > np.pi / 6:  # Skip if not horizontal (30 degree tolerance)
                continue

            # Calculate line length
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

            if length > best_length:
                best_length = length
                # Average y coordinate, offset by search region
                best_y = int((y1 + y2) / 2 + h * (1 - config.horizon_search_ratio))

        return best_y

    def _find_horizon_density(
        self, edges: np.ndarray, config: EdgeDetectionConfig
    ) -> Optional[int]:
        """Find horizon line using edge density analysis.

        Finds the row with the highest edge density as the horizon.

        Args:
            edges: Edge image from Canny detector.
            config: Edge detection configuration.

        Returns:
            Y-coordinate of horizon, or None if not found.
        """
        h, w = edges.shape

        # Search region
        start_y = int(h * (1 - config.horizon_search_ratio))
        search_region = edges[start_y:, :]

        if search_region.shape[0] == 0:
            return None

        # Calculate row-wise edge density
        row_density = np.sum(search_region > 0, axis=1)

        # Find peak density
        if np.max(row_density) < config.min_edge_pixels:
            return None

        # Smooth density to find best horizon
        kernel_size = min(21, len(row_density) // 2)
        if kernel_size % 2 == 0:
            kernel_size += 1
        if kernel_size >= 3:
            smoothed = np.convolve(row_density, np.ones(kernel_size) / kernel_size, mode="same")
        else:
            smoothed = row_density

        best_y = int(np.argmax(smoothed) + start_y)

        return best_y

    def _find_horizon_simple(self, sky_mask: np.ndarray) -> Optional[int]:
        """Find horizon by finding the lowest sky pixel per column.

        Args:
            sky_mask: Binary sky mask.

        Returns:
            Y-coordinate of horizon, or None if not found.
        """
        h, w = sky_mask.shape

        # Find the bottom-most sky pixel in each column
        horizon_points = []
        for x in range(w):
            column = sky_mask[:, x]
            sky_pixels = np.where(column)[0]
            if len(sky_pixels) > 0:
                horizon_points.append(sky_pixels[-1])

        if len(horizon_points) < w * 0.1:  # Need at least 10% of columns with sky
            return None

        # Return median horizon position
        return int(np.median(horizon_points))

    def _apply_temporal_smoothing(self, current_mask: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing to sky mask.

        Blends current mask with previous frame's mask for stability.

        Args:
            current_mask: Current frame's sky mask.

        Returns:
            Temporally smoothed mask.
        """
        if self._previous_mask is None:
            return current_mask

        # Ensure masks have same shape
        if self._previous_mask.shape != current_mask.shape:
            return current_mask

        # Blend with previous mask
        alpha = 1.0 / self.config.smoothing_frames
        blended = alpha * current_mask.astype(np.float32) + (
            1 - alpha
        ) * self._previous_mask.astype(np.float32)

        # Threshold
        return blended > 0.5

    def reset_temporal_state(self) -> None:
        """Reset temporal smoothing state."""
        self._previous_mask = None
        self._frame_count = 0


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_sky_detector(**kwargs: Any) -> SkyDetector:
    """Create a sky detector with the specified configuration.

    Args:
        **kwargs: Configuration values for SkyboxConfig.

    Returns:
        Configured SkyDetector instance.
    """
    config = SkyboxConfig(**kwargs)
    return SkyDetector(config=config)


def detect_sky(image: np.ndarray, method: str = "combined") -> SkyDetectionResult:
    """Detect sky in an image with default settings.

    Args:
        image: Input RGB image.
        method: Detection method ('color', 'position', 'edge', 'combined').

    Returns:
        SkyDetectionResult containing sky mask and metadata.
    """
    config = SkyboxConfig(detection_method=method)
    detector = SkyDetector(config=config)
    return detector.detect(image)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "SkyDetector",
    "SkyDetectionResult",
    # Exceptions
    "SkyDetectionError",
    # Functions
    "create_sky_detector",
    "detect_sky",
    # Constants
    "_COLOR_WEIGHT",
    "_POSITION_WEIGHT",
    "_EDGE_WEIGHT",
    "_BLUR_KERNEL_SIZE",
    "_MORPHOLOGY_KERNEL_SIZE",
]
