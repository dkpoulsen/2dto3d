"""Live preview window for video processing quality assessment.

This module provides optional real-time preview functionality using OpenCV,
displaying the original frame, depth map, and stereoscopic result side-by-side
during processing for quality assessment.
"""

from video2d3d.preview.preview_window import (
    PreviewConfig,
    PreviewLayout,
    PreviewWindow,
    PreviewWindowError,
    create_preview_window,
)

__all__ = [
    "PreviewConfig",
    "PreviewLayout",
    "PreviewWindow",
    "PreviewWindowError",
    "create_preview_window",
]
