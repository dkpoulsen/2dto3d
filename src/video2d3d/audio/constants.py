"""Constants and shared utilities for audio processing."""

from __future__ import annotations

import shutil
from typing import Optional

# Timeout constants (in seconds)
FFPROBE_TIMEOUT = 30
FFMPEG_EXTRACT_TIMEOUT = 120
FFMPEG_PROCESS_TIMEOUT = 180
FFMPEG_SPATIAL_TIMEOUT = 300

# Error message truncation limits
ERROR_MESSAGE_MAX_LENGTH = 500
ERROR_MESSAGE_SHORT_LENGTH = 200

# Codec to file extension mapping
CODEC_EXTENSIONS: dict[str, str] = {
    "aac": "m4a",
    "opus": "opus",
    "mp3": "mp3",
    "flac": "flac",
    "pcm_s16le": "wav",
    "pcm_s24le": "wav",
    "ac3": "ac3",
    "eac3": "eac3",
    "truehd": "thd",
}

# Default codec for output
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_AUDIO_EXTENSION = "m4a"

# Valid codecs for configuration validation
VALID_CODECS = [
    "aac",
    "opus",
    "mp3",
    "flac",
    "pcm_s16le",
    "pcm_s24le",
    "ac3",
    "eac3",
    "truehd",
]

# Valid quality presets
VALID_QUALITIES = ["low", "medium", "high"]

# Valid spatial audio formats
VALID_SPATIAL_FORMATS = [
    "binaural",
    "ambisonics_1st",
    "ambisonics_2nd",
    "ambisonics_3rd",
]

# Valid room sizes
VALID_ROOM_SIZES = ["small", "medium", "large", "cathedral"]


def check_ffmpeg_available() -> None:
    """Check if FFmpeg is available in PATH.

    Raises:
        RuntimeError: If FFmpeg is not found.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")


def get_extension_for_codec(codec: str) -> str:
    """Get file extension for a codec.

    Args:
        codec: Codec name.

    Returns:
        File extension without dot.
    """
    return CODEC_EXTENSIONS.get(codec, DEFAULT_AUDIO_EXTENSION)


def truncate_error_message(
    message: Optional[str], max_length: int = ERROR_MESSAGE_MAX_LENGTH
) -> str:
    """Truncate an error message to a maximum length.

    Args:
        message: Error message to truncate.
        max_length: Maximum length for the message.

    Returns:
        Truncated error message or "Unknown error" if message is None.
    """
    if message is None:
        return "Unknown error"
    return message[:max_length] if len(message) > max_length else message
