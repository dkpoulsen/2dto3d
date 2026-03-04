"""Custom exceptions for video input handling."""

from __future__ import annotations

from pathlib import Path


class VideoError(Exception):
    """Base exception for video-related errors."""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        """
        Initialize VideoError.

        Args:
            message: Error description.
            file_path: Path to the video file that caused the error.
        """
        self.file_path = file_path
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.file_path:
            return f"{super().__str__()} (file: {self.file_path})"
        return super().__str__()


class VideoFileNotFoundError(VideoError):
    """Raised when a video file does not exist."""

    def __init__(self, file_path: Path) -> None:
        """
        Initialize VideoFileNotFoundError.

        Args:
            file_path: Path to the non-existent file.
        """
        super().__init__(f"Video file not found: {file_path}", file_path)


class VideoFormatNotSupportedError(VideoError):
    """Raised when the video format is not supported."""

    def __init__(
        self,
        file_path: Path,
        format: str | None = None,
        supported_formats: list[str] | None = None,
    ) -> None:
        """
        Initialize VideoFormatNotSupportedError.

        Args:
            file_path: Path to the video file.
            format: The detected or specified format.
            supported_formats: List of supported formats.
        """
        self.format = format
        self.supported_formats = supported_formats or []
        message = f"Video format not supported: {format or 'unknown'}"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"
        super().__init__(message, file_path)


class VideoCorruptedError(VideoError):
    """Raised when a video file is corrupted or unreadable."""

    def __init__(
        self,
        file_path: Path,
        reason: str | None = None,
    ) -> None:
        """
        Initialize VideoCorruptedError.

        Args:
            file_path: Path to the corrupted video file.
            reason: Specific reason for corruption detection.
        """
        self.reason = reason
        message = "Video file is corrupted or unreadable"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)


class VideoCodecNotSupportedError(VideoError):
    """Raised when the video codec is not supported."""

    def __init__(
        self,
        file_path: Path,
        codec: str | None = None,
    ) -> None:
        """
        Initialize VideoCodecNotSupportedError.

        Args:
            file_path: Path to the video file.
            codec: The detected codec.
        """
        self.codec = codec
        message = f"Video codec not supported: {codec or 'unknown'}"
        super().__init__(message, file_path)


class VideoValidationError(VideoError):
    """Raised when video validation fails."""

    def __init__(
        self,
        file_path: Path,
        errors: list[str],
    ) -> None:
        """
        Initialize VideoValidationError.

        Args:
            file_path: Path to the video file.
            errors: List of validation error messages.
        """
        self.errors = errors
        message = f"Video validation failed: {'; '.join(errors)}"
        super().__init__(message, file_path)


class VideoMetadataExtractionError(VideoError):
    """Raised when metadata extraction fails."""

    def __init__(
        self,
        file_path: Path,
        metadata_field: str | None = None,
        reason: str | None = None,
    ) -> None:
        """
        Initialize VideoMetadataExtractionError.

        Args:
            file_path: Path to the video file.
            metadata_field: The field that failed to extract.
            reason: Specific reason for the failure.
        """
        self.metadata_field = metadata_field
        self.reason = reason
        message = "Failed to extract video metadata"
        if metadata_field:
            message += f" ({metadata_field})"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)
