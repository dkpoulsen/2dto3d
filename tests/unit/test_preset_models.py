"""Tests for preset data models.

This module tests all preset data models including:
- PresetCategory enum
- Settings dataclasses with validation
- Preset class with serialization/deserialization
"""

import json
from datetime import datetime

import pytest

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


class TestPresetCategory:
    """Tests for PresetCategory enum."""

    def test_all_categories_exist(self):
        """Test that all expected categories are defined."""
        assert PresetCategory.CINEMA.value == "cinema"
        assert PresetCategory.VR.value == "vr"
        assert PresetCategory.WEB.value == "web"
        assert PresetCategory.MOBILE.value == "mobile"
        assert PresetCategory.CUSTOM.value == "custom"
        assert PresetCategory.GENERAL.value == "general"

    def test_category_is_string_enum(self):
        """Test that PresetCategory is a string enum."""
        assert isinstance(PresetCategory.CINEMA, str)
        assert PresetCategory.CINEMA == "cinema"


class TestDepthEstimationSettings:
    """Tests for DepthEstimationSettings dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = DepthEstimationSettings()
        assert settings.model == "midas_small"
        assert settings.output_width == 384
        assert settings.output_height == 384
        assert settings.min_depth == 0.0
        assert settings.max_depth == 1.0
        assert settings.temporal_consistency is True
        assert settings.temporal_smoothing_factor == 0.5

    def test_custom_values(self):
        """Test custom values are set correctly."""
        settings = DepthEstimationSettings(
            model="dpt_large",
            output_width=512,
            output_height=512,
            min_depth=0.1,
            max_depth=10.0,
            temporal_consistency=False,
            temporal_smoothing_factor=0.3,
        )
        assert settings.model == "dpt_large"
        assert settings.output_width == 512
        assert settings.min_depth == 0.1

    def test_to_dict(self):
        """Test serialization to dictionary."""
        settings = DepthEstimationSettings(model="dpt_hybrid")
        data = settings.to_dict()
        assert isinstance(data, dict)
        assert data["model"] == "dpt_hybrid"
        assert data["output_width"] == 384

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "model": "midas_hybrid",
            "output_width": 256,
            "output_height": 256,
        }
        settings = DepthEstimationSettings.from_dict(data)
        assert settings.model == "midas_hybrid"
        assert settings.output_width == 256
        # Default values for missing keys
        assert settings.temporal_consistency is True

    def test_from_dict_empty(self):
        """Test deserialization from empty dictionary uses defaults."""
        settings = DepthEstimationSettings.from_dict({})
        assert settings.model == "midas_small"
        assert settings.output_width == 384


class TestStereoGenerationSettings:
    """Tests for StereoGenerationSettings dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = StereoGenerationSettings()
        assert settings.format == "side_by_side"
        assert settings.baseline == 0.05
        assert settings.focal_length == 1.0
        assert settings.convergence == 0.5
        assert settings.anaglyph_type == "red_cyan"
        assert settings.anaglyph_color_method == "dubois"
        assert settings.sbs_layout == "horizontal"
        assert settings.sbs_swap_eyes is False
        assert settings.sbs_half_width is False

    def test_validation_positive_baseline(self):
        """Test that baseline must be positive."""
        with pytest.raises(ValueError, match="baseline must be positive"):
            StereoGenerationSettings(baseline=0)

        with pytest.raises(ValueError, match="baseline must be positive"):
            StereoGenerationSettings(baseline=-0.1)

    def test_validation_positive_focal_length(self):
        """Test that focal_length must be positive."""
        with pytest.raises(ValueError, match="focal_length must be positive"):
            StereoGenerationSettings(focal_length=0)

        with pytest.raises(ValueError, match="focal_length must be positive"):
            StereoGenerationSettings(focal_length=-1.0)

    def test_valid_positive_values(self):
        """Test that positive values are accepted."""
        settings = StereoGenerationSettings(baseline=0.1, focal_length=2.0)
        assert settings.baseline == 0.1
        assert settings.focal_length == 2.0

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        original = StereoGenerationSettings(
            format="anaglyph",
            baseline=0.08,
            anaglyph_type="green_magenta",
        )
        data = original.to_dict()
        restored = StereoGenerationSettings.from_dict(data)
        assert restored.format == "anaglyph"
        assert restored.baseline == 0.08
        assert restored.anaglyph_type == "green_magenta"


class TestVideoOutputSettings:
    """Tests for VideoOutputSettings dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = VideoOutputSettings()
        assert settings.format == "mp4"
        assert settings.codec == "libx264"
        assert settings.preset == "medium"
        assert settings.crf == 23
        assert settings.pixel_format == "yuv420p"

    def test_validation_crf_range_min(self):
        """Test that CRF must be >= 0."""
        with pytest.raises(ValueError, match="crf must be between 0 and 51"):
            VideoOutputSettings(crf=-1)

    def test_validation_crf_range_max(self):
        """Test that CRF must be <= 51."""
        with pytest.raises(ValueError, match="crf must be between 0 and 51"):
            VideoOutputSettings(crf=52)

    def test_valid_crf_boundary_values(self):
        """Test that boundary CRF values are accepted."""
        settings_min = VideoOutputSettings(crf=0)
        assert settings_min.crf == 0

        settings_max = VideoOutputSettings(crf=51)
        assert settings_max.crf == 51

    def test_valid_crf_common_values(self):
        """Test that common CRF values are accepted."""
        for crf in [18, 20, 23, 26, 28]:
            settings = VideoOutputSettings(crf=crf)
            assert settings.crf == crf

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        original = VideoOutputSettings(
            format="mkv",
            codec="libx265",
            preset="slow",
            crf=18,
        )
        data = original.to_dict()
        restored = VideoOutputSettings.from_dict(data)
        assert restored.format == "mkv"
        assert restored.codec == "libx265"
        assert restored.crf == 18


class TestProcessingSettings:
    """Tests for ProcessingSettings dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = ProcessingSettings()
        assert settings.batch_size == 4
        assert settings.num_workers == 4
        assert settings.use_gpu is True
        assert settings.gpu_device == 0
        assert settings.mixed_precision is True
        assert settings.max_memory_percent == 80

    def test_validation_batch_size_minimum(self):
        """Test that batch_size must be at least 1."""
        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            ProcessingSettings(batch_size=0)

        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            ProcessingSettings(batch_size=-1)

    def test_validation_num_workers_non_negative(self):
        """Test that num_workers must be non-negative."""
        with pytest.raises(ValueError, match="num_workers must be non-negative"):
            ProcessingSettings(num_workers=-1)

    def test_validation_max_memory_percent_range(self):
        """Test that max_memory_percent must be 0-100."""
        with pytest.raises(ValueError, match="max_memory_percent must be 0-100"):
            ProcessingSettings(max_memory_percent=-1)

        with pytest.raises(ValueError, match="max_memory_percent must be 0-100"):
            ProcessingSettings(max_memory_percent=101)

    def test_valid_boundary_values(self):
        """Test that boundary values are accepted."""
        settings = ProcessingSettings(
            batch_size=1,
            num_workers=0,
            max_memory_percent=0,
        )
        assert settings.batch_size == 1
        assert settings.num_workers == 0
        assert settings.max_memory_percent == 0

        settings_max = ProcessingSettings(max_memory_percent=100)
        assert settings_max.max_memory_percent == 100

    def test_cpu_only_settings(self):
        """Test CPU-only processing settings."""
        settings = ProcessingSettings(
            use_gpu=False,
            num_workers=8,
        )
        assert settings.use_gpu is False
        assert settings.num_workers == 8


class TestQualitySettings:
    """Tests for QualitySettings dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        settings = QualitySettings()
        assert settings.preset == "balanced"
        assert settings.post_processing is True
        assert settings.calculate_metrics is False

    def test_custom_values(self):
        """Test custom values are set correctly."""
        settings = QualitySettings(
            preset="quality",
            post_processing=False,
            calculate_metrics=True,
        )
        assert settings.preset == "quality"
        assert settings.post_processing is False
        assert settings.calculate_metrics is True

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        original = QualitySettings(preset="fast", calculate_metrics=True)
        data = original.to_dict()
        restored = QualitySettings.from_dict(data)
        assert restored.preset == "fast"
        assert restored.calculate_metrics is True


class TestPresetSettings:
    """Tests for PresetSettings dataclass."""

    def test_default_values(self):
        """Test default values create all sub-settings."""
        settings = PresetSettings()
        assert isinstance(settings.depth_estimation, DepthEstimationSettings)
        assert isinstance(settings.stereo_generation, StereoGenerationSettings)
        assert isinstance(settings.video_output, VideoOutputSettings)
        assert isinstance(settings.processing, ProcessingSettings)
        assert isinstance(settings.quality, QualitySettings)

    def test_custom_sub_settings(self):
        """Test custom sub-settings are preserved."""
        depth = DepthEstimationSettings(model="dpt_large")
        settings = PresetSettings(depth_estimation=depth)
        assert settings.depth_estimation.model == "dpt_large"

    def test_to_dict_contains_all_sections(self):
        """Test that to_dict includes all sections."""
        settings = PresetSettings()
        data = settings.to_dict()
        assert "depth_estimation" in data
        assert "stereo_generation" in data
        assert "video_output" in data
        assert "processing" in data
        assert "quality" in data

    def test_from_dict_creates_nested_objects(self):
        """Test that from_dict creates proper nested objects."""
        data = {
            "depth_estimation": {"model": "dpt_hybrid"},
            "video_output": {"crf": 20},
        }
        settings = PresetSettings.from_dict(data)
        assert settings.depth_estimation.model == "dpt_hybrid"
        assert settings.video_output.crf == 20
        # Defaults for missing sections
        assert settings.stereo_generation.format == "side_by_side"

    def test_round_trip_preserves_all_data(self):
        """Test that serialization round-trip preserves all data."""
        original = PresetSettings(
            depth_estimation=DepthEstimationSettings(model="dpt_large"),
            stereo_generation=StereoGenerationSettings(baseline=0.08),
            video_output=VideoOutputSettings(crf=18),
            processing=ProcessingSettings(batch_size=2),
            quality=QualitySettings(preset="quality"),
        )
        data = original.to_dict()
        restored = PresetSettings.from_dict(data)
        assert restored.depth_estimation.model == "dpt_large"
        assert restored.stereo_generation.baseline == 0.08
        assert restored.video_output.crf == 18
        assert restored.processing.batch_size == 2
        assert restored.quality.preset == "quality"


class TestPreset:
    """Tests for Preset dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        preset = Preset()
        assert preset.name == ""
        assert preset.description == ""
        assert preset.category == PresetCategory.GENERAL
        assert preset.tags == []
        assert preset.is_builtin is False
        assert preset.version == "1.0.0"
        assert preset.author == ""

    def test_auto_generated_id(self):
        """Test that ID is auto-generated and unique."""
        preset1 = Preset(name="test1")
        preset2 = Preset(name="test2")
        assert preset1.id != preset2.id
        assert len(preset1.id) == 36  # UUID format

    def test_auto_generated_timestamps(self):
        """Test that timestamps are auto-generated."""
        preset = Preset(name="test")
        # ISO format: 2024-01-15T10:30:00.123456
        assert "T" in preset.created_at
        assert "T" in preset.updated_at

    def test_custom_values(self):
        """Test custom values are set correctly."""
        settings = PresetSettings()
        preset = Preset(
            name="My Preset",
            description="Test preset",
            category=PresetCategory.CINEMA,
            tags=["4k", "hdr"],
            settings=settings,
            author="Test Author",
            version="2.0.0",
        )
        assert preset.name == "My Preset"
        assert preset.category == PresetCategory.CINEMA
        assert "4k" in preset.tags
        assert preset.author == "Test Author"

    def test_update_timestamp(self):
        """Test update_timestamp method."""
        preset = Preset(name="test")
        original_updated = preset.updated_at
        preset.update_timestamp()
        assert preset.updated_at != original_updated

    def test_to_dict(self):
        """Test serialization to dictionary."""
        preset = Preset(
            name="Test",
            category=PresetCategory.VR,
            tags=["test"],
        )
        data = preset.to_dict()
        assert data["name"] == "Test"
        assert data["category"] == "vr"
        assert data["tags"] == ["test"]
        assert "settings" in data
        assert "id" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-id-123",
            "name": "Restored Preset",
            "description": "A restored preset",
            "category": "web",
            "tags": ["restored"],
            "settings": {
                "depth_estimation": {"model": "midas_hybrid"},
            },
            "is_builtin": True,
            "version": "1.5.0",
        }
        preset = Preset.from_dict(data)
        assert preset.id == "test-id-123"
        assert preset.name == "Restored Preset"
        assert preset.category == PresetCategory.WEB
        assert preset.is_builtin is True
        assert preset.settings.depth_estimation.model == "midas_hybrid"

    def test_from_dict_invalid_category_defaults_to_general(self):
        """Test that invalid category defaults to GENERAL."""
        data = {
            "name": "Test",
            "category": "invalid_category",
        }
        preset = Preset.from_dict(data)
        assert preset.category == PresetCategory.GENERAL

    def test_to_json(self):
        """Test serialization to JSON string."""
        preset = Preset(name="JSON Test")
        json_str = preset.to_json()
        assert isinstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["name"] == "JSON Test"

    def test_from_json(self):
        """Test deserialization from JSON string."""
        json_str = """{
            "id": "json-test-id",
            "name": "From JSON",
            "category": "mobile",
            "settings": {
                "video_output": {"crf": 25}
            }
        }"""
        preset = Preset.from_json(json_str)
        assert preset.id == "json-test-id"
        assert preset.name == "From JSON"
        assert preset.category == PresetCategory.MOBILE
        assert preset.settings.video_output.crf == 25

    def test_json_round_trip(self):
        """Test JSON serialization round-trip."""
        original = Preset(
            name="Round Trip",
            description="Testing JSON round trip",
            category=PresetCategory.CINEMA,
            tags=["json", "test"],
        )
        json_str = original.to_json()
        restored = Preset.from_json(json_str)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.category == original.category
        assert restored.tags == original.tags

    def test_equality_by_id(self):
        """Test equality is based on ID."""
        preset1 = Preset(id="same-id", name="First")
        preset2 = Preset(id="same-id", name="Second")
        preset3 = Preset(id="different-id", name="First")
        assert preset1 == preset2
        assert preset1 != preset3

    def test_equality_with_non_preset(self):
        """Test equality with non-Preset objects."""
        preset = Preset(name="test")
        assert preset != "test"
        assert preset != 123
        assert preset != None

    def test_hash_by_id(self):
        """Test hashing is based on ID."""
        preset1 = Preset(id="same-id", name="First")
        preset2 = Preset(id="same-id", name="Second")
        # Same ID means same hash
        assert hash(preset1) == hash(preset2)
        # Can be used in sets
        preset_set = {preset1, preset2}
        assert len(preset_set) == 1

    def test_str_representation(self):
        """Test string representation."""
        preset = Preset(name="Test Preset", category=PresetCategory.VR)
        assert "Test Preset" in str(preset)
        assert "vr" in str(preset)

    def test_repr_representation(self):
        """Test repr representation."""
        preset = Preset(id="test-id", name="Test", category=PresetCategory.WEB)
        repr_str = repr(preset)
        assert "test-id" in repr_str
        assert "Test" in repr_str
        assert "web" in repr_str


class TestPresetSettingsValidationIntegration:
    """Integration tests for settings validation within Preset."""

    def test_preset_validates_nested_stereo_settings(self):
        """Test that Preset validates nested stereo settings."""
        with pytest.raises(ValueError, match="baseline must be positive"):
            Preset(
                name="Invalid",
                settings=PresetSettings(stereo_generation=StereoGenerationSettings(baseline=-1)),
            )

    def test_preset_validates_nested_video_settings(self):
        """Test that Preset validates nested video settings."""
        with pytest.raises(ValueError, match="crf must be between 0 and 51"):
            Preset(
                name="Invalid",
                settings=PresetSettings(video_output=VideoOutputSettings(crf=100)),
            )

    def test_preset_validates_nested_processing_settings(self):
        """Test that Preset validates nested processing settings."""
        with pytest.raises(ValueError, match="batch_size must be at least 1"):
            Preset(
                name="Invalid",
                settings=PresetSettings(processing=ProcessingSettings(batch_size=0)),
            )

    def test_preset_accepts_all_valid_settings(self):
        """Test that Preset accepts all valid settings combinations."""
        preset = Preset(
            name="Valid Preset",
            settings=PresetSettings(
                depth_estimation=DepthEstimationSettings(model="dpt_large"),
                stereo_generation=StereoGenerationSettings(
                    format="anaglyph",
                    baseline=0.1,
                    focal_length=2.0,
                ),
                video_output=VideoOutputSettings(crf=18),
                processing=ProcessingSettings(batch_size=1, num_workers=0),
                quality=QualitySettings(preset="quality"),
            ),
        )
        assert preset.name == "Valid Preset"
        assert preset.settings.depth_estimation.model == "dpt_large"
        assert preset.settings.video_output.crf == 18
