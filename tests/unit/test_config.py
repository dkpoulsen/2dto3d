"""Test configuration loading and management."""

import pytest
from pathlib import Path

from video2d3d.utils.config import (
    Config,
    ProcessingConfig,
    VideoInputConfig,
    VideoOutputConfig,
    DepthEstimationConfig,
    StereoGenerationConfig,
    load_config,
    get_config_path,
    deep_update,
)


class TestConfigLoading:
    """Tests for configuration loading functionality."""

    def test_get_config_path_returns_path(self):
        """Test that get_config_path returns a Path object."""
        path = get_config_path()
        assert isinstance(path, Path)

    def test_deep_update_merges_dicts(self):
        """Test deep dictionary merging."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        update = {"b": {"c": 10}}
        result = deep_update(base, update)
        assert result == {"a": 1, "b": {"c": 10, "d": 3}}

    def test_load_config_returns_config_object(self, tmp_path: Path):
        """Test that load_config returns a Config instance."""
        # Create a minimal config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config_file = config_dir / "default.yaml"
        config_file.write_text("project:\n  name: Test\n  version: 0.1.0\n")

        config = load_config(config_path=config_dir, environment="production")
        assert isinstance(config, Config)

    def test_config_has_default_values(self):
        """Test that Config has sensible defaults."""
        config = Config()
        assert config.processing.batch_size == 4
        assert config.video_output.format == "mp4"
        assert config.depth_estimation.model == "midas_small"

    def test_processing_config_defaults(self):
        """Test ProcessingConfig default values."""
        proc = ProcessingConfig()
        assert proc.use_gpu is True
        assert proc.num_workers == 4
        assert proc.mixed_precision is True

    def test_depth_estimation_config_defaults(self):
        """Test DepthEstimationConfig default values."""
        depth = DepthEstimationConfig()
        assert depth.model == "midas_small"
        assert depth.auto_download is True
        assert depth.temporal_consistency is True

    def test_stereo_generation_config_defaults(self):
        """Test StereoGenerationConfig default values."""
        stereo = StereoGenerationConfig()
        assert stereo.format == "side_by_side"
        assert stereo.baseline == 0.05


class TestConfigDataclasses:
    """Tests for configuration dataclasses."""

    def test_video_input_config_formats(self):
        """Test VideoInputConfig supported formats."""
        video_in = VideoInputConfig()
        assert "mp4" in video_in.supported_formats
        assert "avi" in video_in.supported_formats

    def test_video_output_config_defaults(self):
        """Test VideoOutputConfig defaults."""
        video_out = VideoOutputConfig()
        assert video_out.codec == "libx264"
        assert video_out.crf == 23
