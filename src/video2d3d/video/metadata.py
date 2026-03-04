"""Video metadata dataclass for storing extracted video information."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoMetadata:
    """
    Metadata extracted from a video file.

    Contains all essential information about a video needed for processing,
    including resolution, frame rate, codec, duration, and file details.

    Attributes:
        file_path: Path to the video file.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second.
        frame_count: Total number of frames in the video.
        duration: Video duration in seconds.
        codec: Video codec name (e.g., 'h264', 'hevc').
        format: Container format (e.g., 'mp4', 'avi').
        bitrate: Video bitrate in bits per second.
        has_audio: Whether the video contains an audio stream.
        audio_codec: Audio codec name if audio is present.
        audio_sample_rate: Audio sample rate in Hz.
        audio_channels: Number of audio channels.
        file_size: File size in bytes.
        is_valid: Whether the video passed validation.
        validation_errors: List of validation errors if any.
    """

    file_path: Path
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    duration: float = 0.0
    codec: str = ""
    format: str = ""
    bitrate: int = 0
    has_audio: bool = False
    audio_codec: str = ""
    audio_sample_rate: int = 0
    audio_channels: int = 0
    file_size: int = 0
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    @property
    def resolution(self) -> tuple[int, int]:
        """Return video resolution as (width, height) tuple."""
        return (self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        """Calculate and return the aspect ratio."""
        if self.height == 0:
            return 0.0
        return self.width / self.height

    @property
    def duration_formatted(self) -> str:
        """Return duration in HH:MM:SS format."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def file_size_mb(self) -> float:
        """Return file size in megabytes."""
        return self.file_size / (1024 * 1024)

    @property
    def is_4k(self) -> bool:
        """Check if video is 4K resolution (3840x2160 or higher)."""
        return self.width >= 3840 and self.height >= 2160

    @property
    def is_hd(self) -> bool:
        """Check if video is HD resolution (1280x720 or higher)."""
        return self.width >= 1280 and self.height >= 720

    @property
    def is_full_hd(self) -> bool:
        """Check if video is Full HD resolution (1920x1080 or higher)."""
        return self.width >= 1920 and self.height >= 1080

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        parts = [
            f"Video: {self.file_path.name}",
            f"Resolution: {self.width}x{self.height}",
            f"FPS: {self.fps:.2f}",
            f"Duration: {self.duration_formatted}",
            f"Codec: {self.codec or 'unknown'}",
            f"Format: {self.format or 'unknown'}",
        ]
        if self.has_audio:
            parts.append(f"Audio: {self.audio_codec or 'unknown'}")
        return " | ".join(parts)

    def to_dict(self) -> dict[str, str | int | float | bool | list[str]]:
        """Convert metadata to a dictionary."""
        return {
            "file_path": str(self.file_path),
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "duration": self.duration,
            "codec": self.codec,
            "format": self.format,
            "bitrate": self.bitrate,
            "has_audio": self.has_audio,
            "audio_codec": self.audio_codec,
            "audio_sample_rate": self.audio_sample_rate,
            "audio_channels": self.audio_channels,
            "file_size": self.file_size,
            "file_size_mb": self.file_size_mb,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }
