"""Video denoising module.

This module provides video denoising functionality using AI models
including FastDVDNet and BasicVSR++ for reducing noise in video frames
before depth estimation.

Supported models:
- FastDVDNet: Fast video denoising without flow estimation
- BasicVSR++: High-quality video restoration with bidirectional propagation

Example usage:
    ```python
    from video2d3d.denoising import (
        VideoDenoiserSelector,
        VideoDenoiserConfig,
        DenoiserModelType,
    )

    # Basic usage
    config = VideoDenoiserConfig(
        enabled=True,
        model_type=DenoiserModelType.FASTDVDNET,
    )
    denoiser = VideoDenoiserSelector(config=config)
    denoised_frames = denoiser.denoise_frames(frames)

    # Context manager
    with VideoDenoiserSelector(model_type="fastdvdnet") as denoiser:
        denoised = denoiser.denoise_frames(frames)
    ```
"""

from __future__ import annotations

# Configuration
from video2d3d.denoising.config import (
    DenoiserModelType,
    NoiseLevelMode,
    FastDVDNetConfig,
    BasicVSRPlusPlusConfig,
    VideoDenoiserConfig,
    VideoDenoisingPipelineConfig,
    _DEFAULT_NUM_INPUT_FRAMES,
    _DEFAULT_NOISE_LEVEL,
    _DEFAULT_BATCH_SIZE,
)

# Base class
from video2d3d.denoising.base import VideoDenoiserBase

# Exceptions
from video2d3d.denoising.exceptions import (
    VideoDenoisingError,
    ModelLoadError,
    InferenceError,
    UnsupportedModelError,
    PretrainedModelError,
    FrameBufferError,
)

# Model implementations
from video2d3d.denoising.fastdvdnet import (
    FastDVDNetDenoiser,
    FastDVDNetModel,
    create_fastdvdnet_denoiser,
)

from video2d3d.denoising.basicvsr_plusplus import (
    BasicVSRPlusPlusDenoiser,
    BasicVSRPlusPlusModel,
    create_basicvsr_plusplus_denoiser,
)

# Selector with fallback
from video2d3d.denoising.selector import (
    VideoDenoiserSelector,
    create_video_denoiser,
    denoise_frames_auto,
)


__all__ = [
    # Enums
    "DenoiserModelType",
    "NoiseLevelMode",
    # Config classes
    "FastDVDNetConfig",
    "BasicVSRPlusPlusConfig",
    "VideoDenoiserConfig",
    "VideoDenoisingPipelineConfig",
    # Base class
    "VideoDenoiserBase",
    # Exceptions
    "VideoDenoisingError",
    "ModelLoadError",
    "InferenceError",
    "UnsupportedModelError",
    "PretrainedModelError",
    "FrameBufferError",
    # FastDVDNet
    "FastDVDNetDenoiser",
    "FastDVDNetModel",
    "create_fastdvdnet_denoiser",
    # BasicVSR++
    "BasicVSRPlusPlusDenoiser",
    "BasicVSRPlusPlusModel",
    "create_basicvsr_plusplus_denoiser",
    # Selector
    "VideoDenoiserSelector",
    "create_video_denoiser",
    "denoise_frames_auto",
    # Constants
    "_DEFAULT_NUM_INPUT_FRAMES",
    "_DEFAULT_NOISE_LEVEL",
    "_DEFAULT_BATCH_SIZE",
]
