"""Video input and output handling.

This module provides robust video file handling capabilities including:
- Format validation using file extensions and magic bytes
- Metadata extraction using OpenCV and FFmpeg
- Comprehensive error handling for corrupted/unsupported files
- Configurable validation rules

Example usage:
    ```python
    from video2d3d.video import VideoInputHandler, validate_video

    # Using the handler class
    handler = VideoInputHandler()
    metadata = handler.validate_and_extract("video.mp4")
    print(f"Resolution: {metadata.width}x{metadata.height}")
    print(f"Duration: {metadata.duration_formatted}")

    # Using the convenience function
    metadata = validate_video("video.mp4")
    ```
"""

from video2d3d.video.exceptions import (
    VideoCodecNotSupportedError,
    VideoCorruptedError,
    VideoError,
    VideoFileNotFoundError,
    VideoFormatNotSupportedError,
    VideoMetadataExtractionError,
    VideoValidationError,
)
from video2d3d.video.handler import VideoInputHandler, validate_video
from video2d3d.video.metadata import VideoMetadata

__all__ = [
    # Handler classes
    "VideoInputHandler",
    "validate_video",
    # Metadata
    "VideoMetadata",
    # Exceptions
    "VideoError",
    "VideoFileNotFoundError",
    "VideoFormatNotSupportedError",
    "VideoCorruptedError",
    "VideoCodecNotSupportedError",
    "VideoValidationError",
    "VideoMetadataExtractionError",
]
