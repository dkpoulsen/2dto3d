"""Video denoising configuration.

This module provides configuration dataclasses for video denoising models
including FastDVDNet and BasicVSR++.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from video2d3d.utils.gpu import GPUConfig, select_device


# Default configuration values
_DEFAULT_NUM_INPUT_FRAMES: int = 5  # Number of frames for temporal denoising
_DEFAULT_NOISE_LEVEL: float = 30.0  # Default noise level (sigma)
_DEFAULT_BATCH_SIZE: int = 4


class DenoiserModelType(Enum):
    """Available video denoising model types."""

    FASTDVDNET = "fastdvdnet"
    BASICVSR_PLUSPLUS = "basicvsr_plusplus"
    BASICVSR = "basicvsr"
    NONE = "none"  # Disable denoising

    @classmethod
    def from_string(cls, name: str) -> "DenoiserModelType":
        """Get model type from string name.

        Args:
            name: Model name (case-insensitive).

        Returns:
            DenoiserModelType enum value.

        Raises:
            ValueError: If model name is not recognized.
        """
        normalized = name.lower().replace("-", "_").replace(" ", "_")

        name_mapping = {
            "fastdvdnet": cls.FASTDVDNET,
            "fast_dvdnet": cls.FASTDVDNET,
            "fast-dvdnet": cls.FASTDVDNET,
            "basicvsr_plusplus": cls.BASICVSR_PLUSPLUS,
            "basicvsr++": cls.BASICVSR_PLUSPLUS,
            "basicvsr_pp": cls.BASICVSR_PLUSPLUS,
            "basicvsrplusplus": cls.BASICVSR_PLUSPLUS,
            "basicvsr": cls.BASICVSR,
            "none": cls.NONE,
            "disabled": cls.NONE,
            "off": cls.NONE,
        }

        if normalized not in name_mapping:
            valid_names = [m.value for m in cls]
            raise ValueError(f"Unknown denoising model '{name}'. Valid options: {valid_names}")

        return name_mapping[normalized]

    @property
    def is_enabled(self) -> bool:
        """Check if this model type enables denoising."""
        return self != DenoiserModelType.NONE

    @property
    def requires_temporal_context(self) -> bool:
        """Check if this model requires temporal context (multiple frames)."""
        return self in (
            DenoiserModelType.FASTDVDNET,
            DenoiserModelType.BASICVSR_PLUSPLUS,
            DenoiserModelType.BASICVSR,
        )


class NoiseLevelMode(Enum):
    """Noise level estimation mode."""

    FIXED = "fixed"  # Use fixed noise level
    ESTIMATED = "estimated"  # Automatically estimate noise level
    BLIND = "blind"  # Blind denoising (no noise level needed)


@dataclass
class FastDVDNetConfig:
    """Configuration for FastDVDNet denoiser.

    FastDVDNet is a fast video denoising network that uses temporal information
    from multiple frames to reduce noise.

    Attributes:
        num_input_frames: Number of input frames for temporal context (odd number, typically 5).
        noise_level: Fixed noise level (sigma) when using fixed mode.
        noise_level_mode: How to determine noise level.
        pretrained_model: Path to pretrained model weights.
        auto_download: Whether to automatically download pretrained models.
    """

    num_input_frames: int = _DEFAULT_NUM_INPUT_FRAMES
    noise_level: float = _DEFAULT_NOISE_LEVEL
    noise_level_mode: str = "blind"
    pretrained_model: Optional[Path] = None
    auto_download: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.num_input_frames < 1:
            raise ValueError(f"num_input_frames must be >= 1, got {self.num_input_frames}")
        if self.num_input_frames % 2 == 0:
            # FastDVDNet expects odd number of frames (center frame + neighbors)
            import warnings

            warnings.warn(
                f"num_input_frames should be odd for FastDVDNet, got {self.num_input_frames}. "
                f"Consider using {self.num_input_frames + 1}."
            )
        if self.noise_level <= 0:
            raise ValueError(f"noise_level must be positive, got {self.noise_level}")
        if self.noise_level_mode not in [m.value for m in NoiseLevelMode]:
            raise ValueError(
                f"Invalid noise_level_mode '{self.noise_level_mode}'. "
                f"Valid options: {[m.value for m in NoiseLevelMode]}"
            )
        if isinstance(self.pretrained_model, str):
            self.pretrained_model = Path(self.pretrained_model)


@dataclass
class BasicVSRPlusPlusConfig:
    """Configuration for BasicVSR++ denoiser.

    BasicVSR++ is a video restoration network that can handle denoising,
    super-resolution, and other restoration tasks.

    Attributes:
        num_input_frames: Number of input frames for temporal context.
        scale: Super-resolution scale factor (1 for denoising only).
        pretrained_model: Path to pretrained model weights.
        auto_download: Whether to automatically download pretrained models.
        use_spynet: Whether to use SPyNet for optical flow.
    """

    num_input_frames: int = 15
    scale: int = 1  # 1 for denoising only
    pretrained_model: Optional[Path] = None
    auto_download: bool = True
    use_spynet: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.num_input_frames < 1:
            raise ValueError(f"num_input_frames must be >= 1, got {self.num_input_frames}")
        if self.scale < 1:
            raise ValueError(f"scale must be >= 1, got {self.scale}")
        if isinstance(self.pretrained_model, str):
            self.pretrained_model = Path(self.pretrained_model)


@dataclass
class VideoDenoiserConfig:
    """Main configuration for video denoising.

    This configuration controls all aspects of video denoising including
    model selection, GPU settings, and processing parameters.

    Attributes:
        enabled: Whether video denoising is enabled.
        model_type: Type of denoising model to use.
        device: Device for inference ('cuda', 'cpu', or 'auto').
        cache_dir: Directory to cache downloaded models.
        fastdvdnet: FastDVDNet-specific configuration.
        basicvsr_plusplus: BasicVSR++-specific configuration.
        fallback_chain: List of model types to try if primary fails.
        enable_fallback: Whether to enable fallback to simpler models.
        preserve_temporal: Whether to preserve temporal consistency.
        output_dtype: Output data type ('float32', 'uint8').
        batch_size: Batch size for processing frames.
        gpu_config: GPU configuration for acceleration.
    """

    enabled: bool = False
    model_type: DenoiserModelType = DenoiserModelType.FASTDVDNET
    device: str = "auto"
    cache_dir: Optional[Path] = None
    fastdvdnet: FastDVDNetConfig = field(default_factory=FastDVDNetConfig)
    basicvsr_plusplus: BasicVSRPlusPlusConfig = field(default_factory=BasicVSRPlusPlusConfig)
    fallback_chain: List[DenoiserModelType] = field(
        default_factory=lambda: [
            DenoiserModelType.FASTDVDNET,
        ]
    )
    enable_fallback: bool = True
    preserve_temporal: bool = True
    output_dtype: str = "float32"
    batch_size: int = _DEFAULT_BATCH_SIZE
    gpu_config: Optional[GPUConfig] = None

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Handle string model type
        if isinstance(self.model_type, str):
            self.model_type = DenoiserModelType.from_string(self.model_type)

        # Normalize fallback chain
        self.fallback_chain = [
            DenoiserModelType.from_string(m) if isinstance(m, str) else m
            for m in self.fallback_chain
        ]

        # Initialize GPU config if not provided
        if self.gpu_config is None:
            self.gpu_config = GPUConfig(enabled=True, device=self.device)

        # Auto-detect device
        if self.device == "auto":
            selection = select_device(self.gpu_config)
            self.device = selection.device

        # Normalize cache_dir to Path
        if self.cache_dir is not None and isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)

        # Validate output dtype
        valid_dtypes = ["float32", "float64", "uint8", "uint16"]
        if self.output_dtype not in valid_dtypes:
            raise ValueError(
                f"Invalid output_dtype '{self.output_dtype}'. Valid options: {valid_dtypes}"
            )

    @property
    def effective_model(self) -> DenoiserModelType:
        """Get the effective model type, respecting enabled flag."""
        if not self.enabled:
            return DenoiserModelType.NONE
        return self.model_type


@dataclass
class VideoDenoisingPipelineConfig:
    """Configuration for the video denoising pipeline.

    This configuration controls how frames are processed through the
    denoising pipeline including frame buffering and progress tracking.

    Attributes:
        buffer_size: Number of frames to buffer for temporal processing.
        overlap: Number of frames to overlap between batches.
        progress_callback: Optional callback for progress updates.
        enable_profiling: Whether to enable profiling/timing.
    """

    buffer_size: int = 30
    overlap: int = 2
    progress_callback: Optional[callable] = None
    enable_profiling: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.buffer_size < 1:
            raise ValueError(f"buffer_size must be >= 1, got {self.buffer_size}")
        if self.overlap < 0:
            raise ValueError(f"overlap must be >= 0, got {self.overlap}")


__all__ = [
    # Enums
    "DenoiserModelType",
    "NoiseLevelMode",
    # Config classes
    "FastDVDNetConfig",
    "BasicVSRPlusPlusConfig",
    "VideoDenoiserConfig",
    "VideoDenoisingPipelineConfig",
    # Constants
    "_DEFAULT_NUM_INPUT_FRAMES",
    "_DEFAULT_NOISE_LEVEL",
    "_DEFAULT_BATCH_SIZE",
]
