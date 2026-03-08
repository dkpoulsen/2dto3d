"""Tests for built-in presets.

This module tests the built-in preset definitions including:
- All built-in presets are valid
- Preset lookup functions
- Preset category consistency
"""

import pytest

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
from video2d3d.presets.models import Preset, PresetCategory, PresetSettings


class TestBuiltinPresetsExist:
    """Tests that all expected built-in presets exist."""

    def test_cinema_presets_exist(self):
        """Test that cinema presets are defined."""
        assert CINEMA_SBS is not None
        assert CINEMA_ANAGLYPH is not None
        assert CINEMA_SBS.name == "Cinema (Side-by-Side)"
        assert CINEMA_ANAGLYPH.name == "Cinema (Anaglyph)"

    def test_vr_presets_exist(self):
        """Test that VR presets are defined."""
        assert VR_OVER_UNDER is not None
        assert VR_SIDE_BY_SIDE is not None
        assert VR_OVER_UNDER.name == "VR (Over-Under)"
        assert VR_SIDE_BY_SIDE.name == "VR (Side-by-Side)"

    def test_web_presets_exist(self):
        """Test that web presets are defined."""
        assert WEB_SBS is not None
        assert WEB_ANAGLYPH is not None
        assert WEB_SBS.name == "Web (Side-by-Side)"
        assert WEB_ANAGLYPH.name == "Web (Anaglyph)"

    def test_mobile_presets_exist(self):
        """Test that mobile presets are defined."""
        assert MOBILE_SBS is not None
        assert MOBILE_ANAGLYPH is not None
        assert MOBILE_SBS.name == "Mobile (Side-by-Side)"
        assert MOBILE_ANAGLYPH.name == "Mobile (Anaglyph)"

    def test_quality_presets_exist(self):
        """Test that quality presets are defined."""
        assert FAST_PREVIEW is not None
        assert MAX_QUALITY is not None
        assert BALANCED is not None
        assert FAST_PREVIEW.name == "Fast Preview"
        assert MAX_QUALITY.name == "Maximum Quality"
        assert BALANCED.name == "Balanced"


class TestBuiltinPresetsValidity:
    """Tests that all built-in presets are valid."""

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_are_builtin(self, preset: Preset):
        """Test that all built-in presets have is_builtin=True."""
        assert preset.is_builtin is True

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_id(self, preset: Preset):
        """Test that all presets have a valid ID."""
        assert preset.id is not None
        assert len(preset.id) > 0
        assert preset.id.startswith("builtin-")

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_name(self, preset: Preset):
        """Test that all presets have a name."""
        assert preset.name is not None
        assert len(preset.name) > 0

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_description(self, preset: Preset):
        """Test that all presets have a description."""
        assert preset.description is not None
        assert len(preset.description) > 0

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_category(self, preset: Preset):
        """Test that all presets have a category."""
        assert preset.category is not None
        assert isinstance(preset.category, PresetCategory)

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_tags(self, preset: Preset):
        """Test that all presets have tags."""
        assert preset.tags is not None
        assert isinstance(preset.tags, list)
        assert len(preset.tags) > 0

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_settings(self, preset: Preset):
        """Test that all presets have complete settings."""
        assert preset.settings is not None
        assert isinstance(preset.settings, PresetSettings)

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_valid_depth_model(self, preset: Preset):
        """Test that all presets use valid depth models."""
        valid_models = ["midas_small", "midas_hybrid", "dpt_large", "dpt_hybrid"]
        assert preset.settings.depth_estimation.model in valid_models

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_valid_crf(self, preset: Preset):
        """Test that all presets have CRF in valid range."""
        crf = preset.settings.video_output.crf
        assert 0 <= crf <= 51

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_valid_baseline(self, preset: Preset):
        """Test that all presets have positive baseline."""
        baseline = preset.settings.stereo_generation.baseline
        assert baseline > 0

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_all_presets_have_valid_batch_size(self, preset: Preset):
        """Test that all presets have batch_size >= 1."""
        batch_size = preset.settings.processing.batch_size
        assert batch_size >= 1


class TestBuiltinPresetsCollections:
    """Tests for preset collections."""

    def test_all_builtin_presets_count(self):
        """Test that we have the expected number of built-in presets."""
        assert len(ALL_BUILTIN_PRESETS) == 11

    def test_by_id_mapping_complete(self):
        """Test that BY_ID mapping contains all presets."""
        assert len(BUILTIN_PRESETS_BY_ID) == len(ALL_BUILTIN_PRESETS)
        for preset in ALL_BUILTIN_PRESETS:
            assert preset.id in BUILTIN_PRESETS_BY_ID

    def test_by_name_mapping_complete(self):
        """Test that BY_NAME mapping contains all presets."""
        assert len(BUILTIN_PRESETS_BY_NAME) == len(ALL_BUILTIN_PRESETS)
        for preset in ALL_BUILTIN_PRESETS:
            assert preset.name in BUILTIN_PRESETS_BY_NAME

    def test_unique_ids(self):
        """Test that all preset IDs are unique."""
        ids = [p.id for p in ALL_BUILTIN_PRESETS]
        assert len(ids) == len(set(ids))

    def test_unique_names(self):
        """Test that all preset names are unique."""
        names = [p.name for p in ALL_BUILTIN_PRESETS]
        assert len(names) == len(set(names))


class TestGetBuiltinPreset:
    """Tests for get_builtin_preset function."""

    def test_get_existing_preset(self):
        """Test getting an existing preset by ID."""
        preset = get_builtin_preset("builtin-cinema-sbs")
        assert preset is not None
        assert preset.name == "Cinema (Side-by-Side)"

    def test_get_nonexistent_preset(self):
        """Test getting a nonexistent preset returns None."""
        preset = get_builtin_preset("nonexistent-id")
        assert preset is None


class TestGetBuiltinPresetByName:
    """Tests for get_builtin_preset_by_name function."""

    def test_get_by_name_exact(self):
        """Test getting a preset by exact name."""
        preset = get_builtin_preset_by_name("Cinema (Side-by-Side)")
        assert preset is not None
        assert preset.id == "builtin-cinema-sbs"

    def test_get_by_name_case_insensitive(self):
        """Test getting a preset is case-insensitive."""
        preset = get_builtin_preset_by_name("CINEMA (SIDE-BY-SIDE)")
        assert preset is not None
        assert preset.id == "builtin-cinema-sbs"

    def test_get_by_name_nonexistent(self):
        """Test getting a nonexistent preset returns None."""
        preset = get_builtin_preset_by_name("Nonexistent Preset")
        assert preset is None


class TestPresetCategories:
    """Tests for preset category assignments."""

    def test_cinema_category(self):
        """Test that cinema presets have correct category."""
        assert CINEMA_SBS.category == PresetCategory.CINEMA
        assert CINEMA_ANAGLYPH.category == PresetCategory.CINEMA

    def test_vr_category(self):
        """Test that VR presets have correct category."""
        assert VR_OVER_UNDER.category == PresetCategory.VR
        assert VR_SIDE_BY_SIDE.category == PresetCategory.VR

    def test_web_category(self):
        """Test that web presets have correct category."""
        assert WEB_SBS.category == PresetCategory.WEB
        assert WEB_ANAGLYPH.category == PresetCategory.WEB

    def test_mobile_category(self):
        """Test that mobile presets have correct category."""
        assert MOBILE_SBS.category == PresetCategory.MOBILE
        assert MOBILE_ANAGLYPH.category == PresetCategory.MOBILE

    def test_general_category(self):
        """Test that general presets have correct category."""
        assert FAST_PREVIEW.category == PresetCategory.GENERAL
        assert MAX_QUALITY.category == PresetCategory.GENERAL
        assert BALANCED.category == PresetCategory.GENERAL


class TestPresetSettingsOptimizations:
    """Tests that presets are optimized for their use cases."""

    def test_cinema_uses_quality_model(self):
        """Test that cinema presets use quality depth models."""
        assert CINEMA_SBS.settings.depth_estimation.model == "dpt_large"
        assert CINEMA_ANAGLYPH.settings.depth_estimation.model == "dpt_large"

    def test_cinema_uses_slow_encoding(self):
        """Test that cinema presets use slow encoding for quality."""
        assert CINEMA_SBS.settings.video_output.preset == "slow"
        assert CINEMA_ANAGLYPH.settings.video_output.preset == "slow"

    def test_cinema_uses_low_crf(self):
        """Test that cinema presets use low CRF for quality."""
        assert CINEMA_SBS.settings.video_output.crf <= 20

    def test_vr_has_stronger_3d(self):
        """Test that VR presets have stronger baseline for 3D effect."""
        assert VR_OVER_UNDER.settings.stereo_generation.baseline >= 0.07

    def test_mobile_uses_fast_encoding(self):
        """Test that mobile presets use fast encoding."""
        assert MOBILE_SBS.settings.video_output.preset == "fast"
        assert MOBILE_ANAGLYPH.settings.video_output.preset == "fast"

    def test_mobile_uses_small_model(self):
        """Test that mobile presets use small/fast depth model."""
        assert MOBILE_SBS.settings.depth_estimation.model == "midas_small"

    def test_fast_preview_uses_ultrafast(self):
        """Test that fast preview uses ultrafast encoding."""
        assert FAST_PREVIEW.settings.video_output.preset == "ultrafast"

    def test_fast_preview_uses_high_crf(self):
        """Test that fast preview uses high CRF for speed."""
        assert FAST_PREVIEW.settings.video_output.crf >= 25

    def test_max_quality_uses_slowest_encoding(self):
        """Test that max quality uses veryslow encoding."""
        assert MAX_QUALITY.settings.video_output.preset == "veryslow"

    def test_max_quality_uses_lowest_crf(self):
        """Test that max quality uses lowest CRF for quality."""
        assert MAX_QUALITY.settings.video_output.crf <= 18

    def test_max_quality_uses_small_batch(self):
        """Test that max quality uses batch_size=1 for quality."""
        assert MAX_QUALITY.settings.processing.batch_size == 1

    def test_fast_preview_uses_large_batch(self):
        """Test that fast preview uses large batch_size for speed."""
        assert FAST_PREVIEW.settings.processing.batch_size >= 4

    def test_half_width_for_vr_and_mobile(self):
        """Test that VR and mobile side-by-side use half-width."""
        assert VR_SIDE_BY_SIDE.settings.stereo_generation.sbs_half_width is True
        assert MOBILE_SBS.settings.stereo_generation.sbs_half_width is True


class TestPresetSerialization:
    """Tests for preset serialization."""

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_to_dict_round_trip(self, preset: Preset):
        """Test that presets survive to_dict/from_dict round trip."""
        data = preset.to_dict()
        restored = Preset.from_dict(data)

        assert restored.id == preset.id
        assert restored.name == preset.name
        assert restored.category == preset.category
        assert restored.settings.depth_estimation.model == preset.settings.depth_estimation.model
        assert restored.settings.video_output.crf == preset.settings.video_output.crf

    @pytest.mark.parametrize("preset", ALL_BUILTIN_PRESETS, ids=lambda p: p.name)
    def test_to_json_round_trip(self, preset: Preset):
        """Test that presets survive JSON round trip."""

        json_str = preset.to_json()
        restored = Preset.from_json(json_str)

        assert restored.id == preset.id
        assert restored.name == preset.name
