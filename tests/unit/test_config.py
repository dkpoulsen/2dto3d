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
    ProgressTrackingConfig,
    RateLimitConfig,
    WebApiConfig,
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
        assert video_out.codec == "libx264"
        assert video_out.crf == 23


class TestProgressTrackingConfig:
    """Tests for progress tracking configuration."""

    def test_progress_tracking_config_defaults(self):
        """Test ProgressTrackingConfig default values."""
        progress = ProgressTrackingConfig()
        assert progress.enabled is True
        assert progress.show_speed is True
        assert progress.show_eta is True
        assert progress.show_elapsed is True
        assert progress.show_percent is True
        assert progress.show_overall is True
        assert progress.refresh_rate == 0.1
        assert progress.transient is False

    def test_progress_tracking_config_disabled(self):
        """Test ProgressTrackingConfig disabled state."""
        progress = ProgressTrackingConfig(enabled=False)
        assert progress.enabled is False

    def test_progress_tracking_config_custom_values(self):
        """Test ProgressTrackingConfig with custom values."""
        progress = ProgressTrackingConfig(
            enabled=True,
            show_speed=False,
            show_eta=False,
            show_elapsed=False,
            show_percent=False,
            show_overall=False,
            refresh_rate=0.5,
            transient=True,
        )
        assert progress.show_speed is False
        assert progress.show_eta is False
        assert progress.show_elapsed is False
        assert progress.show_percent is False
        assert progress.show_overall is False
        assert progress.refresh_rate == 0.5
        assert isinstance(config.progress, ProgressTrackingConfig)


class TestRateLimitConfig:
    """Tests for rate limiting configuration."""

    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values."""
        rate_limit = RateLimitConfig()
        assert rate_limit.enabled is True
        assert rate_limit.requests_per_minute == 60
        assert rate_limit.requests_per_hour == 1000
        assert rate_limit.upload_requests_per_minute == 10
        assert rate_limit.storage_uri == "memory://"
        assert rate_limit.whitelist_ips == []

    def test_rate_limit_config_disabled(self):
        """Test RateLimitConfig disabled state."""
        rate_limit = RateLimitConfig(enabled=False)
        assert rate_limit.enabled is False

    def test_rate_limit_config_custom_values(self):
        """Test RateLimitConfig with custom values."""
        rate_limit = RateLimitConfig(
            enabled=True,
            requests_per_minute=120,
            requests_per_hour=5000,
            upload_requests_per_minute=20,
            storage_uri="redis://localhost:6379",
            whitelist_ips=["127.0.0.1", "10.0.0.1"],
        )
        assert rate_limit.requests_per_minute == 120
        assert rate_limit.requests_per_hour == 5000
        assert rate_limit.upload_requests_per_minute == 20
        assert rate_limit.storage_uri == "redis://localhost:6379"
        assert rate_limit.whitelist_ips == ["127.0.0.1", "10.0.0.1"]

    def test_rate_limit_config_with_redis_storage(self):
        """Test RateLimitConfig with Redis storage URI."""
        rate_limit = RateLimitConfig(storage_uri="redis://redis-server:6379/0")
        assert "redis" in rate_limit.storage_uri

    def test_rate_limit_config_with_whitelist(self):
        """Test RateLimitConfig with IP whitelist."""
        rate_limit = RateLimitConfig(
            whitelist_ips=["192.168.1.0/24", "10.0.0.1"]
        )
        assert len(rate_limit.whitelist_ips) == 2


class TestWebApiConfig:
    """Tests for Web API configuration."""

    def test_web_api_config_defaults(self):
        """Test WebApiConfig default values."""
        web_api = WebApiConfig()
        assert web_api.enabled is False
        assert web_api.host == "0.0.0.0"
        assert web_api.port == 8000
        assert web_api.prefix == "/api/v1"
        assert web_api.max_upload_size == 500
        assert web_api.upload_dir == "uploads"

    def test_web_api_config_has_rate_limit(self):
        """Test that WebApiConfig includes rate_limit field."""
        web_api = WebApiConfig()
        assert hasattr(web_api, "rate_limit")
        assert isinstance(web_api.rate_limit, RateLimitConfig)

    def test_web_api_config_custom_values(self):
        """Test WebApiConfig with custom values."""
        web_api = WebApiConfig(
            enabled=True,
            host="127.0.0.1",
            port=9000,
            prefix="/api/v2",
            max_upload_size=1000,
            upload_dir="/tmp/uploads",
        )
        assert web_api.enabled is True
        assert web_api.host == "127.0.0.1"
        assert web_api.port == 9000
        assert web_api.prefix == "/api/v2"
        assert web_api.max_upload_size == 1000
        assert web_api.upload_dir == "/tmp/uploads"

    def test_web_api_config_with_custom_rate_limit(self):
        """Test WebApiConfig with custom rate limit settings."""
        rate_limit = RateLimitConfig(
            enabled=True,
            requests_per_minute=30,
        )
        web_api = WebApiConfig(
            enabled=True,
            rate_limit=rate_limit,
        )
        assert web_api.rate_limit.requests_per_minute == 30

    def test_web_api_config_cors_origins_default(self):
        """Test WebApiConfig CORS origins default."""
        web_api = WebApiConfig()
        assert "http://localhost:3000" in web_api.cors_origins

    def test_config_has_web_api_field(self):
        """Test that Config includes web_api field."""
        config = Config()
        assert hasattr(config, "web_api")
        assert isinstance(config.web_api, WebApiConfig)
