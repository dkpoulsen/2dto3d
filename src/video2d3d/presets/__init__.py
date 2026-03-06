"""Preset management for video2d3d.

This module provides a system for saving, loading, and sharing processing
presets with optimized settings for different use cases (cinema, VR, web, mobile).

Usage:
    from video2d3d.presets import PresetManager, get_preset_manager
    from video2d3d.presets.models import Preset, PresetCategory

    # Get the preset manager
    manager = get_preset_manager()

    # List all presets
    presets = manager.list_all()

    # Create a new preset
    preset = manager.create(
        name="My Custom Preset",
        category=PresetCategory.CUSTOM,
        description="My custom settings",
    )

    # Get a preset by ID or name
    preset = manager.get("preset-id")
    preset = manager.get_by_name("My Custom Preset")

    # Apply preset to a job config
    from video2d3d.utils.config import get_config
    config = get_config()
    config = manager.apply_preset_to_config(preset, config)

Built-in Presets:
    - Cinema (Side-by-Side, Anaglyph): High quality for large screens
    - VR (Over-Under, Side-by-Side): Optimized for VR headsets
    - Web (Side-by-Side, Anaglyph): Optimized for streaming/sharing
    - Mobile (Side-by-Side, Anaglyph): Optimized for mobile devices
    - Fast Preview: Quick testing with minimal processing time
    - Maximum Quality: Best quality for archival use
    - Balanced: Default balanced settings
"""

from video2d3d.presets.builtins import (
    ALL_BUILTIN_PRESETS,
    BALANCED,
    BUILTIN_PRESETS_BY_ID,
    BUILTIN_PRESETS_BY_NAME,
    CINEMA_ANAGLYPH,
    CINEMA_SBS,
    FAST_PREVIEW,
    MAX_QUALITY,
    MOBILE_ANAGLYPH,
    MOBILE_SBS,
    VR_OVER_UNDER,
    VR_SIDE_BY_SIDE,
    WEB_ANAGLYPH,
    WEB_SBS,
    get_builtin_preset,
    get_builtin_preset_by_name,
)
from video2d3d.presets.manager import PresetManager, PresetManagerError, get_preset_manager
from video2d3d.presets.models import (
    DepthEstimationSettings,
    Preset,
    PresetCategory,
    PresetSettings,
    ProcessingSettings,
    QualitySettings,
    StereoGenerationSettings,
    VideoOutputSettings,
)
from video2d3d.presets.storage import PresetStorage, PresetStorageError

__all__ = [
    # Manager
    "PresetManager",
    "PresetManagerError",
    "get_preset_manager",
    # Storage
    "PresetStorage",
    "PresetStorageError",
    # Models
    "Preset",
    "PresetSettings",
    "PresetCategory",
    "DepthEstimationSettings",
    "StereoGenerationSettings",
    "VideoOutputSettings",
    "ProcessingSettings",
    "QualitySettings",
    # Built-in presets
    "CINEMA_SBS",
    "CINEMA_ANAGLYPH",
    "VR_OVER_UNDER",
    "VR_SIDE_BY_SIDE",
    "WEB_SBS",
    "WEB_ANAGLYPH",
    "MOBILE_SBS",
    "MOBILE_ANAGLYPH",
    "FAST_PREVIEW",
    "MAX_QUALITY",
    "BALANCED",
    "ALL_BUILTIN_PRESETS",
    "BUILTIN_PRESETS_BY_ID",
    "BUILTIN_PRESETS_BY_NAME",
    "get_builtin_preset",
    "get_builtin_preset_by_name",
]
