"""Unit tests for audio metadata extraction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.audio.config import AudioChannelLayout
from video2d3d.audio.exceptions import AudioExtractionError
from video2d3d.audio.metadata import AudioMetadata, AudioTrackInfo


class TestAudioTrackInfo:
    """Tests for AudioTrackInfo dataclass."""

    def test_default_values(self) -> None:
        """Test default track info values."""
        track = AudioTrackInfo()
        assert track.index == 0
        assert track.codec == ""
        assert track.sample_rate == 48000
        assert track.channels == 2
        assert track.language == "und"

    def test_channel_layout_enum(self) -> None:
        """Test channel layout enum property."""
        track = AudioTrackInfo(channels=2)
        assert track.channel_layout_enum == AudioChannelLayout.STEREO

        track = AudioTrackInfo(channels=6)
        assert track.channel_layout_enum == AudioChannelLayout.SURROUND_5_1

    def test_bitrate_kbps(self) -> None:
        """Test bitrate in kbps property."""
        track = AudioTrackInfo(bit_rate=192000)
        assert track.bitrate_kbps == 192.0

    def test_duration_formatted(self) -> None:
        """Test duration formatting."""
        track = AudioTrackInfo(duration=125.5)
        assert track.duration_formatted == "02:05"

        track = AudioTrackInfo(duration=3725.0)
        assert track.duration_formatted == "01:02:05"

    def test_is_lossless(self) -> None:
        """Test lossless codec detection."""
        track = AudioTrackInfo(codec="flac")
        assert track.is_lossless is True

        track = AudioTrackInfo(codec="aac")
        assert track.is_lossless is False

        track = AudioTrackInfo(codec="pcm_s24le")
        assert track.is_lossless is True

    def test_is_spatial(self) -> None:
        """Test spatial audio detection."""
        track = AudioTrackInfo(channels=2)
        assert track.is_spatial is False

        track = AudioTrackInfo(channels=6)
        assert track.is_spatial is True

        track = AudioTrackInfo(channels=8)
        assert track.is_spatial is True

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        track = AudioTrackInfo(
            index=0,
            codec="aac",
            sample_rate=48000,
            channels=2,
        )
        d = track.to_dict()
        assert d["index"] == 0
        assert d["codec"] == "aac"
        assert d["sample_rate"] == 48000
        assert d["channels"] == 2


class TestAudioMetadata:
    """Tests for AudioMetadata dataclass."""

    def test_default_values(self) -> None:
        """Test default metadata values."""
        metadata = AudioMetadata(file_path=Path("test.mp4"))
        assert metadata.has_audio is False
        assert metadata.track_count == 0
        assert metadata.tracks == []

    @patch("video2d3d.audio.metadata.subprocess.run")
    def test_extract_from_video_no_audio(self, mock_run: MagicMock, tmp_path) -> None:
        """Test extraction when video has no audio."""
        video = tmp_path / "no_audio.mp4"
        video.touch()
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"streams": []}',
        )

        metadata = AudioMetadata.extract_from_video(video)
        assert metadata.has_audio is False
        assert metadata.track_count == 0

    @patch("video2d3d.audio.metadata.subprocess.run")
    def test_extract_from_video_with_audio(self, mock_run: MagicMock, tmp_path) -> None:
        """Test extraction with single audio track."""
        video = tmp_path / "with_audio.mp4"
        video.touch()
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"streams": [{"index": 1, "codec_name": "aac", "channels": 2, "sample_rate": "48000"}]}',
        )

        metadata = AudioMetadata.extract_from_video(video)
        assert metadata.has_audio is True
        assert metadata.track_count == 1

    @patch("video2d3d.audio.metadata.subprocess.run")
    def test_extract_from_video_file_not_found(self, mock_run: MagicMock) -> None:
        """Test extraction with non-existent file."""
        with pytest.raises(AudioExtractionError, match="File does not exist"):
            AudioMetadata.extract_from_video("nonexistent.mp4")

    def test_get_track(self) -> None:
        """Test getting track by index."""
        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[
                AudioTrackInfo(index=0, codec="aac"),
                AudioTrackInfo(index=1, codec="ac3"),
            ],
        )

        track = metadata.get_track(0)
        assert track is not None
        assert track.codec == "aac"

        track = metadata.get_track(2)
        assert track is None

    def test_get_default_track(self) -> None:
        """Test getting default track."""
        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            default_track_index=1,
            tracks=[
                AudioTrackInfo(index=0, codec="aac"),
                AudioTrackInfo(index=1, codec="ac3", is_default=True),
            ],
        )

        track = metadata.get_default_track()
        assert track is not None
        assert track.codec == "ac3"

    def test_has_multi_channel(self) -> None:
        """Test multi-channel detection."""
        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(channels=2)],
        )
        assert metadata.has_multi_channel is False

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(channels=6)],
        )
        assert metadata.has_multi_channel is True

    def test_has_multiple_tracks(self) -> None:
        """Test multiple track detection."""
        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[AudioTrackInfo(index=0)],
        )
        assert metadata.has_multiple_tracks is False

        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            tracks=[
                AudioTrackInfo(index=0),
                AudioTrackInfo(index=1),
            ],
        )
        assert metadata.has_multiple_tracks is True

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        metadata = AudioMetadata(
            file_path=Path("test.mp4"),
            has_audio=True,
            track_count=1,
            tracks=[AudioTrackInfo(index=0, codec="aac")],
        )
        d = metadata.to_dict()
        assert d["has_audio"] is True
        assert d["track_count"] == 1
        assert len(d["tracks"]) == 1
