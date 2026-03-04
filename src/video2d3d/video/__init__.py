"""Video input and output handling.

This module provides robust video file handling capabilities including:
- Format validation using file extensions and magic bytes
- Metadata extraction using OpenCV and FFmpeg
- Comprehensive error handling for corrupted/unsupported files
- Configurable validation rules
- Efficient frame extraction with memory management

Example usage:
    ```python
    from video2d3d.video import VideoInputHandler, validate_video, FrameExtractor

    # Using the handler class
    handler = VideoInputHandler()
    metadata = handler.validate_and_extract("video.mp4")
    print(f"Resolution: {metadata.width}x{metadata.height}")
    print(f"Duration: {metadata.duration_formatted}")

    # Using the convenience function
    metadata = validate_video("video.mp4")

    # Extract frames with sampling
    extractor = FrameExtractor("video.mp4", sampling_interval=10)
    for frame_num, frame in extractor.extract_frames():
        print(f"Frame {frame_num}: {frame.shape}")
    ```
"""

from video2d3d.video.exceptions import (
    FrameBufferError,
    FrameExtractionError,
    InvalidSamplingStrategyError,
    MemoryLimitExceededError,
    VideoCodecNotSupportedError,
    VideoCorruptedError,
    VideoError,
    VideoFileNotFoundError,
    VideoFormatNotSupportedError,
    VideoMetadataExtractionError,
    VideoValidationError,
)
from video2d3d.video.frame_extractor import (
    FrameBuffer,
    FrameExtractor,
    FrameExtractorConfig,
    FrameInfo,
    SamplingStrategy,
    extract_frame_at,
    extract_frames,
)
from video2d3d.video.handler import VideoInputHandler, validate_video
from video2d3d.video.metadata import VideoMetadata

__all__ = [
    # Handler classes
    "VideoInputHandler",
    "validate_video",
    # Metadata
    "VideoMetadata",
    # Frame extraction
    "FrameExtractor",
    "FrameExtractorConfig",
    "FrameBuffer",
    "FrameInfo",
    "SamplingStrategy",
    "extract_frames",
    "extract_frame_at",
    # Exceptions
    "VideoError",
    "VideoFileNotFoundError",
    "VideoFormatNotSupportedError",
    "VideoCorruptedError",
    "VideoCodecNotSupportedError",
    "VideoValidationError",
    "VideoMetadataExtractionError",
    "FrameExtractionError",
    "FrameBufferError",
    "MemoryLimitExceededError",
    "InvalidSamplingStrategyError",
]
