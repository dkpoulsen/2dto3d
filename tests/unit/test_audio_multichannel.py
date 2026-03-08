"""Unit tests for multi-channel audio processor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.audio.config import AudioChannelLayout, AudioFormatConfig
from video2d3d.audio.exceptions import AudioProcessingError
from video2d3d.audio.metadata import AudioMetadata, AudioTrackInfo
from video2d3d.audio.multichannel import DownmixResult, MultiChannelAudioProcessor


class TestDownmixResult:
    """Tests for DownmixResult dataclass."""

    def test_default_values(self) -> None:
        """Test default result values."""
        result = DownmixResult()
        assert result.success is True
        assert result.output_path is None
        assert result.input_channels == 6
        assert result.output_channels == 2
        assert result.input_layout == AudioChannelLayout.SURROUND_5_1
        assert result.output_layout == AudioChannelLayout.STEREO
        assert result.error_message is None

    def test_custom_values(self) -> None:
        """Test custom result values."""
        result = DownmixResult(
            success=False,
            input_channels=8,
            output_channels=2,
            error_message="Test error",
        )
        assert result.success is False
        assert result.input_channels == 8
        assert result.error_message == "Test error"


class TestMultiChannelAudioProcessor:
    """Tests for MultiChannelAudioProcessor class."""

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_init_default(self, mock_which: pytest.Mock) -> None:
        """Test processor initialization with defaults."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        assert processor.format_config is not None

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_init_with_config(self, mock_which: pytest.Mock) -> None:
        """Test processor initialization with custom config."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        format_config = AudioFormatConfig(codec="ac3", channels=6)
        processor = MultiChannelAudioProcessor(format_config=format_config)
        assert processor.format_config.codec == "ac3"

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_ffmpeg_not_available_raises_error(self, mock_which: pytest.Mock) -> None:
        """Test that missing FFmpeg raises error."""
        mock_which.return_value = None
        with pytest.raises(AudioProcessingError, match="FFmpeg not found"):
            MultiChannelAudioProcessor()

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_downmix_coefficients_defined(self, mock_which: pytest.Mock) -> None:
        """Test that downmix coefficients are defined."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        assert "5.1_to_stereo" in processor.DOWNMIX_COEFFICIENTS
        assert "7.1_to_stereo" in processor.DOWNMIX_COEFFICIENTS
        assert "center" in processor.DOWNMIX_COEFFICIENTS["5.1_to_stereo"]

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_downmix_filter_51_to_stereo(self, mock_which: pytest.Mock) -> None:
        """Test building 5.1 to stereo downmix filter."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_downmix_filter(6, 2, coefficient=0.707)
        assert "pan=stereo" in filter_str

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_downmix_filter_71_to_stereo(self, mock_which: pytest.Mock) -> None:
        """Test building 7.1 to stereo downmix filter."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_downmix_filter(8, 2, coefficient=0.707)
        assert "pan=stereo" in filter_str

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_downmix_filter_no_downmix_needed(self, mock_which: pytest.Mock) -> None:
        """Test filter when no downmix needed."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_downmix_filter(2, 2)
        assert filter_str == ""

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_upmix_filter_mono_to_stereo(self, mock_which: pytest.Mock) -> None:
        """Test building mono to stereo upmix filter."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_upmix_filter(1, 2)
        assert "stereo" in filter_str

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_upmix_filter_stereo_to_51(self, mock_which: pytest.Mock) -> None:
        """Test building stereo to 5.1 upmix filter."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_upmix_filter(2, 6)
        assert "pan=5.1" in filter_str

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_build_upmix_filter_no_upmix_needed(self, mock_which: pytest.Mock) -> None:
        """Test filter when no upmix needed."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        filter_str = processor._build_upmix_filter(6, 2)
        assert filter_str == ""

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_downmix_to_stereo_input_not_found(self, mock_which: pytest.Mock) -> None:
        """Test downmix with non-existent input."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()
        result = processor.downmix_to_stereo("nonexistent.mp4", "output.m4a")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    @patch("video2d3d.audio.multichannel.shutil.which")
    @patch("video2d3d.audio.multichannel.AudioMetadata.extract_from_video")
    def test_downmix_to_stereo_no_audio(
        self, mock_extract: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test downmix when input has no audio."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_extract.return_value = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=False,
        )

        with patch.object(Path, "exists", return_value=True):
            processor = MultiChannelAudioProcessor()
            result = processor.downmix_to_stereo("test.mp4", "output.m4a")

        assert result.success is False
        assert "no audio" in result.error_message.lower()

    @patch("video2d3d.audio.multichannel.shutil.which")
    @patch("video2d3d.audio.multichannel.AudioMetadata.extract_from_video")
    @patch("video2d3d.audio.multichannel.subprocess.run")
    def test_downmix_to_stereo_success(
        self, mock_run: pytest.Mock, mock_extract: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test successful downmix."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_extract.return_value = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=6)],
        )
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "resolve", return_value=Path("/tmp/input.mp4")):
                processor = MultiChannelAudioProcessor()
                result = processor.downmix_to_stereo("test.mp4", "output.m4a")

        assert result.success is True
        assert result.input_channels == 6
        assert result.output_channels == 2

    @patch("video2d3d.audio.multichannel.shutil.which")
    @patch("video2d3d.audio.multichannel.AudioMetadata.extract_from_video")
    @patch("video2d3d.audio.multichannel.subprocess.run")
    def test_downmix_to_stereo_ffmpeg_error(
        self, mock_run: pytest.Mock, mock_extract: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test downmix when FFmpeg fails."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_extract.return_value = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=6)],
        )
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="FFmpeg error",
        )

        with patch.object(Path, "exists", return_value=True):
            processor = MultiChannelAudioProcessor()
            result = processor.downmix_to_stereo("test.mp4", "output.m4a")

        assert result.success is False
        assert "FFmpeg error" in result.error_message

    @patch("video2d3d.audio.multichannel.shutil.which")
    @patch("video2d3d.audio.multichannel.AudioMetadata.extract_from_video")
    @patch("video2d3d.audio.multichannel.subprocess.run")
    def test_upmix_to_surround_success(
        self, mock_run: pytest.Mock, mock_extract: pytest.Mock, mock_which: pytest.Mock
    ) -> None:
        """Test successful upmix to surround."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_extract.return_value = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=2)],
        )
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with patch.object(Path, "exists", return_value=True):
            processor = MultiChannelAudioProcessor()
            result = processor.upmix_to_surround(
                "test.mp4",
                "output.m4a",
                target_layout=AudioChannelLayout.SURROUND_5_1,
            )

        assert result.success is True
        assert result.input_channels == 2
        assert result.output_channels == 6

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_convert_channel_layout_downmix(self, mock_which: pytest.Mock) -> None:
        """Test channel layout conversion with downmix."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=6)],
        )

        with patch.object(processor, "downmix_to_stereo") as mock_downmix:
            mock_downmix.return_value = DownmixResult(success=True)
            with patch.object(Path, "exists", return_value=True):
                result = processor.convert_channel_layout(
                    "test.mp4",
                    "output.m4a",
                    AudioChannelLayout.STEREO,
                )
            mock_downmix.assert_called_once()

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_convert_channel_layout_upmix(self, mock_which: pytest.Mock) -> None:
        """Test channel layout conversion with upmix."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=2)],
        )

        with patch.object(processor, "upmix_to_surround") as mock_upmix:
            mock_upmix.return_value = DownmixResult(success=True)
            with patch.object(Path, "exists", return_value=True):
                result = processor.convert_channel_layout(
                    "test.mp4",
                    "output.m4a",
                    AudioChannelLayout.SURROUND_5_1,
                )
            mock_upmix.assert_called_once()

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_convert_channel_layout_same_channels(self, mock_which: pytest.Mock) -> None:
        """Test channel layout conversion with same channel count."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        with patch("shutil.copy") as mock_copy:
            with (
                patch.object(Path, "exists", return_value=True),
                patch.object(
                    AudioMetadata,
                    "extract_from_video",
                    return_value=AudioMetadata(
                        file_path=Path("test.mp4"),
                        has_audio=True,
                        tracks=[AudioTrackInfo(index=0, channels=2)],
                    ),
                ),
            ):
                result = processor.convert_channel_layout(
                    "test.mp4",
                    "output.m4a",
                    AudioChannelLayout.STEREO,
                )
            mock_copy.assert_called_once()

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_get_optimal_layout_no_audio(self, mock_which: pytest.Mock) -> None:
        """Test optimal layout when no audio present."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(file_path=Path("test.mp4"), has_audio=False)
        layout = processor.get_optimal_layout(metadata)
        assert layout == AudioChannelLayout.STEREO

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_get_optimal_layout_stereo(self, mock_which: pytest.Mock) -> None:
        """Test optimal layout for stereo source."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=2)],
        )
        layout = processor.get_optimal_layout(metadata)
        assert layout == AudioChannelLayout.STEREO

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_get_optimal_layout_surround_prefer_surround(self, mock_which: pytest.Mock) -> None:
        """Test optimal layout for surround source with prefer_surround=True."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=6)],
        )
        layout = processor.get_optimal_layout(metadata, prefer_surround=True)
        assert layout == AudioChannelLayout.SURROUND_5_1

    @patch("video2d3d.audio.multichannel.shutil.which")
    def test_get_optimal_layout_surround_default(self, mock_which: pytest.Mock) -> None:
        """Test optimal layout for surround source with default settings."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        processor = MultiChannelAudioProcessor()

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0, channels=6)],
        )
        layout = processor.get_optimal_layout(metadata, prefer_surround=False)
        # Default should be stereo for compatibility
        assert layout == AudioChannelLayout.STEREO
