"""Depth-Image-Based Rendering (DIBR) engine for stereoscopic 3D generation.

This module implements the core DIBR algorithm that generates left and right
eye views by shifting pixels horizontally based on depth values.

The algorithm:
1. Compute disparity map from depth values using baseline and focal length
2. Generate left eye view by shifting pixels based on disparity
3. Generate right eye view by shifting in opposite direction
4. Handle disocclusions (holes) revealed by pixel shifts

Key parameters:
- baseline: Virtual camera separation (eye distance) - controls 3D effect strength
- focal_length: Virtual camera focal length - affects depth perception
- convergence: Distance where objects appear at screen depth (zero parallax)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional, Tuple

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger, log_exception, log_performance


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default values matching config/default.yaml
_DEFAULT_BASELINE: float = 0.05
_DEFAULT_FOCAL_LENGTH: float = 1.0
_DEFAULT_CONVERGENCE: float = 0.5

# Algorithm constants
_DEPTH_INVERSE_OFFSET: float = 0.01  # Offset to avoid division by zero in inverse depth
_HOLE_FILL_KERNEL_SIZE: int = 5  # Kernel size for morphological hole filling
_HOLE_FILL_ITERATIONS: int = 5  # Number of dilation iterations for hole filling
_INPAINT_RADIUS: int = 3  # Radius for CV2 inpainting
_MIN_IMAGE_DIMENSION: int = 1  # Minimum allowed image dimension

class HoleFillingMethod(Enum):
    """Available hole-filling methods for disocclusions."""

    NONE = "none"  # Leave holes as-is (black)
    NEAREST = "nearest"  # Nearest-neighbor interpolation
    LINEAR = "linear"  # Linear interpolation (horizontal)
    INPAINT = "inpaint"  # CV2 inpainting


class DepthInterpretation(Enum):
    """How to interpret depth values."""

    INVERSE = "inverse"  # High value = far (like MiDaS output)
    DIRECT = "direct"  # High value = close


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class DIBRConfig:
    """Configuration for DIBR rendering.

    Attributes:
        baseline: Virtual camera baseline (eye separation). Higher values
            create stronger 3D effect but may cause eye strain.
        focal_length: Virtual camera focal length. Affects depth perception.
        convergence: Convergence distance (normalized 0-1). Objects at this
            depth appear at screen level (zero parallax).
        hole_filling: Method to fill disocclusion holes.
        depth_interpretation: How to interpret depth values.
        max_disparity: Maximum disparity in pixels (safety limit).
        depth_scale: Scale factor for depth values.
    """

    baseline: float = _DEFAULT_BASELINE
    focal_length: float = _DEFAULT_FOCAL_LENGTH
    convergence: float = _DEFAULT_CONVERGENCE
    hole_filling: str = "nearest"
    depth_interpretation: str = "inverse"
    max_disparity: int = 64
    depth_scale: float = 1.0

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.baseline <= 0:
            raise ValueError(f"baseline must be positive, got {self.baseline}")
        if self.focal_length <= 0:
            raise ValueError(f"focal_length must be positive, got {self.focal_length}")
        if not 0.0 <= self.convergence <= 1.0:
            raise ValueError(f"convergence must be in [0, 1], got {self.convergence}")
        if self.max_disparity <= 0:
            raise ValueError(f"max_disparity must be positive, got {self.max_disparity}")
        if self.depth_scale <= 0:
            raise ValueError(f"depth_scale must be positive, got {self.depth_scale}")

        valid_hole_filling = [m.value for m in HoleFillingMethod]
        if self.hole_filling not in valid_hole_filling:
            raise ValueError(
                f"Invalid hole_filling '{self.hole_filling}'. Valid options: {valid_hole_filling}"
            )

        valid_depth_interp = [m.value for m in DepthInterpretation]
        if self.depth_interpretation not in valid_depth_interp:
            raise ValueError(
                f"Invalid depth_interpretation '{self.depth_interpretation}'. "
                f"Valid options: {valid_depth_interp}"
            )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DIBRError(Exception):
    """Exception raised for DIBR rendering errors."""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        original_exception: Optional[Exception] = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            operation: Operation that caused the error.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.operation = operation
        self.original_exception = original_exception


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


def _get_dibr_logger() -> "Logger":
    """Get the DIBR module logger (lazy initialization)."""
    return get_logger("stereo.dibr")


# ---------------------------------------------------------------------------
# DIBR Engine
# ---------------------------------------------------------------------------


class DIBREngine:
    """Depth-Image-Based Rendering engine for stereoscopic 3D generation.

    This class implements the core DIBR algorithm that generates left and right
    eye views by shifting pixels horizontally based on depth values.

    The disparity formula:
        disparity = (baseline * focal_length * image_width) / depth

    For convergence adjustment:
        - Objects at convergence depth appear at screen level
        - Closer objects pop out of screen
        - Farther objects appear behind screen

    Example usage:
        ```python
        # Basic usage
        engine = DIBREngine()
        left_view, right_view = engine.render(frame, depth_map)

        # With configuration
        config = DIBRConfig(
            baseline=0.08,
            convergence=0.4,
            hole_filling="inpaint"
        )
        engine = DIBREngine(config=config)
        left_view, right_view = engine.render(frame, depth_map)

        # Get disparity map for visualization
        disparity = engine.compute_disparity(depth_map, frame.shape[1])
        ```
    """

    def __init__(
        self,
        config: Optional[DIBRConfig] = None,
        *,
        baseline: float = _DEFAULT_BASELINE,
        focal_length: float = _DEFAULT_FOCAL_LENGTH,
        convergence: float = _DEFAULT_CONVERGENCE,
        hole_filling: str = "nearest",
    ) -> None:
        """Initialize the DIBR engine.

        Args:
            config: DIBRConfig object. If provided, other args are ignored.
            baseline: Virtual camera baseline (eye separation).
            focal_length: Virtual camera focal length.
            convergence: Convergence distance (normalized 0-1).
            hole_filling: Method to fill disocclusion holes.
        """
        if config is not None:
            self.config = config
        else:
            self.config = DIBRConfig(
                baseline=baseline,
                focal_length=focal_length,
                convergence=convergence,
                hole_filling=hole_filling,
            )

        self._logger = _get_dibr_logger()
        self._logger.debug(
            f"DIBREngine initialized: baseline={self.config.baseline}, "
            f"focal_length={self.config.focal_length}, "
            f"convergence={self.config.convergence}"
        )

    def compute_disparity(
        self,
        depth_map: np.ndarray,
        image_width: int,
    ) -> np.ndarray:
        """Compute disparity map from depth values.

        The disparity determines how many pixels each point should be shifted
        between left and right views.

        Args:
            depth_map: Normalized depth map with values in [0, 1].
                Higher values = farther (inverse depth interpretation).
            image_width: Width of the target image in pixels.

        Returns:
            Disparity map with same shape as depth_map, values in pixels.

        Raises:
            DIBRError: If computation fails.
        """
        try:
            # Ensure depth map is float
            depth = depth_map.astype(np.float32)

            # Apply depth interpretation
            if self.config.depth_interpretation == DepthInterpretation.INVERSE.value:
                # MiDaS-style: high value = far, so we need to invert
                # First, normalize to ensure proper disparity calculation
                depth = np.clip(depth, 1e-6, None)  # Avoid division by zero
                # Convert to actual depth (closer = larger disparity)
                actual_depth = 1.0 / (depth + _DEPTH_INVERSE_OFFSET)
            else:
                # Direct interpretation: high value = close
                actual_depth = depth

            # Apply depth scale
            actual_depth = actual_depth * self.config.depth_scale

            # Compute disparity: disparity = baseline * focal_length * width / depth
            disparity = self.config.baseline * self.config.focal_length * image_width / actual_depth

            # Clamp to max disparity for safety
            disparity = np.clip(disparity, 0, self.config.max_disparity)

            return disparity.astype(np.float32)

        except Exception as e:
            log_exception("Disparity computation failed", exception=e)
            raise DIBRError(
                f"Disparity computation failed: {e}",
                operation="compute_disparity",
                original_exception=e,
            ) from e

    def _warp_image(
        self,
        image: np.ndarray,
        disparity: np.ndarray,
        shift_sign: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Warp image by shifting pixels based on disparity.

        Args:
            image: Input image (H, W) or (H, W, C).
            disparity: Disparity map (H, W).
            shift_sign: +1 for left shift, -1 for right shift.

        Returns:
            Tuple of (warped_image, hole_mask).
        """
        h, w = image.shape[:2]

        # Create coordinate grids
        y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)

        # Compute source coordinates (where to sample from)
        # For left view: shift left (subtract disparity)
        # For right view: shift right (add disparity)
        shift = shift_sign * disparity
        src_x = x_coords - shift

        # Clamp source coordinates to valid range
        src_x_clamped = np.clip(src_x, 0, w - 1)

        # Track which pixels are holes (disocclusions)
        hole_mask = (src_x < 0) | (src_x >= w)

        # Perform the warping using remap for efficiency
        # remap expects (x, y) coordinates for each output pixel
        map_x = src_x_clamped
        map_y = y_coords

        # Use bilinear interpolation (works for both grayscale and color)
        warped = cv2.remap(
            image,
            map_x,
            map_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )

        return warped, hole_mask

    def _fill_holes(
        self,
        image: np.ndarray,
        hole_mask: np.ndarray,
    ) -> np.ndarray:
        """Fill holes (disocclusions) in warped image.

        Args:
            image: Warped image with holes.
            hole_mask: Boolean mask where True indicates holes.

        Returns:
            Image with holes filled.
        """
        method = self.config.hole_filling

        if method == HoleFillingMethod.NONE.value:
            return image

        if not hole_mask.any():
            return image

        # Select the appropriate hole-filling function
        if method == HoleFillingMethod.NEAREST.value:
            fill_func = self._fill_holes_nearest
        elif method == HoleFillingMethod.LINEAR.value:
            fill_func = self._fill_holes_linear
        else:  # INPAINT
            return self._fill_holes_inpaint(image, hole_mask)

        # Apply hole-filling (handle both grayscale and color images)
        if len(image.shape) == 3:
            result = image.copy()
            for c in range(image.shape[2]):
                result[:, :, c] = fill_func(image[:, :, c], hole_mask)
            return result
        else:
            return fill_func(image, hole_mask)

    def _fill_holes_nearest(
        self,
        channel: np.ndarray,
        hole_mask: np.ndarray,
    ) -> np.ndarray:
        """Fill holes using nearest-neighbor (dilation)."""
        result = channel.copy()

        # Use morphological dilation to fill from valid neighbors
        kernel = np.ones((_HOLE_FILL_KERNEL_SIZE, _HOLE_FILL_KERNEL_SIZE), np.uint8)

        # Dilate multiple times to fill larger holes
        for _ in range(_HOLE_FILL_ITERATIONS):
            dilated = cv2.dilate(result, kernel)
            result[hole_mask] = dilated[hole_mask]

        return result

    def _fill_holes_linear(
        self,
        channel: np.ndarray,
        hole_mask: np.ndarray,
    ) -> np.ndarray:
        """Fill holes using linear interpolation along rows."""
        result = channel.copy()
        h, w = channel.shape

        for y in range(h):
            row_mask = hole_mask[y, :]
            if not row_mask.any():
                continue

            # Find valid regions and interpolate
            row = result[y, :].astype(np.float32)

            # Get indices of valid pixels
            valid_indices = np.where(~row_mask)[0]
            if len(valid_indices) < 2:
                # Not enough valid pixels, use nearest
                if len(valid_indices) == 1:
                    result[y, row_mask] = row[valid_indices[0]]
                continue

            # Interpolate
            hole_indices = np.where(row_mask)[0]
            row[hole_indices] = np.interp(hole_indices, valid_indices, row[valid_indices])
            result[y, :] = row

        return result.astype(channel.dtype)

    def _fill_holes_inpaint(
        self,
        image: np.ndarray,
        hole_mask: np.ndarray,
    ) -> np.ndarray:
        """Fill holes using CV2 inpainting."""
        # Convert mask to uint8 format expected by cv2.inpaint
        mask_uint8 = hole_mask.astype(np.uint8) * 255

        # Determine image format for inpainting
        if len(image.shape) == 3:
            # Color image
            if image.dtype == np.uint8:
                result = cv2.inpaint(image, mask_uint8, inpaintRadius=_INPAINT_RADIUS, flags=cv2.INPAINT_TELEA)
            else:
                # Convert to uint8 for inpainting
                image_uint8 = self._to_uint8(image)
                result = cv2.inpaint(
                    image_uint8, mask_uint8, inpaintRadius=_INPAINT_RADIUS, flags=cv2.INPAINT_TELEA
                )
                # Convert back if needed
                if image.dtype != np.uint8:
                    result = result.astype(image.dtype) / 255.0
        else:
            # Grayscale - convert to color for inpainting
            if image.dtype == np.uint8:
                color_img = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                result = cv2.inpaint(
                    color_img, mask_uint8, inpaintRadius=_INPAINT_RADIUS, flags=cv2.INPAINT_TELEA
                )
                result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            else:
                image_uint8 = self._to_uint8(image)
                color_img = cv2.cvtColor(image_uint8, cv2.COLOR_GRAY2BGR)
                result = cv2.inpaint(
                    color_img, mask_uint8, inpaintRadius=_INPAINT_RADIUS, flags=cv2.INPAINT_TELEA
                )
                result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
                result = result.astype(image.dtype) / 255.0

        return result

    def _to_uint8(self, image: np.ndarray) -> np.ndarray:
        """Convert image to uint8 format."""
        if image.dtype == np.uint8:
            return image

        # Normalize and convert
        img_min, img_max = image.min(), image.max()
        if img_max - img_min > 1e-8:
            normalized = (image - img_min) / (img_max - img_min)
        else:
            normalized = np.zeros_like(image)

        return (normalized * 255).astype(np.uint8)

    def render(
        self,
        image: np.ndarray,
        depth_map: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate left and right eye views from image and depth map.

        This is the main entry point for DIBR rendering.

        Args:
            image: Input image (H, W) grayscale or (H, W, C) color.
            depth_map: Depth map with same height and width as image.
                Values should be normalized to [0, 1] range.
                With inverse interpretation (default): 0 = close, 1 = far.
                With direct interpretation: 0 = far, 1 = close.

        Returns:
            Tuple of (left_view, right_view) as numpy arrays.

        Raises:
            DIBRError: If rendering fails.
        """
        start_time = time.time()

        try:
            # Validate inputs
            if image.shape[:2] != depth_map.shape[:2]:
                raise DIBRError(
                    f"Image and depth map dimensions must match. "
                    f"Image: {image.shape[:2]}, Depth: {depth_map.shape[:2]}"
                )

            h, w = image.shape[:2]

            # Validate minimum dimensions
            if h < _MIN_IMAGE_DIMENSION or w < _MIN_IMAGE_DIMENSION:
                raise DIBRError(
                    f"Image dimensions must be at least {_MIN_IMAGE_DIMENSION}x{_MIN_IMAGE_DIMENSION}. "
                    f"Got: {h}x{w}"
                )

            # Normalize depth map to [0, 1]
            depth = depth_map.astype(np.float32)
            depth_min, depth_max = depth.min(), depth.max()
            if depth_max > 1.0 or depth_min < 0.0:
                depth_range = depth_max - depth_min
                if depth_range > 1e-8:
                    depth = (depth - depth_min) / depth_range
                else:
                    # Constant depth - set to middle value
                    depth = np.full_like(depth, 0.5)

            # Compute disparity
            disparity = self.compute_disparity(depth, w)

            # Apply convergence adjustment
            # Objects at convergence depth should have zero disparity
            # This creates the "pop-out" or "push-back" effect
            convergence_disparity = self.compute_disparity(
                np.full_like(depth, self.config.convergence), w
            )
            adjusted_disparity = disparity - convergence_disparity

            # Generate left view (shift left for positive disparity)
            left_view, left_holes = self._warp_image(image, adjusted_disparity, -1)

            # Generate right view (shift right)
            right_view, right_holes = self._warp_image(image, adjusted_disparity, 1)

            # Fill holes
            left_view = self._fill_holes(left_view, left_holes)
            right_view = self._fill_holes(right_view, right_holes)

            # Log performance
            elapsed_ms = (time.time() - start_time) * 1000
            log_performance(
                "dibr_render",
                elapsed_ms,
                width=w,
                height=h,
                baseline=self.config.baseline,
                hole_filling=self.config.hole_filling,
            )

            return left_view, right_view

        except DIBRError:
            raise
        except Exception as e:
            log_exception("DIBR rendering failed", exception=e)
            raise DIBRError(
                f"DIBR rendering failed: {e}",
                operation="render",
                original_exception=e,
            ) from e

    def __call__(
        self,
        image: np.ndarray,
        depth_map: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Render left and right views (callable interface).

        Args:
            image: Input image.
            depth_map: Depth map.

        Returns:
            Tuple of (left_view, right_view).
        """
        return self.render(image, depth_map)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_dibr_engine(
    baseline: float = _DEFAULT_BASELINE,
    focal_length: float = _DEFAULT_FOCAL_LENGTH,
    convergence: float = _DEFAULT_CONVERGENCE,
    **kwargs: float | str | int,
) -> DIBREngine:
    """Create a DIBR engine with the specified configuration.

    Args:
        baseline: Virtual camera baseline (eye separation).
        focal_length: Virtual camera focal length.
        convergence: Convergence distance (normalized 0-1).
        **kwargs: Additional DIBRConfig field values.

    Returns:
        Configured DIBREngine instance.
    """
    config = DIBRConfig(
        baseline=baseline,
        focal_length=focal_length,
        convergence=convergence,
        **kwargs,  # type: ignore[arg-type]
    )
    return DIBREngine(config=config)


def render_stereo_pair(
    image: np.ndarray,
    depth_map: np.ndarray,
    baseline: float = _DEFAULT_BASELINE,
    convergence: float = _DEFAULT_CONVERGENCE,
) -> Tuple[np.ndarray, np.ndarray]:
    """Render stereo pair with default settings (convenience function).

    Args:
        image: Input image.
        depth_map: Depth map.
        baseline: Virtual camera baseline.
        convergence: Convergence distance.

    Returns:
        Tuple of (left_view, right_view).
    """
    engine = DIBREngine(baseline=baseline, convergence=convergence)
    return engine.render(image, depth_map)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "DIBREngine",
    "DIBRConfig",
    "DIBRError",
    # Enums
    "HoleFillingMethod",
    "DepthInterpretation",
    # Functions
    "create_dibr_engine",
    "render_stereo_pair",
    # Constants
    "_DEFAULT_BASELINE",
    "_DEFAULT_FOCAL_LENGTH",
    "_DEFAULT_CONVERGENCE",
]
