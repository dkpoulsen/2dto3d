"""AI-based video upscaling module using ESRGAN/Real-ESRGAN models.

This module provides video frame upscaling capabilities using state-of-the-art
super-resolution models like ESRGAN and Real-ESRGAN. It supports:

- Multiple upscaling models (ESRGAN, Real-ESRGAN variants)
- Tile-based processing for large images
- GPU acceleration via CUDA/ROCm
- Configurable scale factors (2x, 4x)
- Integration with the video processing pipeline

Example usage:
    ```python
    from video2d3d.upscaling import (
        UpscalerConfig,
        ModelType,
        RealESRGANUpscaler,
        VideoUpscaler,
    )

    # Configure upscaler
    config = UpscalerConfig(
        model_type=ModelType.REAL_ESRGAN_X4PLUS,
        scale=4,
        use_gpu=True,
        tile_size=512,
    )

    # Create upscaler
    upscaler = RealESRGANUpscaler(config)

    # Upscale a single frame
    upscaled_frame = upscaler.upscale(frame)

    # Or use the video upscaler for batch processing
    video_upscaler = VideoUpscaler(config)
    upscaled_frames = video_upscaler.upscale_frames(frames)
    ```
"""

from __future__ import annotations

from video2d3d.upscaling.base import BaseUpscaler, UpscaleResult
from video2d3d.upscaling.config import (
    ModelType,
    UpscalerConfig,
    get_default_model_path,
    get_model_info,
    get_model_scale,
    list_available_models,
)
from video2d3d.upscaling.esrgan import DummyUpscaler, RealESRGANUpscaler, create_upscaler
from video2d3d.upscaling.processor import (
    VideoUpscaler,
    VideoUpscaleStats,
    upscale_frames,
    upscale_video,
)

__all__ = [
    # Configuration
    "UpscalerConfig",
    "ModelType",
    "get_default_model_path",
    "get_model_info",
    "get_model_scale",
    "list_available_models",
    # Core classes
    "BaseUpscaler",
    "UpscaleResult",
    "RealESRGANUpscaler",
    "DummyUpscaler",
    "VideoUpscaler",
    "VideoUpscaleStats",
    # Factory functions
    "create_upscaler",
    "upscale_video",
    "upscale_frames",
]
