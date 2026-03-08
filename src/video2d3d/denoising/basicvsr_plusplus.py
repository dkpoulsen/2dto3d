"""BasicVSR++ video denoiser implementation.

This module implements the BasicVSR++ video restoration model.
BasicVSR++ is a high-quality video restoration network that supports
denoising, super-resolution, and other restoration tasks.

Reference:
    "BasicVSR++: Improving Video Super-Resolution with Enhanced Propagation and Alignment"
    https://arxiv.org/abs/2104.13371

GitHub: https://github.com/ckkelvinchan/BasicVSR_PlusPlus
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from video2d3d.utils.gpu import clear_gpu_memory
from video2d3d.utils.logger import log_exception

from .base import VideoDenoiserBase
from .config import BasicVSRPlusPlusConfig
from .exceptions import InferenceError, ModelLoadError, PretrainedModelError

if TYPE_CHECKING:
    pass


# Model configuration
_BASICVSR_PLUSPLUS_MODEL_URL = "https://github.com/ckkelvinchan/BasicVSR_PlusPlus/releases/download/v1.0/basicvsr_plusplus_ntire_deblur.pth"
_DEFAULT_NUM_FRAMES = 15


class SPyNetBasic(nn.Module):
    """Simplified SPyNet for optical flow estimation.

    This is a lightweight version of SPyNet for computing optical flow
    between adjacent frames.
    """

    def __init__(self) -> None:
        """Initialize SPyNet basic."""
        super().__init__()
        # Simplified flow estimation network
        self.flow_conv = nn.Sequential(
            nn.Conv2d(6, 32, kernel_size=7, padding=3),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=7, padding=3),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 32, kernel_size=7, padding=3),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 2, kernel_size=7, padding=3),
        )

    def forward(self, ref: torch.Tensor, supp: torch.Tensor) -> torch.Tensor:
        """Estimate optical flow from supp to ref.

        Args:
            ref: Reference frame (B, C, H, W).
            supp: Support frame (B, C, H, W).

        Returns:
            Flow tensor (B, 2, H, W).
        """
        # Concatenate frames
        x = torch.cat([ref, supp], dim=1)
        return self.flow_conv(x)


class ResidualBlock(nn.Module):
    """Residual block for BasicVSR++."""

    def __init__(self, num_features: int = 64) -> None:
        """Initialize residual block.

        Args:
            num_features: Number of features.
        """
        super().__init__()
        self.conv1 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        residual = x
        x = self.relu(self.conv1(x))
        x = self.conv2(x)
        return x + residual


class PropagationBlock(nn.Module):
    """Propagation block for temporal information."""

    def __init__(self, num_features: int = 64) -> None:
        """Initialize propagation block.

        Args:
            num_features: Number of features.
        """
        super().__init__()
        self.flow_net = SPyNetBasic()
        self.warp_conv = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.fusion = nn.Sequential(
            nn.Conv2d(num_features * 3, num_features, kernel_size=1),
            nn.ReLU(inplace=True),
            ResidualBlock(num_features),
        )

    def forward(
        self,
        current: torch.Tensor,
        prev_feat: torch.Tensor | None,
    ) -> torch.Tensor:
        """Forward pass with temporal propagation.

        Args:
            current: Current frame features (B, C, H, W).
            prev_feat: Previous frame features (B, C, H, W) or None.

        Returns:
            Propagated features (B, C, H, W).
        """
        if prev_feat is None:
            return self.fusion(torch.cat([current, current, current], dim=1))

        # Estimate flow from current to previous
        # Use mean of features as pseudo-frame for flow
        current_pseudo = current.mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)
        prev_pseudo = prev_feat.mean(dim=1, keepdim=True).expand(-1, 3, -1, -1)
        flow = self.flow_net(current_pseudo, prev_pseudo)

        # Warp previous features
        warped_prev = self._warp(prev_feat, flow)

        # Fuse features
        return self.fusion(torch.cat([current, warped_prev, current], dim=1))

    def _warp(self, x: torch.Tensor, flow: torch.Tensor) -> torch.Tensor:
        """Warp features using optical flow.

        Args:
            x: Features to warp (B, C, H, W).
            flow: Optical flow (B, 2, H, W).

        Returns:
            Warped features (B, C, H, W).
        """
        B, C, H, W = x.size()

        # Create grid
        grid_y, grid_x = torch.meshgrid(
            torch.arange(H, device=x.device), torch.arange(W, device=x.device), indexing="ij"
        )
        grid = torch.stack([grid_x, grid_y], dim=-1).float()  # (H, W, 2)
        grid = grid.unsqueeze(0).expand(B, -1, -1, -1)  # (B, H, W, 2)

        # Add flow to grid
        flow_permuted = flow.permute(0, 2, 3, 1)  # (B, H, W, 2)
        grid_new = grid + flow_permuted

        # Normalize to [-1, 1]
        grid_new[..., 0] = 2.0 * grid_new[..., 0] / (W - 1) - 1.0
        grid_new[..., 1] = 2.0 * grid_new[..., 1] / (H - 1) - 1.0

        # Warp
        return F.grid_sample(
            x, grid_new, mode="bilinear", padding_mode="border", align_corners=True
        )


class BasicVSRPlusPlusModel(nn.Module):
    """BasicVSR++ neural network architecture.

    This implements the BasicVSR++ architecture for video restoration.
    It uses bidirectional propagation with optical flow alignment.
    """

    def __init__(
        self,
        num_in_ch: int = 3,
        num_out_ch: int = 3,
        num_feat: int = 64,
        num_block: int = 7,
        scale: int = 1,
    ) -> None:
        """Initialize BasicVSR++ model.

        Args:
            num_in_ch: Number of input channels.
            num_out_ch: Number of output channels.
            num_feat: Number of features in intermediate layers.
            num_block: Number of residual blocks.
            scale: Super-resolution scale factor (1 for denoising).
        """
        super().__init__()
        self.num_feat = num_feat
        self.scale = scale

        # Feature extraction
        self.feat_extract = nn.Sequential(
            nn.Conv2d(num_in_ch, num_feat, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(num_feat, num_feat, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )

        # Propagation blocks
        self.prop_blocks = nn.ModuleList([PropagationBlock(num_feat) for _ in range(num_block)])

        # Reconstruction
        self.recon = nn.Sequential(
            nn.Conv2d(num_feat, num_feat, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(num_feat, num_out_ch, kernel_size=3, padding=1),
        )

        # Upsampling (if scale > 1)
        if scale > 1:
            self.upsample = nn.Sequential(
                nn.Conv2d(num_feat, num_feat * scale * scale, kernel_size=3, padding=1),
                nn.PixelShuffle(scale),
                nn.ReLU(inplace=True),
            )
        else:
            self.upsample = None

    def forward(self, frames: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            frames: Input tensor of shape (B, T, C, H, W).

        Returns:
            Output tensor of shape (B, T, C, H*scale, W*scale).
        """
        B, T, C, H, W = frames.size()

        # Extract features for all frames
        frames_flat = frames.view(B * T, C, H, W)
        feats = self.feat_extract(frames_flat)
        feats = feats.view(B, T, self.num_feat, H, W)

        # Bidirectional propagation
        outputs = []

        for t in range(T):
            current = feats[:, t, :, :, :]

            # Forward propagation
            prev_feat = None
            for prop_block in self.prop_blocks:
                current = prop_block(current, prev_feat)
                prev_feat = current

            # Reconstruction
            if self.upsample is not None:
                current = self.upsample(current)
            output = self.recon(current)
            outputs.append(output)

        # Stack outputs
        outputs = torch.stack(outputs, dim=1)
        return outputs


class BasicVSRPlusPlusDenoiser(VideoDenoiserBase):
    """BasicVSR++ video denoiser.

    BasicVSR++ is a high-quality video restoration network that uses
    bidirectional propagation with optical flow alignment for effective
    denoising and restoration.

    Example usage:
        ```python
        from video2d3d.denoising import BasicVSRPlusPlusDenoiser, BasicVSRPlusPlusConfig

        # Basic usage
        config = BasicVSRPlusPlusConfig(num_input_frames=15)
        denoiser = BasicVSRPlusPlusDenoiser(config=config)
        denoised_frames = denoiser.denoise_frames(frames)

        # Context manager
        with BasicVSRPlusPlusDenoiser() as denoiser:
            denoised = denoiser.denoise_frame(frame, context_frames)
        ```
    """

    def __init__(
        self,
        config: BasicVSRPlusPlusConfig | None = None,
        *,
        device: str = "auto",
        cache_dir: Path | None = None,
    ) -> None:
        """Initialize BasicVSR++ denoiser.

        Args:
            config: Configuration for BasicVSR++.
            device: Device for inference ('cuda', 'cpu', or 'auto').
            cache_dir: Directory to cache downloaded models.
        """
        self._basicvsr_config = config or BasicVSRPlusPlusConfig()
        self._cache_dir = cache_dir
        self._model: nn.Module | None = None

        super().__init__(
            model_name="basicvsr_plusplus",
            device=device,
        )

    @property
    def num_input_frames(self) -> int:
        """Get the number of input frames required."""
        return self._basicvsr_config.num_input_frames

    @property
    def model(self) -> nn.Module | None:
        """Get the loaded model (loads if not already loaded)."""
        if not self._is_loaded:
            self.load_model()
        return self._model

    def _get_model_path(self) -> Path:
        """Get the path to the model weights."""
        if self._basicvsr_config.pretrained_model is not None:
            return self._basicvsr_config.pretrained_model

        if self._cache_dir is not None:
            return self._cache_dir / "basicvsr_plusplus_model.pth"

        hub_dir = Path(torch.hub.get_dir())
        return hub_dir / "basicvsr_plusplus_model.pth"

    def _download_model(self, path: Path) -> None:
        """Download pretrained model weights.

        Args:
            path: Path to save the model weights.

        Raises:
            PretrainedModelError: If download fails.
        """
        self.logger.info(f"Downloading BasicVSR++ model to {path}")

        try:
            import urllib.request

            path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(_BASICVSR_PLUSPLUS_MODEL_URL, str(path))
            self.logger.info("Model downloaded successfully")

        except Exception as e:
            raise PretrainedModelError(
                f"Failed to download BasicVSR++ model: {e}",
                model_name="basicvsr_plusplus",
                original_exception=e,
            ) from e

    def load_model(self) -> None:
        """Load the BasicVSR++ model.

        This method:
        1. Downloads model weights if not cached
        2. Creates the model architecture
        3. Loads the weights
        4. Moves the model to the target device

        Raises:
            ModelLoadError: If model loading fails.
        """
        self.logger.info("Loading BasicVSR++ model")
        start_time = time.time()

        try:
            # Get model path
            model_path = self._get_model_path()

            # Download if needed
            if not model_path.exists() and self._basicvsr_config.auto_download:
                self._download_model(model_path)

            # Create model architecture
            self._model = BasicVSRPlusPlusModel(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=7,
                scale=self._basicvsr_config.scale,
            )

            # Load weights if available
            if model_path.exists():
                state_dict = torch.load(model_path, map_location="cpu")
                # Handle potential key mismatches
                if any(k.startswith("module.") for k in state_dict):
                    state_dict = {k[7:]: v for k, v in state_dict.items()}
                self._model.load_state_dict(state_dict, strict=False)
                self.logger.debug(f"Loaded weights from {model_path}")
            else:
                self.logger.warning(
                    "No pretrained weights found. Using random initialization. "
                    "Set auto_download=True to download pretrained weights."
                )

            # Move to device
            self._model = self._model.to(self._device)
            self._model.eval()

            self._is_loaded = True

            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.info(f"BasicVSR++ model loaded in {elapsed_ms:.0f}ms on {self._device}")

        except Exception as e:
            log_exception("Failed to load BasicVSR++ model", exception=e)
            raise ModelLoadError(
                f"Failed to load BasicVSR++ model: {e}",
                model_name="basicvsr_plusplus",
                device=self._device,
                original_exception=e,
            ) from e

    def _preprocess_frames(self, frames: list[np.ndarray]) -> torch.Tensor:
        """Preprocess frames for the model.

        Args:
            frames: List of input frames (H, W, C) uint8.

        Returns:
            Tensor of shape (B, T, C, H, W) normalized to [0, 1].
        """
        frame_tensors = []
        for frame in frames:
            # Convert to float and normalize
            tensor = torch.from_numpy(frame.astype(np.float32) / 255.0)
            # (H, W, C) -> (C, H, W)
            tensor = tensor.permute(2, 0, 1)
            frame_tensors.append(tensor)

        # Stack frames: (T, C, H, W)
        stacked = torch.stack(frame_tensors, dim=0)
        # Add batch dimension: (1, T, C, H, W)
        return stacked.unsqueeze(0)

    def _postprocess_frames(self, tensor: torch.Tensor) -> list[np.ndarray]:
        """Postprocess model output to frames.

        Args:
            tensor: Output tensor of shape (B, T, C, H, W).

        Returns:
            List of numpy arrays (H, W, C) uint8.
        """
        # Remove batch dimension: (T, C, H, W)
        tensor = tensor.squeeze(0)

        frames = []
        for i in range(tensor.size(0)):
            frame = tensor[i]
            # (C, H, W) -> (H, W, C)
            frame = frame.permute(1, 2, 0)
            # Clip and convert to uint8
            frame = frame.clamp(0, 1).numpy()
            frame = (frame * 255).astype(np.uint8)
            frames.append(frame)

        return frames

    def _denoise_frames_impl(
        self,
        frames: list[np.ndarray],
        **kwargs,
    ) -> list[np.ndarray]:
        """Implement BasicVSR++ denoising logic.

        Args:
            frames: List of input frames as numpy arrays.
            **kwargs: Additional parameters (ignored).

        Returns:
            List of denoised frames.
        """
        if self._model is None:
            raise InferenceError(
                "Model not loaded",
                model_name="basicvsr_plusplus",
                device=self._device,
            )

        # BasicVSR++ processes all frames together
        input_tensor = self._preprocess_frames(frames)
        input_tensor = input_tensor.to(self._device)

        with torch.no_grad():
            output_tensor = self._model(input_tensor)

        denoised_frames = self._postprocess_frames(output_tensor)

        return denoised_frames

    def close(self) -> None:
        """Release model resources."""
        if self._model is not None:
            del self._model
            self._model = None

        self._is_loaded = False

        if self._device.startswith("cuda"):
            clear_gpu_memory(self._device)

        self.logger.debug("BasicVSR++ resources released")


def create_basicvsr_plusplus_denoiser(
    num_input_frames: int = 15,
    scale: int = 1,
    device: str = "auto",
    auto_download: bool = True,
    **kwargs,
) -> BasicVSRPlusPlusDenoiser:
    """Create a BasicVSR++ denoiser with the specified configuration.

    Args:
        num_input_frames: Number of input frames for temporal context.
        scale: Super-resolution scale (1 for denoising only).
        device: Device for inference ('cuda', 'cpu', or 'auto').
        auto_download: Whether to automatically download pretrained weights.
        **kwargs: Additional BasicVSRPlusPlusConfig field values.

    Returns:
        Configured BasicVSRPlusPlusDenoiser instance.
    """
    config = BasicVSRPlusPlusConfig(
        num_input_frames=num_input_frames,
        scale=scale,
        auto_download=auto_download,
        **kwargs,
    )
    return BasicVSRPlusPlusDenoiser(config=config, device=device)


__all__ = [
    "BasicVSRPlusPlusDenoiser",
    "BasicVSRPlusPlusModel",
    "BasicVSRPlusPlusConfig",
    "create_basicvsr_plusplus_denoiser",
]
