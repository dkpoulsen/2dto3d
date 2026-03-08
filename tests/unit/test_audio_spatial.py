"""Unit tests for spatial audio processor."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.audio.config import AudioFormatConfig, SpatialAudioConfig, SpatialAudioFormat
from video2d3d.audio.exceptions import SpatialAudioError
from video2d3d.audio.spatial import SpatialAudioProcessor, SpatialProcessingResult


class TestSpatialProcessingResult:
    """Tests for SpatialProcessingResult dataclass."""

    def test_default_values(self) -> None:
        """Test default result values."""
        result = SpatialProcessingResult()
        assert result.success is True
        assert result.output_path is None
        assert result.spatial_format == SpatialAudioFormat.NONE
        assert result.channels == 2
        assert result.duration == 0.0
        assert result.error_message is None

    def test_error_result(self) -> None:
        """Test error result creation."""
        result = SpatialProcessingResult(
            success=False,
            error_message="Test error",
        )
        assert result.success is False
        assert result.error_message == "Test error"


class TestSpatialAudioProcessor:
    """Tests for SpatialAudioProcessor class."""

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_init_default(self, mock_which: pytest.Mock) -> None:
        """Test processor initialization with defaults."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = SpatialAudioProcessor()
        assert processor.config is not None
        assert processor.format_config is not None

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_init_with_config(self, mock_which: pytest.Mock) -> None:
        """Test processor initialization with custom config."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(enable_spatial=True)
        format_config = AudioFormatConfig(codec="opus")
        processor = SpatialAudioProcessor(config=config, format_config=format_config)
        assert processor.config.enable_spatial is True
        assert processor.format_config.codec == "opus"

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_ffmpeg_not_available_raises_error(self, mock_which: pytest.Mock) -> None:
        """Test that missing FFmpeg raises error."""
        mock_which.return_value = None
        with pytest.raises(SpatialAudioError, match="FFmpeg not found"):
            SpatialAudioProcessor()

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_get_output_channel_count_disabled(self, mock_which: pytest.Mock) -> None:
        """Test output channel count when spatial disabled."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(enable_spatial=False)
        format_config = AudioFormatConfig(channels=6)
        processor = SpatialAudioProcessor(config=config, format_config=format_config)
        assert processor.get_output_channel_count() == 6

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_get_output_channel_count_binaural(self, mock_which: pytest.Mock) -> None:
        """Test output channel count for binaural format."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.BINAURAL,
        )
        processor = SpatialAudioProcessor(config=config)
        assert processor.get_output_channel_count() == 2

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_get_output_channel_count_ambisonics_1st(self, mock_which: pytest.Mock) -> None:
        """Test output channel count for 1st order Ambisonics."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.AMBISONICS_1ST,
        )
        processor = SpatialAudioProcessor(config=config)
        assert processor.get_output_channel_count() == 4

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_get_output_channel_count_ambisonics_2nd(self, mock_which: pytest.Mock) -> None:
        """Test output channel count for 2nd order Ambisonics."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.AMBISONICS_2ND,
        )
        processor = SpatialAudioProcessor(config=config)
        assert processor.get_output_channel_count() == 9

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_process_input_not_found(self, mock_which: pytest.Mock) -> None:
        """Test processing with non-existent input."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = SpatialAudioProcessor()
        result = processor.process("nonexistent.mp4", "output.m4a")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_process_success(self, mock_run: pytest.Mock, mock_which: pytest.Mock) -> None:
        """Test successful processing."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        # Create a temp file to simulate input exists
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "resolve", return_value=Path("/tmp/input.mp4")):
                processor = SpatialAudioProcessor()
                # Mock _get_audio_duration
                with patch.object(processor, "_get_audio_duration", return_value=10.0):
                    result = processor.process("/tmp/input.mp4", "/tmp/output.m4a")

        assert result.success is True

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_process_ffmpeg_error(self, mock_run: pytest.Mock, mock_which: pytest.Mock) -> None:
        """Test processing when FFmpeg fails."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="FFmpeg encoding error",
        )

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "resolve", return_value=Path("/tmp/input.mp4")):
                processor = SpatialAudioProcessor()
                result = processor.process("/tmp/input.mp4", "/tmp/output.m4a")

        assert result.success is False
        assert "FFmpeg error" in result.error_message

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_process_timeout(self, mock_run: pytest.Mock, mock_which: pytest.Mock) -> None:
        """Test processing timeout handling."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=300)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "resolve", return_value=Path("/tmp/input.mp4")):
                processor = SpatialAudioProcessor()
                result = processor.process("/tmp/input.mp4", "/tmp/output.m4a")

        assert result.success is False
        assert "timed out" in result.error_message.lower()

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_process_video_audio(self, mock_which: pytest.Mock) -> None:
        """Test process_video_audio method."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = SpatialAudioProcessor()

        # process_video_audio should just call process
        with patch.object(processor, "process") as mock_process:
            mock_process.return_value = SpatialProcessingResult(success=True)
            result = processor.process_video_audio("video.mp4", "audio.m4a")
            mock_process.assert_called_once_with("video.mp4", "audio.m4a")
            assert result.success is True

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_build_binaural_filter_center_sound(self, mock_which: pytest.Mock) -> None:
        """Test binaural filter for center-positioned sound."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.BINAURAL,
            source_position=(0.0, 0.0, 1.0),  # Center front
        )
        processor = SpatialAudioProcessor(config=config)
        filters = processor._build_binaural_filter()
        # Center sound should have minimal or no delay
        assert isinstance(filters, list)

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_build_binaural_filter_left_sound(self, mock_which: pytest.Mock) -> None:
        """Test binaural filter for left-positioned sound."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.BINAURAL,
            source_position=(-1.0, 0.0, 1.0),  # Left front
        )
        processor = SpatialAudioProcessor(config=config)
        filters = processor._build_binaural_filter()
        assert isinstance(filters, list)

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_build_binaural_filter_with_hrtf(self, mock_which: pytest.Mock) -> None:
        """Test binaural filter with custom HRTF file."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.BINAURAL,
            hrtf_file="/path/to/hrtf.sofa",
        )
        processor = SpatialAudioProcessor(config=config)
        filters = processor._build_binaural_filter()
        # Should use sofalizer filter when HRTF file is provided
        assert any("sofalizer" in f for f in filters)

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_build_ambisonics_filter(self, mock_which: pytest.Mock) -> None:
        """Test Ambisonics filter building."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.AMBISONICS_1ST,
        )
        processor = SpatialAudioProcessor(config=config)
        filters = processor._build_ambisonics_filter()
        assert isinstance(filters, list)
        assert len(filters) > 0

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_build_spatial_filter_chain_disabled(self, mock_which: pytest.Mock) -> None:
        """Test filter chain when spatial disabled."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        config = SpatialAudioConfig(enable_spatial=False)
        processor = SpatialAudioProcessor(config=config)
        filter_chain = processor._build_spatial_filter_chain()
        assert filter_chain == ""

    @patch("video2d3d.audio.spatial.shutil.which")
    def test_room_presets_defined(self, mock_which: pytest.Mock) -> None:
        """Test that room presets are defined."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = SpatialAudioProcessor()
        assert "small" in processor.ROOM_PRESETS
        assert "medium" in processor.ROOM_PRESETS
        assert "large" in processor.ROOM_PRESETS
        assert "cathedral" in processor.ROOM_PRESETS

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_get_audio_duration_success(
        self, mock_run: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test getting audio duration."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="120.5\n",
        )

        processor = SpatialAudioProcessor()
        duration = processor._get_audio_duration(Path("/tmp/audio.m4a"))
        assert duration == 120.5

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_get_audio_duration_failure(
        self, mock_run: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test getting audio duration when ffprobe fails."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        processor = SpatialAudioProcessor()
        duration = processor._get_audio_duration(Path("/tmp/audio.m4a"))
        assert duration == 0.0

    @patch("video2d3d.audio.spatial.shutil.which")
    @patch("video2d3d.audio.spatial.subprocess.run")
    def test_get_audio_duration_timeout(
        self, mock_run: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test getting audio duration with timeout."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffprobe", timeout=30)

        processor = SpatialAudioProcessor()
        duration = processor._get_audio_duration(Path("/tmp/audio.m4a"))
        assert duration == 0.0
