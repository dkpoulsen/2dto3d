"""Top-bottom 3D image generation module.

This module provides functionality for generating top-bottom 3D images
where left and right eye views are placed vertically adjacent (over/under).
This format is also known as:

- Over/Under 3D
- Top/Bottom 3D
- Vertical SBS (Side-by-Side)
- Frame Packing 3D (HDMI 3D standard)

Layout:
    +------------------+
    |    Left View     |  <- Top half
    +------------------+
    |   Right View     |  <- Bottom half
    +------------------+

This format is commonly used for:
- 3D TVs with frame sequential input
- HDMI 1.4 Frame Packing 3D
- VR headsets that accept over/under format
- Passive 3D projectors

Width modes:
- Full-width: Each eye at full resolution (total width = input width, height = 2x input height)
- Half-width: Each eye scaled to half width (total width = input width / 2, height = 2x input height)

Half-width mode is commonly used for:
- Bandwidth-constrained applications
- 3D TV broadcast standards
- Streaming 3D content

Full-width mode preserves full horizontal resolution for each eye and is used when:
- Maximum quality is required
- Post-processing will handle scaling
- Display supports full-resolution top-bottom
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


def _get_top_bottom_logger() -> Logger:
    """Get the top-bottom module logger (lazy initialization)."""
    return get_logger("stereo.top_bottom")


class TopBottomLayout(Enum):
    """Available layout modes for top-bottom encoding.

    - STANDARD: Left view on top, right view on bottom (most common)
      This is the standard format for most 3D displays.
      Top half = left eye, bottom half = right eye.
    - SWAPPED: Right view on top, left view on bottom
      Used for displays or content that expect reversed eye order.
      Top half = right eye, bottom half = left eye.
    """

    STANDARD = "standard"
    SWAPPED = "swapped"


class TopBottomEncoder:
    """Encode stereoscopic left/right views into top-bottom 3D format.

    This class combines left and right eye views into a top-bottom format
    where views are stacked vertically. This format is compatible with
    3D TVs, VR headsets, and HDMI 1.4 Frame Packing 3D.

    The encoder supports:
    - **Layout**: Standard (left on top) or swapped (right on top)
    - **Width mode**: Full-width or half-width per eye

    Half-width mode scales each eye to half its original width before
    combining, resulting in an output with the same width as half the
    input but double the height.

    Full-width mode combines both eyes at full resolution, resulting
    in an output with double the height of the input.

    Example usage:
        ```python
        # Basic usage (standard layout, full-width)
        encoder = TopBottomEncoder()
        tb = encoder.encode(left_view, right_view)

        # Half-width for 3D TV compatibility
        encoder = TopBottomEncoder(half_width=True)
        tb = encoder.encode(left_view, right_view)

        # Swapped layout (right on top)
        encoder = TopBottomEncoder(layout=TopBottomLayout.SWAPPED)
        tb = encoder.encode(left_view, right_view)

        # Convenience methods
        tb = encoder.encode_standard(left_view, right_view)
        tb = encoder.encode_swapped(left_view, right_view)
        tb = encoder.encode_half_width(left_view, right_view)
        ```
    """

    def __init__(
        self,
        layout: TopBottomLayout = TopBottomLayout.STANDARD,
        half_width: bool = False,
    ) -> None:
        """Initialize the top-bottom encoder.

        Args:
            layout: Layout mode (standard or swapped).
            half_width: Scale each eye to half width before combining.
                When True, output has half the width but double the height.
                When False, output has double the height at full width.
        """
        self.layout = layout
        self.half_width = half_width
        self._logger = _get_top_bottom_logger()
        self._logger.debug(
            f"TopBottomEncoder initialized: layout={layout}, half_width={half_width}"
        )

    def __repr__(self) -> str:
        """Return a string representation of the encoder."""
        return f"TopBottomEncoder(layout={self.layout.value}, half_width={self.half_width})"

    def encode(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[TopBottomLayout] = None,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Combine left and right views into a top-bottom 3D image.

        Args:
            left: Left eye view as numpy array (H, W) or (H, W, C).
                Expected dtype: uint8 for images, float32/float64 for normalized.
            right: Right eye view as numpy array (H, W) or (H, W, C).
                Must have same dimensions as left.
            layout: Layout mode. If None, uses instance default.
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Top-bottom 3D image as numpy array with same dtype as input.

        Raises:
            ValueError: If input dimensions don't match or are invalid.
        """
        # Use provided values or fall back to instance defaults
        layout = layout if layout is not None else self.layout
        half_width = half_width if half_width is not None else self.half_width

        self._logger.debug(f"Encoding top-bottom: layout={layout}, half_width={half_width}")

        # Validate inputs - check for None first
        if left is None or right is None:
            raise ValueError(
                f"Left and right views cannot be None. "
                f"Left: {type(left).__name__}, Right: {type(right).__name__}"
            )

        # Validate shape match
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

        # Combine based on layout
        if layout == TopBottomLayout.STANDARD:
            # Left on top, right on bottom
            result = np.concatenate([left_scaled, right_scaled], axis=0)
        else:  # SWAPPED
            # Right on top, left on bottom
            result = np.concatenate([right_scaled, left_scaled], axis=0)

        return result

    def encode_standard(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode using standard layout (left on top, right on bottom).

        This is the most common format for 3D displays.

        Args:
            left: Left eye view (placed on top).
            right: Right eye view (placed on bottom).
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Top-bottom 3D image with standard layout.
        """
        return self.encode(left, right, layout=TopBottomLayout.STANDARD, half_width=half_width)

    def encode_swapped(
        self,
        left: np.ndarray,
        right: np.ndarray,
        half_width: Optional[bool] = None,
    ) -> np.ndarray:
        """Encode using swapped layout (right on top, left on bottom).

        Used for displays or content that expect reversed eye order.

        Args:
            left: Left eye view (placed on bottom).
            right: Right eye view (placed on top).
            half_width: Scale to half width. If None, uses instance default.

        Returns:
            Top-bottom 3D image with swapped layout.
        """
        return self.encode(left, right, layout=TopBottomLayout.SWAPPED, half_width=half_width)

    def encode_half_width(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[TopBottomLayout] = None,
    ) -> np.ndarray:
        """Encode with half-width mode for bandwidth-constrained applications.

        Each eye is scaled to half width before combining. The output
        will have half the width and double the height of the input,
        with each eye at half horizontal resolution.

        This is commonly used for 3D TV broadcast and streaming.

        Args:
            left: Left eye view.
            right: Right eye view.
            layout: Layout mode. If None, uses instance default.

        Returns:
            Top-bottom 3D image with half-width encoding.
        """
        return self.encode(left, right, layout=layout, half_width=True)

    def encode_full_width(
        self,
        left: np.ndarray,
        right: np.ndarray,
        layout: Optional[TopBottomLayout] = None,
    ) -> np.ndarray:
        """Encode with full-width mode for maximum quality.

        Both eyes are combined at full resolution. The output
        will have the same width and double the height of the input.

        Use this when maximum quality is required and the display
        or post-processing supports full-resolution top-bottom.

        Args:
            left: Left eye view.
            right: Right eye view.
            layout: Layout mode. If None, uses instance default.

        Returns:
            Top-bottom 3D image with full-width encoding.
        """
        return self.encode(left, right, layout=layout, half_width=False)


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------


def create_top_bottom_encoder(
    layout: TopBottomLayout = TopBottomLayout.STANDARD,
    half_width: bool = False,
) -> TopBottomEncoder:
    """Create a top-bottom encoder with the specified configuration.

    Args:
        layout: Layout mode (standard or swapped).
        half_width: Scale each eye to half width.

    Returns:
        Configured TopBottomEncoder instance.
    """
    return TopBottomEncoder(layout=layout, half_width=half_width)


def encode_top_bottom(
    left: np.ndarray,
    right: np.ndarray,
    layout: TopBottomLayout = TopBottomLayout.STANDARD,
    half_width: bool = False,
) -> np.ndarray:
    """Encode left and right views into top-bottom format (convenience function).

    Args:
        left: Left eye view.
        right: Right eye view.
        layout: Layout mode (standard or swapped).
        half_width: Scale each eye to half width.

    Returns:
        Top-bottom 3D image.
    """
    encoder = TopBottomEncoder(layout=layout, half_width=half_width)
    return encoder.encode(left, right)


# ---------------------------------------------------------------------------
# Module Exports
# ---------------------------------------------------------------------------

__all__ = [
    # Classes
    "TopBottomEncoder",
    # Enums
    "TopBottomLayout",
    # Functions
    "create_top_bottom_encoder",
    "encode_top_bottom",
    # Constants
    "MIN_IMAGE_DIMENSION",
    "LUMINANCE_R",
    "LUMINANCE_G",
    "LUMINANCE_B",
    # Logger
    "_get_top_bottom_logger",
]
