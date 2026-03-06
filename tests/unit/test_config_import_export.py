"""Tests for configuration import/export functionality."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from video2d3d.utils.config import (
    FORMAT_JSON,
    FORMAT_YAML,
    SUPPORTED_EXPORT_FORMATS,
    AnaglyphConfig,
    Config,
    DepthEstimationConfig,
    LoggingConfig,
    PreviewConfig,
    ProcessingConfig,
    ProgressTrackingConfig,
    QualityConfig,
    RateLimitConfig,
    SideBySideConfig,
    StereoGenerationConfig,
    VideoInputConfig,
    VideoOutputConfig,
    WebApiConfig,
    export_config,
    export_current_config,
    import_and_apply_config,
    import_config,
)


class TestToDictMethods:
    """Tests for to_dict() serialization methods."""

    def test_processing_config_to_dict(self):
        """Test ProcessingConfig serialization."""
        config = ProcessingConfig(batch_size=8, num_workers=2)
        result = config.to_dict()
        assert result["batch_size"] == 8
        assert result["num_workers"] == 2
        assert "use_gpu" in result
        assert isinstance(result, dict)

    def test_video_input_config_to_dict(self):
        """Test VideoInputConfig serialization."""
        config = VideoInputConfig(default_width=1920, default_height=1080)
        result = config.to_dict()
        assert result["default_width"] == 1920
        assert result["default_height"] == 1080
        assert "supported_formats" in result

    def test_video_output_config_to_dict(self):
        """Test VideoOutputConfig serialization."""
        config = VideoOutputConfig(format="mkv", codec="libx265", crf=28)
        result = config.to_dict()
        assert result["format"] == "mkv"
        assert result["codec"] == "libx265"
        assert result["crf"] == 28

    def test_depth_estimation_config_to_dict(self):
        """Test DepthEstimationConfig serialization."""
        config = DepthEstimationConfig(model="dpt_large", output_width=512)
        result = config.to_dict()
        assert result["model"] == "dpt_large"
        assert result["output_width"] == 512
        assert "temporal_consistency" in result

    def test_anaglyph_config_to_dict(self):
        """Test AnaglyphConfig serialization."""
        config = AnaglyphConfig(type="color", color_method="dubois")
        result = config.to_dict()
        assert result["type"] == "color"
        assert result["color_method"] == "dubois"

    def test_side_by_side_config_to_dict(self):
        """Test SideBySideConfig serialization."""
        config = SideBySideConfig(layout="parallel", swap_eyes=True)
        result = config.to_dict()
        assert result["layout"] == "parallel"
        assert result["swap_eyes"] is True

    def test_stereo_generation_config_to_dict(self):
        """Test StereoGenerationConfig serialization with nested configs."""
        config = StereoGenerationConfig(
            format="anaglyph",
            baseline=0.06,
            anaglyph=AnaglyphConfig(type="grayscale"),
            side_by_side=SideBySideConfig(half_width=True),
        )
        result = config.to_dict()
        assert result["format"] == "anaglyph"
        assert result["baseline"] == 0.06
        assert "anaglyph" in result
        assert "side_by_side" in result
        assert result["anaglyph"]["type"] == "grayscale"
        assert result["side_by_side"]["half_width"] is True

    def test_quality_config_to_dict(self):
        """Test QualityConfig serialization."""
        config = QualityConfig(preset="high", calculate_metrics=True)
        result = config.to_dict()
        assert result["preset"] == "high"
        assert result["calculate_metrics"] is True

    def test_logging_config_to_dict(self):
        """Test LoggingConfig serialization."""
        config = LoggingConfig(level="DEBUG", format="%(message)s")
        result = config.to_dict()
        assert result["level"] == "DEBUG"
        assert "format" in result

    def test_rate_limit_config_to_dict(self):
        """Test RateLimitConfig serialization."""
        config = RateLimitConfig(requests_per_minute=120, enabled=False)
        result = config.to_dict()
        assert result["requests_per_minute"] == 120
        assert result["enabled"] is False

    def test_web_api_config_to_dict(self):
        """Test WebApiConfig serialization with nested rate_limit."""
        config = WebApiConfig(
            enabled=True,
            port=9000,
            rate_limit=RateLimitConfig(requests_per_minute=30),
        )
        result = config.to_dict()
        assert result["enabled"] is True
        assert result["port"] == 9000
        assert "rate_limit" in result
        assert result["rate_limit"]["requests_per_minute"] == 30

    def test_preview_config_to_dict(self):
        """Test PreviewConfig serialization."""
        config = PreviewConfig(enabled=True, show_fps=True, scale=1.5)
        result = config.to_dict()
        assert result["enabled"] is True
        assert result["show_fps"] is True
        assert result["scale"] == 1.5

    def test_progress_tracking_config_to_dict(self):
        """Test ProgressTrackingConfig serialization."""
        config = ProgressTrackingConfig(enabled=True, show_eta=False)
        result = config.to_dict()
        assert result["enabled"] is True
        assert result["show_eta"] is False

    def test_full_config_to_dict(self):
        """Test full Config serialization."""
        config = Config()
        config.project_name = "TestProject"
        config.version = "2.0.0"
        config.processing.batch_size = 16

        result = config.to_dict()

        assert result["project_name"] == "TestProject"
        assert result["version"] == "2.0.0"
        assert "processing" in result
        assert result["processing"]["batch_size"] == 16
        assert "depth_estimation" in result
        assert "stereo_generation" in result
        assert "web_api" in result


class TestFromDictMethod:
    """Tests for Config.from_dict() deserialization."""

    def test_from_dict_with_minimal_data(self):
        """Test from_dict with minimal data uses defaults."""
        data = {}
        config = Config.from_dict(data)
        assert isinstance(config, Config)
        # Should have default values
        assert config.processing.batch_size == 4
        assert config.depth_estimation.model == "midas_small"

    def test_from_dict_with_project_info(self):
        """Test from_dict with project metadata."""
        data = {
            "project_name": "MyProject",
            "version": "1.2.3",
        }
        config = Config.from_dict(data)
        assert config.project_name == "MyProject"
        assert config.version == "1.2.3"

    def test_from_dict_with_processing_section(self):
        """Test from_dict with processing configuration."""
        data = {
            "processing": {
                "batch_size": 8,
                "num_workers": 2,
                "use_gpu": False,
            }
        }
        config = Config.from_dict(data)
        assert config.processing.batch_size == 8
        assert config.processing.num_workers == 2
        assert config.processing.use_gpu is False

    def test_from_dict_with_depth_estimation(self):
        """Test from_dict with depth estimation settings."""
        data = {
            "depth_estimation": {
                "model": "dpt_large",
                "output_width": 512,
                "temporal_consistency": False,
            }
        }
        config = Config.from_dict(data)
        assert config.depth_estimation.model == "dpt_large"
        assert config.depth_estimation.output_width == 512
        assert config.depth_estimation.temporal_consistency is False

    def test_from_dict_with_stereo_generation(self):
        """Test from_dict with nested stereo_generation section."""
        data = {
            "stereo_generation": {
                "format": "anaglyph",
                "baseline": 0.08,
                "anaglyph": {
                    "type": "color",
                    "color_method": "dubois",
                },
                "side_by_side": {
                    "layout": "cross",
                    "swap_eyes": True,
                },
            }
        }
        config = Config.from_dict(data)
        assert config.stereo_generation.format == "anaglyph"
        assert config.stereo_generation.baseline == 0.08
        assert config.stereo_generation.anaglyph.type == "color"
        assert config.stereo_generation.anaglyph.color_method == "dubois"
        assert config.stereo_generation.side_by_side.layout == "cross"
        assert config.stereo_generation.side_by_side.swap_eyes is True

    def test_from_dict_with_web_api(self):
        """Test from_dict with nested web_api section."""
        data = {
            "web_api": {
                "enabled": True,
                "port": 9000,
                "rate_limit": {
                    "enabled": True,
                    "requests_per_minute": 30,
                },
            }
        }
        config = Config.from_dict(data)
        assert config.web_api.enabled is True
        assert config.web_api.port == 9000
        assert config.web_api.rate_limit.enabled is True
        assert config.web_api.rate_limit.requests_per_minute == 30

    def test_from_dict_ignores_unknown_fields(self):
        """Test that from_dict ignores unknown fields gracefully."""
        data = {
            "processing": {
                "batch_size": 8,
                "unknown_field": "should_be_ignored",
            },
            "unknown_section": {"foo": "bar"},
        }
        # Should not raise an error
        config = Config.from_dict(data)
        assert config.processing.batch_size == 8

    def test_from_dict_with_invalid_data_raises_error(self):
        """Test that from_dict raises ValueError for invalid data types."""
        data = {
            "processing": {
                "batch_size": "not_an_integer",  # Invalid type
            }
        }
        with pytest.raises(ValueError):
            Config.from_dict(data)


class TestExportConfig:
    """Tests for export_config() function."""

    def test_export_to_json(self, tmp_path: Path):
        """Test exporting configuration to JSON file."""
        config = Config()
        config.project_name = "ExportTest"
        output_file = tmp_path / "config.json"

        result = export_config(config, output_file, FORMAT_JSON)

        assert result == output_file
        assert output_file.exists()

        # Verify content
        with open(output_file) as f:
            data = json.load(f)
        assert data["project_name"] == "ExportTest"
        assert "processing" in data

    def test_export_to_yaml(self, tmp_path: Path):
        """Test exporting configuration to YAML file."""
        config = Config()
        config.project_name = "YAMLExport"
        output_file = tmp_path / "config.yaml"

        result = export_config(config, output_file, FORMAT_YAML)

        assert result == output_file
        assert output_file.exists()

        # Verify content
        with open(output_file) as f:
            data = yaml.safe_load(f)
        assert data["project_name"] == "YAMLExport"
        assert "processing" in data

    def test_export_creates_parent_directories(self, tmp_path: Path):
        """Test that export creates parent directories if needed."""
        config = Config()
        output_file = tmp_path / "nested" / "dir" / "config.json"

        export_config(config, output_file, FORMAT_JSON)

        assert output_file.exists()

    def test_export_rejects_unsupported_format(self, tmp_path: Path):
        """Test that export raises ValueError for unsupported formats."""
        config = Config()
        output_file = tmp_path / "config.xml"

        with pytest.raises(ValueError, match="Unsupported format"):
            export_config(config, output_file, "xml")

    def test_export_format_case_insensitive(self, tmp_path: Path):
        """Test that format is case-insensitive."""
        config = Config()
        output_file = tmp_path / "config.json"

        # Should work with uppercase
        export_config(config, output_file, "JSON")
        assert output_file.exists()

    def test_export_preserves_nested_structure(self, tmp_path: Path):
        """Test that export preserves nested configuration structure."""
        config = Config()
        config.web_api.rate_limit.requests_per_minute = 45
        output_file = tmp_path / "config.json"

        export_config(config, output_file, FORMAT_JSON)

        with open(output_file) as f:
            data = json.load(f)
        assert data["web_api"]["rate_limit"]["requests_per_minute"] == 45


class TestImportConfig:
    """Tests for import_config() function."""

    def test_import_from_json(self, tmp_path: Path):
        """Test importing configuration from JSON file."""
        data = {
            "project_name": "ImportTest",
            "version": "3.0.0",
            "processing": {"batch_size": 16},
        }
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(data, f)

        config = import_config(config_file)

        assert config.project_name == "ImportTest"
        assert config.version == "3.0.0"
        assert config.processing.batch_size == 16

    def test_import_from_yaml(self, tmp_path: Path):
        """Test importing configuration from YAML file."""
        yaml_content = """
project_name: YAMLImport
version: "2.5.0"
processing:
  batch_size: 12
  use_gpu: false
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml_content)

        config = import_config(config_file)

        assert config.project_name == "YAMLImport"
        assert config.version == "2.5.0"
        assert config.processing.batch_size == 12
        assert config.processing.use_gpu is False

    def test_import_from_yml_extension(self, tmp_path: Path):
        """Test importing from .yml extension."""
        data = {"project_name": "YMLTest"}
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(data, f)

        config = import_config(config_file)
        assert config.project_name == "YMLTest"

    def test_import_raises_for_missing_file(self, tmp_path: Path):
        """Test that import raises FileNotFoundError for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            import_config(missing_file)

    def test_import_raises_for_unsupported_format(self, tmp_path: Path):
        """Test that import raises ValueError for unsupported formats."""
        config_file = tmp_path / "config.xml"
        config_file.write_text("<config></config>")

        with pytest.raises(ValueError, match="Unsupported file format"):
            import_config(config_file)

    def test_import_raises_for_invalid_json(self, tmp_path: Path):
        """Test that import raises ValueError for invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            import_config(config_file)

    def test_import_raises_for_non_dict_json(self, tmp_path: Path):
        """Test that import raises ValueError for non-dict JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text('"just a string"')

        with pytest.raises(ValueError, match="expected a dictionary"):
            import_config(config_file)


class TestExportCurrentConfig:
    """Tests for export_current_config() function."""

    def test_export_current_config(self, tmp_path: Path):
        """Test exporting the current global configuration."""
        output_file = tmp_path / "current_config.json"

        result = export_current_config(output_file, FORMAT_JSON)

        assert result == output_file
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
        assert "project_name" in data
        assert "processing" in data


class TestImportAndApplyConfig:
    """Tests for import_and_apply_config() function."""

    def test_import_and_apply_updates_global_config(self, tmp_path: Path):
        """Test that import_and_apply_config updates global config."""
        data = {
            "project_name": "AppliedConfig",
            "processing": {"batch_size": 32},
        }
        config_file = tmp_path / "apply_config.json"
        with open(config_file, "w") as f:
            json.dump(data, f)

        config = import_and_apply_config(config_file)

        assert config.project_name == "AppliedConfig"
        assert config.processing.batch_size == 32


class TestRoundTripExportImport:
    """Integration tests for export/import round-trip."""

    def test_roundtrip_json_preserves_config(self, tmp_path: Path):
        """Test that JSON export/import preserves configuration."""
        original = Config()
        original.project_name = "RoundTripJSON"
        original.version = "1.0.0"
        original.processing.batch_size = 24
        original.processing.num_workers = 8
        original.depth_estimation.model = "dpt_hybrid"
        original.depth_estimation.output_width = 640
        original.stereo_generation.format = "anaglyph"
        original.stereo_generation.baseline = 0.07
        original.stereo_generation.anaglyph.type = "color"
        original.web_api.enabled = True
        original.web_api.port = 8080
        original.web_api.rate_limit.requests_per_minute = 100

        # Export
        export_file = tmp_path / "roundtrip.json"
        export_config(original, export_file, FORMAT_JSON)

        # Import
        restored = import_config(export_file)

        # Verify all values preserved
        assert restored.project_name == original.project_name
        assert restored.version == original.version
        assert restored.processing.batch_size == original.processing.batch_size
        assert restored.processing.num_workers == original.processing.num_workers
        assert restored.depth_estimation.model == original.depth_estimation.model
        assert restored.depth_estimation.output_width == original.depth_estimation.output_width
        assert restored.stereo_generation.format == original.stereo_generation.format
        assert restored.stereo_generation.baseline == original.stereo_generation.baseline
        assert restored.stereo_generation.anaglyph.type == original.stereo_generation.anaglyph.type
        assert restored.web_api.enabled == original.web_api.enabled
        assert restored.web_api.port == original.web_api.port
        assert (
            restored.web_api.rate_limit.requests_per_minute
            == original.web_api.rate_limit.requests_per_minute
        )

    def test_roundtrip_yaml_preserves_config(self, tmp_path: Path):
        """Test that YAML export/import preserves configuration."""
        original = Config()
        original.project_name = "RoundTripYAML"
        original.processing.batch_size = 16
        original.depth_estimation.temporal_consistency = False
        original.stereo_generation.side_by_side.swap_eyes = True

        # Export
        export_file = tmp_path / "roundtrip.yaml"
        export_config(original, export_file, FORMAT_YAML)

        # Import
        restored = import_config(export_file)

        # Verify values preserved
        assert restored.project_name == original.project_name
        assert restored.processing.batch_size == original.processing.batch_size
        assert (
            restored.depth_estimation.temporal_consistency
            == original.depth_estimation.temporal_consistency
        )
        assert (
            restored.stereo_generation.side_by_side.swap_eyes
            == original.stereo_generation.side_by_side.swap_eyes
        )

    def test_roundtrip_default_config(self, tmp_path: Path):
        """Test round-trip with default configuration."""
        original = Config()

        export_file = tmp_path / "defaults.json"
        export_config(original, export_file, FORMAT_JSON)
        restored = import_config(export_file)

        # All defaults should be preserved
        assert restored.to_dict() == original.to_dict()


class TestConstants:
    """Tests for configuration constants."""

    def test_format_constants(self):
        """Test that format constants are defined correctly."""
        assert FORMAT_JSON == "json"
        assert FORMAT_YAML == "yaml"

    def test_supported_formats_tuple(self):
        """Test that SUPPORTED_EXPORT_FORMATS contains expected values."""
        assert FORMAT_JSON in SUPPORTED_EXPORT_FORMATS
        assert FORMAT_YAML in SUPPORTED_EXPORT_FORMATS
        assert len(SUPPORTED_EXPORT_FORMATS) == 2


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_export_with_unicode_values(self, tmp_path: Path):
        """Test export handles Unicode characters correctly."""
        config = Config()
        config.project_name = "Тест测试🎉"  # Cyrillic, Chinese, Emoji

        export_file = tmp_path / "unicode.json"
        export_config(config, export_file, FORMAT_JSON)

        restored = import_config(export_file)
        assert restored.project_name == "Тест测试🎉"

    def test_export_with_special_characters_in_path(self, tmp_path: Path):
        """Test export handles special characters in file path."""
        config = Config()
        config.project_name = "SpecialPath"

        # Create path with spaces
        special_dir = tmp_path / "my config files"
        special_dir.mkdir()
        export_file = special_dir / "config file.json"

        export_config(config, export_file, FORMAT_JSON)
        assert export_file.exists()

    def test_export_overwrites_existing_file(self, tmp_path: Path):
        """Test that export overwrites existing file."""
        config1 = Config()
        config1.project_name = "First"

        config2 = Config()
        config2.project_name = "Second"

        export_file = tmp_path / "overwrite.json"

        export_config(config1, export_file, FORMAT_JSON)
        export_config(config2, export_file, FORMAT_JSON)

        restored = import_config(export_file)
        assert restored.project_name == "Second"

    def test_import_with_extra_nested_fields(self, tmp_path: Path):
        """Test import handles extra nested fields gracefully."""
        data = {
            "processing": {
                "batch_size": 8,
                "extra_nested": {"ignored": True},
            }
        }
        config_file = tmp_path / "extra_fields.json"
        with open(config_file, "w") as f:
            json.dump(data, f)

        # Should not raise - unknown fields are ignored
        config = import_config(config_file)
        assert config.processing.batch_size == 8

    def test_empty_config_export_import(self, tmp_path: Path):
        """Test export/import of empty/minimal configuration."""
        data = {}
        config_file = tmp_path / "empty.json"
        with open(config_file, "w") as f:
            json.dump(data, f)

        config = import_config(config_file)
        assert isinstance(config, Config)

        # Re-export should work
        export_file = tmp_path / "reexport.json"
        export_config(config, export_file, FORMAT_JSON)
        assert export_file.exists()
