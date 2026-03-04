"""Unit tests for video input handling."""

from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from video2d3d.utils.config import VideoInputConfig
from video2d3d.video import (
    VideoCodecNotSupportedError,
    VideoCorruptedError,
    VideoError,
    VideoFileNotFoundError,
    VideoFormatNotSupportedError,
    VideoInputHandler,
    VideoMetadata,
    VideoMetadataExtractionError,
    VideoValidationError,
    validate_video,
)
)

# Fixtures
@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Create a sample video file path."""
    return tmp_path / "sample.mp4"


@pytest.fixture
def valid_video_metadata() -> VideoMetadata:
    """Create a sample valid video metadata."""
    return VideoMetadata(
        file_path=Path("/test/video.mp4"),
        width=1920,
        height=1080,
        fps=30.0,
        frame_count=900,
        duration=30.0,
        codec="h264",
        format="mp4",
        bitrate=5000000,
        file_size=18750000,
        is_valid=True,
    )


@pytest.fixture
def mock_opencv_capture() -> Generator[MagicMock, None, None]:
    """Mock OpenCV VideoCapture."""
    with patch("cv2.VideoCapture") as mock_cap_class:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 1920,
            cv2.CAP_PROP_FRAME_HEIGHT: 1080,
            cv2.CAP_PROP_FPS: 30.0,
            cv2.CAP_PROP_FRAME_COUNT: 900,
            cv2.CAP_PROP_FOURCC: cv2.VideoWriter_fourcc(*"H264"),
        }.get(prop, 0)
        mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))
        mock_cap_class.return_value = mock_cap
        yield mock_cap


# Tests for VideoMetadata
class TestVideoMetadata:
    """Tests for VideoMetadata dataclass."""

    def test_metadata_creation(self) -> None:
        """Test creating VideoMetadata instance."""
        metadata = VideoMetadata(
            file_path=Path("/test/video.mp4"),
            width=1920,
            height=1080,
            fps=30.0,
        )
        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0
        assert metadata.is_valid is True

    def test_resolution_property(self, valid_video_metadata: VideoMetadata) -> None:
        """Test resolution property returns correct tuple."""
        assert valid_video_metadata.resolution == (1920, 1080)

    def test_aspect_ratio(self, valid_video_metadata: VideoMetadata) -> None:
        """Test aspect ratio calculation."""
        assert valid_video_metadata.aspect_ratio == 16 / 9

    def test_aspect_ratio_zero_height(self) -> None:
        """Test aspect ratio with zero height."""
        metadata = VideoMetadata(file_path=Path("/test.mp4"), height=0)
        assert metadata.aspect_ratio == 0.0

    def test_duration_formatted(self, valid_video_metadata: VideoMetadata) -> None:
        """Test duration formatting."""
        assert valid_video_metadata.duration_formatted == "00:30"

    def test_duration_formatted_with_hours(self) -> None:
        """Test duration formatting with hours."""
        metadata = VideoMetadata(
            file_path=Path("/test.mp4"),
            duration=3661.5,  # 1 hour, 1 minute, 1.5 seconds
        )
        assert metadata.duration_formatted == "01:01:01"

    def test_file_size_mb(self, valid_video_metadata: VideoMetadata) -> None:
        """Test file size in megabytes."""
        assert pytest.approx(valid_video_metadata.file_size_mb, rel=0.01) == 17.88

    def test_is_4k(self) -> None:
        """Test 4K detection."""
        video_4k = VideoMetadata(file_path=Path("/test.mp4"), width=3840, height=2160)
        video_hd = VideoMetadata(file_path=Path("/test.mp4"), width=1920, height=1080)

        assert video_4k.is_4k is True
        assert video_hd.is_4k is False

    def test_is_hd(self) -> None:
        """Test HD detection."""
        video_hd = VideoMetadata(file_path=Path("/test.mp4"), width=1280, height=720)
        video_sd = VideoMetadata(file_path=Path("/test.mp4"), width=640, height=480)

        assert video_hd.is_hd is True
        assert video_sd.is_hd is False

    def test_is_full_hd(self) -> None:
        """Test Full HD detection."""
        video_fhd = VideoMetadata(file_path=Path("/test.mp4"), width=1920, height=1080)
        video_hd = VideoMetadata(file_path=Path("/test.mp4"), width=1280, height=720)

        assert video_fhd.is_full_hd is True
        assert video_hd.is_full_hd is False

    def test_str_representation(self, valid_video_metadata: VideoMetadata) -> None:
        """Test string representation."""
        result = str(valid_video_metadata)
        assert "1920x1080" in result
        assert "30.00" in result
        assert "h264" in result

    def test_to_dict(self, valid_video_metadata: VideoMetadata) -> None:
        """Test conversion to dictionary."""
        result = valid_video_metadata.to_dict()
        assert isinstance(result, dict)
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["fps"] == 30.0


# Tests for Exceptions
class TestVideoExceptions:
    """Tests for video exception classes."""

    def test_video_error_basic(self) -> None:
        """Test basic VideoError."""
        error = VideoError("Test error")
        assert str(error) == "Test error"
        assert error.file_path is None

    def test_video_error_with_path(self) -> None:
        """Test VideoError with file path."""
        path = Path("/test/video.mp4")
        error = VideoError("Test error", file_path=path)
        assert "Test error" in str(error)
        assert str(path) in str(error)
        assert error.file_path == path

    def test_video_file_not_found_error(self) -> None:
        """Test VideoFileNotFoundError."""
        path = Path("/test/missing.mp4")
        error = VideoFileNotFoundError(path)
        assert "not found" in str(error).lower()
        assert error.file_path == path

    def test_video_format_not_supported_error(self) -> None:
        """Test VideoFormatNotSupportedError."""
        path = Path("/test/video.xyz")
        error = VideoFormatNotSupportedError(path, format="xyz", supported_formats=["mp4", "avi"])
        assert "xyz" in str(error)
        assert "mp4" in str(error)
        assert error.format == "xyz"
        assert error.supported_formats == ["mp4", "avi"]

    def test_video_corrupted_error(self) -> None:
        """Test VideoCorruptedError."""
        path = Path("/test/corrupted.mp4")
        error = VideoCorruptedError(path, reason="Invalid header")
        assert "corrupted" in str(error).lower()
        assert "Invalid header" in str(error)
        assert error.reason == "Invalid header"

    def test_video_codec_not_supported_error(self) -> None:
        """Test VideoCodecNotSupportedError."""
        path = Path("/test/video.mp4")
        error = VideoCodecNotSupportedError(path, codec="unknown")
        assert "codec" in str(error).lower()
        assert error.codec == "unknown"

    def test_video_validation_error(self) -> None:
        """Test VideoValidationError."""
        path = Path("/test/video.mp4")
        error = VideoValidationError(path, errors=["Invalid width", "No frames"])
        assert "validation failed" in str(error).lower()
        assert error.errors == ["Invalid width", "No frames"]


# Tests for VideoInputHandler
class TestVideoInputHandler:
    """Tests for VideoInputHandler class."""

    def test_handler_creation(self) -> None:
        """Test creating VideoInputHandler instance."""
        handler = VideoInputHandler()
        assert handler.config is not None
        assert handler.strict_validation is True

    def test_handler_with_custom_config(self) -> None:
        """Test handler with custom configuration."""
        config = VideoInputConfig(supported_formats=["mp4", "avi"])
        handler = VideoInputHandler(config=config, strict_validation=False)
        assert handler.config.supported_formats == ["mp4", "avi"]
        assert handler.strict_validation is False

    def test_validate_file_exists_missing(self, tmp_path: Path) -> None:
        """Test validation fails for missing file."""
        handler = VideoInputHandler()
        missing_file = tmp_path / "missing.mp4"

        with pytest.raises(VideoFileNotFoundError):
            handler.validate_file_exists(missing_file)

    def test_validate_file_exists(self, sample_video_path: Path) -> None:
        """Test validation passes for existing file."""
        sample_video_path.touch()
        handler = VideoInputHandler()

        # Should not raise
        handler.validate_file_exists(sample_video_path)

    def test_validate_format_unsupported(self, tmp_path: Path) -> None:
        """Test format validation fails for unsupported format."""
        handler = VideoInputHandler()
        unsupported_file = tmp_path / "video.xyz"

        with pytest.raises(VideoFormatNotSupportedError) as exc_info:
            handler.validate_format(unsupported_file)

        assert "xyz" in str(exc_info.value)

    def test_validate_format_supported(self, sample_video_path: Path) -> None:
        """Test format validation passes for supported format."""
        handler = VideoInputHandler()

        result = handler.validate_format(sample_video_path)
        assert result == "mp4"

    def test_validate_format_no_extension(self, tmp_path: Path) -> None:
        """Test format validation fails for file without extension."""
        handler = VideoInputHandler()
        no_ext_file = tmp_path / "video"

        with pytest.raises(VideoFormatNotSupportedError) as exc_info:
            handler.validate_format(no_ext_file)

        assert "unknown" in str(exc_info.value)

    def test_is_codec_supported(self) -> None:
        """Test codec support checking."""
        handler = VideoInputHandler()

        assert handler.is_codec_supported("h264") is True
        assert handler.is_codec_supported("H264") is True
        assert handler.is_codec_supported("unknown") is False

    def test_context_manager(self, sample_video_path: Path, mock_opencv_capture: MagicMock) -> None:
        """Test handler as context manager."""
        sample_video_path.touch()

        with patch.object(VideoInputHandler, "validate_magic_bytes", return_value=True):
            with VideoInputHandler() as handler:
                # Handler should be available
                assert handler is not None


# Tests for validate_video convenience function
class TestValidateVideoFunction:
    """Tests for validate_video convenience function."""

    def test_validate_video_missing_file(self, tmp_path: Path) -> None:
        """Test validate_video with missing file."""
        missing_file = tmp_path / "missing.mp4"

        with pytest.raises(VideoFileNotFoundError):
            validate_video(missing_file)

    def test_validate_video_unsupported_format(self, tmp_path: Path) -> None:
        """Test validate_video with unsupported format."""
        unsupported_file = tmp_path / "video.xyz"
        unsupported_file.touch()

        with pytest.raises(VideoFormatNotSupportedError):
            validate_video(unsupported_file)


# Tests for VideoMetadata with audio
class TestVideoMetadataWithAudio:
    """Tests for VideoMetadata with audio information."""

    def test_metadata_with_audio(self) -> None:
        """Test metadata with audio information."""
        metadata = VideoMetadata(
            file_path=Path("/test/video.mp4"),
            width=1920,
            height=1080,
            fps=30.0,
            has_audio=True,
            audio_codec="aac",
            audio_sample_rate=48000,
            audio_channels=2,
        )
        assert metadata.has_audio is True
        assert metadata.audio_codec == "aac"
        assert metadata.audio_sample_rate == 48000
        assert metadata.audio_channels == 2

    def test_str_with_audio(self) -> None:
        """Test string representation includes audio."""
        metadata = VideoMetadata(
            file_path=Path("/test/video.mp4"),
            width=1920,
            height=1080,
            fps=30.0,
            has_audio=True,
            audio_codec="aac",
        )
        result = str(metadata)
        assert "aac" in result


# Tests for edge cases
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_zero_fps_handling(self) -> None:
        """Test handling of zero FPS."""
        metadata = VideoMetadata(
            file_path=Path("/test/video.mp4"),
            fps=0.0,
            frame_count=100,
        )
        # Duration should be 0 when FPS is 0
        assert metadata.duration == 0.0

    def test_validation_errors_list(self) -> None:
        """Test validation errors are recorded."""
        metadata = VideoMetadata(
            file_path=Path("/test/video.mp4"),
            width=0,  # Invalid
            height=1080,
            validation_errors=["Invalid video width"],
            is_valid=False,
        )
        assert metadata.is_valid is False
        assert len(metadata.validation_errors) == 1
        assert "Invalid video width" in metadata.validation_errors
