"""Unit tests for batch file discovery.

Tests cover:
- FileDiscovery class
- Pattern matching functionality
- Recursive directory discovery
- File filtering
- Convenience functions
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.config import FileDiscoveryConfig
from video2d3d.batch.exceptions import FileDiscoveryError
from video2d3d.batch.file_discovery import FileDiscovery, discover_videos


@pytest.fixture
def mock_logger() -> Generator[None, None, None]:
    """Mock the logger to avoid actual logging."""
    with patch("video2d3d.batch.file_discovery.get_logger"):
        yield


@pytest.fixture
def sample_video_dir(tmp_path: Path) -> Path:
    """Create a sample directory structure with video files."""
    # Create directories
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    sub_dir = videos_dir / "subfolder"
    sub_dir.mkdir()

    # Create video files
    (videos_dir / "video1.mp4").touch()
    (videos_dir / "video2.avi").touch()
    (videos_dir / "video3.mov").touch()
    (videos_dir / "document.txt").touch()

    # Create files in subdirectory
    (sub_dir / "video4.mp4").touch()
    (sub_dir / "video5.mkv").touch()
    (sub_dir / "temp.tmp").touch()

    return videos_dir


class TestFileDiscovery:
    """Tests for FileDiscovery class."""

    def test_init_default_config(self, mock_logger: None) -> None:
        """Test initialization with default config."""
        discovery = FileDiscovery()
        assert discovery.config is not None
        assert "*.mp4" in discovery.config.patterns

    def test_init_custom_config(self, mock_logger: None) -> None:
        """Test initialization with custom config."""
        config = FileDiscoveryConfig(patterns=["*.mkv"])
        discovery = FileDiscovery(config)
        assert discovery.config.patterns == ["*.mkv"]

    def test_discover_single_file(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovering a single file."""
        discovery = FileDiscovery()
        file_path = sample_video_dir / "video1.mp4"
        results = list(discovery.discover(file_path))
        assert len(results) == 1
        assert results[0] == file_path

    def test_discover_directory(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovering files in a directory."""
        config = FileDiscoveryConfig(recursive=False)
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        # Should find video1.mp4, video2.avi, video3.mov (3 video files)
        assert len(results) == 3
        filenames = [f.name for f in results]
        assert "video1.mp4" in filenames
        assert "video2.avi" in filenames
        assert "video3.mov" in filenames
        assert "document.txt" not in filenames

    def test_discover_recursive(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test recursive directory discovery."""
        config = FileDiscoveryConfig(recursive=True)
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        # Should find all 5 video files
        assert len(results) == 5
        filenames = [f.name for f in results]
        assert "video4.mp4" in filenames
        assert "video5.mkv" in filenames

    def test_discover_non_recursive(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test non-recursive directory discovery."""
        config = FileDiscoveryConfig(recursive=False)
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        # Should only find files in root directory
        filenames = [f.name for f in results]
        assert "video4.mp4" not in filenames

    def test_discover_custom_patterns(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery with custom patterns."""
        config = FileDiscoveryConfig(patterns=["*.mp4"])
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        # Should find video1.mp4 and video4.mp4
        assert len(results) == 2
        for result in results:
            assert result.suffix == ".mp4"

    def test_discover_exclude_patterns(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery with exclude patterns."""
        config = FileDiscoveryConfig(
            patterns=["*.mp4", "*.avi"],
            exclude_patterns=["*2*"],  # Exclude files with '2' in name
        )
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        filenames = [f.name for f in results]
        assert "video2.avi" not in filenames
        assert "video1.mp4" in filenames

    def test_discover_max_depth(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery with max depth limit."""
        config = FileDiscoveryConfig(recursive=True, max_depth=0)
        discovery = FileDiscovery(config)
        results = list(discovery.discover(sample_video_dir))
        # max_depth=0 means only current directory
        filenames = [f.name for f in results]
        assert "video4.mp4" not in filenames

    def test_discover_nonexistent_path(self, mock_logger: None) -> None:
        """Test discovery handles nonexistent paths gracefully."""
        discovery = FileDiscovery()
        results = list(discovery.discover(Path("/nonexistent/path")))
        assert len(results) == 0

    def test_discover_string_path(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery accepts string paths."""
        discovery = FileDiscovery()
        results = list(discovery.discover(str(sample_video_dir / "video1.mp4")))
        assert len(results) == 1

    def test_discover_multiple_paths(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery with multiple paths."""
        discovery = FileDiscovery()
        file1 = sample_video_dir / "video1.mp4"
        file2 = sample_video_dir / "video2.avi"
        results = list(discovery.discover([file1, file2]))
        assert len(results) == 2

    def test_matches_patterns_case_insensitive(self, mock_logger: None, tmp_path: Path) -> None:
        """Test pattern matching is case insensitive by default."""
        config = FileDiscoveryConfig(
            patterns=["*.MP4"],
            case_sensitive=False,
        )
        discovery = FileDiscovery(config)

        # Create file with lowercase extension
        test_file = tmp_path / "video.mp4"
        test_file.touch()

        results = list(discovery.discover(test_file))
        assert len(results) == 1

    def test_matches_patterns_case_sensitive(self, mock_logger: None, tmp_path: Path) -> None:
        """Test pattern matching is case sensitive when configured."""
        config = FileDiscoveryConfig(
            patterns=["*.MP4"],
            case_sensitive=True,
        )
        discovery = FileDiscovery(config)

        # Create file with lowercase extension
        test_file = tmp_path / "video.mp4"
        test_file.touch()

        results = list(discovery.discover(test_file))
        assert len(results) == 0

    def test_file_size_filter_min(self, mock_logger: None, tmp_path: Path) -> None:
        """Test file size filter with minimum size."""
        config = FileDiscoveryConfig(
            patterns=["*.mp4"],
            min_file_size_mb=0.001,  # 1KB minimum
        )
        discovery = FileDiscovery(config)

        # Create small file
        small_file = tmp_path / "small.mp4"
        small_file.touch()

        # Create larger file
        large_file = tmp_path / "large.mp4"
        large_file.write_bytes(b"x" * 2000)  # 2KB

        results = list(discovery.discover(tmp_path))
        filenames = [f.name for f in results]
        assert "large.mp4" in filenames
        assert "small.mp4" not in filenames

    def test_file_size_filter_max(self, mock_logger: None, tmp_path: Path) -> None:
        """Test file size filter with maximum size."""
        config = FileDiscoveryConfig(
            patterns=["*.mp4"],
            max_file_size_mb=0.001,  # 1KB maximum
        )
        discovery = FileDiscovery(config)

        # Create small file
        small_file = tmp_path / "small.mp4"
        small_file.touch()

        # Create larger file
        large_file = tmp_path / "large.mp4"
        large_file.write_bytes(b"x" * 2000)  # 2KB

        results = list(discovery.discover(tmp_path))
        filenames = [f.name for f in results]
        assert "small.mp4" in filenames
        assert "large.mp4" not in filenames


class TestFileDiscoveryWildcard:
    """Tests for wildcard pattern discovery."""

    def test_discover_by_wildcard_simple(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test simple wildcard pattern."""
        discovery = FileDiscovery()
        results = list(discovery.discover_by_wildcard("*.mp4", sample_video_dir))
        assert len(results) >= 1
        for result in results:
            assert result.suffix == ".mp4"

    def test_discover_by_wildcard_with_prefix(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test wildcard pattern with prefix."""
        discovery = FileDiscovery()
        results = list(discovery.discover_by_wildcard("video*.mp4", sample_video_dir))
        for result in results:
            assert result.name.startswith("video")
            assert result.suffix == ".mp4"

    def test_discover_by_wildcard_absolute_path(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test wildcard with absolute path."""
        discovery = FileDiscovery()
        pattern = str(sample_video_dir / "*.mp4")
        results = list(discovery.discover_by_wildcard(pattern))
        assert len(results) >= 1


class TestFileDiscoveryFromList:
    """Tests for file discovery from list."""

    def test_discover_from_list(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discovery from file list."""
        discovery = FileDiscovery()
        files = [
            sample_video_dir / "video1.mp4",
            sample_video_dir / "video2.avi",
        ]
        results = list(discovery.discover_from_list(files))
        assert len(results) == 2

    def test_discover_from_list_with_invalid(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test discovery from list handles invalid files."""
        discovery = FileDiscovery()
        files = [
            sample_video_dir / "video1.mp4",
            sample_video_dir / "nonexistent.mp4",
        ]
        results = list(discovery.discover_from_list(files, validate=True))
        assert len(results) == 1

    def test_discover_from_list_without_validation(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test discovery from list without validation."""
        discovery = FileDiscovery()
        files = [
            sample_video_dir / "video1.mp4",
            sample_video_dir / "nonexistent.mp4",
        ]
        results = list(discovery.discover_from_list(files, validate=False))
        assert len(results) == 2

    def test_discover_from_list_string_paths(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test discovery from list with string paths."""
        discovery = FileDiscovery()
        files = [
            str(sample_video_dir / "video1.mp4"),
        ]
        results = list(discovery.discover_from_list(files))
        assert len(results) == 1


class TestFileDiscoveryFromTextFile:
    """Tests for file discovery from text file."""

    def test_discover_from_text_file(
        self, mock_logger: None, sample_video_dir: Path, tmp_path: Path
    ) -> None:
        """Test discovery from text file."""
        # Create list file
        list_file = tmp_path / "file_list.txt"
        list_file.write_text(
            f"{sample_video_dir / 'video1.mp4'}\n{sample_video_dir / 'video2.avi'}\n"
        )

        discovery = FileDiscovery()
        results = list(discovery.discover_from_text_file(list_file))
        assert len(results) == 2

    def test_discover_from_text_file_with_comments(
        self, mock_logger: None, sample_video_dir: Path, tmp_path: Path
    ) -> None:
        """Test discovery from text file ignores comments and blank lines."""
        list_file = tmp_path / "file_list.txt"
        list_file.write_text(f"# This is a comment\n\n{sample_video_dir / 'video1.mp4'}\n\n")

        discovery = FileDiscovery()
        results = list(discovery.discover_from_text_file(list_file))
        assert len(results) == 1

    def test_discover_from_text_file_with_base_dir(
        self, mock_logger: None, sample_video_dir: Path, tmp_path: Path
    ) -> None:
        """Test discovery from text file with base directory."""
        list_file = tmp_path / "file_list.txt"
        list_file.write_text("video1.mp4\nvideo2.avi\n")

        discovery = FileDiscovery()
        results = list(discovery.discover_from_text_file(list_file, base_dir=sample_video_dir))
        assert len(results) == 2

    def test_discover_from_text_file_not_found(self, mock_logger: None) -> None:
        """Test discovery from nonexistent text file raises error."""
        discovery = FileDiscovery()
        with pytest.raises(FileDiscoveryError, match="not found"):
            list(discovery.discover_from_text_file(Path("/nonexistent/list.txt")))


class TestFileDiscoveryGrouping:
    """Tests for file grouping functionality."""

    def test_group_by_directory(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test grouping files by directory."""
        discovery = FileDiscovery()
        files = list(discovery.discover(sample_video_dir))
        groups = discovery.group_by_directory(files)

        # Should have at least two directories
        assert len(groups) >= 1
        # Check that files are correctly grouped
        for directory, dir_files in groups.items():
            for f in dir_files:
                assert f.parent == directory


class TestDiscoverVideosConvenienceFunction:
    """Tests for the discover_videos convenience function."""

    def test_discover_videos_default(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discover_videos with default settings."""
        results = discover_videos(sample_video_dir)
        assert len(results) == 5
        # All results should be video files
        video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        for result in results:
            assert result.suffix in video_extensions

    def test_discover_videos_custom_patterns(
        self, mock_logger: None, sample_video_dir: Path
    ) -> None:
        """Test discover_videos with custom patterns."""
        results = discover_videos(
            sample_video_dir,
            patterns=["*.mp4"],
            recursive=True,
        )
        assert len(results) == 2
        for result in results:
            assert result.suffix == ".mp4"

    def test_discover_videos_non_recursive(self, mock_logger: None, sample_video_dir: Path) -> None:
        """Test discover_videos without recursion."""
        results = discover_videos(
            sample_video_dir,
            recursive=False,
        )
        # Should only find 3 files in root directory
        assert len(results) == 3


class TestFileDiscoveryErrorHandling:
    """Tests for error handling in file discovery."""

    def test_permission_error_handling(self, mock_logger: None, tmp_path: Path) -> None:
        """Test that permission errors are handled gracefully."""
        discovery = FileDiscovery()

        # Mock os.walk to raise PermissionError
        with patch("os.walk", side_effect=PermissionError("Access denied")):
            with pytest.raises(FileDiscoveryError, match="Permission denied"):
                list(discovery.discover(tmp_path))

    def test_os_error_handling(self, mock_logger: None, tmp_path: Path) -> None:
        """Test that OS errors are handled gracefully."""
        discovery = FileDiscovery()

        # Mock os.walk to raise OSError
        with patch("os.walk", side_effect=OSError("IO Error")):
            with pytest.raises(FileDiscoveryError, match="Error accessing"):
                list(discovery.discover(tmp_path))
