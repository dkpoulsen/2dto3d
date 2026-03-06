"""Unit tests for audio configuration classes."""

from __future__ import annotations

import pytest

from video2d3d.audio.config import (
    AudioChannelLayout,
    AudioConfig,
    AudioFormatConfig,
    SpatialAudioConfig,
    SpatialAudioFormat,
)


class TestAudioChannelLayout:
    """Tests for AudioChannelLayout enum."""

    def test_channel_layout_values(self) -> None:
        """Test that all expected layouts are defined."""
        assert AudioChannelLayout.MONO.value == "mono"
        assert AudioChannelLayout.STEREO.value == "stereo"
        assert AudioChannelLayout.SURROUND_5_1.value == "5.1"
        assert AudioChannelLayout.SURROUND_7_1.value == "7.1"

    def test_from_channel_count(self) -> None:
        """Test channel layout from channel count."""
        assert AudioChannelLayout.from_channel_count(1) == AudioChannelLayout.MONO
        assert AudioChannelLayout.from_channel_count(2) == AudioChannelLayout.STEREO
        assert AudioChannelLayout.from_channel_count(6) == AudioChannelLayout.SURROUND_5_1
        assert AudioChannelLayout.from_channel_count(8) == AudioChannelLayout.SURROUND_7_1

    def test_channel_count_property(self) -> None:
        """Test channel count property."""
        assert AudioChannelLayout.MONO.channel_count == 1
        assert AudioChannelLayout.STEREO.channel_count == 2
        assert AudioChannelLayout.SURROUND_5_1.channel_count == 6
        assert AudioChannelLayout.SURROUND_7_1.channel_count == 8

    def test_to_ffmpeg_layout(self) -> None:
        """Test FFmpeg layout string conversion."""
        assert AudioChannelLayout.MONO.to_ffmpeg_layout() == "mono"
        assert AudioChannelLayout.STEREO.to_ffmpeg_layout() == "stereo"
        assert AudioChannelLayout.SURROUND_5_1.to_ffmpeg_layout() == "5.1"


class TestSpatialAudioFormat:
    """Tests for SpatialAudioFormat enum."""

    def test_spatial_format_values(self) -> None:
        """Test that all expected formats are defined."""
        assert SpatialAudioFormat.NONE.value == "none"
        assert SpatialAudioFormat.BINAURAL.value == "binaural"
        assert SpatialAudioFormat.AMBISONICS_1ST.value == "ambisonics_1st"

    def test_is_ambisonics(self) -> None:
        """Test is_ambisonics property."""
        assert SpatialAudioFormat.NONE.is_ambisonics is False
        assert SpatialAudioFormat.BINAURAL.is_ambisonics is False
        assert SpatialAudioFormat.AMBISONICS_1ST.is_ambisonics is True
        assert SpatialAudioFormat.AMBISONICS_2ND.is_ambisonics is True

    def test_requires_encoding(self) -> None:
        """Test requires_encoding property."""
        assert SpatialAudioFormat.NONE.requires_encoding is False
        assert SpatialAudioFormat.BINAURAL.requires_encoding is False
        assert SpatialAudioFormat.DOLBY_ATMOS.requires_encoding is True


class TestAudioFormatConfig:
    """Tests for AudioFormatConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = AudioFormatConfig()
        assert config.codec == "aac"
        assert config.bitrate == 192000
        assert config.sample_rate == 48000
        assert config.channels == 2

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = AudioFormatConfig(
            codec="opus",
            bitrate=128000,
            sample_rate=44100,
            channels=6,
        )
        assert config.codec == "opus"
        assert config.bitrate == 128000
        assert config.sample_rate == 44100
        assert config.channels == 6

    def test_invalid_codec_raises_error(self) -> None:
        """Test that invalid codec raises ValueError."""
        with pytest.raises(ValueError, match="Invalid codec"):
            AudioFormatConfig(codec="invalid_codec")

    def test_invalid_bitrate_raises_error(self) -> None:
        """Test that invalid bitrate raises ValueError."""
        with pytest.raises(ValueError, match="Bitrate must be positive"):
            AudioFormatConfig(bitrate=-1)

    def test_invalid_quality_raises_error(self) -> None:
        """Test that invalid quality raises ValueError."""
        with pytest.raises(ValueError, match="Invalid quality"):
            AudioFormatConfig(quality="ultra")

    def test_to_ffmpeg_args(self) -> None:
        """Test FFmpeg argument generation."""
        config = AudioFormatConfig(codec="aac", bitrate=192000, sample_rate=48000)
        args = config.to_ffmpeg_args()
        assert "-c:a" in args
        assert "aac" in args
        assert "-b:a" in args
        assert "192000" in args
        assert "-ar" in args
        assert "48000" in args

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        config = AudioFormatConfig()
        d = config.to_dict()
        assert d["codec"] == "aac"
        assert d["bitrate"] == 192000
        assert d["sample_rate"] == 48000
        assert d["channels"] == 2


class TestSpatialAudioConfig:
    """Tests for SpatialAudioConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = SpatialAudioConfig()
        assert config.enable_spatial is False
        assert config.spatial_format == SpatialAudioFormat.BINAURAL
        assert config.room_size == "medium"
        assert config.reverb_amount == 0.3

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.AMBISONICS_1ST,
            room_size="large",
            reverb_amount=0.5,
        )
        assert config.enable_spatial is True
        assert config.spatial_format == SpatialAudioFormat.AMBISONICS_1ST
        assert config.room_size == "large"
        assert config.reverb_amount == 0.5

    def test_invalid_room_size_raises_error(self) -> None:
        """Test that invalid room size raises ValueError."""
        with pytest.raises(ValueError, match="Invalid room_size"):
            SpatialAudioConfig(room_size="huge")

    def test_invalid_reverb_raises_error(self) -> None:
        """Test that invalid reverb amount raises ValueError."""
        with pytest.raises(ValueError, match="reverb_amount must be between"):
            SpatialAudioConfig(reverb_amount=1.5)

    def test_to_ffmpeg_filter_disabled(self) -> None:
        """Test that disabled spatial audio returns empty filter."""
        config = SpatialAudioConfig(enable_spatial=False)
        assert config.to_ffmpeg_filter() == ""

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        config = SpatialAudioConfig(enable_spatial=True)
        d = config.to_dict()
        assert d["enable_spatial"] is True
        assert d["spatial_format"] == "binaural"


class TestAudioConfig:
    """Tests for AudioConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = AudioConfig()
        assert config.preserve_tracks is True
        assert config.normalize is True
        assert config.normalization_target == -14.0

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = AudioConfig(
            preserve_tracks=False,
            normalize=False,
            tracks_to_preserve=[0, 1],
        )
        assert config.preserve_tracks is False
        assert config.normalize is False
        assert config.tracks_to_preserve == [0, 1]

    def test_invalid_normalization_target_raises_error(self) -> None:
        """Test that invalid normalization target raises ValueError."""
        with pytest.raises(ValueError, match="normalization_target must be between"):
            AudioConfig(normalization_target=10)

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        config = AudioConfig()
        d = config.to_dict()
        assert d["preserve_tracks"] is True
        assert d["normalize"] is True
