"""Video denoiser selector with automatic model selection and fallback.

This module provides a unified interface for video denoising that automatically
selects the best available model and handles fallback between different models.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

import numpy as np

from video2d3d.utils.logger import get_logger

from .base import VideoDenoiserBase
from .basicvsr_plusplus import BasicVSRPlusPlusDenoiser
from .config import DenoiserModelType, VideoDenoiserConfig
from .exceptions import InferenceError, VideoDenoisingError
from .fastdvdnet import FastDVDNetDenoiser

if TYPE_CHECKING:
    pass


class VideoDenoiserSelector:
    """Unified video denoising with automatic model selection and fallback.

    This class provides a single interface for video denoising that handles
    model selection, loading, and fallback automatically.

    Example usage:
        ```python
        # Basic usage
        config = VideoDenoiserConfig(
            model_type=DenoiserModelType.FASTDVDNET,
            enable_fallback=True,
        )
        selector = VideoDenoiserSelector(config=config)
        denoised_frames = selector.denoise_frames(frames)

        # Context manager
        with VideoDenoiserSelector() as selector:
            denoised = selector.denoise_frames(frames)
        ```
    """

    def __init__(
        self,
        config: Optional[VideoDenoiserConfig] = None,
        *,
        model_type: str = "fastdvdnet",
        device: str = "auto",
        cache_dir: Optional[Path] = None,
    ) -> None:
        """Initialize the video denoiser selector.

        Args:
            config: VideoDenoiserConfig object. If provided, model_type and device
                   are ignored.
            model_type: Primary model type to use.
            device: Device for inference.
            cache_dir: Directory to cache downloaded models.
        """
        if config is not None:
            self.config = config
        else:
            self.config = VideoDenoiserConfig(
                model_type=DenoiserModelType.from_string(model_type),
                device=device,
            )

        self._cache_dir = cache_dir

        # Loaded denoisers cache
        self._denoisers: dict[DenoiserModelType, VideoDenoiserBase] = {}
        self._active_model: Optional[DenoiserModelType] = None

        self._logger = get_logger("denoising.selector")
        self._logger.info(
            f"VideoDenoiserSelector initialized: model={self.config.model_type.value}, "
            f"enabled={self.config.enabled}, device={self.config.device}"
        )

    @property
    def active_model(self) -> Optional[DenoiserModelType]:
        """Get the currently active model type."""
        return self._active_model

    @property
    def is_enabled(self) -> bool:
        """Check if denoising is enabled."""
        return self.config.enabled and self.config.model_type != DenoiserModelType.NONE

    def _get_denoiser(self, model_type: DenoiserModelType) -> VideoDenoiserBase:
        """Get or create a denoiser for the specified model type.

        Args:
            model_type: Model type to get denoiser for.

        Returns:
            Denoiser instance for the model.

        Raises:
            VideoDenoisingError: If model loading fails.
        """
        if model_type in self._denoisers:
            return self._denoisers[model_type]

        try:
            denoiser = self._create_denoiser(model_type)
            self._denoisers[model_type] = denoiser
            return denoiser
        except Exception as e:
            self._logger.warning(f"Failed to create {model_type.value} denoiser: {e}")
            raise

    def _create_denoiser(self, model_type: DenoiserModelType) -> VideoDenoiserBase:
        """Create a new denoiser for the specified model type.

        Args:
            model_type: Model type to create denoiser for.

        Returns:
            New denoiser instance.

        Raises:
            VideoDenoisingError: If model creation fails.
        """
        if model_type == DenoiserModelType.FASTDVDNET:
            return FastDVDNetDenoiser(
                config=self.config.fastdvdnet,
                device=self.config.device,
                cache_dir=self._cache_dir,
            )
        elif model_type in (DenoiserModelType.BASICVSR_PLUSPLUS, DenoiserModelType.BASICVSR):
            return BasicVSRPlusPlusDenoiser(
                config=self.config.basicvsr_plusplus,
                device=self.config.device,
                cache_dir=self._cache_dir,
            )
        else:
            raise VideoDenoisingError(
                f"Unknown model type: {model_type}",
                model_name=model_type.value,
            )

    def _build_attempt_order(self) -> List[DenoiserModelType]:
        """Build the order of models to try.

        Returns:
            List of model types to try in order.
        """
        if not self.config.enable_fallback:
            return [self.config.model_type]

        # Start with primary model
        attempt_order = [self.config.model_type]

        # Add fallback chain
        for model in self.config.fallback_chain:
            if model not in attempt_order and model != DenoiserModelType.NONE:
                attempt_order.append(model)

        return attempt_order

    def denoise_frames(
        self,
        frames: List[np.ndarray],
    ) -> List[np.ndarray]:
        """Denoise a sequence of frames with automatic model selection and fallback.

        Args:
            frames: List of input frames as numpy arrays (H, W, C) in RGB format.

        Returns:
            List of denoised frames.

        Raises:
            InferenceError: If all models fail.
        """
        # If denoising is disabled, return frames unchanged
        if not self.is_enabled:
            return frames

        if not frames:
            return frames

        start_time = time.time()

        # Build attempt order
        attempt_order = self._build_attempt_order()

        # Try each model
        errors: List[tuple[DenoiserModelType, Exception]] = []

        for model_type in attempt_order:
            try:
                denoiser = self._get_denoiser(model_type)
                result = denoiser.denoise_frames(frames)
                self._active_model = model_type

                elapsed_ms = (time.time() - start_time) * 1000
                self._logger.debug(
                    f"Denoising completed with {model_type.value} in {elapsed_ms:.2f}ms"
                )

                return result

            except Exception as e:
                self._logger.warning(f"Model {model_type.value} failed: {e}. Trying next model...")
                errors.append((model_type, e))
                continue

        # All models failed
        error_msg = f"All denoising models failed. Attempted: {[m.value for m, _ in errors]}"
        self._logger.error(error_msg)

        # If fallback to original frames is desired, return them
        # Otherwise, raise an error
        if self.config.enable_fallback and errors:
            self._logger.warning("All denoising models failed. Returning original frames.")
            return frames

        raise InferenceError(
            error_msg,
            attempted_models=[m.value for m, _ in errors],
            original_exceptions=[e for _, e in errors],
        )

    def denoise_frame(
        self,
        frame: np.ndarray,
        context_frames: Optional[List[np.ndarray]] = None,
    ) -> np.ndarray:
        """Denoise a single frame using optional temporal context.

        Args:
            frame: Input frame as numpy array (H, W, C) in RGB format.
            context_frames: Optional list of surrounding frames for temporal context.

        Returns:
            Denoised frame as numpy array.

        Raises:
            InferenceError: If denoising fails.
        """
        if not self.is_enabled:
            return frame

        if context_frames is None:
            context_frames = [frame]

        denoised = self.denoise_frames(context_frames)

        # Return the center frame (the denoised version of the input)
        center_idx = len(denoised) // 2
        return denoised[center_idx]

    def get_available_models(self) -> List[DenoiserModelType]:
        """Get list of available model types.

        Returns:
            List of model types that are available (successfully loaded).
        """
        return list(self._denoisers.keys())

    def preload_models(
        self,
        models: Optional[List[Union[str, DenoiserModelType]]] = None,
    ) -> dict[str, bool]:
        """Preload specified models or all models in fallback chain.

        Args:
            models: List of models to preload. If None, preloads fallback chain.

        Returns:
            Dictionary mapping model names to load success status.
        """
        if models is None:
            models = [self.config.model_type] + self.config.fallback_chain
        else:
            models = [DenoiserModelType.from_string(m) if isinstance(m, str) else m for m in models]

        results: dict[str, bool] = {}

        for model_type in models:
            if model_type == DenoiserModelType.NONE:
                continue

            try:
                self._get_denoiser(model_type)
                results[model_type.value] = True
                self._logger.info(f"Preloaded model: {model_type.value}")
            except Exception as e:
                results[model_type.value] = False
                self._logger.warning(f"Failed to preload {model_type.value}: {e}")

        return results

    def switch_model(self, model_type: Union[str, DenoiserModelType]) -> bool:
        """Switch to a different model.

        Args:
            model_type: Model type to switch to.

        Returns:
            True if switch was successful, False otherwise.
        """
        if isinstance(model_type, str):
            model_type = DenoiserModelType.from_string(model_type)

        try:
            self._get_denoiser(model_type)
            self._active_model = model_type
            self._logger.info(f"Switched to model: {model_type.value}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to switch to model {model_type.value}: {e}")
            return False

    def close(self) -> None:
        """Release all loaded model resources."""
        for model_type, denoiser in self._denoisers.items():
            try:
                denoiser.close()
            except Exception as e:
                self._logger.warning(f"Error closing {model_type.value}: {e}")

        self._denoisers.clear()
        self._active_model = None
        self._logger.debug("VideoDenoiserSelector resources released")

    def __enter__(self) -> VideoDenoiserSelector:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        self.close()


def create_video_denoiser(
    model_type: str = "fastdvdnet",
    enabled: bool = True,
    device: str = "auto",
    **kwargs,
) -> VideoDenoiserSelector:
    """Create a video denoiser with the specified configuration.

    Args:
        model_type: Model type string ('fastdvdnet', 'basicvsr_plusplus', etc.).
        enabled: Whether denoising is enabled.
        device: Device for inference.
        **kwargs: Additional VideoDenoiserConfig field values.

    Returns:
        Configured VideoDenoiserSelector instance.
    """
    config = VideoDenoiserConfig(
        enabled=enabled,
        model_type=DenoiserModelType.from_string(model_type),
        device=device,
        **kwargs,
    )
    return VideoDenoiserSelector(config=config)


def denoise_frames_auto(
    frames: List[np.ndarray],
    model_type: str = "fastdvdnet",
    device: str = "auto",
) -> List[np.ndarray]:
    """Denoise frames with automatic model selection (convenience function).

    Args:
        frames: List of input frames as numpy arrays.
        model_type: Model type string.
        device: Device for inference.

    Returns:
        List of denoised frames.
    """
    with create_video_denoiser(model_type=model_type, device=device) as denoiser:
        return denoiser.denoise_frames(frames)


__all__ = [
    "VideoDenoiserSelector",
    "create_video_denoiser",
    "denoise_frames_auto",
]
