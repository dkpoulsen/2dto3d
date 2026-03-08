"""Anaglyph 3D image generation module.

This module provides functionality for generating various types of anaglyph 3D images
that combine left and right eye views using different color filtering methods.
Anaglyph images can be viewed with corresponding colored 3D glasses.

Supported anaglyph types:
- Red-Cyan (Dubois, Color, Gray, Half-Color)
- Magenta-Green (Trioscopic)
- Amber-Blue (ColorCode3D)

Each method has different characteristics:
- Dubois: Optimized for minimal ghosting and color preservation
- Color: Simple channel mixing, may have ghosting
- Gray: Grayscale, no color information but good depth
- Half-Color: Compromise between color and ghosting reduction
- Trioscopic: Uses magenta-green filters, better color reproduction
- ColorCode3D: Uses amber-blue filters, excellent color preservation
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Luminance coefficients for RGB to grayscale conversion (ITU-R BT.601)
LUMINANCE_R: Final[float] = 0.299
LUMINANCE_G: Final[float] = 0.587
LUMINANCE_B: Final[float] = 0.114

# Minimum valid image dimension
MIN_IMAGE_DIMENSION: Final[int] = 1


def _get_anaglyph_logger() -> Logger:
    """Get the anaglyph module logger (lazy initialization)."""
    return get_logger("stereo.anaglyph")


class AnaglyphType(Enum):
    """Available anaglyph encoding methods.

    Each method is designed for specific colored 3D glasses:

    - RED_CYAN_DUBOIS: High-quality red-cyan using Dubois algorithm
    - RED_CYAN_COLOR: Simple red-cyan channel mixing
    - RED_CYAN_GRAY: Grayscale red-cyan (no color)
    - RED_CYAN_HALF_COLOR: Half-color red-cyan (reduced ghosting)
    - MAGENTA_GREEN: Magenta-green (Trioscopic) glasses
    - AMBER_BLUE: Amber-blue (ColorCode3D) glasses
    """

    RED_CYAN_DUBOIS = "red_cyan_dubois"
    RED_CYAN_COLOR = "red_cyan_color"
    RED_CYAN_GRAY = "red_cyan_gray"
    RED_CYAN_HALF_COLOR = "red_cyan_half_color"
    MAGENTA_GREEN = "magenta_green"
    AMBER_BLUE = "amber_blue"


class AnaglyphEncoder:
    """Encode stereoscopic left/right views into anaglyph 3D images.

    This class provides various methods for combining left and right eye views
    into anaglyph 3D images compatible with different types of 3D glasses.

    The encoder supports multiple anaglyph types, each optimized for specific
    colored glasses and use cases:

    - **Red-Cyan**: Most common, works with standard red-cyan glasses
      - Dubois: Best quality, minimal ghosting
      - Color: Simple method, more ghosting
      - Gray: No color, pure depth
      - Half-Color: Compromise between color and ghosting

    - **Magenta-Green (Trioscopic)**: Better color reproduction than red-cyan
    - **Amber-Blue (ColorCode3D)**: Best color preservation, premium glasses

    Example usage:
        ```python
        encoder = AnaglyphEncoder()
        anaglyph = encoder.encode(left_view, right_view, AnaglyphType.RED_CYAN_DUBOIS)

        # Or use convenience methods
        anaglyph = encoder.encode_red_cyan_dubois(left_view, right_view)
        anaglyph = encoder.encode_magenta_green(left_view, right_view)
        ```
    """

    # Dubois anaglyph matrices (optimized for minimal ghosting)
    # These matrices are derived from Eric Dubois' research on anaglyph stereoscopy
    # Reference: Dubois, E. (2001). "A projection method to generate anaglyph stereo images"

    # Dubois matrix for red-cyan anaglyph
    # Left eye (red filter): extracts luminance information for red channel
    # Right eye (cyan filter): extracts color information for green and blue channels
    _DUBOIS_RED_CYAN_LEFT = np.array(
        [
            [0.437, 0.449, 0.164],
            [0.000, 0.000, 0.000],
            [0.000, 0.000, 0.000],
        ]
    )

    _DUBOIS_RED_CYAN_RIGHT = np.array(
        [
            [0.000, 0.000, 0.000],
            [0.062, 0.736, 0.228],
            [-0.046, -0.140, 0.917],
        ]
    )

    # Dubois matrix for magenta-green anaglyph (Trioscopic)
    # Left eye (magenta filter): red and blue channels
    # Right eye (green filter): green channel
    _DUBOIS_MAGENTA_GREEN_LEFT = np.array(
        [
            [0.615, 0.299, 0.086],
            [0.000, 0.000, 0.000],
            [0.543, 0.357, 0.100],
        ]
    )

    _DUBOIS_MAGENTA_GREEN_RIGHT = np.array(
        [
            [0.000, 0.000, 0.000],
            [0.143, 0.857, 0.000],
            [0.000, 0.000, 0.000],
        ]
    )

    # Dubois matrix for amber-blue anaglyph (ColorCode3D)
    # Left eye (amber filter): red and green channels
    # Right eye (blue filter): blue channel
    _DUBOIS_AMBER_BLUE_LEFT = np.array(
        [
            [0.858, 0.142, 0.000],
            [0.072, 0.928, 0.000],
            [0.000, 0.000, 0.000],
        ]
    )

    _DUBOIS_AMBER_BLUE_RIGHT = np.array(
        [
            [0.000, 0.000, 0.000],
            [0.000, 0.000, 0.000],
            [0.142, 0.072, 0.786],
        ]
    )

    def __init__(self, default_type: AnaglyphType = AnaglyphType.RED_CYAN_DUBOIS) -> None:
        """Initialize the anaglyph encoder.

        Args:
            default_type: Default anaglyph type to use when encoding.
        """
        self.default_type = default_type
        self._logger = _get_anaglyph_logger()
        self._logger.debug(f"AnaglyphEncoder initialized: default_type={default_type}")

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        anaglyph_type: AnaglyphType | None = None,
    ) -> np.ndarray:
        """Combine left and right views into an anaglyph 3D image.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, 3).
                Expected dtype: uint8 for images, float32/float64 for normalized.
            right: Right eye view as numpy array (H, W) or (H, W, 3).
                Must have same dimensions as left.
            anaglyph_type: Type of anaglyph encoding. If None, uses default_type.

        Returns:
            Anaglyph 3D image as uint8 numpy array (H, W, 3).

        Raises:
            ValueError: If input dimensions don't match or are invalid.
        """
        anaglyph_type = anaglyph_type or self.default_type
        self._logger.debug(f"Encoding anaglyph: type={anaglyph_type}")

        # Validate inputs
        if left.shape != right.shape:
            raise ValueError(
                f"Left and right views must have the same shape. "
                f"Left: {left.shape}, Right: {right.shape}"
            )

        # Ensure RGB format
        left_rgb = self._ensure_rgb(left)
        right_rgb = self._ensure_rgb(right)

        # Convert to float [0, 1] for processing
        left_f = self._to_float(left_rgb)
        right_f = self._to_float(right_rgb)

        # Encode based on type
        if anaglyph_type == AnaglyphType.RED_CYAN_DUBOIS:
            result = self._encode_dubois(
                left_f, right_f, self._DUBOIS_RED_CYAN_LEFT, self._DUBOIS_RED_CYAN_RIGHT
            )
        elif anaglyph_type == AnaglyphType.RED_CYAN_COLOR:
            result = self._encode_color(left_f, right_f)
        elif anaglyph_type == AnaglyphType.RED_CYAN_GRAY:
            result = self._encode_gray(left_f, right_f)
        elif anaglyph_type == AnaglyphType.RED_CYAN_HALF_COLOR:
            result = self._encode_half_color(left_f, right_f)
        elif anaglyph_type == AnaglyphType.MAGENTA_GREEN:
            result = self._encode_dubois(
                left_f, right_f, self._DUBOIS_MAGENTA_GREEN_LEFT, self._DUBOIS_MAGENTA_GREEN_RIGHT
            )
        elif anaglyph_type == AnaglyphType.AMBER_BLUE:
            result = self._encode_dubois(
                left_f, right_f, self._DUBOIS_AMBER_BLUE_LEFT, self._DUBOIS_AMBER_BLUE_RIGHT
            )
        else:
            raise ValueError(f"Unknown anaglyph type: {anaglyph_type}")

        return result

    def encode_red_cyan_dubois(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using Dubois red-cyan method (high quality, minimal ghosting).

        This is the recommended method for red-cyan glasses.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.RED_CYAN_DUBOIS)

    def encode_red_cyan_color(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using simple color red-cyan method.

        Simple channel extraction - may have more ghosting but preserves colors.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.RED_CYAN_COLOR)

    def encode_red_cyan_gray(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using grayscale red-cyan method.

        No color information, but good depth perception with minimal ghosting.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.RED_CYAN_GRAY)

    def encode_red_cyan_half_color(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using half-color red-cyan method.

        Compromise between color preservation and ghosting reduction.
        Left eye gets grayscale, right eye keeps full color.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.RED_CYAN_HALF_COLOR)

    def encode_magenta_green(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using magenta-green (Trioscopic) method.

        Better color reproduction than red-cyan, works with magenta-green glasses.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.MAGENTA_GREEN)

    def encode_amber_blue(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Encode using amber-blue (ColorCode3D) method.

        Best color preservation of all anaglyph methods.
        Works with amber-blue (ColorCode3D) glasses.

        Args:
            left: Left eye view.
            right: Right eye view.

        Returns:
            Anaglyph 3D image.
        """
        return self.encode(left, right, AnaglyphType.AMBER_BLUE)

    def _ensure_rgb(self, image: np.ndarray) -> np.ndarray:
        """Ensure image is in RGB format (H, W, 3).

        Args:
            image: Input image array.

        Returns:
            RGB image array with shape (H, W, 3).

        Raises:
            ValueError: If image has invalid shape or dimensions.
        """
        # Validate minimum dimensions
        if len(image.shape) < 2:
            raise ValueError(f"Invalid image shape: {image.shape}. Expected at least 2D array.")
        if image.shape[0] < MIN_IMAGE_DIMENSION or image.shape[1] < MIN_IMAGE_DIMENSION:
            raise ValueError(
                f"Image dimensions too small: {image.shape}. "
                f"Minimum dimension is {MIN_IMAGE_DIMENSION}."
            )

        if len(image.shape) == 2:
            # Grayscale - convert to RGB
            return np.stack([image, image, image], axis=-1)
        elif len(image.shape) == 3 and image.shape[2] == 1:
            # Single channel - convert to RGB
            return np.concatenate([image, image, image], axis=-1)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            return image
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # RGBA - drop alpha channel
            return image[:, :, :3]
        else:
            raise ValueError(
                f"Invalid image shape: {image.shape}. "
                f"Expected (H, W), (H, W, 1), (H, W, 3), or (H, W, 4)."
            )

    def _to_float(self, image: np.ndarray) -> np.ndarray:
        """Convert image to float32 in [0, 1] range.

        Args:
            image: Input image array.

        Returns:
            Float32 image array normalized to [0, 1].
        """
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        elif image.dtype in (np.float32, np.float64):
            img_float = image.astype(np.float32)
            # Clip to valid range if needed
            if img_float.max() > 1.0 or img_float.min() < 0.0:
                self._logger.warning(
                    f"Float image values outside [0,1] range: "
                    f"min={img_float.min():.2f}, max={img_float.max():.2f}. Clipping."
                )
                img_float = np.clip(img_float, 0.0, 1.0)
            return img_float
        else:
            # Convert to float and normalize to [0, 1]
            return image.astype(np.float32)

    def _encode_dubois(
        self,
        left_f: np.ndarray,
        right_f: np.ndarray,
        left_matrix: np.ndarray,
        right_matrix: np.ndarray,
    ) -> np.ndarray:
        """Encode using Dubois method with custom matrices.

        The Dubois algorithm applies color transformation matrices to minimize
        ghosting (crosstalk) between the left and right eye images.

        Uses optimized numpy einsum for efficient batch matrix multiplication.

        Args:
            left_f: Left eye view (float32, [0, 1]).
            right_f: Right eye view (float32, [0, 1]).
            left_matrix: 3x3 color transformation matrix for left eye.
            right_matrix: 3x3 color transformation matrix for right eye.

        Returns:
            Anaglyph image as uint8.
        """
        # Optimized: Use einsum for efficient batch matrix multiplication
        # Instead of nested loops, we compute: output[c] = sum_j(matrix[c,j] * input[j])
        left_contribution = np.einsum("ij,hwj->hwi", left_matrix, left_f)
        right_contribution = np.einsum("ij,hwj->hwi", right_matrix, right_f)

        # Combine contributions
        anaglyph = left_contribution + right_contribution

        # Clip and convert to uint8
        anaglyph = np.clip(anaglyph, 0, 1)
        return (anaglyph * 255).astype(np.uint8)

    def _encode_color(self, left_f: np.ndarray, right_f: np.ndarray) -> np.ndarray:
        """Encode using simple color method (red from left, cyan from right)."""
        anaglyph = np.zeros_like(left_f)
        anaglyph[:, :, 0] = left_f[:, :, 0]  # Red from left
        anaglyph[:, :, 1] = right_f[:, :, 1]  # Green from right
        anaglyph[:, :, 2] = right_f[:, :, 2]  # Blue from right
        return (np.clip(anaglyph, 0, 1) * 255).astype(np.uint8)

    def _encode_gray(self, left_f: np.ndarray, right_f: np.ndarray) -> np.ndarray:
        """Encode using grayscale method.

        Both eyes are converted to grayscale first, then combined.
        This eliminates color rivalry but loses color information.
        """
        # Convert to grayscale using ITU-R BT.601 luminance formula
        gray_left = (
            LUMINANCE_R * left_f[:, :, 0]
            + LUMINANCE_G * left_f[:, :, 1]
            + LUMINANCE_B * left_f[:, :, 2]
        )
        gray_right = (
            LUMINANCE_R * right_f[:, :, 0]
            + LUMINANCE_G * right_f[:, :, 1]
            + LUMINANCE_B * right_f[:, :, 2]
        )

        # Create anaglyph: red from left gray, green+blue from right gray
        anaglyph = np.stack([gray_left, gray_right, gray_right], axis=-1)
        return (np.clip(anaglyph, 0, 1) * 255).astype(np.uint8)

    def _encode_half_color(self, left_f: np.ndarray, right_f: np.ndarray) -> np.ndarray:
        """Encode using half-color method.

        Left eye uses grayscale (for red channel), right eye keeps full color.
        This reduces ghosting while preserving some color information.
        """
        # Convert left to grayscale for red channel using ITU-R BT.601 luminance formula
        gray_left = (
            LUMINANCE_R * left_f[:, :, 0]
            + LUMINANCE_G * left_f[:, :, 1]
            + LUMINANCE_B * left_f[:, :, 2]
        )

        # Create anaglyph: red from left gray, green+blue from right color
        anaglyph = np.zeros_like(left_f)
        anaglyph[:, :, 0] = gray_left
        anaglyph[:, :, 1] = right_f[:, :, 1]
        anaglyph[:, :, 2] = right_f[:, :, 2]
        return (np.clip(anaglyph, 0, 1) * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_anaglyph_encoder(
    default_type: AnaglyphType = AnaglyphType.RED_CYAN_DUBOIS,
) -> AnaglyphEncoder:
    """Create an anaglyph encoder with the specified default type.

    Args:
        default_type: Default anaglyph encoding type.

    Returns:
        Configured AnaglyphEncoder instance.
    """
    return AnaglyphEncoder(default_type=default_type)


def encode_anaglyph(
    left: np.ndarray,
    right: np.ndarray,
    anaglyph_type: AnaglyphType = AnaglyphType.RED_CYAN_DUBOIS,
) -> np.ndarray:
    """Encode left and right views into an anaglyph image (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        anaglyph_type: Type of anaglyph encoding.

    Returns:
        Anaglyph 3D image.
    """
    encoder = AnaglyphEncoder(default_type=anaglyph_type)
    return encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "AnaglyphEncoder",
    # Enums
    "AnaglyphType",
    # Functions
    "create_anaglyph_encoder",
    "encode_anaglyph",
    # Constants
    "LUMINANCE_R",
    "LUMINANCE_G",
    "LUMINANCE_B",
    "MIN_IMAGE_DIMENSION",
    # Logger
    "_get_anaglyph_logger",
]
