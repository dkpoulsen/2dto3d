"""Configuration for AI-based video upscaling.

This module provides configuration classes for the upscaler, including
model selection, processing parameters, and GPU settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ModelType(str, Enum):
    """Available upscaling model types.

    Each model has different characteristics:

    - ESRGAN: Original Enhanced Super-Resolution GAN
    - REAL_ESRGAN_X4PLUS: Real-ESRGAN 4x general purpose
    - REAL_ESRGAN_X4PLUS_ANIME: Real-ESRGAN optimized for anime/illustrations
    - REAL_ESRGAN_X2PLUS: Real-ESRGAN 2x upscaling
    - REAL_ESRGAN_GENERAL_X4V3: Latest general purpose model
    """

    ESRGAN = "esrgan"
    REAL_ESRGAN_X4PLUS = "realesrgan-x4plus"
    REAL_ESRGAN_X4PLUS_ANIME = "realesrgan-x4plus-anime"
    REAL_ESRGAN_X2PLUS = "realesrgan-x2plus"
    REAL_ESRGAN_GENERAL_X4V3 = "realesrgan-general-x4v3"


# Model information dictionary
MODEL_INFO: dict[str, dict[str, Any]] = {
    ModelType.ESRGAN: {
        "name": "ESRGAN",
        "scale": 4,
        "description": "Original Enhanced Super-Resolution GAN",
        "url": "https://github.com/xinntao/ESRGAN",
        "onnx_file": "ESRGAN.onnx",
        "input_channels": 3,
        "output_channels": 3,
    },
    ModelType.REAL_ESRGAN_X4PLUS: {
        "name": "Real-ESRGAN x4plus",
        "scale": 4,
        "description": "General-purpose 4x upscaling model",
        "url": "https://github.com/xinntao/Real-ESRGAN",
        "onnx_file": "realesrgan-x4plus.onnx",
        "input_channels": 3,
        "output_channels": 3,
    },
    ModelType.REAL_ESRGAN_X4PLUS_ANIME: {
        "name": "Real-ESRGAN x4plus Anime",
        "scale": 4,
        "description": "Optimized for anime and illustrations",
        "url": "https://github.com/xinntao/Real-ESRGAN",
        "onnx_file": "realesrgan-x4plus-anime.onnx",
        "input_channels": 3,
        "output_channels": 3,
    },
    ModelType.REAL_ESRGAN_X2PLUS: {
        "name": "Real-ESRGAN x2plus",
        "scale": 2,
        "description": "General-purpose 2x upscaling model",
        "url": "https://github.com/xinntao/Real-ESRGAN",
        "onnx_file": "realesrgan-x2plus.onnx",
        "input_channels": 3,
        "output_channels": 3,
    },
    ModelType.REAL_ESRGAN_GENERAL_X4V3: {
        "name": "Real-ESRGAN General x4v3",
        "scale": 4,
        "description": "Latest general-purpose model with better quality",
        "url": "https://github.com/xinntao/Real-ESRGAN",
        "onnx_file": "realesrgan-general-x4v3.onnx",
        "input_channels": 3,
        "output_channels": 3,
    },
}


def get_model_info(model_type: str | ModelType) -> dict[str, Any]:
    """Get information about a specific model.

    Args:
        model_type: The model type to get info for.

    Returns:
        Dictionary with model information.

    Raises:
        ValueError: If model type is not found.
    """
    if isinstance(model_type, str):
        model_type = ModelType(model_type)
    if model_type not in MODEL_INFO:
        raise ValueError(f"Unknown model type: {model_type}")
    return MODEL_INFO[model_type].copy()


def list_available_models() -> list[str]:
    """List all available model types.

    Returns:
        List of model type strings.
    """
    return [m.value for m in ModelType]


def get_default_model_path() -> Path:
    """Get the default path for storing model files.

    Returns:
        Path to the models directory.
    """
    # Check for environment variable first
    import os

    custom_path = os.getenv("VIDEO2D3D_MODELS_PATH")
    if custom_path:
        return Path(custom_path)

    # Default to models/ directory relative to project root
    return Path(__file__).parent.parent.parent.parent / "models" / "upscaling"


def get_model_scale(model_type: str | ModelType) -> int:
    """Get the scale factor for a model.

    Args:
        model_type: The model type.

    Returns:
        Scale factor (e.g., 2, 4).
    """
    info = get_model_info(model_type)
    return info["scale"]


@dataclass
class UpscalerConfig:
    """Configuration for AI-based video upscaling.

    Attributes:
        enabled: Whether upscaling is enabled.
        model_type: The upscaling model to use.
        model_path: Custom path to the ONNX model file. If None, uses default.
        scale: Upscaling factor. If None, uses model's default scale.
        use_gpu: Whether to use GPU acceleration.
        gpu_device: GPU device ID to use.
        tile_size: Size of tiles for processing large images. 0 = no tiling.
        tile_pad: Padding around tiles to avoid artifacts.
        pre_pad: Padding to add before processing.
        half_precision: Use FP16 for faster inference (requires GPU).
        denoise_strength: Denoising strength (0.0 = none, 1.0 = max).
        output_format: Output format for upscaled frames.
        preserve_alpha: Whether to preserve alpha channel.
        max_memory_mb: Maximum memory usage for tile processing.
        batch_size: Number of tiles to process in parallel.
    """

    enabled: bool = False
    model_type: ModelType = ModelType.REAL_ESRGAN_X4PLUS
    model_path: Path | None = None
    scale: int | None = None
    use_gpu: bool = True
    gpu_device: int = 0
    tile_size: int = 0  # 0 = auto (no tiling for small images)
    tile_pad: int = 16
    pre_pad: int = 0
    half_precision: bool = True
    denoise_strength: float = 0.5
    output_format: str = "RGB"
    preserve_alpha: bool = False
    max_memory_mb: float = 2048.0  # 2GB default
    batch_size: int = 1

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Convert string model type to enum if needed
        if isinstance(self.model_type, str):
            self.model_type = ModelType(self.model_type)

        # Set default scale from model if not specified
        if self.scale is None:
            self.scale = get_model_scale(self.model_type)

        # Validate scale
        if self.scale not in (2, 4):
            raise ValueError(f"Scale must be 2 or 4, got {self.scale}")

        # Validate denoise strength
        if not 0.0 <= self.denoise_strength <= 1.0:
            raise ValueError(
                f"Denoise strength must be between 0.0 and 1.0, got {self.denoise_strength}"
            )

        # Validate tile size
        if self.tile_size < 0:
            raise ValueError(f"Tile size must be >= 0, got {self.tile_size}")
        if self.tile_size > 0 and self.tile_size < 64:
            raise ValueError(f"Tile size must be >= 64 or 0, got {self.tile_size}")

        # Set model path
        if self.model_path is not None:
            self.model_path = Path(self.model_path)

    @property
    def model_info(self) -> dict[str, Any]:
        """Get information about the selected model."""
        return get_model_info(self.model_type)

    @property
    def effective_scale(self) -> int:
        """Get the effective scale factor."""
        return self.scale or get_model_scale(self.model_type)

    def get_model_file_path(self) -> Path:
        """Get the full path to the model file.

        Returns:
            Path to the ONNX model file.
        """
        if self.model_path:
            return self.model_path

        model_dir = get_default_model_path()
        onnx_file = self.model_info["onnx_file"]
        return model_dir / onnx_file

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        return {
            "enabled": self.enabled,
            "model_type": self.model_type.value,
            "model_path": str(self.model_path) if self.model_path else None,
            "scale": self.scale,
            "use_gpu": self.use_gpu,
            "gpu_device": self.gpu_device,
            "tile_size": self.tile_size,
            "tile_pad": self.tile_pad,
            "pre_pad": self.pre_pad,
            "half_precision": self.half_precision,
            "denoise_strength": self.denoise_strength,
            "output_format": self.output_format,
            "preserve_alpha": self.preserve_alpha,
            "max_memory_mb": self.max_memory_mb,
            "batch_size": self.batch_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UpscalerConfig:
        """Create config from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            UpscalerConfig instance.
        """
        model_type = data.get("model_type", ModelType.REAL_ESRGAN_X4PLUS)
        if isinstance(model_type, str):
            model_type = ModelType(model_type)

        model_path = data.get("model_path")
        if model_path:
            model_path = Path(model_path)

        return cls(
            enabled=data.get("enabled", False),
            model_type=model_type,
            model_path=model_path,
            scale=data.get("scale"),
            use_gpu=data.get("use_gpu", True),
            gpu_device=data.get("gpu_device", 0),
            tile_size=data.get("tile_size", 0),
            tile_pad=data.get("tile_pad", 16),
            pre_pad=data.get("pre_pad", 0),
            half_precision=data.get("half_precision", True),
            denoise_strength=data.get("denoise_strength", 0.5),
            output_format=data.get("output_format", "RGB"),
            preserve_alpha=data.get("preserve_alpha", False),
            max_memory_mb=data.get("max_memory_mb", 2048.0),
            batch_size=data.get("batch_size", 1),
        )


__all__ = [
    "ModelType",
    "MODEL_INFO",
    "UpscalerConfig",
    "get_model_info",
    "list_available_models",
    "get_default_model_path",
    "get_model_scale",
]
