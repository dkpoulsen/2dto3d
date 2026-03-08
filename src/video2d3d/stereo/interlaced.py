"""Interlaced (field sequential) 3D image generation module.

This module provides functionality for generating interlaced 3D images
where left and right eye views are encoded in alternating scan lines.
This format is used by passive 3D displays such as:

- Passive 3D TVs (LG Cinema 3D, Vizio Theater 3D)
- Passive 3D monitors (with polarized screens)
- Some 3D projectors with passive technology

The interlaced pattern assigns scanlines to each eye:
- Even scanlines (0, 2, 4, ...): typically left eye
- Odd scanlines (1, 3, 5, ...): typically right eye

This can be inverted with swap_eyes=True for displays that expect
the opposite pattern.

The format is also known as:
- Row-interleaved 3D
- Line-alternate 3D
- Field-sequential 3D (for CRT displays)
- Passive 3D format

Note: This format works with displays that use polarized filters
where alternate rows have different polarizations.
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

# Minimum valid image dimension
MIN_IMAGE_DIMENSION: Final[int] = 1


def _get_interlaced_logger() -> Logger:
    """Get the interlaced module logger (lazy initialization)."""
    return get_logger("stereo.interlaced")


class InterlacedPattern(Enum):
    """Available interlaced pattern orientations.

    - ROW_INTERLEAVED: Left eye at even rows (0, 2, 4, ...)
      This is the most common format for passive 3D displays.
      Row 0, 2, 4, ... = left eye
      Row 1, 3, 5, ... = right eye
    - COLUMN_INTERLEAVED: Left eye at even columns (0, 2, 4, ...)
      Less common, used for some specific displays.
      Column 0, 2, 4, ... = left eye
      Column 1, 3, 5, ... = right eye
    """

    ROW_INTERLEAVED = "row_interleaved"
    COLUMN_INTERLEAVED = "column_interleaved"


class InterlacedEncoder:
    """Encode stereoscopic left/right views into interlaced 3D format.

    This class combines left and right eye views into an interlaced pattern
    where scanlines (or columns) from each eye are interleaved. This format
    is compatible with passive 3D displays that use polarized screens.

    The encoder supports:
    - **Pattern orientation**: Row-interleaved (most common) or column-interleaved
    - **Eye swap**: Option to swap left and right eye assignments

    Interlaced encoding preserves full horizontal resolution but reduces
    vertical resolution by half for each eye (in row-interleaved mode).
    Each eye sees every other scanline.

    Example usage:
        ```python
        # Basic usage (row-interleaved)
        encoder = InterlacedEncoder()
        interlaced = encoder.encode(left_view, right_view)

        # With eye swap for displays with opposite polarization
        encoder = InterlacedEncoder(swap_eyes=True)
        interlaced = encoder.encode(left_view, right_view)

        # Column-interleaved (less common)
        encoder = InterlacedEncoder(pattern=InterlacedPattern.COLUMN_INTERLEAVED)
        interlaced = encoder.encode(left_view, right_view)

        # Convenience methods
        interlaced = encoder.encode_row_interleaved(left_view, right_view)
        interlaced = encoder.encode_column_interleaved(left_view, right_view)
        ```
    """

    __slots__ = ("pattern", "swap_eyes", "_logger")

    def __init__(
        self,
        pattern: InterlacedPattern = InterlacedPattern.ROW_INTERLEAVED,
        swap_eyes: bool = False,
    ) -> None:
        """Initialize the interlaced encoder.

        Args:
            pattern: Interlaced pattern orientation (row or column interleaved).
            swap_eyes: Swap left and right eye assignments in the pattern.
        """
        self.pattern = pattern
        self.swap_eyes = swap_eyes
        self._logger = _get_interlaced_logger()
        self._logger.debug(
            f"InterlacedEncoder initialized: pattern={pattern}, swap_eyes={swap_eyes}"
        )

    def __repr__(self) -> str:
        """Return a string representation of the encoder configuration."""
        return (
            f"{self.__class__.__name__}(pattern={self.pattern.value!r}, swap_eyes={self.swap_eyes})"
        )

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        pattern: InterlacedPattern | None = None,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Combine left and right views into an interlaced 3D image.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, C).
                Expected dtype: uint8 for images, float32/float64 for normalized.
            right: Right eye view as numpy array (H, W) or (H, W, C).
                Must have same dimensions as left.
            pattern: Pattern orientation. If None, uses instance default.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Interlaced 3D image as numpy array with same dtype as input.
            Output has the same dimensions as input images.

        Raises:
            ValueError: If input dimensions don't match or are invalid.
        """
        # Use provided values or fall back to instance defaults
        pattern = pattern if pattern is not None else self.pattern
        swap_eyes = swap_eyes if swap_eyes is not None else self.swap_eyes

        self._logger.debug(f"Encoding interlaced: pattern={pattern}, swap_eyes={swap_eyes}")

        # Validate inputs
        if left.shape != right.shape:
            raise ValueError(
                f"Left and right views must have the same shape. "
                f"Left: {left.shape}, Right: {right.shape}"
            )

        h, w = left.shape[:2]
        if h < MIN_IMAGE_DIMENSION or w < MIN_IMAGE_DIMENSION:
            raise ValueError(
                f"Image dimensions must be at least {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}. "
                f"Got: {h}x{w}"
            )

        # Create output array
        result = np.empty_like(left)

        if pattern == InterlacedPattern.ROW_INTERLEAVED:
            # Row-interleaved: even rows = left, odd rows = right (unless swapped)
            if swap_eyes:
                result[0::2] = right[0::2]  # Even rows: right
                result[1::2] = left[1::2]  # Odd rows: left
            else:
                result[0::2] = left[0::2]  # Even rows: left
                result[1::2] = right[1::2]  # Odd rows: right
        else:  # COLUMN_INTERLEAVED
            # Column-interleaved: even columns = left, odd columns = right (unless swapped)
            if swap_eyes:
                result[:, 0::2] = right[:, 0::2]  # Even columns: right
                result[:, 1::2] = left[:, 1::2]  # Odd columns: left
            else:
                result[:, 0::2] = left[:, 0::2]  # Even columns: left
                result[:, 1::2] = right[:, 1::2]  # Odd columns: right

        return result

    def encode_row_interleaved(
        self,
        left: np.ndarray,
        right: np.ndarray,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Encode using row-interleaved pattern (even rows = left eye).

        This is the most common format for passive 3D displays.

        Args:
            left: Left eye view.
            right: Right eye view.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Interlaced 3D image with row-interleaved pattern.
        """
        return self.encode(
            left, right, pattern=InterlacedPattern.ROW_INTERLEAVED, swap_eyes=swap_eyes
        )

    def encode_column_interleaved(
        self,
        left: np.ndarray,
        right: np.ndarray,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Encode using column-interleaved pattern (even columns = left eye).

        Less common format, used for some specific displays.

        Args:
            left: Left eye view.
            right: Right eye view.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Interlaced 3D image with column-interleaved pattern.
        """
        return self.encode(
            left, right, pattern=InterlacedPattern.COLUMN_INTERLEAVED, swap_eyes=swap_eyes
        )

    def encode_with_swap(
        self,
        left: np.ndarray,
        right: np.ndarray,
        pattern: InterlacedPattern | None = None,
    ) -> np.ndarray:
        """Encode with eyes swapped.

        This swaps the left and right eye assignments in the pattern.

        Args:
            left: Left eye view.
            right: Right eye view.
            pattern: Pattern orientation. If None, uses instance default.

        Returns:
            Interlaced 3D image with swapped eyes.
        """
        return self.encode(left, right, pattern=pattern, swap_eyes=True)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_interlaced_encoder(
    pattern: InterlacedPattern = InterlacedPattern.ROW_INTERLEAVED,
    swap_eyes: bool = False,
) -> InterlacedEncoder:
    """Create an interlaced encoder with the specified configuration.

    Args:
        pattern: Pattern orientation (row or column interleaved).
        swap_eyes: Swap left and right eye assignments.

    Returns:
        Configured InterlacedEncoder instance.
    """
    return InterlacedEncoder(pattern=pattern, swap_eyes=swap_eyes)


def encode_interlaced(
    left: np.ndarray,
    right: np.ndarray,
    pattern: InterlacedPattern = InterlacedPattern.ROW_INTERLEAVED,
    swap_eyes: bool = False,
) -> np.ndarray:
    """Encode left and right views into interlaced format (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        pattern: Pattern orientation (row or column interleaved).
        swap_eyes: Swap left and right eye assignments.

    Returns:
        Interlaced 3D image.
    """
    encoder = InterlacedEncoder(pattern=pattern, swap_eyes=swap_eyes)
    return encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "InterlacedEncoder",
    # Enums
    "InterlacedPattern",
    # Functions
    "create_interlaced_encoder",
    "encode_interlaced",
    # Constants
    "MIN_IMAGE_DIMENSION",
    # Logger
    "_get_interlaced_logger",
]
