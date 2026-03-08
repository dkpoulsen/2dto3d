"""Unit tests for web API utilities.

Tests cover:
- MIME type utilities
- File extension validation
- File ID validation (path traversal prevention)
- Filename sanitization
- File finding utilities
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.utils import (
    MIME_TYPES,
    SUPPORTED_VIDEO_EXTENSIONS,
    find_file_by_id,
    get_content_type,
    is_supported_video_extension,
    sanitize_filename,
    validate_file_id,
)


class TestSupportedContentTypes:
    """Tests for content type constants."""

    def test_supported_extensions_not_empty(self) -> None:
        """Test that supported extensions set is not empty."""
        assert len(SUPPORTED_VIDEO_EXTENSIONS) > 0

    def test_common_extensions_supported(self) -> None:
        """Test that common video extensions are supported."""
        assert ".mp4" in SUPPORTED_VIDEO_EXTENSIONS
        assert ".avi" in SUPPORTED_VIDEO_EXTENSIONS
        assert ".mov" in SUPPORTED_VIDEO_EXTENSIONS
        assert ".mkv" in SUPPORTED_VIDEO_EXTENSIONS
        assert ".webm" in SUPPORTED_VIDEO_EXTENSIONS

    def test_mime_types_mapping_exists(self) -> None:
        """Test that MIME types mapping exists for supported extensions."""
        for ext in SUPPORTED_VIDEO_EXTENSIONS:
            assert ext in MIME_TYPES, f"Missing MIME type for {ext}"

    def test_mime_types_are_video(self) -> None:
        """Test that MIME types are video types."""
        for _ext, mime in MIME_TYPES.items():
            assert mime.startswith("video/") or mime == "application/octet-stream"


class TestGetContentType:
    """Tests for get_content_type function."""

    def test_mp4_content_type(self) -> None:
        """Test MP4 content type."""
        assert get_content_type(".mp4") == "video/mp4"

    def test_avi_content_type(self) -> None:
        """Test AVI content type."""
        assert get_content_type(".avi") == "video/x-msvideo"

    def test_mov_content_type(self) -> None:
        """Test MOV content type."""
        assert get_content_type(".mov") == "video/quicktime"

    def test_mkv_content_type(self) -> None:
        """Test MKV content type."""
        assert get_content_type(".mkv") == "video/x-matroska"

    def test_webm_content_type(self) -> None:
        """Test WebM content type."""
        assert get_content_type(".webm") == "video/webm"

    def test_unknown_extension(self) -> None:
        """Test unknown extension returns octet-stream."""
        assert get_content_type(".unknown") == "application/octet-stream"

    def test_case_sensitive(self) -> None:
        """Test that extension matching is case-sensitive (lowercase expected)."""
        # Should return default for uppercase
        assert get_content_type(".MP4") == "application/octet-stream"


class TestIsSupportedVideoExtension:
    """Tests for is_supported_video_extension function."""

    def test_supported_extension_with_dot(self) -> None:
        """Test supported extension with leading dot."""
        assert is_supported_video_extension(".mp4") is True

    def test_supported_extension_without_dot(self) -> None:
        """Test supported extension without leading dot."""
        assert is_supported_video_extension("mp4") is True

    def test_unsupported_extension(self) -> None:
        """Test unsupported extension."""
        assert is_supported_video_extension(".txt") is False

    def test_uppercase_extension(self) -> None:
        """Test uppercase extension (should be lowercased)."""
        assert is_supported_video_extension(".MP4") is True

    def test_empty_string(self) -> None:
        """Test empty string."""
        assert is_supported_video_extension("") is False


class TestValidateFileId:
    """Tests for validate_file_id function (path traversal prevention)."""

    def test_valid_uuid(self) -> None:
        """Test valid UUID format."""
        assert validate_file_id("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self) -> None:
        """Test valid UUID format (uppercase)."""
        assert validate_file_id("550E8400-E29B-41D4-A716-446655440000") is True

    def test_valid_alphanumeric(self) -> None:
        """Test valid alphanumeric ID."""
        assert validate_file_id("abc123") is True

    def test_valid_with_underscores(self) -> None:
        """Test valid ID with underscores."""
        assert validate_file_id("my_video_file_123") is True

    def test_valid_with_hyphens(self) -> None:
        """Test valid ID with hyphens."""
        assert validate_file_id("my-video-file-123") is True

    def test_invalid_path_traversal_dotdot(self) -> None:
        """Test path traversal with .. is rejected."""
        assert validate_file_id("../etc/passwd") is False

    def test_invalid_path_traversal_slash(self) -> None:
        """Test path traversal with / is rejected."""
        assert validate_file_id("/etc/passwd") is False

    def test_invalid_path_traversal_backslash(self) -> None:
        """Test path traversal with backslash is rejected."""
        assert validate_file_id("..\\windows\\system32") is False

    def test_invalid_null_byte(self) -> None:
        """Test null byte injection is rejected."""
        assert validate_file_id("file\x00.txt") is False

    def test_invalid_empty_string(self) -> None:
        """Test empty string is rejected."""
        assert validate_file_id("") is False

    def test_invalid_special_chars(self) -> None:
        """Test special characters are rejected."""
        assert validate_file_id("file@name") is False

    def test_invalid_spaces(self) -> None:
        """Test spaces are rejected."""
        assert validate_file_id("file name") is False


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename(self) -> None:
        """Test simple filename is unchanged."""
        assert sanitize_filename("video.mp4") == "video.mp4"

    def test_removes_forward_slash(self) -> None:
        """Test forward slash is removed."""
        assert "/" not in sanitize_filename("path/to/video.mp4")

    def test_removes_backslash(self) -> None:
        """Test backslash is removed."""
        assert "\\" not in sanitize_filename("path\\to\\video.mp4")

    def test_removes_null_byte(self) -> None:
        """Test null byte is removed."""
        assert "\x00" not in sanitize_filename("video\x00.mp4")

    def test_removes_dangerous_chars(self) -> None:
        """Test dangerous characters are removed."""
        dangerous = '<>:"|?*'
        result = sanitize_filename(f"video{dangerous}.mp4")
        for char in dangerous:
            assert char not in result

    def test_limits_length(self) -> None:
        """Test filename length is limited."""
        long_name = "a" * 300 + ".mp4"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_preserves_extension_in_length_limit(self) -> None:
        """Test extension is preserved when truncating."""
        long_name = "a" * 300 + ".mp4"
        result = sanitize_filename(long_name)
        assert result.endswith(".mp4")

    def test_path_traversal_prevention(self) -> None:
        """Test path traversal attempt is sanitized."""
        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result


class TestFindFileById:
    """Tests for find_file_by_id function."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Generator[Path, None, None]:
        """Create a temporary directory with test files."""
        # Create test files
        (tmp_path / "550e8400-e29b-41d4-a716-446655440000.mp4").touch()
        (tmp_path / "test-video.avi").touch()
        (tmp_path / "550e8400-e29b-41d4-a716-446655440001_3d.mp4").touch()
        (tmp_path / "readme.txt").touch()  # Non-video file
        yield tmp_path

    def test_find_by_exact_id(self, temp_dir: Path) -> None:
        """Test finding file by exact ID match."""
        result = find_file_by_id(temp_dir, "550e8400-e29b-41d4-a716-446655440000")
        assert result is not None
        assert result.name == "550e8400-e29b-41d4-a716-446655440000.mp4"

    def test_find_by_custom_id(self, temp_dir: Path) -> None:
        """Test finding file by custom ID."""
        result = find_file_by_id(temp_dir, "test-video")
        assert result is not None
        assert result.name == "test-video.avi"

    def test_find_by_prefix(self, temp_dir: Path) -> None:
        """Test finding file by ID prefix (for generated output names)."""
        result = find_file_by_id(temp_dir, "550e8400-e29b-41d4-a716-446655440001")
        assert result is not None
        assert result.name == "550e8400-e29b-41d4-a716-446655440001_3d.mp4"

    def test_find_with_extension_filter(self, temp_dir: Path) -> None:
        """Test finding file with extension filter."""
        result = find_file_by_id(
            temp_dir,
            "550e8400-e29b-41d4-a716-446655440000",
            extensions={".mp4"},
        )
        assert result is not None
        assert result.suffix == ".mp4"

    def test_not_found(self, temp_dir: Path) -> None:
        """Test returns None when file not found."""
        result = find_file_by_id(temp_dir, "nonexistent")
        assert result is None

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test returns None for empty directory."""
        result = find_file_by_id(tmp_path, "any-id")
        assert result is None

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test returns None for nonexistent directory."""
        result = find_file_by_id(tmp_path / "nonexistent", "any-id")
        assert result is None

    def test_ignores_directories(self, tmp_path: Path) -> None:
        """Test that subdirectories are ignored."""
        (tmp_path / "subdir").mkdir()
        result = find_file_by_id(tmp_path, "subdir")
        assert result is None

    def test_extension_filter_excludes(self, temp_dir: Path) -> None:
        """Test extension filter excludes non-matching files."""
        # Try to find the txt file with video extensions filter
        result = find_file_by_id(temp_dir, "readme", extensions={".mp4", ".avi"})
        assert result is None
