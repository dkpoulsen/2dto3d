"""Video denoising exceptions.

This module provides custom exceptions for the video denoising functionality.
"""

from __future__ import annotations


class VideoDenoisingError(Exception):
    """Base exception for video denoising errors."""

    def __init__(
        self,
        message: str,
        *,
        model_name: str | None = None,
        device: str | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            model_name: Name of the model that caused the error.
            device: Device being used.
            original_exception: Original exception if wrapping.
        """
        super().__init__(message)
        self.model_name = model_name
        self.device = device
        self.original_exception = original_exception


class ModelLoadError(VideoDenoisingError):
    """Exception raised when denoising model loading fails."""

    pass


class InferenceError(VideoDenoisingError):
    """Exception raised when denoising inference fails.

    Attributes:
        attempted_models: List of model names that were attempted before failure.
        original_exceptions: List of original exceptions from each attempt.
    """

    def __init__(
        self,
        message: str,
        *,
        attempted_models: list[str] | None = None,
        original_exceptions: list[Exception] | None = None,
        **kwargs,
    ) -> None:
        """Initialize the inference error.

        Args:
            message: Error description.
            attempted_models: List of model names that were attempted.
            original_exceptions: List of exceptions from each attempt.
            **kwargs: Additional arguments passed to parent.
        """
        super().__init__(message, **kwargs)
        self.attempted_models = attempted_models or []
        self.original_exceptions = original_exceptions or []

class UnsupportedModelError(VideoDenoisingError):
    """Exception raised when an unsupported model type is requested."""

    pass


class PretrainedModelError(VideoDenoisingError):
    """Exception raised when pretrained model download/loading fails."""

    pass


class FrameBufferError(VideoDenoisingError):
    """Exception raised when frame buffer operations fail."""

    def __init__(
        self,
        message: str,
        *,
        buffer_size: int | None = None,
        required_frames: int | None = None,
        **kwargs,
    ) -> None:
        """Initialize the error.

        Args:
            message: Error description.
            buffer_size: Current buffer size.
            required_frames: Number of frames required.
            **kwargs: Additional arguments passed to parent.
        """
        super().__init__(message, **kwargs)
        self.buffer_size = buffer_size
        self.required_frames = required_frames


__all__ = [
    "VideoDenoisingError",
    "ModelLoadError",
    "InferenceError",
    "UnsupportedModelError",
    "PretrainedModelError",
    "FrameBufferError",
]
