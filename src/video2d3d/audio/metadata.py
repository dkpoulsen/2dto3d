"""Audio metadata extraction and management."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from video2d3d.audio.config import AudioChannelLayout
from video2d3d.audio.exceptions import AudioExtractionError
from video2d3d.utils.logger import get_logger


def _get_audio_logger():
    """Get the audio module logger (lazy initialization)."""
    return get_logger("audio.metadata")


@dataclass
class AudioTrackInfo:
    """Information about a single audio track.

    Attributes:
        index: Track index in the container.
        codec: Audio codec name (e.g., 'aac', 'opus', 'mp3').
        codec_long_name: Full codec name.
        sample_rate: Sample rate in Hz.
        channels: Number of audio channels.
        channel_layout: Channel layout description.
        bit_rate: Bitrate in bits per second.
        duration: Duration in seconds.
        language: Language code (e.g., 'en', 'es').
        title: Track title if available.
        is_default: Whether this is the default track.
        is_forced: Whether this is a forced track.
        disposition: Track disposition flags.
        tags: Additional metadata tags.
    """

    index: int = 0
    codec: str = ""
    codec_long_name: str = ""
    sample_rate: int = 48000
    channels: int = 2
    channel_layout: str = "stereo"
    bit_rate: int = 0
    duration: float = 0.0
    language: str = "und"
    title: str = ""
    is_default: bool = False
    is_forced: bool = False
    disposition: dict[str, bool] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def channel_layout_enum(self) -> AudioChannelLayout:
        """Get channel layout as enum."""
        return AudioChannelLayout.from_channel_count(self.channels)

    @property
    def bitrate_kbps(self) -> float:
        """Get bitrate in kilobits per second."""
        return self.bit_rate / 1000

    @property
    def duration_formatted(self) -> str:
        """Return duration in HH:MM:SS format."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def is_lossless(self) -> bool:
        """Check if this track uses a lossless codec."""
        lossless_codecs = {"flac", "alac", "pcm_s16le", "pcm_s24le", "pcm_s32le", "truehd", "mlp"}
        return self.codec.lower() in lossless_codecs

    @property
    def is_spatial(self) -> bool:
        """Check if this track has spatial audio channels."""
        return self.channels > 2

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "index": self.index,
            "codec": self.codec,
            "codec_long_name": self.codec_long_name,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "channel_layout": self.channel_layout,
            "bit_rate": self.bit_rate,
            "bitrate_kbps": self.bitrate_kbps,
            "duration": self.duration,
            "duration_formatted": self.duration_formatted,
            "language": self.language,
            "title": self.title,
            "is_default": self.is_default,
            "is_forced": self.is_forced,
            "is_lossless": self.is_lossless,
            "is_spatial": self.is_spatial,
            "disposition": self.disposition,
            "tags": self.tags,
        }


@dataclass
class AudioMetadata:
    """Complete audio metadata for a video file.

    Attributes:
        file_path: Path to the video file.
        has_audio: Whether the file contains audio.
        track_count: Number of audio tracks.
        tracks: List of AudioTrackInfo for each track.
        default_track_index: Index of the default audio track.
        total_duration: Total audio duration in seconds.
        overall_bitrate: Combined bitrate of all tracks.
    """

    file_path: Path
    has_audio: bool = False
    track_count: int = 0
    tracks: list[AudioTrackInfo] = field(default_factory=list)
    default_track_index: int = 0
    total_duration: float = 0.0
    overall_bitrate: int = 0

    @classmethod
    def extract_from_video(cls, video_path: Path | str) -> AudioMetadata:
        """Extract audio metadata from a video file using FFprobe.

        Args:
            video_path: Path to the video file.

        Returns:
            AudioMetadata with extracted information.

        Raises:
            AudioExtractionError: If metadata extraction fails.
        """
        file_path = Path(video_path).resolve()
        logger = _get_audio_logger()

        if not file_path.exists():
            raise AudioExtractionError(file_path, reason="File does not exist")

        try:
            # Run ffprobe to get audio stream information
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    "-select_streams",
                    "a",  # Audio streams only
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"FFprobe failed for {file_path}: {result.stderr}")
                return cls(file_path=file_path, has_audio=False)

            data = json.loads(result.stdout)
            streams = data.get("streams", [])

            if not streams:
                logger.debug(f"No audio streams found in {file_path}")
                return cls(file_path=file_path, has_audio=False)

            tracks = []
            default_track_index = 0
            total_duration = 0.0
            overall_bitrate = 0

            for stream in streams:
                # Extract disposition
                disposition = stream.get("disposition", {})
                disposition_dict = {
                    "default": disposition.get("default", 0) == 1,
                    "dub": disposition.get("dub", 0) == 1,
                    "original": disposition.get("original", 0) == 1,
                    "comment": disposition.get("comment", 0) == 1,
                    "lyrics": disposition.get("lyrics", 0) == 1,
                    "karaoke": disposition.get("karaoke", 0) == 1,
                    "forced": disposition.get("forced", 0) == 1,
                    "hearing_impaired": disposition.get("hearing_impaired", 0) == 1,
                }

                # Extract tags
                tags = stream.get("tags", {})

                track = AudioTrackInfo(
                    index=stream.get("index", 0),
                    codec=stream.get("codec_name", ""),
                    codec_long_name=stream.get("codec_long_name", ""),
                    sample_rate=int(stream.get("sample_rate", 48000) or 48000),
                    channels=int(stream.get("channels", 2) or 2),
                    channel_layout=stream.get("channel_layout", "stereo"),
                    bit_rate=int(stream.get("bit_rate", 0) or 0),
                    duration=float(stream.get("duration", 0) or 0),
                    language=tags.get("language", "und"),
                    title=tags.get("title", ""),
                    is_default=disposition_dict.get("default", False),
                    is_forced=disposition_dict.get("forced", False),
                    disposition=disposition_dict,
                    tags=tags,
                )
                tracks.append(track)

                if track.is_default:
                    default_track_index = track.index

                if track.duration > total_duration:
                    total_duration = track.duration

                overall_bitrate += track.bit_rate

            logger.debug(
                f"Found {len(tracks)} audio tracks in {file_path.name}, "
                f"duration: {total_duration:.2f}s"
            )

            return cls(
                file_path=file_path,
                has_audio=True,
                track_count=len(tracks),
                tracks=tracks,
                default_track_index=default_track_index,
                total_duration=total_duration,
                overall_bitrate=overall_bitrate,
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"FFprobe timed out for {file_path}")
            raise AudioExtractionError(file_path, reason="FFprobe timed out")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse FFprobe output: {e}")
            raise AudioExtractionError(file_path, reason=f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            raise AudioExtractionError(file_path, reason=str(e))

    def get_track(self, index: int) -> AudioTrackInfo | None:
        """Get audio track by index.

        Args:
            index: Track index.

        Returns:
            AudioTrackInfo if found, None otherwise.
        """
        for track in self.tracks:
            if track.index == index:
                return track
        return None

    def get_tracks_by_language(self, language: str) -> list[AudioTrackInfo]:
        """Get all tracks with a specific language.

        Args:
            language: Language code (e.g., 'en', 'es').

        Returns:
            List of matching tracks.
        """
        return [t for t in self.tracks if t.language == language]

    def get_default_track(self) -> AudioTrackInfo | None:
        """Get the default audio track.

        Returns:
            Default AudioTrackInfo if found, None otherwise.
        """
        return self.get_track(self.default_track_index)

    def get_track_indices(self) -> list[int]:
        """Get all track indices.

        Returns:
            List of track indices.
        """
        return [t.index for t in self.tracks]

    @property
    def has_multi_channel(self) -> bool:
        """Check if any track has more than 2 channels."""
        return any(t.channels > 2 for t in self.tracks)

    @property
    def has_spatial_audio(self) -> bool:
        """Check if any track is spatial (surround sound)."""
        return any(t.is_spatial for t in self.tracks)

    @property
    def has_multiple_tracks(self) -> bool:
        """Check if there are multiple audio tracks."""
        return self.track_count > 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": str(self.file_path),
            "has_audio": self.has_audio,
            "track_count": self.track_count,
            "tracks": [t.to_dict() for t in self.tracks],
            "default_track_index": self.default_track_index,
            "total_duration": self.total_duration,
            "overall_bitrate": self.overall_bitrate,
            "has_multi_channel": self.has_multi_channel,
            "has_spatial_audio": self.has_spatial_audio,
            "has_multiple_tracks": self.has_multiple_tracks,
        }
