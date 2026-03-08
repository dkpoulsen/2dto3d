"""FastDVDNet video denoiser implementation.

This module implements the FastDVDNet video denoising model.
FastDVDNet is a fast and efficient video denoising network that uses
temporal information from multiple frames to reduce noise.

Reference:
    "FastDVDNet: Towards Real-Time Deep Video Denoising Without Flow Estimation"
    https://arxiv.org/abs/2006.07669

GitHub: https://github.com/m-tassano/fastdvdnet
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import numpy as np
import torch
import torch.nn as nn

from video2d3d.utils.gpu import clear_gpu_memory
from video2d3d.utils.logger import log_exception

from .base import VideoDenoiserBase
from .config import FastDVDNetConfig
from .exceptions import InferenceError, ModelLoadError, PretrainedModelError

if TYPE_CHECKING:
    pass


# Default model URL
_FASTDVDNET_MODEL_URL = "https://github.com/m-tassano/fastdvdnet/releases/download/v1.0/model.pt"

# Default number of frames
_DEFAULT_NUM_FRAMES = 5


class FastDVDNetModel(nn.Module):
    """FastDVDNet neural network architecture.

    This implements the FastDVDNet architecture for video denoising.
    It uses a compact CNN with temporal information from multiple frames.
    """

    def __init__(
        self,
        num_input_frames: int = 5,
        num_layers: int = 8,
        num_features: int = 64,
    ) -> None:
        """Initialize FastDVDNet model.

        Args:
            num_input_frames: Number of input frames (odd number).
            num_layers: Number of convolutional layers.
            num_features: Number of features in intermediate layers.
        """
        super().__init__()
        self.num_input_frames = num_input_frames
        self.num_layers = num_layers
        self.num_features = num_features

        # Input: num_frames * 3 channels
        in_channels = num_input_frames * 3

        # Build the network layers
        layers = []

        # First layer
        layers.append(nn.Conv2d(in_channels, num_features, kernel_size=3, padding=1))
        layers.append(nn.ReLU(inplace=True))

        # Middle layers
        for _ in range(num_layers - 2):
            layers.append(nn.Conv2d(num_features, num_features, kernel_size=3, padding=1))
            layers.append(nn.ReLU(inplace=True))

        # Output layer (residual learning)
        layers.append(nn.Conv2d(num_features, 3, kernel_size=3, padding=1))

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (B, T*C, H, W) where T is num_input_frames.

        Returns:
            Denoised tensor of shape (B, 3, H, W).
        """
        # Learn the noise residual
        residual = self.net(x)

        # Extract the center frame
        center_idx = self.num_input_frames // 2
        center_frame = x[:, center_idx * 3 : (center_idx + 1) * 3, :, :]

        # Subtract residual from center frame
        return center_frame - residual


class FastDVDNetDenoiser(VideoDenoiserBase):
    """FastDVDNet video denoiser.

    FastDVDNet is a fast video denoising network that uses temporal information
    from multiple frames to reduce noise. It is designed for real-time
    video denoising applications.

    Example usage:
        ```python
        from video2d3d.denoising import FastDVDNetDenoiser, FastDVDNetConfig

        # Basic usage
        config = FastDVDNetConfig(num_input_frames=5)
        denoiser = FastDVDNetDenoiser(config=config)
        denoised_frames = denoiser.denoise_frames(frames)

        # Context manager
        with FastDVDNetDenoiser() as denoiser:
            denoised = denoiser.denoise_frame(frame, context_frames)
        ```
    """

    def __init__(
        self,
        config: Optional[FastDVDNetConfig] = None,
        *,
        device: str = "auto",
        cache_dir: Optional[Path] = None,
    ) -> None:
        """Initialize FastDVDNet denoiser.

        Args:
            config: Configuration for FastDVDNet.
            device: Device for inference ('cuda', 'cpu', or 'auto').
            cache_dir: Directory to cache downloaded models.
        """
        self._fastdvdnet_config = config or FastDVDNetConfig()
        self._cache_dir = cache_dir
        self._model: Optional[nn.Module] = None

        super().__init__(
            model_name="fastdvdnet",
            device=device,
        )

    @property
    def num_input_frames(self) -> int:
        """Get the number of input frames required."""
        return self._fastdvdnet_config.num_input_frames

    @property
    def model(self) -> Optional[nn.Module]:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    def _get_model_path(self) -> Path:
        """Get the path to the model weights."""
        if self._fastdvdnet_config.pretrained_model is not None:
            return self._fastdvdnet_config.pretrained_model

        if self._cache_dir is not None:
            return self._cache_dir / "fastdvdnet_model.pt"

        # Use default torch hub directory
        hub_dir = Path(torch.hub.get_dir())
        return hub_dir / "fastdvdnet_model.pt"

    def _download_model(self, path: Path) -> None:
        """Download pretrained model weights.

        Args:
            path: Path to save the model weights.

        Raises:
            PretrainedModelError: If download fails.
        """
        self.logger.info(f"Downloading FastDVDNet model to {path}")

        try:
            import urllib.request

            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(_FASTDVDNET_MODEL_URL, str(path))
            self.logger.info("Model downloaded successfully")

        except Exception as e:
            raise PretrainedModelError(
                f"Failed to download FastDVDNet model: {e}",
                model_name="fastdvdnet",
                original_exception=e,
            ) from e

    def load_model(self) -> None:
        """Load the FastDVDNet model.

        This method:
        1. Downloads model weights if not cached
        2. Creates the model architecture
        3. Loads the weights
        4. Moves the model to the target device

        Raises:
            ModelLoadError: If model loading fails.
        """
        self.logger.info("Loading FastDVDNet model")
        start_time = time.time()

        try:
            # Get model path
            model_path = self._get_model_path()

            # Download if needed and auto_download is enabled
            if not model_path.exists() and self._fastdvdnet_config.auto_download:
                self._download_model(model_path)

            # Create model architecture
            self._model = FastDVDNetModel(
                num_input_frames=self._fastdvdnet_config.num_input_frames,
            )

            # Load weights if available
            if model_path.exists():
                state_dict = torch.load(model_path, map_location="cpu")
                self._model.load_state_dict(state_dict)
                self.logger.debug(f"Loaded weights from {model_path}")
            else:
                # Initialize with random weights (not recommended for production)
                self.logger.warning(
                    "No pretrained weights found. Using random initialization. "
                    "Set auto_download=True to download pretrained weights."
                )

            # Move to device
            self._model = self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.info(f"FastDVDNet model loaded in {elapsed_ms:.0f}ms on {self._device}")

        except Exception as e:
            log_exception("Failed to load FastDVDNet model", exception=e)
            raise ModelLoadError(
                f"Failed to load FastDVDNet model: {e}",
                model_name="fastdvdnet",
                device=self._device,
                original_exception=e,
            ) from e

    def _preprocess_frames(self, frames: List[np.ndarray]) -> torch.Tensor:
        """Preprocess frames for the model.

        Converts frames from numpy arrays to normalized tensor.

        Args:
            frames: List of input frames (H, W, C) uint8.

        Returns:
            Tensor of shape (1, T*C, H, W) where T is num_input_frames.
        """
        # Stack frames and convert to tensor
        frame_tensors = []
        for frame in frames:
            # Convert to float and normalize to [0, 1]
            tensor = torch.from_numpy(frame.astype(np.float32) / 255.0)
            # Change from (H, W, C) to (C, H, W)
            tensor = tensor.permute(2, 0, 1)
            frame_tensors.append(tensor)

        # Concatenate along channel dimension
        batch_tensor = torch.cat(frame_tensors, dim=0)

        # Add batch dimension
        batch_tensor = batch_tensor.unsqueeze(0)

        return batch_tensor

    def _postprocess_frame(self, tensor: torch.Tensor) -> np.ndarray:
        """Postprocess model output to frame.

        Args:
            tensor: Output tensor of shape (1, C, H, W).

        Returns:
            Numpy array of shape (H, W, C) uint8.
        """
        # Remove batch dimension
        tensor = tensor.squeeze(0)

        # Change from (C, H, W) to (H, W, C)
        tensor = tensor.permute(1, 2, 0)

        # Clip and convert to uint8
        frame = tensor.clamp(0, 1).numpy()
        frame = (frame * 255).astype(np.uint8)

        return frame

    def _denoise_frames_impl(
        self,
        frames: List[np.ndarray],
        **kwargs,
    ) -> List[np.ndarray]:
        """Implement FastDVDNet denoising logic.

        Args:
            frames: List of input frames as numpy arrays.
            **kwargs: Additional parameters (ignored for FastDVDNet).

        Returns:
            List of denoised frames.
        """
        if self._model is None:
            raise InferenceError(
                "Model not loaded",
                model_name="fastdvdnet",
                device=self._device,
            )

        denoised_frames = []
        num_frames = len(frames)
        num_context = self._fastdvdnet_config.num_input_frames
        half_context = num_context // 2

        # Process frames with sliding window
        for i in range(num_frames):
            # Gather context frames with reflection padding at boundaries
            context_indices = list(range(i - half_context, i + half_context + 1))
            context_indices = [max(0, min(idx, num_frames - 1)) for idx in context_indices]
            context_frames = [frames[idx] for idx in context_indices]

            # Preprocess
            input_tensor = self._preprocess_frames(context_frames)
            input_tensor = input_tensor.to(self._device)

            # Denoise
            with torch.no_grad():
                output_tensor = self._model(input_tensor)

            # Postprocess
            denoised_frame = self._postprocess_frame(output_tensor)
            denoised_frames.append(denoised_frame)

        return denoised_frames

    def close(self) -> None:
        """Release model resources."""
        if self._model is not None:
            del self._model
            self._model = None

        self._is_loaded = False

        if self._device.startswith("cuda"):
            clear_gpu_memory(self._device)

        self.logger.debug("FastDVDNet resources released")


def create_fastdvdnet_denoiser(
    num_input_frames: int = 5,
    device: str = "auto",
    auto_download: bool = True,
    **kwargs,
) -> FastDVDNetDenoiser:
    """Create a FastDVDNet denoiser with the specified configuration.

    Args:
        num_input_frames: Number of input frames for temporal context.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        auto_download: Whether to automatically download pretrained weights.
        **kwargs: Additional FastDVDNetConfig field values.

    Returns:
        Configured FastDVDNetDenoiser instance.
    """
    config = FastDVDNetConfig(
        num_input_frames=num_input_frames,
        auto_download=auto_download,
        **kwargs,
    )
    return FastDVDNetDenoiser(config=config, device=device)


__all__ = [
    "FastDVDNetDenoiser",
    "FastDVDNetModel",
    "FastDVDNetConfig",
    "create_fastdvdnet_denoiser",
]
