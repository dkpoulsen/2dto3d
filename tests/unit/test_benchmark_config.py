"""Unit tests for the benchmark configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest

from video2d3d.benchmark.config import (
    BenchmarkCategory,
    BenchmarkConfig,
    FullBenchmarkConfig,
    QuickBenchmarkConfig,
    ResolutionPreset,
)


class TestBenchmarkCategory:
    """Tests for BenchmarkCategory enum."""

    def test_category_values(self):
        """Test that all expected categories exist."""
        assert BenchmarkCategory.MODEL_COMPARISON.value == "model_comparison"
        assert BenchmarkCategory.RESOLUTION_SCALING.value == "resolution_scaling"
        assert BenchmarkCategory.HARDWARE_COMPARISON.value == "hardware_comparison"
        assert BenchmarkCategory.BATCH_PROCESSING.value == "batch_processing"
        assert BenchmarkCategory.FULL_PIPELINE.value == "full_pipeline"

    def test_all_categories_defined(self):
        """Test that we have 5 categories."""
        assert len(BenchmarkCategory) == 5


class TestResolutionPreset:
    """Tests for ResolutionPreset enum."""

    def test_preset_dimensions(self):
        """Test resolution preset dimensions."""
        assert ResolutionPreset.SD_480P.width == 640
        assert ResolutionPreset.SD_480P.height == 480
        assert ResolutionPreset.UHD_4K.width == 3840
        assert ResolutionPreset.UHD_4K.height == 2160

    def test_preset_labels(self):
        """Test resolution preset labels."""
        assert ResolutionPreset.SD_480P.label == "480p (SD)"
        assert ResolutionPreset.HD_720P.label == "720p (HD)"
        assert ResolutionPreset.FHD_1080P.label == "1080p (FHD)"
        assert ResolutionPreset.QHD_1440P.label == "1440p (QHD)"
        assert ResolutionPreset.UHD_4K.label == "2160p (4K)"

    def test_value_tuple(self):
        """Test that value is a tuple of (width, height)."""
        assert ResolutionPreset.FHD_1080P.value == (1920, 1080)


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BenchmarkConfig()

        assert len(config.models) == 4
        assert "midas_small" in config.models
        assert config.warmup_iterations == 3
        assert config.test_iterations == 10
        assert config.seed == 42
        assert config.report_format == "markdown"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = BenchmarkConfig(
            models=["midas_small"],
            warmup_iterations=1,
            test_iterations=5,
            seed=123,
        )

        assert config.models == ["midas_small"]
        assert config.warmup_iterations == 1
        assert config.test_iterations == 5
        assert config.seed == 123

    def test_output_dir_path_conversion(self):
        """Test that output_dir is converted to Path."""
        config = BenchmarkConfig(output_dir="custom/path")

        assert isinstance(config.output_dir, Path)
        assert config.output_dir == Path("custom/path")

    def test_all_resolutions_property(self):
        """Test all_resolutions combines explicit and preset resolutions."""
        config = BenchmarkConfig(
            resolutions=[(320, 240)],
            resolution_presets=[ResolutionPreset.SD_480P],
        )

        all_res = config.all_resolutions
        assert (320, 240) in all_res
        assert (640, 480) in all_res

    def test_all_resolutions_sorted_by_pixels(self):
        """Test that resolutions are sorted by pixel count."""
        config = BenchmarkConfig(
            resolution_presets=[
                ResolutionPreset.FHD_1080P,
                ResolutionPreset.SD_480P,
                ResolutionPreset.HD_720P,
            ]
        )

        all_res = config.all_resolutions
        # Should be sorted by width * height
        pixels = [w * h for w, h in all_res]
        assert pixels == sorted(pixels)

    def test_invalid_warmup_iterations(self):
        """Test that negative warmup_iterations raises ValueError."""
        with pytest.raises(ValueError, match="warmup_iterations"):
            BenchmarkConfig(warmup_iterations=-1)

    def test_invalid_test_iterations(self):
        """Test that zero test_iterations raises ValueError."""
        with pytest.raises(ValueError, match="test_iterations"):
            BenchmarkConfig(test_iterations=0)

    def test_invalid_timeout(self):
        """Test that non-positive timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds"):
            BenchmarkConfig(timeout_seconds=0)

        with pytest.raises(ValueError, match="timeout_seconds"):
            BenchmarkConfig(timeout_seconds=-1)

    def test_invalid_report_format(self):
        """Test that invalid report_format raises ValueError."""
        with pytest.raises(ValueError, match="report_format"):
            BenchmarkConfig(report_format="invalid")

    def test_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models"):
            BenchmarkConfig(models=[])

    def test_model_display_names(self):
        """Test model display name mapping."""
        config = BenchmarkConfig()
        names = config.get_model_display_names()

        assert names["midas_small"] == "MiDaS v2.1 Small"
        assert names["dpt_large"] == "DPT Large"


class TestQuickBenchmarkConfig:
    """Tests for QuickBenchmarkConfig."""

    def test_quick_config_values(self):
        """Test that quick config has minimal values."""
        config = QuickBenchmarkConfig()

        assert config.models == ["midas_small"]
        assert config.warmup_iterations == 1
        assert config.test_iterations == 3
        assert config.categories == [BenchmarkCategory.MODEL_COMPARISON]


class TestFullBenchmarkConfig:
    """Tests for FullBenchmarkConfig."""

    def test_full_config_values(self):
        """Test that full config has comprehensive values."""
        config = FullBenchmarkConfig()

        assert len(config.models) == 4
        assert config.warmup_iterations == 5
        assert config.test_iterations == 20
        assert len(config.batch_sizes) == 5
        assert len(config.categories) == 5  # All categories

    def test_full_config_all_resolutions(self):
        """Test that full config includes all resolution presets."""
        config = FullBenchmarkConfig()

        # Should have all 5 presets
        assert len(config.resolution_presets) == 5


class TestBenchmarkConfigIntegration:
    """Integration tests for configuration."""

    def test_config_can_be_created_with_pathlib_path(self):
        """Test config accepts pathlib Path objects."""
        config = BenchmarkConfig(
            output_dir=Path("/tmp/benchmarks"),
            custom_test_images=[Path("/tmp/test.jpg")],
        )

        assert config.output_dir == Path("/tmp/benchmarks")
        assert config.custom_test_images == [Path("/tmp/test.jpg")]

    def test_config_categories_can_be_filtered(self):
        """Test that config can specify subset of categories."""
        config = BenchmarkConfig(
            categories=[
                BenchmarkCategory.MODEL_COMPARISON,
                BenchmarkCategory.RESOLUTION_SCALING,
            ]
        )

        assert len(config.categories) == 2
        assert BenchmarkCategory.HARDWARE_COMPARISON not in config.categories
