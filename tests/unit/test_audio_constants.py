"""Unit tests for audio constants and utility functions."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from video2d3d.audio.constants import (
    CODEC_EXTENSIONS,
    DEFAULT_AUDIO_CODEC,
    DEFAULT_AUDIO_EXTENSION,
    ERROR_MESSAGE_MAX_LENGTH,
    FFMPEG_EXTRACT_TIMEOUT,
    FFMPEG_PROCESS_TIMEOUT,
    FFMPEG_SPATIAL_TIMEOUT,
    FFPROBE_TIMEOUT,
    check_ffmpeg_available,
    get_extension_for_codec,
    truncate_error_message,
)


class TestConstants:
    """Tests for audio module constants."""

    def test_timeout_values_are_positive(self) -> None:
        """Test that all timeout constants are positive."""
        assert FFPROBE_TIMEOUT > 0
        assert FFMPEG_EXTRACT_TIMEOUT > 0
        assert FFMPEG_PROCESS_TIMEOUT > 0
        assert FFMPEG_SPATIAL_TIMEOUT > 0

    def test_timeout_hierarchy(self) -> None:
        """Test that timeout values make sense (spatial > process > extract)."""
        assert FFMPEG_SPATIAL_TIMEOUT >= FFMPEG_PROCESS_TIMEOUT
        assert FFMPEG_PROCESS_TIMEOUT >= FFMPEG_EXTRACT_TIMEOUT

    def test_error_message_max_length(self) -> None:
        """Test error message max length is reasonable."""
        assert ERROR_MESSAGE_MAX_LENGTH > 0
        assert ERROR_MESSAGE_MAX_LENGTH <= 10000  # Reasonable upper bound

    def test_codec_extensions_mapping(self) -> None:
        """Test codec to extension mapping contains expected entries."""
        assert "aac" in CODEC_EXTENSIONS
        assert "opus" in CODEC_EXTENSIONS
        assert "mp3" in CODEC_EXTENSIONS
        assert "flac" in CODEC_EXTENSIONS
        assert CODEC_EXTENSIONS["aac"] == "m4a"
        assert CODEC_EXTENSIONS["flac"] == "flac"
        assert CODEC_EXTENSIONS["opus"] == "opus"

    def test_default_values(self) -> None:
        """Test default codec and extension values."""
        assert DEFAULT_AUDIO_CODEC == "aac"
        assert DEFAULT_AUDIO_EXTENSION == "m4a"


class TestCheckFfmpegAvailable:
    """Tests for check_ffmpeg_available function."""

    @patch("video2d3d.audio.constants.shutil.which")
    def test_ffmpeg_available(self, mock_which: pytest.Mock) -> None:
        """Test when FFmpeg is available."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        # Should not raise
        check_ffmpeg_available()

    @patch("video2d3d.audio.constants.shutil.which")
    def test_ffmpeg_not_available(self, mock_which: pytest.Mock) -> None:
        """Test when FFmpeg is not available."""
        mock_which.return_value = None
        with pytest.raises(RuntimeError, match="FFmpeg not found"):
            check_ffmpeg_available()


class TestGetExtensionForCodec:
    """Tests for get_extension_for_codec function."""

    def test_known_codec(self) -> None:
        """Test extension for known codecs."""
        assert get_extension_for_codec("aac") == "m4a"
        assert get_extension_for_codec("opus") == "opus"
        assert get_extension_for_codec("mp3") == "mp3"
        assert get_extension_for_codec("flac") == "flac"
        assert get_extension_for_codec("ac3") == "ac3"

    def test_unknown_codec_returns_default(self) -> None:
        """Test extension for unknown codec returns default."""
        assert get_extension_for_codec("unknown_codec") == DEFAULT_AUDIO_EXTENSION
        assert get_extension_for_codec("") == DEFAULT_AUDIO_EXTENSION
        assert get_extension_for_codec("invalid") == DEFAULT_AUDIO_EXTENSION

    def test_returns_string(self) -> None:
        """Test that return type is string."""
        result = get_extension_for_codec("aac")
        assert isinstance(result, str)


class TestTruncateErrorMessage:
    """Tests for truncate_error_message function."""

    def test_none_message(self) -> None:
        """Test with None message."""
        assert truncate_error_message(None) == "Unknown error"

    def test_short_message_unchanged(self) -> None:
        """Test short message is unchanged."""
        message = "Short error"
        assert truncate_error_message(message) == message

    def test_long_message_truncated(self) -> None:
        """Test long message is truncated."""
        message = "A" * 1000
        result = truncate_error_message(message, max_length=100)
        assert len(result) == 100
        assert result == "A" * 100

    def test_exact_length_message(self) -> None:
        """Test message at exact max length."""
        message = "A" * 100
        result = truncate_error_message(message, max_length=100)
        assert len(result) == 100
        assert result == message

    def test_default_max_length(self) -> None:
        """Test default max length is used."""
        message = "B" * 1000
        result = truncate_error_message(message)
        assert len(result) == ERROR_MESSAGE_MAX_LENGTH

    def test_custom_max_length(self) -> None:
        """Test custom max length."""
        message = "C" * 1000
        result = truncate_error_message(message, max_length=50)
        assert len(result) == 50

    def test_empty_string(self) -> None:
        """Test empty string returns empty string."""
        assert truncate_error_message("") == ""

    def test_returns_string(self) -> None:
        """Test that return type is string."""
        assert isinstance(truncate_error_message("test"), str)
        assert isinstance(truncate_error_message(None), str)
