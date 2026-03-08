"""Side-by-side 3D image generation module.

This module provides functionality for generating side-by-side 3D images
that combine left and right eye views into a single frame. This format
is widely compatible with 3D TVs, VR headsets, and passive 3D displays.

Supported layouts:
- Horizontal: Left and right views side by side (most common)
- Vertical: Top and bottom arrangement (over/under)

Width modes:
- Full-width: Each eye at full resolution (total width = 2x input width)
- Half-width: Each eye scaled to half width (total width = input width)

Half-width mode is commonly used for:
- 3D TVs that expect half-resolution side-by-side input
- VR video encoding (SBS 3D)
- Bandwidth-constrained applications

Full-width mode preserves full resolution for each eye and is used when:
- Maximum quality is required
- Post-processing will handle scaling
- Display supports full-resolution SBS
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Final, Optional

import cv2
import numpy as np

if TYPE_CHECKING:
    from loguru import Logger

from video2d3d.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum valid image dimension
MIN_IMAGE_DIMENSION: Final[int] = 1

# Luminance coefficients for RGB to grayscale conversion (ITU-R BT.601)
# Used for potential grayscale conversion operations
LUMINANCE_R: Final[float] = 0.299
LUMINANCE_G: Final[float] = 0.587
LUMINANCE_B: Final[float] = 0.114


def _get_sbs_logger() -> Logger:
    """Get the side-by-side module logger (lazy initialization)."""
    return get_logger("stereo.side_by_side")


class SideBySideLayout(Enum):
    """Available layout modes for side-by-side encoding.

    - HORIZONTAL: Left and right views placed horizontally adjacent.
      Output width = left.width + right.width (or same if half_width).
      Most common format for 3D TVs and VR headsets.
    - VERTICAL: Left and right views placed vertically adjacent (top/bottom).
      Output height = left.height + right.height.
      Less common, used for some specific displays.
    """

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class SideBySideEncoder:
    """Encode stereoscopic left/right views into side-by-side 3D format.

    This class combines left and right eye views into side-by-side format
    compatible with most 3D TVs, VR headsets, and passive 3D displays.

    The encoder supports:
    - **Layout**: Horizontal (left-right) or vertical (top-bottom)
    - **Width mode**: Full-width or half-width per eye
    - **Eye swap**: Option to swap left and right positions

    Half-width mode scales each eye to half its original width before
    combining, resulting in an output with the same width as the input
    but with each eye at half resolution.

    Full-width mode combines both eyes at full resolution, resulting
    in an output with double the width of the input.

    Example usage:
        ```python
        # Basic usage (horizontal, full-width)
        encoder = SideBySideEncoder()
        sbs = encoder.encode(left_view, right_view)

        # Half-width for 3D TV compatibility
        encoder = SideBySideEncoder(half_width=True)
        sbs = encoder.encode(left_view, right_view)

        # Vertical layout (over/under)
        encoder = SideBySideEncoder(layout=SideBySideLayout.VERTICAL)
        sbs = encoder.encode(left_view, right_view)

        # Convenience methods
        sbs = encoder.encode_horizontal(left_view, right_view)
        sbs = encoder.encode_half_width(left_view, right_view)
        ```
    """

    def __init__(
        self,
        layout: SideBySideLayout = SideBySideLayout.HORIZONTAL,
        half_width: bool = False,
        swap_eyes: bool = False,
    ) -> None:
        """Initialize the side-by-side encoder.

        Args:
            layout: Layout mode (horizontal or vertical).
            half_width: Scale each eye to half width before combining.
                When True, output has same dimensions as input (per eye).
                When False, output has double width (horizontal) or height (vertical).
            swap_eyes: Swap left and right eye positions in output.
        """
        self.layout = layout
        self.half_width = half_width
        self.swap_eyes = swap_eyes
        self._logger = _get_sbs_logger()
        self._logger.debug(
            f"SideBySideEncoder initialized: layout={layout}, "
            f"half_width={half_width}, swap_eyes={swap_eyes}"
        )

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[SideBySideLayout] = None,
        half_width: Optional[bool] = None,
        swap_eyes: Optional[bool] = None,
    ) -> np.ndarray:
        """Combine left and right views into a side-by-side 3D image.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, C).
                Expected dtype: uint8 for images, float32/float64 for normalized.
            right: Right eye view as numpy array (H, W) or (H, W, C).
                Must have same dimensions as left.
            layout: Layout mode. If None, uses instance default.
            half_width: Scale to half width. If None, uses instance default.
            swap_eyes: Swap eye positions. If None, uses instance default.

        Returns:
            Side-by-side 3D image as numpy array with same dtype as input.

        Raises:
            ValueError: If input dimensions don't match or are invalid.
        """
        # Use provided values or fall back to instance defaults
        layout = layout if layout is not None else self.layout
        half_width = half_width if half_width is not None else self.half_width
        swap_eyes = swap_eyes if swap_eyes is not None else self.swap_eyes

        self._logger.debug(
            f"Encoding side-by-side: layout={layout}, half_width={half_width}, swap_eyes={swap_eyes}"
        )

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

        # Apply half-width scaling if requested
        if half_width:
            new_w = w // 2
            # Use INTER_AREA for downscaling (better quality than INTER_LINEAR)
            # See: https://docs.opencv.org/4.x/da/d54/group__imgproc__transform.html
            left_scaled = cv2.resize(left, (new_w, h), interpolation=cv2.INTER_AREA)
            right_scaled = cv2.resize(right, (new_w, h), interpolation=cv2.INTER_AREA)
        else:
            left_scaled = left
            right_scaled = right

        # Swap eyes if requested
        if swap_eyes:
            left_scaled, right_scaled = right_scaled, left_scaled

        # Combine based on layout
        if layout == SideBySideLayout.HORIZONTAL:
            result = np.concatenate([left_scaled, right_scaled], axis=1)
        else:  # VERTICAL
            result = np.concatenate([left_scaled, right_scaled], axis=0)

        return result

    def encode_horizontal(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode using horizontal layout (left-right).

        This is the most common format for 3D TVs and VR headsets.

        Args:
            left: Left eye view.
            right: Right eye view.
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Side-by-side 3D image with horizontal layout.
        """
        return self.encode(left, right, layout=SideBySideLayout.HORIZONTAL, half_width=half_width)

    def encode_vertical(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode using vertical layout (top-bottom / over-under).

        Less common format, used for some specific displays.

        Args:
            left: Left eye view (placed on top).
            right: Right eye view (placed on bottom).
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Side-by-side 3D image with vertical layout.
        """
        return self.encode(left, right, layout=SideBySideLayout.VERTICAL, half_width=half_width)

    def encode_half_width(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[SideBySideLayout] = None,
    ) -> np.ndarray:
        """Encode with half-width mode for 3D TV compatibility.

        Each eye is scaled to half width before combining. The output
        will have the same width (horizontal) or height (vertical) as
        the input, with each eye at half resolution.

        This is the standard format for most consumer 3D TVs.

        Args:
            left: Left eye view.
            right: Right eye view.
            layout: Layout mode. If None, uses instance default.

        Returns:
            Side-by-side 3D image with half-width encoding.
        """
        return self.encode(left, right, layout=layout, half_width=True)

    def encode_full_width(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[SideBySideLayout] = None,
    ) -> np.ndarray:
        """Encode with full-width mode for maximum quality.

        Both eyes are combined at full resolution. The output
        will have double the width (horizontal) or height (vertical)
        of the input.

        Use this when maximum quality is required and the display
        or post-processing supports full-resolution SBS.

        Args:
            left: Left eye view.
            right: Right eye view.
            layout: Layout mode. If None, uses instance default.

        Returns:
            Side-by-side 3D image with full-width encoding.
        """
        return self.encode(left, right, layout=layout, half_width=False)

    def encode_cross_eye(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode for cross-eye free-viewing (swapped eyes).

        This places the right eye view on the left and left eye view
        on the right, which is required for cross-eye viewing technique.

        Args:
            left: Left eye view.
            right: Right eye view.
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Side-by-side 3D image with swapped eyes for cross-eye viewing.
        """
        return self.encode(
            left, right, layout=SideBySideLayout.HORIZONTAL, half_width=half_width, swap_eyes=True
        )

    def encode_parallel(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode for parallel free-viewing (normal eye order).

        This places the left eye view on the left and right eye view
        on the right, which is the standard arrangement for parallel
        viewing technique.

        Args:
            left: Left eye view.
            right: Right eye view.
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Side-by-side 3D image with normal eye order for parallel viewing.
        """
        return self.encode(
            left, right, layout=SideBySideLayout.HORIZONTAL, half_width=half_width, swap_eyes=False
        )


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_side_by_side_encoder(
    layout: SideBySideLayout = SideBySideLayout.HORIZONTAL,
    half_width: bool = False,
    swap_eyes: bool = False,
) -> SideBySideEncoder:
    """Create a side-by-side encoder with the specified configuration.

    Args:
        layout: Layout mode (horizontal or vertical).
        half_width: Scale each eye to half width.
        swap_eyes: Swap left and right eye positions.

    Returns:
        Configured SideBySideEncoder instance.
    """
    return SideBySideEncoder(layout=layout, half_width=half_width, swap_eyes=swap_eyes)


def encode_side_by_side(
    left: np.ndarray,
    right: np.ndarray,
    layout: SideBySideLayout = SideBySideLayout.HORIZONTAL,
    half_width: bool = False,
    swap_eyes: bool = False,
) -> np.ndarray:
    """Encode left and right views into side-by-side format (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        layout: Layout mode (horizontal or vertical).
        half_width: Scale each eye to half width.
        swap_eyes: Swap left and right eye positions.

    Returns:
        Side-by-side 3D image.
    """
    encoder = SideBySideEncoder(layout=layout, half_width=half_width, swap_eyes=swap_eyes)
    return encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "SideBySideEncoder",
    # Enums
    "SideBySideLayout",
    # Functions
    "create_side_by_side_encoder",
    "encode_side_by_side",
    # Constants
    "MIN_IMAGE_DIMENSION",
    "LUMINANCE_R",
    "LUMINANCE_G",
    "LUMINANCE_B",
    # Logger
    "_get_sbs_logger",
]
