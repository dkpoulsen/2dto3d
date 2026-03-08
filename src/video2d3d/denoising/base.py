"""Abstract base class for video denoisers.

This module provides the abstract base class that all video denoising
implementations must follow.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

import numpy as np

from video2d3d.utils.logger import get_logger, log_model_inference

from .exceptions import InferenceError

if TYPE_CHECKING:
    from loguru import Logger

    from .config import VideoDenoiserConfig


class VideoDenoiserBase(ABC):
    """Abstract base class for video denoisers.

    All video denoising implementations (FastDVDNet, BasicVSR++, etc.)
    must inherit from this class and implement its abstract methods.

    The base class provides common functionality including:
    - Model loading and caching
    - Input validation
    - Progress tracking
    - Error handling
    - Resource management

    Example usage:
        ```python
        class FastDVDNetDenoiser(VideoDenoiserBase):
            def load_model(self) -> None:
                # Load model weights
                pass

            def _denoise_frames_impl(self, frames: List[np.ndarray]) -> List[np.ndarray]:
                # Implement denoising
                pass
        ```
    """

    def __init__(
        self,
        config: Optional[VideoDenoiserConfig] = None,
        *,
        model_name: str = "unknown",
        device: str = "auto",
    ) -> None:
        """Initialize the video denoiser.

        Args:
            config: Configuration for the denoiser.
            model_name: Name of the model (for logging).
            device: Device for inference.
        """
        self._config = config
        self._model_name = model_name
        self._device = device
        self._is_loaded: bool = False
        self._logger: Optional[Logger] = None

    @property
    def config(self) -> Optional[VideoDenoiserConfig]:
        """Get the configuration."""
        return self._config

    @property
    def is_loaded(self) -> bool:
        """Check if the model is loaded."""
        return self._is_loaded

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def device(self) -> str:
        """Get the device being used."""
        return self._device

    @property
    def logger(self) -> Logger:
        """Get the logger (lazy initialization)."""
        if self._logger is None:
            self._logger = get_logger(f"denoising.{self._model_name}")
        return self._logger

    @property
    @abstractmethod
    def num_input_frames(self) -> int:
        """Get the number of input frames required for temporal processing.

        Returns:
            Number of frames needed for one denoising operation.
        """
        pass

    @abstractmethod
    def load_model(self) -> None:
        """Load the denoising model.

        This method should:
        1. Load pretrained weights
        2. Move model to device
        3. Set model to evaluation mode
        4. Set _is_loaded to True

        Raises:
            ModelLoadError: If model loading fails.
        """
        pass

    @abstractmethod
    def _denoise_frames_impl(
        self,
        frames: List[np.ndarray],
        **kwargs,
    ) -> List[np.ndarray]:
        """Implement the actual denoising logic.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
            **kwargs: Additional model-specific parameters.

        Returns:
            List of denoised frames as numpy arrays.

        Raises:
            InferenceError: If denoising fails.
        """
        pass

    def _validate_input(self, frames: List[np.ndarray]) -> None:
        """Validate input frames.

        Args:
            frames: List of input frames to validate.

        Raises:
            InferenceError: If validation fails.
        """
        if not frames:
            raise InferenceError(
                "Input frames list cannot be empty",
                model_name=self._model_name,
                device=self._device,
            )

        for i, frame in enumerate(frames):
            if not isinstance(frame, np.ndarray):
                raise InferenceError(
                    f"Frame {i} must be a numpy array, got {type(frame).__name__}",
                    model_name=self._model_name,
                    device=self._device,
                )
            if frame.ndim != 3:
                raise InferenceError(
                    f"Frame {i} must be 3D array (H, W, C), got {frame.ndim}D",
                    model_name=self._model_name,
                    device=self._device,
                )
            if frame.shape[2] != 3:
                raise InferenceError(
                    f"Frame {i} must have 3 channels (RGB), got {frame.shape[2]}",
                    model_name=self._model_name,
                    device=self._device,
                )

    def _ensure_loaded(self) -> None:
        """Ensure the model is loaded.

        Raises:
            InferenceError: If model is not loaded and cannot be loaded.
        """
        if not self._is_loaded:
            try:
                self.load_model()
            except Exception as e:
                raise InferenceError(
                    f"Failed to load model: {e}",
                    model_name=self._model_name,
                    device=self._device,
                    original_exception=e,
                ) from e

    def denoise_frames(
        self,
        frames: List[np.ndarray],
        **kwargs,
    ) -> List[np.ndarray]:
        """Denoise a sequence of frames.

        This is the main entry point for denoising. It handles:
        - Model loading (lazy)
        - Input validation
        - Timing and logging
        - Error handling

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.
                   Expected dtype: uint8 with values 0-255.
            **kwargs: Additional model-specific parameters.

        Returns:
            List of denoised frames as numpy arrays in the same format.

        Raises:
            InferenceError: If denoising fails.
        """
        self._validate_input(frames)
        self._ensure_loaded()

        start_time = time.time()
        self.logger.debug(f"Denoising {len(frames)} frames with {self._model_name}")

        try:
            result = self._denoise_frames_impl(frames, **kwargs)

            elapsed_ms = (time.time() - start_time) * 1000
            log_model_inference(
                model_name=self._model_name,
                batch_size=len(frames),
                inference_time_ms=elapsed_ms,
                operation="denoise",
            )

            self.logger.debug(
                f"Denoising completed: {len(frames)} frames in {elapsed_ms:.2f}ms "
                f"({elapsed_ms / len(frames):.2f}ms/frame)"
            )

            return result

        except InferenceError:
            raise
        except Exception as e:
            self.logger.error(f"Denoising failed: {e}")
            raise InferenceError(
                f"Denoising failed: {e}",
                model_name=self._model_name,
                device=self._device,
                original_exception=e,
            ) from e

    def denoise_frame(
        self,
        frame: np.ndarray,
        context_frames: Optional[List[np.ndarray]] = None,
        **kwargs,
    ) -> np.ndarray:
        """Denoise a single frame using optional temporal context.

        For temporal denoisers, context_frames provides the surrounding
        frames needed for temporal processing.

        Args:
            frame: Input frame as numpy array (H, W, C) in RGB format.
            context_frames: Optional list of surrounding frames for temporal context.
            **kwargs: Additional model-specific parameters.

        Returns:
            Denoised frame as numpy array.

        Raises:
            InferenceError: If denoising fails.
        """
        if context_frames is None:
            # If no context provided, duplicate the frame
            context_frames = [frame] * self.num_input_frames
        else:
            # Include the current frame
            context_frames = list(context_frames)

        denoised = self.denoise_frames(context_frames, **kwargs)

        # Return the center frame (the denoised version of the input)
        center_idx = len(denoised) // 2
        return denoised[center_idx]

    def close(self) -> None:
        """Release model resources.

        Subclasses should override this method to properly release
        GPU memory and other resources.
        """
        self._is_loaded = False
        self.logger.debug(f"{self._model_name} resources released")

    def __enter__(self) -> VideoDenoiserBase:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.close()


__all__ = [
    "VideoDenoiserBase",
]
