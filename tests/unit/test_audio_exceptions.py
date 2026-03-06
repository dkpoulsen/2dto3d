"""Unit tests for audio exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from video2d3d.audio.exceptions import (
    AudioChannelLayoutError,
    AudioCodecNotSupportedError,
    AudioExtractionError,
    AudioMixError,
    AudioProcessingError,
    AudioTrackNotFoundError,
    SpatialAudioError,
)


class TestAudioProcessingError:
    """Tests for AudioProcessingError base exception."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = AudioProcessingError("Test error")
        assert "Test error" in str(error)

    def test_error_with_file_path(self) -> None:
        """Test error with file path."""
        error = AudioProcessingError("Test error", file_path=Path("test.mp4"))
        assert "Test error" in str(error)
        assert "test.mp4" in str(error)

    def test_error_with_reason(self) -> None:
        """Test error with reason."""
        error = AudioProcessingError("Test error", reason="Something went wrong")
        assert "Test error" in str(error)
        assert "Something went wrong" in str(error)


class TestAudioExtractionError:
    """Tests for AudioExtractionError."""

    def test_basic_error(self) -> None:
        """Test basic extraction error."""
        error = AudioExtractionError()
        assert "Failed to extract audio" in str(error)

    def test_error_with_track_index(self) -> None:
        """Test error with track index."""
        error = AudioExtractionError(track_index=2)
        assert "track 2" in str(error)

    def test_error_with_reason(self) -> None:
        """Test error with reason."""
        error = AudioExtractionError(reason="Invalid codec")
        assert "Invalid codec" in str(error)


class TestAudioCodecNotSupportedError:
    """Tests for AudioCodecNotSupportedError."""

    def test_basic_error(self) -> None:
        """Test basic codec error."""
        error = AudioCodecNotSupportedError("unknown_codec")
        assert "unknown_codec" in str(error)

    def test_error_with_supported_codecs(self) -> None:
        """Test error with supported codec list."""
        error = AudioCodecNotSupportedError(
            "unknown_codec",
            supported_codecs=["aac", "opus", "mp3"],
        )
        assert "aac" in str(error)
        assert "opus" in str(error)


class TestAudioTrackNotFoundError:
    """Tests for AudioTrackNotFoundError."""

    def test_basic_error(self) -> None:
        """Test basic track not found error."""
        error = AudioTrackNotFoundError(track_index=5)
        assert "track 5" in str(error)

    def test_error_with_available_tracks(self) -> None:
        """Test error with available track count."""
        error = AudioTrackNotFoundError(track_index=5, available_tracks=3)
        assert "Available tracks" in str(error)
        assert "0-2" in str(error)


class TestAudioChannelLayoutError:
    """Tests for AudioChannelLayoutError."""

    def test_basic_error(self) -> None:
        """Test basic layout error."""
        error = AudioChannelLayoutError("invalid_layout")
        assert "invalid_layout" in str(error)

    def test_error_with_reason(self) -> None:
        """Test error with reason."""
        error = AudioChannelLayoutError("9.1", reason="Not supported")
        assert "9.1" in str(error)
        assert "Not supported" in str(error)


class TestAudioMixError:
    """Tests for AudioMixError."""

    def test_basic_error(self) -> None:
        """Test basic mix error."""
        error = AudioMixError()
        assert "Failed to mix audio" in str(error)


class TestSpatialAudioError:
    """Tests for SpatialAudioError."""

    def test_basic_error(self) -> None:
        """Test basic spatial audio error."""
        error = SpatialAudioError(operation="binaural rendering")
        assert "binaural rendering" in str(error)

    def test_error_with_reason(self) -> None:
        """Test error with reason."""
        error = SpatialAudioError(
            operation="HRTF processing",
            reason="HRTF file not found",
        )
        assert "HRTF processing" in str(error)
        assert "HRTF file not found" in str(error)
