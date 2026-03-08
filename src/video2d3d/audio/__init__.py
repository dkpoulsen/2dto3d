"""Audio processing module for 3D spatial audio, track preservation, and multi-channel support.

This module provides comprehensive audio processing capabilities including:
- 3D spatial audio generation using FFmpeg filters
- Audio track preservation from source videos
- Multi-channel audio support (5.1, 7.1 surround)
- Audio metadata extraction and management
- Integration with video processing pipeline

Example usage:
    ```python
    from video2d3d.audio import (
        AudioProcessor,
        SpatialAudioConfig,
        AudioTrackPreserver,
        AudioMetadata,
    )

    # Extract audio metadata
    metadata = AudioMetadata.extract_from_video("input.mp4")
    print(f"Audio tracks: {metadata.track_count}")

    # Configure spatial audio
    config = SpatialAudioConfig(
        enable_spatial=True,
        spatial_format="binaural",
        room_size="medium",
    )

    # Process audio
    processor = AudioProcessor(config=config)
    processor.process_audio("input.mp4", "output.m4a")
    ```
"""

from __future__ import annotations

from video2d3d.audio.config import (
    AudioChannelLayout,
    AudioConfig,
    AudioFormatConfig,
    SpatialAudioConfig,
    SpatialAudioFormat,
)
from video2d3d.audio.exceptions import (
    AudioChannelLayoutError,
    AudioCodecNotSupportedError,
    AudioExtractionError,
    AudioMixError,
    AudioProcessingError,
    AudioTrackNotFoundError,
    SpatialAudioError,
)
from video2d3d.audio.metadata import AudioMetadata, AudioTrackInfo
from video2d3d.audio.multichannel import MultiChannelAudioProcessor
from video2d3d.audio.processor import AudioProcessor
from video2d3d.audio.spatial import SpatialAudioProcessor
from video2d3d.audio.tracks import AudioTrackPreserver

__all__ = [
    # Main processor
    "AudioProcessor",
    # Configuration
    "AudioConfig",
    "AudioFormatConfig",
    "SpatialAudioConfig",
    "AudioChannelLayout",
    "SpatialAudioFormat",
    # Metadata
    "AudioMetadata",
    "AudioTrackInfo",
    # Specialized processors
    "SpatialAudioProcessor",
    "AudioTrackPreserver",
    "MultiChannelAudioProcessor",
    # Exceptions
    "AudioProcessingError",
    "AudioExtractionError",
    "AudioCodecNotSupportedError",
    "AudioTrackNotFoundError",
    "AudioChannelLayoutError",
    "AudioMixError",
    "SpatialAudioError",
]
