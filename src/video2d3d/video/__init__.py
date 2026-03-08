"""Video input and output handling.

This module provides robust video file handling capabilities including:
- Format validation using file extensions and magic bytes
- Metadata extraction using OpenCV and FFmpeg
- Comprehensive error handling for corrupted/unsupported files
- Configurable validation rules
- Efficient frame extraction with memory management
- Robust video writing with FFmpeg integration

Example usage:
    ```python
    from video2d3d.video import (
        VideoInputHandler,
        validate_video,
        FrameExtractor,
        VideoOutputWriter,
        VideoWriterConfig,
    )

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

    # Write processed frames to a new video
    config = VideoWriterConfig(codec="libx264", preset="medium", crf=23)
    with VideoOutputWriter("output.mp4", config=config,
                           width=1920, height=1080) as writer:
        for frame in processed_frames:
            writer.write_frame(frame)
    ```
"""

from video2d3d.video.exceptions import (
    AudioProcessingError,
    FFmpegProcessError,
    FrameBufferError,
    FrameExtractionError,
    InvalidSamplingStrategyError,
    InvalidVideoDimensionsError,
    MemoryLimitExceededError,
    VideoCodecNotSupportedError,
    VideoCorruptedError,
    VideoError,
    VideoFileNotFoundError,
    VideoFormatNotSupportedError,
    VideoMetadataExtractionError,
    VideoValidationError,
    VideoWriteError,
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
from video2d3d.video.video_writer import (
    PixelFormat,
    Preset,
    VideoCodec,
    VideoOutputWriter,
    VideoWriterConfig,
    WriterStats,
    create_av1_video_writer,
    create_hevc_video_writer,
    create_video_writer,
    create_vr_video_writer,
)

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
    # Video writing
    "VideoOutputWriter",
    "VideoWriterConfig",
    "VideoCodec",
    "PixelFormat",
    "Preset",
    "WriterStats",
    "create_video_writer",
    "create_vr_video_writer",
    "create_av1_video_writer",
    "create_hevc_video_writer",
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
    "VideoWriteError",
    "FFmpegProcessError",
    "AudioProcessingError",
    "InvalidVideoDimensionsError",
]
