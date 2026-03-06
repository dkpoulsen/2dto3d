"""Built-in presets for common use cases.

This module defines ready-to-use presets for different scenarios:
- Cinema: High quality for theatrical/large screen viewing
- VR: Optimized for VR headsets (over-under format)
- Web: Balanced for web streaming and sharing
- Mobile: Optimized for mobile devices
- Fast: Quick preview with lower quality
- Quality: Maximum quality for archival
"""

from __future__ import annotations

from typing import List

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


def _create_builtin_preset(
    preset_id: str,
    name: str,
    description: str,
    category: PresetCategory,
    tags: List[str],
    depth_model: str,
    stereo_format: str,
    video_preset: str,
    video_crf: int,
    quality_preset: str,
    depth_width: int = 384,
    depth_height: int = 384,
    baseline: float = 0.05,
    sbs_half_width: bool = False,
    batch_size: int = 4,
    **kwargs,
) -> Preset:
    """Helper to create built-in presets with consistent structure."""
    settings = PresetSettings(
        depth_estimation=DepthEstimationSettings(
            model=depth_model,
            output_width=depth_width,
            output_height=depth_height,
            temporal_consistency=True,
            temporal_smoothing_factor=0.5,
        ),
        stereo_generation=StereoGenerationSettings(
            format=stereo_format,
            baseline=baseline,
            focal_length=1.0,
            convergence=0.5,
            sbs_half_width=sbs_half_width,
        ),
        video_output=VideoOutputSettings(
            format="mp4",
            codec="libx264",
            preset=video_preset,
            crf=video_crf,
            pixel_format="yuv420p",
        ),
        processing=ProcessingSettings(
            batch_size=batch_size,
            num_workers=4,
            use_gpu=True,
            mixed_precision=True,
        ),
        quality=QualitySettings(
            preset=quality_preset,
            post_processing=True,
            calculate_metrics=False,
        ),
    )

    return Preset(
        id=preset_id,
        name=name,
        description=description,
        category=category,
        tags=tags,
        settings=settings,
        is_builtin=True,
        version="1.0.0",
        author="2Dto3D",
    )


# =============================================================================
# CINEMA PRESETS - High quality for large screens
# =============================================================================

CINEMA_SBS = _create_builtin_preset(
    preset_id="builtin-cinema-sbs",
    name="Cinema (Side-by-Side)",
    description=(
        "High-quality preset optimized for large screen viewing. "
        "Uses DPT Large model for best depth estimation and slow encoding "
        "for optimal quality. Ideal for theatrical presentations and home cinema."
    ),
    category=PresetCategory.CINEMA,
    tags=["cinema", "high-quality", "side-by-side", "large-screen"],
    depth_model="dpt_large",
    stereo_format="side_by_side",
    video_preset="slow",
    video_crf=18,
    quality_preset="quality",
    depth_width=384,
    depth_height=384,
    baseline=0.05,
    batch_size=2,  # Lower batch size for quality
)

CINEMA_ANAGLYPH = _create_builtin_preset(
    preset_id="builtin-cinema-anaglyph",
    name="Cinema (Anaglyph)",
    description=(
        "High-quality anaglyph preset for red-cyan 3D glasses. "
        "Uses Dubois color method for best color reproduction. "
        "Optimized for viewing on large screens with 3D glasses."
    ),
    category=PresetCategory.CINEMA,
    tags=["cinema", "anaglyph", "high-quality", "glasses"],
    depth_model="dpt_large",
    stereo_format="anaglyph",
    video_preset="slow",
    video_crf=18,
    quality_preset="quality",
)


# =============================================================================
# VR PRESETS - Optimized for VR headsets
# =============================================================================

VR_OVER_UNDER = _create_builtin_preset(
    preset_id="builtin-vr-over-under",
    name="VR (Over-Under)",
    description=(
        "Optimized for VR headset viewing with over-under format. "
        "Uses increased baseline for stronger 3D effect and "
        "higher depth resolution. Compatible with most VR players."
    ),
    category=PresetCategory.VR,
    tags=["vr", "over-under", "headset", "immersive"],
    depth_model="dpt_hybrid",
    stereo_format="vr",
    video_preset="medium",
    video_crf=20,
    quality_preset="balanced",
    depth_width=512,
    depth_height=512,
    baseline=0.08,  # Stronger 3D for VR
)

VR_SIDE_BY_SIDE = _create_builtin_preset(
    preset_id="builtin-vr-sbs",
    name="VR (Side-by-Side)",
    description=(
        "Side-by-side format optimized for VR viewing. "
        "Half-width encoding for compatibility with mobile VR. "
        "Good balance of quality and file size."
    ),
    category=PresetCategory.VR,
    tags=["vr", "side-by-side", "mobile-vr", "oculus", "cardboard"],
    depth_model="midas_hybrid",
    stereo_format="side_by_side",
    video_preset="medium",
    video_crf=22,
    quality_preset="balanced",
    sbs_half_width=True,
    baseline=0.07,
)


# =============================================================================
# WEB PRESETS - Optimized for web streaming
# =============================================================================

WEB_SBS = _create_builtin_preset(
    preset_id="builtin-web-sbs",
    name="Web (Side-by-Side)",
    description=(
        "Optimized for web streaming and sharing. "
        "Good quality with reasonable file sizes. "
        "Fast encoding preset for quick processing. "
        "Compatible with YouTube 3D and most web players."
    ),
    category=PresetCategory.WEB,
    tags=["web", "streaming", "youtube", "sharing", "side-by-side"],
    depth_model="midas_hybrid",
    stereo_format="side_by_side",
    video_preset="fast",
    video_crf=23,
    quality_preset="balanced",
)

WEB_ANAGLYPH = _create_builtin_preset(
    preset_id="builtin-web-anaglyph",
    name="Web (Anaglyph)",
    description=(
        "Anaglyph format for easy web sharing. "
        "Works with standard red-cyan glasses. "
        "Small file sizes, fast processing. "
        "Great for social media and quick previews."
    ),
    category=PresetCategory.WEB,
    tags=["web", "anaglyph", "social-media", "sharing", "glasses"],
    depth_model="midas_small",
    stereo_format="anaglyph",
    video_preset="fast",
    video_crf=24,
    quality_preset="fast",
)


# =============================================================================
# MOBILE PRESETS - Optimized for mobile devices
# =============================================================================

MOBILE_SBS = _create_builtin_preset(
    preset_id="builtin-mobile-sbs",
    name="Mobile (Side-by-Side)",
    description=(
        "Optimized for viewing on mobile devices. "
        "Half-width side-by-side for VR cardboards. "
        "Small file sizes and fast processing. "
        "Compatible with Google Cardboard and similar viewers."
    ),
    category=PresetCategory.MOBILE,
    tags=["mobile", "cardboard", "side-by-side", "portable"],
    depth_model="midas_small",
    stereo_format="side_by_side",
    video_preset="fast",
    video_crf=25,
    quality_preset="fast",
    sbs_half_width=True,
    baseline=0.04,
)

MOBILE_ANAGLYPH = _create_builtin_preset(
    preset_id="builtin-mobile-anaglyph",
    name="Mobile (Anaglyph)",
    description=(
        "Lightweight anaglyph preset for mobile devices. "
        "Small file sizes, fast processing. "
        "Good for quick viewing with 3D glasses on phones/tablets."
    ),
    category=PresetCategory.MOBILE,
    tags=["mobile", "anaglyph", "lightweight", "portable"],
    depth_model="midas_small",
    stereo_format="anaglyph",
    video_preset="fast",
    video_crf=26,
    quality_preset="fast",
)


# =============================================================================
# QUALITY PRESETS
# =============================================================================

FAST_PREVIEW = _create_builtin_preset(
    preset_id="builtin-fast-preview",
    name="Fast Preview",
    description=(
        "Quick preview preset for testing and fast iterations. "
        "Uses fastest settings for minimal processing time. "
        "Not recommended for final output."
    ),
    category=PresetCategory.GENERAL,
    tags=["fast", "preview", "test", "quick"],
    depth_model="midas_small",
    stereo_format="side_by_side",
    video_preset="ultrafast",
    video_crf=28,
    quality_preset="fast",
    batch_size=8,
)

MAX_QUALITY = _create_builtin_preset(
    preset_id="builtin-max-quality",
    name="Maximum Quality",
    description=(
        "Highest quality preset for archival and professional use. "
        "Uses best depth model, slowest encoding, and all quality enhancements. "
        "Processing will be slow but results will be optimal."
    ),
    category=PresetCategory.GENERAL,
    tags=["quality", "archive", "professional", "best"],
    depth_model="dpt_large",
    stereo_format="side_by_side",
    video_preset="veryslow",
    video_crf=16,
    quality_preset="quality",
    depth_width=384,
    depth_height=384,
    batch_size=1,  # Max quality, single frame at a time
)

BALANCED = _create_builtin_preset(
    preset_id="builtin-balanced",
    name="Balanced",
    description=(
        "Default balanced preset for general use. "
        "Good compromise between quality and processing speed. "
        "Suitable for most common scenarios."
    ),
    category=PresetCategory.GENERAL,
    tags=["balanced", "default", "general"],
    depth_model="midas_hybrid",
    stereo_format="side_by_side",
    video_preset="medium",
    video_crf=23,
    quality_preset="balanced",
)


# =============================================================================
# ALL BUILT-IN PRESETS
# =============================================================================

ALL_BUILTIN_PRESETS: List[Preset] = [
    # Cinema
    CINEMA_SBS,
    CINEMA_ANAGLYPH,
    # VR
    VR_OVER_UNDER,
    VR_SIDE_BY_SIDE,
    # Web
    WEB_SBS,
    WEB_ANAGLYPH,
    # Mobile
    MOBILE_SBS,
    MOBILE_ANAGLYPH,
    # Quality
    FAST_PREVIEW,
    MAX_QUALITY,
    BALANCED,
]

# Mapping by ID for quick lookup
BUILTIN_PRESETS_BY_ID = {p.id: p for p in ALL_BUILTIN_PRESETS}

# Mapping by name for quick lookup
BUILTIN_PRESETS_BY_NAME = {p.name: p for p in ALL_BUILTIN_PRESETS}


def get_builtin_preset(preset_id: str) -> Preset | None:
    """Get a built-in preset by ID.

    Args:
        preset_id: The preset ID.

    Returns:
        The preset, or None if not found.
    """
    return BUILTIN_PRESETS_BY_ID.get(preset_id)


def get_builtin_preset_by_name(name: str) -> Preset | None:
    """Get a built-in preset by name.

    Args:
        name: The preset name (case-insensitive).

    Returns:
        The preset, or None if not found.
    """
    name_lower = name.lower()
    for preset in ALL_BUILTIN_PRESETS:
        if preset.name.lower() == name_lower:
            return preset
    return None


__all__ = [
    # Individual presets
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
    # Collections
    "ALL_BUILTIN_PRESETS",
    "BUILTIN_PRESETS_BY_ID",
    "BUILTIN_PRESETS_BY_NAME",
    # Functions
    "get_builtin_preset",
    "get_builtin_preset_by_name",
]
