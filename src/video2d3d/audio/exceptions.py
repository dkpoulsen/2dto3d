"""Custom exceptions for audio processing operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Initialize AudioProcessingError.

        Args:
            message: Error description.
            file_path: Path to the audio/video file that caused the error.
            reason: Specific reason for the failure.
        """
        self.file_path = file_path
        self.reason = reason
        full_message = message
        if reason:
            full_message += f": {reason}"
        if file_path:
            full_message += f" (file: {file_path})"
        super().__init__(full_message)


class AudioExtractionError(AudioProcessingError):
    """Raised when audio extraction from video fails."""

    def __init__(
        self,
        file_path: Optional[Path] = None,
        track_index: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Initialize AudioExtractionError.

        Args:
            file_path: Path to the video file.
            track_index: Index of the audio track that failed extraction.
            reason: Specific reason for the failure.
        """
        self.track_index = track_index
        message = "Failed to extract audio"
        if track_index is not None:
            message += f" from track {track_index}"
        super().__init__(message, file_path, reason)


class AudioCodecNotSupportedError(AudioProcessingError):
    """Raised when an audio codec is not supported."""

    def __init__(
        self,
        codec: str,
        file_path: Optional[Path] = None,
        supported_codecs: Optional[list[str]] = None,
    ) -> None:
        """Initialize AudioCodecNotSupportedError.

        Args:
            codec: The unsupported codec name.
            file_path: Path to the file with the unsupported codec.
            supported_codecs: List of supported codecs.
        """
        self.codec = codec
        self.supported_codecs = supported_codecs or []
        message = f"Audio codec not supported: {codec}"
        if supported_codecs:
            message += f". Supported codecs: {', '.join(supported_codecs)}"
        super().__init__(message, file_path)


class AudioTrackNotFoundError(AudioProcessingError):
    """Raised when a requested audio track is not found."""

    def __init__(
        self,
        track_index: int,
        file_path: Optional[Path] = None,
        available_tracks: Optional[int] = None,
    ) -> None:
        """Initialize AudioTrackNotFoundError.

        Args:
            track_index: The requested track index.
            file_path: Path to the video file.
            available_tracks: Number of available audio tracks.
        """
        self.track_index = track_index
        self.available_tracks = available_tracks
        message = f"Audio track {track_index} not found"
        if available_tracks is not None:
            message += f". Available tracks: 0-{available_tracks - 1}"
        super().__init__(message, file_path)


class AudioChannelLayoutError(AudioProcessingError):
    """Raised when audio channel layout is invalid or unsupported."""

    def __init__(
        self,
        layout: str,
        file_path: Optional[Path] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Initialize AudioChannelLayoutError.

        Args:
            layout: The problematic channel layout.
            file_path: Path to the audio/video file.
            reason: Specific reason for the error.
        """
        self.layout = layout
        message = f"Invalid or unsupported audio channel layout: {layout}"
        super().__init__(message, file_path, reason)


class AudioMixError(AudioProcessingError):
    """Raised when audio mixing operations fail."""

    def __init__(
        self,
        reason: Optional[str] = None,
        file_path: Optional[Path] = None,
    ) -> None:
        """Initialize AudioMixError.

        Args:
            reason: Specific reason for the mixing failure.
            file_path: Path to the output file.
        """
        message = "Failed to mix audio tracks"
        super().__init__(message, file_path, reason)


class SpatialAudioError(AudioProcessingError):
    """Raised when spatial audio processing fails."""

    def __init__(
        self,
        operation: str,
        reason: Optional[str] = None,
        file_path: Optional[Path] = None,
    ) -> None:
        """Initialize SpatialAudioError.

        Args:
            operation: The spatial audio operation that failed.
            reason: Specific reason for the failure.
            file_path: Path to the audio/video file.
        """
        self.operation = operation
        message = f"Spatial audio processing failed during {operation}"
        super().__init__(message, file_path, reason)
