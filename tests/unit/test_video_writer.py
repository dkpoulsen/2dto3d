"""Unit tests for video output writer system."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video2d3d.video import (
    AudioProcessingError,
    FFmpegProcessError,
    InvalidVideoDimensionsError,
    PixelFormat,
    Preset,
    VideoCodec,
    VideoOutputWriter,
    VideoWriteError,
    VideoWriterConfig,
    WriterStats,
    create_video_writer,
)


# Fixtures
@pytest.fixture
def output_video_path(tmp_path: Path) -> Path:
    """Create a sample output video file path."""
    return tmp_path / "output.mp4"


@pytest.fixture
def source_video_path(tmp_path: Path) -> Path:
    """Create a sample source video file path."""
    return tmp_path / "source.mp4"


@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample frame for testing."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_frames() -> list[np.ndarray]:
    """Create sample frames for testing."""
    return [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(10)]


@pytest.fixture
def video_writer_config() -> VideoWriterConfig:
    """Create a sample video writer configuration."""
    return VideoWriterConfig(
        codec="libx264",
        preset="medium",
        crf=23,
        pixel_format="yuv420p",
        container_format="mp4",
    )


# Tests for VideoCodec enum
class TestVideoCodec:
    """Tests for VideoCodec enum."""

    def test_video_codec_values(self) -> None:
        """Test that all expected codecs are defined."""
        assert VideoCodec.H264.value == "libx264"
        assert VideoCodec.H265.value == "libx265"
        assert VideoCodec.VP9.value == "libvpx-vp9"
        assert VideoCodec.AV1.value == "libaom-av1"
        assert VideoCodec.MPEG4.value == "mpeg4"
        assert VideoCodec.PRORES.value == "prores_ks"
        assert VideoCodec.MJPEG.value == "mjpeg"


# Tests for Preset enum
class TestPreset:
    """Tests for Preset enum."""

    def test_preset_values(self) -> None:
        """Test that all expected presets are defined."""
        assert Preset.ULTRAFAST.value == "ultrafast"
        assert Preset.MEDIUM.value == "medium"
        assert Preset.VERYSLOW.value == "veryslow"


# Tests for PixelFormat enum
class TestPixelFormat:
    """Tests for PixelFormat enum."""

    def test_pixel_format_values(self) -> None:
        """Test that all expected pixel formats are defined."""
        assert PixelFormat.YUV420P.value == "yuv420p"
        assert PixelFormat.YUV422P.value == "yuv422p"
        assert PixelFormat.YUV444P.value == "yuv444p"
        assert PixelFormat.RGB24.value == "rgb24"


# Tests for VideoWriterConfig
class TestVideoWriterConfig:
    """Tests for VideoWriterConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = VideoWriterConfig()
        assert config.codec == "libx264"
        assert config.preset == "medium"
        assert config.crf == 23
        assert config.pixel_format == "yuv420p"
        assert config.container_format == "mp4"
        assert config.copy_audio is True
        assert config.audio_codec == "aac"
        assert config.audio_bitrate == 192000
        assert config.audio_sample_rate == 48000
        assert config.audio_channels == 2
        assert config.faststart is True
        assert config.threads == 0
        assert config.hwaccel is False

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = VideoWriterConfig(
            codec="libx265",
            preset="slow",
            crf=20,
            pixel_format="yuv422p",
            container_format="mkv",
        )
        assert config.codec == "libx265"
        assert config.preset == "slow"
        assert config.crf == 20
        assert config.pixel_format == "yuv422p"
        assert config.container_format == "mkv"

    def test_invalid_crf_for_h264(self) -> None:
        """Test that invalid CRF values raise an error for H.264."""
        with pytest.raises(ValueError, match="CRF must be 0-51"):
            VideoWriterConfig(codec="libx264", crf=52)

        with pytest.raises(ValueError, match="CRF must be 0-51"):
            VideoWriterConfig(codec="libx264", crf=-1)

    def test_invalid_crf_for_h265(self) -> None:
        """Test that invalid CRF values raise an error for H.265."""
        with pytest.raises(ValueError, match="CRF must be 0-51"):
            VideoWriterConfig(codec="libx265", crf=60)

    def test_invalid_crf_for_vp9(self) -> None:
        """Test that invalid CRF values raise an error for VP9."""
        with pytest.raises(ValueError, match="CRF must be 0-63"):
            VideoWriterConfig(codec="libvpx-vp9", crf=70)

    def test_invalid_preset(self) -> None:
        """Test that invalid preset raises an error."""
        with pytest.raises(ValueError, match="Invalid preset"):
            VideoWriterConfig(preset="invalid_preset")

    def test_get_file_extension(self) -> None:
        """Test getting file extension for container format."""
        assert VideoWriterConfig(container_format="mp4").get_file_extension() == ".mp4"
        assert VideoWriterConfig(container_format="mkv").get_file_extension() == ".mkv"
        assert VideoWriterConfig(container_format="avi").get_file_extension() == ".avi"
        assert VideoWriterConfig(container_format="webm").get_file_extension() == ".webm"

    def test_bitrate_instead_of_crf(self) -> None:
        """Test using bitrate instead of CRF."""
        config = VideoWriterConfig(codec="libx264", bitrate=5000000, crf=None)
        assert config.bitrate == 5000000
        assert config.crf is None


# Tests for WriterStats
class TestWriterStats:
    """Tests for WriterStats dataclass."""

    def test_default_stats(self) -> None:
        """Test default stats values."""
        stats = WriterStats()
        assert stats.frames_written == 0
        assert stats.bytes_written == 0
        assert stats.start_time is None
        assert stats.end_time is None
        assert stats.average_fps == 0.0

    def test_to_dict(self) -> None:
        """Test converting stats to dictionary."""
        stats = WriterStats(frames_written=100, bytes_written=1024000)
        result = stats.to_dict()
        assert result["frames_written"] == 100
        assert result["bytes_written"] == 1024000


# Tests for VideoOutputWriter
class TestVideoOutputWriter:
    """Tests for VideoOutputWriter class."""

    def test_initialization(
        self, output_video_path: Path, video_writer_config: VideoWriterConfig
    ) -> None:
        """Test VideoOutputWriter initialization."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            writer = VideoOutputWriter(
                output_video_path,
                config=video_writer_config,
                width=640,
                height=480,
                fps=30.0,
            )
            assert writer.output_path == output_video_path
            assert writer.width == 640
            assert writer.height == 480
            assert writer.fps == 30.0
            assert writer.is_open is False

    def test_invalid_dimensions(self, output_video_path: Path) -> None:
        """Test that invalid dimensions raise an error."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with pytest.raises(InvalidVideoDimensionsError):
                VideoOutputWriter(output_video_path, width=0, height=480)

            with pytest.raises(InvalidVideoDimensionsError):
                VideoOutputWriter(output_video_path, width=640, height=-1)

    def test_invalid_fps(self, output_video_path: Path) -> None:
        """Test that invalid FPS raises an error."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with pytest.raises(ValueError, match="FPS must be positive"):
                VideoOutputWriter(output_video_path, width=640, height=480, fps=0)

            with pytest.raises(ValueError, match="FPS must be positive"):
                VideoOutputWriter(output_video_path, width=640, height=480, fps=-30)

    def test_ffmpeg_not_available(self, output_video_path: Path) -> None:
        """Test that missing FFmpeg raises an error."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with pytest.raises(VideoWriteError, match="FFmpeg not found"):
                VideoOutputWriter(output_video_path, width=640, height=480)

    def test_context_manager(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test using VideoOutputWriter as a context manager."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.stdin = MagicMock()
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                with VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                ) as writer:
                    assert writer.is_open is True

    def test_write_frame(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test writing a single frame."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()
                writer.write_frame(sample_frame)
                assert writer.frames_written == 1
                mock_stdin.write.assert_called_once()

                writer.close()

    def test_write_frame_wrong_dimensions(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
    ) -> None:
        """Test that writing a frame with wrong dimensions raises an error."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.stdin = MagicMock()
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()

                # Wrong dimensions
                wrong_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
                with pytest.raises(VideoWriteError, match="don't match"):
                    writer.write_frame(wrong_frame)

    def test_write_frames_list(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frames: list[np.ndarray],
    ) -> None:
        """Test writing multiple frames as a list."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()
                count = writer.write_frames(sample_frames)
                assert count == len(sample_frames)
                assert writer.frames_written == len(sample_frames)

                writer.close()

    def test_write_frames_array(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
    ) -> None:
        """Test writing frames as a numpy array."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                # Create 4D array (N, H, W, C)
                frames_array = np.random.randint(0, 255, (10, 480, 640, 3), dtype=np.uint8)

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()
                count = writer.write_frames(frames_array)
                assert count == 10
                assert writer.frames_written == 10

                writer.close()

    def test_ffmpeg_process_failure(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
    ) -> None:
        """Test handling of FFmpeg process failure."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_process.wait.return_value = 1
                mock_process.returncode = 1
                mock_process.stderr.read.return_value = b"FFmpeg error"
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()

                with pytest.raises(FFmpegProcessError):
                    writer.close()

    def test_broken_pipe_handling(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test handling of broken pipe when FFmpeg dies."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_stdin.write.side_effect = BrokenPipeError()
                mock_process.stdin = mock_stdin
                mock_process.stderr.read.return_value = b"FFmpeg crashed"
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()

                with pytest.raises(FFmpegProcessError):
                    writer.write_frame(sample_frame)

    def test_get_stats(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
    ) -> None:
        """Test getting writer statistics."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            writer = VideoOutputWriter(
                output_video_path,
                config=video_writer_config,
                width=640,
                height=480,
            )
            stats = writer.get_stats()
            assert isinstance(stats, WriterStats)
            assert stats.frames_written == 0

    def test_properties(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
    ) -> None:
        """Test VideoOutputWriter properties."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            writer = VideoOutputWriter(
                output_video_path,
                config=video_writer_config,
                width=640,
                height=480,
            )
            assert writer.is_open is False
            assert writer.frames_written == 0


# Tests for create_video_writer
class TestCreateVideoWriter:
    """Tests for create_video_writer convenience function."""

    def test_create_video_writer_default(self, output_video_path: Path) -> None:
        """Test creating a video writer with default settings."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            writer = create_video_writer(
                output_video_path,
                width=640,
                height=480,
            )
            assert isinstance(writer, VideoOutputWriter)
            assert writer.config.codec == "libx264"
            assert writer.config.preset == "medium"
            assert writer.config.crf == 23

    def test_create_video_writer_custom(self, output_video_path: Path) -> None:
        """Test creating a video writer with custom settings."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            writer = create_video_writer(
                output_video_path,
                width=640,
                height=480,
                fps=60.0,
                codec="libx265",
                preset="slow",
                crf=20,
                pixel_format="yuv422p",
            )
            assert writer.config.codec == "libx265"
            assert writer.config.preset == "slow"
            assert writer.config.crf == 20
            assert writer.config.pixel_format == "yuv422p"
            assert writer.fps == 60.0


# Tests for exceptions
class TestExceptions:
    """Tests for new exceptions."""

    def test_video_write_error(self, output_video_path: Path) -> None:
        """Test VideoWriteError."""
        error = VideoWriteError(output_video_path, "Test error")
        assert error.reason == "Test error"
        assert "Failed to write video" in str(error)
        assert str(output_video_path) in str(error)

    def test_ffmpeg_process_error(self, output_video_path: Path) -> None:
        """Test FFmpegProcessError."""
        error = FFmpegProcessError(
            output_video_path,
            return_code=1,
            stderr_output="FFmpeg crashed",
            command=["ffmpeg", "-i", "input.mp4"],
        )
        assert error.return_code == 1
        assert error.stderr_output == "FFmpeg crashed"
        assert error.command == ["ffmpeg", "-i", "input.mp4"]
        assert "return code: 1" in str(error)
        assert "FFmpeg crashed" in str(error)

    def test_ffmpeg_process_error_truncates_long_output(self, output_video_path: Path) -> None:
        """Test FFmpegProcessError truncates long stderr output."""
        long_error = "x" * 1000
        error = FFmpegProcessError(
            output_video_path,
            stderr_output=long_error,
        )
        assert len(str(error)) < len(long_error) + 100
        assert "..." in str(error)

    def test_audio_processing_error(self) -> None:
        """Test AudioProcessingError."""
        error = AudioProcessingError(None, "No audio stream found")
        assert error.reason == "No audio stream found"
        assert "Failed to process audio" in str(error)

    def test_invalid_video_dimensions_error(self) -> None:
        """Test InvalidVideoDimensionsError."""
        error = InvalidVideoDimensionsError(1921, 1081, "Must be even numbers")
        assert error.width == 1921
        assert error.height == 1081
        assert "1921x1081" in str(error)


class TestProgressCallback:
    """Tests for progress callback in video writer."""

    def test_write_frame_with_callback(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test write_frame calls progress callback."""
        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                    progress_callback=callback,
                    total_frames=10,
                )
                writer.open()

                for _ in range(5):
                    writer.write_frame(sample_frame)

                assert len(progress_calls) == 5
                assert progress_calls[-1] == (5, 10)

                writer.close()

    def test_callback_values_increments(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test callback receives incrementing values."""
        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                    progress_callback=callback,
                    total_frames=3,
                )
                writer.open()

                writer.write_frame(sample_frame)
                writer.write_frame(sample_frame)
                writer.write_frame(sample_frame)

                assert progress_calls[0] == (1, 3)
                assert progress_calls[1] == (2, 3)
                assert progress_calls[2] == (3, 3)

                writer.close()

    def test_write_without_callback(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frame: np.ndarray,
    ) -> None:
        """Test writing works without callback."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                )
                writer.open()

                writer.write_frame(sample_frame)
                assert writer.frames_written == 1

                writer.close()

    def test_callback_with_write_frames_list(
        self,
        output_video_path: Path,
        video_writer_config: VideoWriterConfig,
        sample_frames: list[np.ndarray],
    ) -> None:
        """Test callback works with write_frames list."""
        progress_calls = []

        def callback(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ffmpeg"
            with patch("subprocess.Popen") as mock_popen:
                mock_process = MagicMock()
                mock_stdin = MagicMock()
                mock_process.stdin = mock_stdin
                mock_process.wait.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                writer = VideoOutputWriter(
                    output_video_path,
                    config=video_writer_config,
                    width=640,
                    height=480,
                    progress_callback=callback,
                    total_frames=10,
                )
                writer.open()
                writer.write_frames(sample_frames)

                assert len(progress_calls) == len(sample_frames)
                assert progress_calls[-1] == (len(sample_frames), 10)

                writer.close()
