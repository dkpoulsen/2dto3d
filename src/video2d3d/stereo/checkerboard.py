"""Checkerboard 3D image generation module.

This module provides functionality for generating checkerboard pattern 3D images
where left and right eye pixels are interleaved in a checkerboard pattern.
This format is used by specific 3D display technologies such as:

- DLP 3D Ready projectors (Samsung, Mitsubishi)
- Some passive 3D monitors with checkerboard polarization
- Certain 3D TVs with checkerboard input support

The checkerboard pattern alternates between left and right eye pixels in both
horizontal and vertical directions, creating a grid-like interleaving pattern.

Pattern layout:
    L R L R L R ...
    R L R L R L ...
    L R L R L R ...
    R L R L R L ...
    ...

Where:
- L = pixel from left eye view
- R = pixel from right eye view

The eye assignment at position (row, col) follows:
- If (row + col) % 2 == 0: left eye pixel
- If (row + col) % 2 == 1: right eye pixel

This can be inverted with swap_eyes=True for displays that expect
the opposite pattern.
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


def _get_checkerboard_logger() -> Logger:
    """Get the checkerboard module logger (lazy initialization)."""
    return get_logger("stereo.checkerboard")


class CheckerboardPattern(Enum):
    """Available checkerboard pattern orientations.

    - STANDARD: Left eye at even positions (row + col) % 2 == 0
      This is the most common format for DLP 3D Ready displays.
    - INVERTED: Right eye at even positions (row + col) % 2 == 0
      Used by some displays that expect the opposite pattern.
    """

    STANDARD = "standard"
    INVERTED = "inverted"


class CheckerboardEncoder:
    """Encode stereoscopic left/right views into checkerboard 3D format.

    This class combines left and right eye views into a checkerboard pattern
    where pixels from each eye are interleaved in a grid pattern. This format
    is compatible with DLP 3D Ready projectors and certain passive 3D displays.

    The encoder supports:
    - **Pattern orientation**: Standard (left at even positions) or inverted
    - **Eye swap**: Option to swap left and right eye assignments

    Checkerboard encoding preserves full spatial resolution in both dimensions
    but reduces the effective resolution for each eye by half (each eye sees
    half the pixels in a checkerboard pattern).

    Example usage:
        ```python
        # Basic usage (standard pattern)
        encoder = CheckerboardEncoder()
        checkerboard = encoder.encode(left_view, right_view)

        # Inverted pattern for specific displays
        encoder = CheckerboardEncoder(pattern=CheckerboardPattern.INVERTED)
        checkerboard = encoder.encode(left_view, right_view)

        # With eye swap
        encoder = CheckerboardEncoder(swap_eyes=True)
        checkerboard = encoder.encode(left_view, right_view)

        # Convenience methods
        checkerboard = encoder.encode_standard(left_view, right_view)
        checkerboard = encoder.encode_inverted(left_view, right_view)
        ```
    """

    def __init__(
        self,
        pattern: CheckerboardPattern = CheckerboardPattern.STANDARD,
        swap_eyes: bool = False,
    ) -> None:
        """Initialize the checkerboard encoder.

        Args:
            pattern: Checkerboard pattern orientation (standard or inverted).
            swap_eyes: Swap left and right eye assignments in the pattern.
        """
        self.pattern = pattern
        self.swap_eyes = swap_eyes
        self._logger = _get_checkerboard_logger()
        self._logger.debug(
            f"CheckerboardEncoder initialized: pattern={pattern}, swap_eyes={swap_eyes}"
        )

    def __repr__(self) -> str:
        """Return a string representation of the encoder configuration."""
        return (
            f"{self.__class__.__name__}("
            f"pattern={self.pattern.value!r}, "
            f"swap_eyes={self.swap_eyes})"
        )

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        pattern: CheckerboardPattern | None = None,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Combine left and right views into a checkerboard 3D image.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, C).
                Expected dtype: uint8 for images, float32/float64 for normalized.
            right: Right eye view as numpy array (H, W) or (H, W, C).
                Must have same dimensions as left.
            pattern: Pattern orientation. If None, uses instance default.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Checkerboard 3D image as numpy array with same dtype as input.
            Output has the same dimensions as input images.

        Raises:
            ValueError: If input dimensions don't match or are invalid.
        """
        # Use provided values or fall back to instance defaults
        pattern = pattern if pattern is not None else self.pattern
        swap_eyes = swap_eyes if swap_eyes is not None else self.swap_eyes

        self._logger.debug(f"Encoding checkerboard: pattern={pattern}, swap_eyes={swap_eyes}")

        # Validate inputs
        if left.shape != right.shape:
            raise ValueError(
                f"Left and right views must have the same shape. "
                f"Left: {left.shape}, Right: {right.shape}"
            )

        h, w = left.shape[:2]
        if h <= 0 or w <= 0:
            raise ValueError(
                f"Image dimensions must be positive integers. " f"Got height={h}, width={w}"
            )
        if h < MIN_IMAGE_DIMENSION or w < MIN_IMAGE_DIMENSION:
            raise ValueError(
                f"Image dimensions must be at least {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}. "
                f"Got: {h}x{w}"
            )

        # Create checkerboard mask
        # Standard pattern: left at (row + col) % 2 == 0
        # Inverted pattern: right at (row + col) % 2 == 0
        rows, cols = np.ogrid[:h, :w]
        checker_mask = (rows + cols) % 2 == 0

        # Invert mask for inverted pattern
        if pattern == CheckerboardPattern.INVERTED:
            checker_mask = ~checker_mask

        # Swap eyes if requested (this effectively inverts the mask logic)
        if swap_eyes:
            checker_mask = ~checker_mask

        # Create output array and assign pixels based on checkerboard mask
        result = np.empty_like(left)
        result[checker_mask] = left[checker_mask]
        result[~checker_mask] = right[~checker_mask]

        return result

    def encode_standard(
        self,
        left: np.ndarray,
        right: np.ndarray,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Encode using standard pattern (left at even positions).

        This is the most common format for DLP 3D Ready displays.

        Args:
            left: Left eye view.
            right: Right eye view.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Checkerboard 3D image with standard pattern.
        """
        return self.encode(left, right, pattern=CheckerboardPattern.STANDARD, swap_eyes=swap_eyes)

    def encode_inverted(
        self,
        left: np.ndarray,
        right: np.ndarray,
        swap_eyes: bool | None = None,
    ) -> np.ndarray:
        """Encode using inverted pattern (right at even positions).

        Used by some displays that expect the opposite pattern.

        Args:
            left: Left eye view.
            right: Right eye view.
            swap_eyes: Swap eye assignments. If None, uses instance default.

        Returns:
            Checkerboard 3D image with inverted pattern.
        """
        return self.encode(left, right, pattern=CheckerboardPattern.INVERTED, swap_eyes=swap_eyes)

    def encode_with_swap(
        self,
        left: np.ndarray,
        right: np.ndarray,
        pattern: CheckerboardPattern | None = None,
    ) -> np.ndarray:
        """Encode with eyes swapped (right view on even positions in standard mode).

        This is equivalent to using the inverted pattern with swap_eyes=True.

        Args:
            left: Left eye view.
            right: Right eye view.
            pattern: Pattern orientation. If None, uses instance default.

        Returns:
            Checkerboard 3D image with swapped eyes.
        """
        return self.encode(left, right, pattern=pattern, swap_eyes=True)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_checkerboard_encoder(
    pattern: CheckerboardPattern = CheckerboardPattern.STANDARD,
    swap_eyes: bool = False,
) -> CheckerboardEncoder:
    """Create a checkerboard encoder with the specified configuration.

    Args:
        pattern: Pattern orientation (standard or inverted).
        swap_eyes: Swap left and right eye assignments.

    Returns:
        Configured CheckerboardEncoder instance.
    """
    return CheckerboardEncoder(pattern=pattern, swap_eyes=swap_eyes)


def encode_checkerboard(
    left: np.ndarray,
    right: np.ndarray,
    pattern: CheckerboardPattern = CheckerboardPattern.STANDARD,
    swap_eyes: bool = False,
) -> np.ndarray:
    """Encode left and right views into checkerboard format (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        pattern: Pattern orientation (standard or inverted).
        swap_eyes: Swap left and right eye assignments.

    Returns:
        Checkerboard 3D image.
    """
    encoder = CheckerboardEncoder(pattern=pattern, swap_eyes=swap_eyes)
    return encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "CheckerboardEncoder",
    # Enums
    "CheckerboardPattern",
    # Functions
    "create_checkerboard_encoder",
    "encode_checkerboard",
    # Constants
    "MIN_IMAGE_DIMENSION",
    # Logger
    "_get_checkerboard_logger",
]
