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


class FrameExtractionError(VideoError):
    """Raised when frame extraction fails."""

    def __init__(
        self,
        file_path: Path,
        frame_number: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize FrameExtractionError.

        Args:
            file_path: Path to the video file.
            frame_number: The frame number that failed to extract.
            reason: Specific reason for the failure.
        """
        self.frame_number = frame_number
        self.reason = reason
        message = "Failed to extract frame"
        if frame_number is not None:
            message += f" at index {frame_number}"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)


class FrameBufferError(VideoError):
    """Raised when frame buffer operations fail."""

    def __init__(
        self,
        message: str,
        buffer_size: int | None = None,
        file_path: Path | None = None,
    ) -> None:
        """Initialize FrameBufferError.

        Args:
            message: Error description.
            buffer_size: Current buffer size if available.
            file_path: Path to the video file.
        """
        self.buffer_size = buffer_size
        super().__init__(message, file_path)


class MemoryLimitExceededError(VideoError):
    """Raised when memory limit is exceeded during frame extraction."""

    def __init__(
        self,
        file_path: Path,
        required_mb: float,
        available_mb: float,
    ) -> None:
        """Initialize MemoryLimitExceededError.

        Args:
            file_path: Path to the video file.
            required_mb: Required memory in megabytes.
            available_mb: Available memory in megabytes.
        """
        self.required_mb = required_mb
        self.available_mb = available_mb
        message = (
            f"Memory limit exceeded: required {required_mb:.1f}MB, "
            f"available {available_mb:.1f}MB"
        )
        super().__init__(message, file_path)


class InvalidSamplingStrategyError(VideoError):
    """Raised when an invalid sampling strategy is specified."""

    def __init__(
        self,
        strategy: str,
        valid_strategies: list[str] | None = None,
    ) -> None:
        """Initialize InvalidSamplingStrategyError.

        Args:
            strategy: The invalid strategy name.
            valid_strategies: List of valid strategy names.
        """
        self.strategy = strategy
        self.valid_strategies = valid_strategies or []
        message = f"Invalid sampling strategy: {strategy}"
        if self.valid_strategies:
            message += f". Valid strategies: {', '.join(self.valid_strategies)}"
        super().__init__(message)


class VideoWriteError(VideoError):
    """Raised when video writing fails."""

    def __init__(
        self,
        file_path: Path,
        reason: str | None = None,
    ) -> None:
        """Initialize VideoWriteError.

        Args:
            file_path: Path to the output video file.
            reason: Specific reason for the failure.
        """
        self.reason = reason
        message = "Failed to write video"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)


class FFmpegProcessError(VideoError):
    """Raised when FFmpeg process fails."""

    def __init__(
        self,
        file_path: Path | None,
        return_code: int | None = None,
        stderr_output: str | None = None,
        command: list[str] | None = None,
    ) -> None:
        """Initialize FFmpegProcessError.

        Args:
            file_path: Path to the video file.
            return_code: FFmpeg process return code.
            stderr_output: FFmpeg stderr output.
            command: The FFmpeg command that failed.
        """
        self.return_code = return_code
        self.stderr_output = stderr_output
        self.command = command
        message = "FFmpeg process failed"
        if return_code is not None:
            message += f" (return code: {return_code})"
        if stderr_output:
            # Truncate very long error messages
            truncated = stderr_output[:500] + "..." if len(stderr_output) > 500 else stderr_output
            message += f": {truncated}"
        super().__init__(message, file_path)


class AudioProcessingError(VideoError):
    """Raised when audio processing fails."""

    def __init__(
        self,
        file_path: Path | None,
        reason: str | None = None,
    ) -> None:
        """Initialize AudioProcessingError.

        Args:
            file_path: Path to the video file.
            reason: Specific reason for the failure.
        """
        self.reason = reason
        message = "Failed to process audio"
        if reason:
            message += f": {reason}"
        super().__init__(message, file_path)


class InvalidVideoDimensionsError(VideoError):
    """Raised when video dimensions are invalid for the encoder."""

    def __init__(
        self,
        width: int,
        height: int,
        reason: str | None = None,
    ) -> None:
        """Initialize InvalidVideoDimensionsError.

        Args:
            width: Video width.
            height: Video height.
            reason: Specific reason for the failure.
        """
        self.width = width
        self.height = height
        self.reason = reason
        message = f"Invalid video dimensions: {width}x{height}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
