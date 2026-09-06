"""Preset data models for saving, loading, and sharing processing configurations.

This module provides dataclasses for representing presets that capture
all processing settings for different use cases (cinema, VR, web, mobile).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class PresetCategory(str, Enum):
    """Categories for organizing presets by use case."""

    CINEMA = "cinema"
    VR = "vr"
    WEB = "web"
    MOBILE = "mobile"
    CUSTOM = "custom"
    GENERAL = "general"


@dataclass
class DepthEstimationSettings:
    """Depth estimation settings for a preset."""

    model: str = "midas_small"
    output_width: int = 384
    output_height: int = 384
    min_depth: float = 0.0
    max_depth: float = 1.0
    temporal_consistency: bool = True
    temporal_smoothing_factor: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DepthEstimationSettings:
        """Create from dictionary."""
        return cls(
            model=data.get("model", "midas_small"),
            output_width=data.get("output_width", 384),
            output_height=data.get("output_height", 384),
            min_depth=data.get("min_depth", 0.0),
            max_depth=data.get("max_depth", 1.0),
            temporal_consistency=data.get("temporal_consistency", True),
            temporal_smoothing_factor=data.get("temporal_smoothing_factor", 0.5),
        )


@dataclass
class StereoGenerationSettings:
    """Stereoscopic generation settings for a preset."""

    format: str = "side_by_side"
    baseline: float = 0.05
    focal_length: float = 1.0
    convergence: float = 0.5
    # Anaglyph-specific
    anaglyph_type: str = "red_cyan"
    anaglyph_color_method: str = "dubois"
    # Side-by-side specific
    sbs_layout: str = "horizontal"
    sbs_swap_eyes: bool = False
    sbs_half_width: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StereoGenerationSettings:
        """Create from dictionary."""
        return cls(
            format=data.get("format", "side_by_side"),
            baseline=data.get("baseline", 0.05),
            focal_length=data.get("focal_length", 1.0),
            convergence=data.get("convergence", 0.5),
            anaglyph_type=data.get("anaglyph_type", "red_cyan"),
            anaglyph_color_method=data.get("anaglyph_color_method", "dubois"),
            sbs_layout=data.get("sbs_layout", "horizontal"),
            sbs_swap_eyes=data.get("sbs_swap_eyes", False),
            sbs_half_width=data.get("sbs_half_width", False),
        )

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.baseline <= 0:
            raise ValueError(f"baseline must be positive, got {self.baseline}")
        if self.focal_length <= 0:
            raise ValueError(f"focal_length must be positive, got {self.focal_length}")


@dataclass
class VideoOutputSettings:
    """Video output settings for a preset."""

    format: str = "mp4"
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 23
    pixel_format: str = "yuv420p"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VideoOutputSettings:
        """Create from dictionary."""
        return cls(
            format=data.get("format", "mp4"),
            codec=data.get("codec", "libx264"),
            preset=data.get("preset", "medium"),
            crf=data.get("crf", 23),
            pixel_format=data.get("pixel_format", "yuv420p"),
        )

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if not 0 <= self.crf <= 51:
            raise ValueError(f"crf must be between 0 and 51, got {self.crf}")


@dataclass
class ProcessingSettings:
    """Processing settings for a preset."""

    batch_size: int = 4
    num_workers: int = 4
    use_gpu: bool = True
    gpu_device: int = 0
    mixed_precision: bool = True
    max_memory_percent: int = 80

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProcessingSettings:
        """Create from dictionary."""
        return cls(
            batch_size=data.get("batch_size", 4),
            num_workers=data.get("num_workers", 4),
            use_gpu=data.get("use_gpu", True),
            gpu_device=data.get("gpu_device", 0),
            mixed_precision=data.get("mixed_precision", True),
            max_memory_percent=data.get("max_memory_percent", 80),
        )

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be at least 1, got {self.batch_size}")
        if self.num_workers < 0:
            raise ValueError(f"num_workers must be non-negative, got {self.num_workers}")
        if not 0 <= self.max_memory_percent <= 100:
            raise ValueError(f"max_memory_percent must be 0-100, got {self.max_memory_percent}")


@dataclass
class QualitySettings:
    """Quality settings for a preset."""

    preset: str = "balanced"  # fast, balanced, quality
    post_processing: bool = True
    calculate_metrics: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QualitySettings:
        """Create from dictionary."""
        return cls(
            preset=data.get("preset", "balanced"),
            post_processing=data.get("post_processing", True),
            calculate_metrics=data.get("calculate_metrics", False),
        )


@dataclass
class DepthCurveSettings:
    """Depth curve settings for artistic control over 3D effect strength."""

    enabled: bool = False
    preset: str | None = None  # linear, s_curve, contrast_boost, soft_curve, etc.
    control_points: list[dict[str, float]] = field(
        default_factory=lambda: [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DepthCurveSettings:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            preset=data.get("preset"),
            control_points=data.get("control_points", [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}]),
        )


@dataclass
class PresetSettings:
    """Complete settings for a processing preset."""

    depth_estimation: DepthEstimationSettings = field(default_factory=DepthEstimationSettings)
    stereo_generation: StereoGenerationSettings = field(default_factory=StereoGenerationSettings)
    video_output: VideoOutputSettings = field(default_factory=VideoOutputSettings)
    processing: ProcessingSettings = field(default_factory=ProcessingSettings)
    quality: QualitySettings = field(default_factory=QualitySettings)
    depth_curve: DepthCurveSettings = field(default_factory=DepthCurveSettings)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "depth_estimation": self.depth_estimation.to_dict(),
            "stereo_generation": self.stereo_generation.to_dict(),
            "video_output": self.video_output.to_dict(),
            "processing": self.processing.to_dict(),
            "quality": self.quality.to_dict(),
            "depth_curve": self.depth_curve.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresetSettings:
        """Create from dictionary."""
        return cls(
            depth_estimation=DepthEstimationSettings.from_dict(data.get("depth_estimation", {})),
            stereo_generation=StereoGenerationSettings.from_dict(data.get("stereo_generation", {})),
            video_output=VideoOutputSettings.from_dict(data.get("video_output", {})),
            processing=ProcessingSettings.from_dict(data.get("processing", {})),
            quality=QualitySettings.from_dict(data.get("quality", {})),
            depth_curve=DepthCurveSettings.from_dict(data.get("depth_curve", {})),
        )


@dataclass
class Preset:
    """A processing preset with complete settings for a specific use case.

    Presets capture all processing configuration and can be saved, loaded,
    shared, and applied to video conversion jobs.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Classification
    category: PresetCategory = PresetCategory.GENERAL
    tags: list[str] = field(default_factory=list)

    # Settings
    settings: PresetSettings = field(default_factory=PresetSettings)

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    is_builtin: bool = False
    version: str = "1.0.0"
    author: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "tags": self.tags,
            "settings": self.settings.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_builtin": self.is_builtin,
            "version": self.version,
            "author": self.author,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Preset:
        """Create from dictionary."""
        category_str = data.get("category", "general")
        try:
            category = PresetCategory(category_str.lower())
        except ValueError:
            category = PresetCategory.GENERAL

        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=category,
            tags=data.get("tags", []),
            settings=PresetSettings.from_dict(data.get("settings", {})),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            is_builtin=data.get("is_builtin", False),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
        )

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> Preset:
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow().isoformat()

    def __eq__(self, other: object) -> bool:
        """Check equality by ID."""
        if not isinstance(other, Preset):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash by ID."""
        return hash(self.id)

    def __str__(self) -> str:
        """String representation."""
        return f"Preset({self.name}, category={self.category.value})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"Preset(id={self.id!r}, name={self.name!r}, category={self.category.value!r})"


__all__ = [
    "PresetCategory",
    "DepthEstimationSettings",
    "StereoGenerationSettings",
    "VideoOutputSettings",
    "ProcessingSettings",
    "QualitySettings",
    "DepthCurveSettings",
    "PresetSettings",
    "Preset",
]
