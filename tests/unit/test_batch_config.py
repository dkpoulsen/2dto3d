"""Unit tests for batch video processing configuration.

Tests cover:
- FileDiscoveryConfig dataclass
- FolderWatcherConfig dataclass
- BatchQueueConfig dataclass
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch
import warnings

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.config import (
    BatchQueueConfig,
    FileDiscoveryConfig,
    FolderWatcherConfig,
)
from video2d3d.batch.models import JobPriority


@pytest.fixture
def mock_logger() -> Generator[None, None, None]:
    """Mock the logger to avoid actual logging."""
    with patch("video2d3d.batch.config.get_logger"):
        yield


class TestFileDiscoveryConfig:
    """Tests for FileDiscoveryConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = FileDiscoveryConfig()
        assert config.patterns == ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"]
        assert config.exclude_patterns == []
        assert config.recursive is True
        assert config.case_sensitive is False
        assert config.max_depth == 10
        assert config.follow_symlinks is False
        assert config.min_file_size_mb == 0.0
        assert config.max_file_size_mb == 0.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = FileDiscoveryConfig(
            patterns=["*.mp4", "*.mov"],
            exclude_patterns=["*_temp*"],
            recursive=False,
            case_sensitive=True,
            max_depth=5,
            follow_symlinks=True,
            min_file_size_mb=1.0,
            max_file_size_mb=1000.0,
        )
        assert config.patterns == ["*.mp4", "*.mov"]
        assert config.exclude_patterns == ["*_temp*"]
        assert config.recursive is False
        assert config.case_sensitive is True
        assert config.max_depth == 5
        assert config.follow_symlinks is True
        assert config.min_file_size_mb == 1.0
        assert config.max_file_size_mb == 1000.0

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        config = FileDiscoveryConfig(
            patterns=["*.mp4"],
            exclude_patterns=["*.tmp"],
            recursive=True,
        )
        data = config.to_dict()
        assert data["patterns"] == ["*.mp4"]
        assert data["exclude_patterns"] == ["*.tmp"]
        assert data["recursive"] is True
        assert "case_sensitive" in data
        assert "max_depth" in data


class TestFolderWatcherConfig:
    """Tests for FolderWatcherConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = FolderWatcherConfig()
        assert config.enabled is False
        assert config.watch_paths == []
        assert config.poll_interval_seconds == 2.0
        assert config.use_inotify is True
        assert config.stable_time_seconds == 5.0
        assert config.process_existing is True
        assert config.recursive is True

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = FolderWatcherConfig(
            enabled=True,
            watch_paths=[Path("/watch/dir"), "/another/dir"],
            poll_interval_seconds=5.0,
            use_inotify=False,
            stable_time_seconds=10.0,
            process_existing=False,
            recursive=False,
        )
        assert config.enabled is True
        assert len(config.watch_paths) == 2
        assert config.poll_interval_seconds == 5.0
        assert config.use_inotify is False
        assert config.stable_time_seconds == 10.0
        assert config.process_existing is False
        assert config.recursive is False

    def test_post_init_converts_string_paths(self) -> None:
        """Test __post_init__ converts string paths to Path."""
        config = FolderWatcherConfig(
            watch_paths=["/path/to/dir", Path("/another/path")],
        )
        assert all(isinstance(p, Path) for p in config.watch_paths)

    def test_to_dict(self) -> None:
        """Test to_dict serialization."""
        config = FolderWatcherConfig(
            enabled=True,
            watch_paths=[Path("/watch/dir")],
            poll_interval_seconds=3.0,
        )
        data = config.to_dict()
        assert data["enabled"] is True
        assert data["watch_paths"] == ["/watch/dir"]
        assert data["poll_interval_seconds"] == 3.0


class TestBatchQueueConfig:
    """Tests for BatchQueueConfig dataclass."""

    def test_default_values(self, mock_logger: None) -> None:
        """Test default values are set correctly."""
        config = BatchQueueConfig()
        assert config.max_concurrent_jobs == 1
        assert config.default_priority == JobPriority.NORMAL
        assert config.auto_start is True
        assert config.retry_failed is True
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 5.0
        assert config.job_timeout_seconds == 3600.0
        assert config.output_directory is None
        assert config.output_naming_pattern == "{name}_3d{ext}"
        assert config.preserve_directory_structure is False
        assert config.skip_existing is True
        assert config.save_state is True
        assert config.state_file is None
        assert config.state_save_interval == 30.0
        assert isinstance(config.file_discovery, FileDiscoveryConfig)
        assert isinstance(config.folder_watcher, FolderWatcherConfig)
        assert config.progress_update_interval == 1.0
        assert config.error_callback_url is None
        assert config.completion_callback_url is None

    def test_custom_values(self, mock_logger: None) -> None:
        """Test custom values are set correctly."""
        config = BatchQueueConfig(
            max_concurrent_jobs=4,
            default_priority=JobPriority.HIGH,
            auto_start=False,
            retry_failed=False,
            max_retries=5,
            retry_delay_seconds=10.0,
            job_timeout_seconds=1800.0,
            output_directory=Path("/output"),
            output_naming_pattern="{name}_converted{ext}",
            skip_existing=False,
            save_state=False,
        )
        assert config.max_concurrent_jobs == 4
        assert config.default_priority == JobPriority.HIGH
        assert config.auto_start is False
        assert config.retry_failed is False
        assert config.max_retries == 5
        assert config.retry_delay_seconds == 10.0
        assert config.job_timeout_seconds == 1800.0
        assert config.output_directory == Path("/output")
        assert config.output_naming_pattern == "{name}_converted{ext}"
        assert config.skip_existing is False
        assert config.save_state is False

    def test_post_init_converts_string_paths(self, mock_logger: None) -> None:
        """Test __post_init__ converts string paths to Path."""
        config = BatchQueueConfig(
            output_directory="/output/dir",
            state_file="/state/file.json",
        )
        assert isinstance(config.output_directory, Path)
        assert isinstance(config.state_file, Path)

    def test_invalid_max_concurrent_jobs_zero(self, mock_logger: None) -> None:
        """Test ValueError raised for zero max_concurrent_jobs."""
        with pytest.raises(ValueError, match="max_concurrent_jobs"):
            BatchQueueConfig(max_concurrent_jobs=0)

    def test_invalid_max_concurrent_jobs_negative(self, mock_logger: None) -> None:
        """Test ValueError raised for negative max_concurrent_jobs."""
        with pytest.raises(ValueError, match="max_concurrent_jobs"):
            BatchQueueConfig(max_concurrent_jobs=-1)

    def test_high_concurrent_jobs_warning(self, mock_logger: None) -> None:
        """Test warning issued for high max_concurrent_jobs."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            config = BatchQueueConfig(max_concurrent_jobs=20)
            assert len(w) == 1
            assert "max_concurrent_jobs" in str(w[0].message).lower()
            assert config.max_concurrent_jobs == 20  # Value still set

    def test_get_output_path_with_output_directory(self, mock_logger: None) -> None:
        """Test get_output_path with configured output directory."""
        config = BatchQueueConfig(
            output_directory=Path("/output"),
        )
        input_path = Path("/input/videos/test.mp4")
        output_path = config.get_output_path(input_path)
        assert output_path == Path("/output/test_3d.mp4")

    def test_get_output_path_without_output_directory(self, mock_logger: None) -> None:
        """Test get_output_path without configured output directory."""
        config = BatchQueueConfig()
        input_path = Path("/input/videos/test.mp4")
        output_path = config.get_output_path(input_path)
        assert output_path == Path("/input/videos/test_3d.mp4")

    def test_get_output_path_with_base_override(self, mock_logger: None) -> None:
        """Test get_output_path with base_output_dir override."""
        config = BatchQueueConfig(
            output_directory=Path("/default/output"),
        )
        input_path = Path("/input/test.mp4")
        output_path = config.get_output_path(input_path, base_output_dir=Path("/override"))
        assert output_path == Path("/override/test_3d.mp4")

    def test_get_output_path_custom_naming_pattern(self, mock_logger: None) -> None:
        """Test get_output_path with custom naming pattern."""
        config = BatchQueueConfig(
            output_directory=Path("/output"),
            output_naming_pattern="{name}_converted{ext}",
        )
        input_path = Path("/input/test.mp4")
        output_path = config.get_output_path(input_path)
        assert output_path == Path("/output/test_converted.mp4")

    def test_get_output_path_preserve_directory_structure(
        self, mock_logger: None, tmp_path: Path
    ) -> None:
        """Test get_output_path with preserve_directory_structure."""
        # Create a structure where input is inside output_directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = BatchQueueConfig(
            output_directory=output_dir,
            preserve_directory_structure=True,
        )

        # Input file in a subdirectory relative to output dir
        input_path = output_dir / "subdir" / "test.mp4"
        output_path = config.get_output_path(input_path)
        # Should preserve the subdirectory structure
        assert "subdir" in str(output_path)

    def test_to_dict(self, mock_logger: None) -> None:
        """Test to_dict serialization."""
        config = BatchQueueConfig(
            max_concurrent_jobs=4,
            default_priority=JobPriority.HIGH,
            output_directory=Path("/output"),
        )
        data = config.to_dict()
        assert data["max_concurrent_jobs"] == 4
        assert data["default_priority"] == JobPriority.HIGH.value
        assert data["output_directory"] == "/output"
        assert "file_discovery" in data
        assert "folder_watcher" in data

    def test_to_dict_none_paths(self, mock_logger: None) -> None:
        """Test to_dict with None paths."""
        config = BatchQueueConfig()
        data = config.to_dict()
        assert data["output_directory"] is None
        assert data["state_file"] is None

    def test_nested_config_serialization(self, mock_logger: None) -> None:
        """Test nested configs are properly serialized."""
        config = BatchQueueConfig(
            file_discovery=FileDiscoveryConfig(
                patterns=["*.mp4"],
                recursive=False,
            ),
            folder_watcher=FolderWatcherConfig(
                enabled=True,
                stable_time_seconds=10.0,
            ),
        )
        data = config.to_dict()
        assert data["file_discovery"]["patterns"] == ["*.mp4"]
        assert data["file_discovery"]["recursive"] is False
        assert data["folder_watcher"]["enabled"] is True
        assert data["folder_watcher"]["stable_time_seconds"] == 10.0


class TestConfigIntegration:
    """Integration tests for config classes."""

    def test_full_config_roundtrip(self, mock_logger: None, tmp_path: Path) -> None:
        """Test complete config can be created and used."""
        output_dir = tmp_path / "output"
        state_file = tmp_path / "state.json"

        config = BatchQueueConfig(
            max_concurrent_jobs=2,
            default_priority=JobPriority.HIGH,
            auto_start=False,
            retry_failed=True,
            max_retries=5,
            output_directory=output_dir,
            output_naming_pattern="{name}_3d{ext}",
            skip_existing=True,
            save_state=True,
            state_file=state_file,
            file_discovery=FileDiscoveryConfig(
                patterns=["*.mp4", "*.avi"],
                recursive=True,
            ),
            folder_watcher=FolderWatcherConfig(
                enabled=True,
                watch_paths=[tmp_path],
            ),
        )

        # Test that the config works as expected
        assert config.max_concurrent_jobs == 2
        assert config.default_priority == JobPriority.HIGH

        # Test output path generation
        input_path = tmp_path / "video.mp4"
        output_path = config.get_output_path(input_path)
        assert output_path.parent == output_dir
        assert output_path.name == "video_3d.mp4"

        # Test serialization
        data = config.to_dict()
        assert data is not None
