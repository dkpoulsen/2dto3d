"""Audio track preservation for multi-track video files."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from video2d3d.audio.config import AudioConfig, AudioFormatConfig
from video2d3d.audio.constants import (
    check_ffmpeg_available,
    FFMPEG_EXTRACT_TIMEOUT,
    get_extension_for_codec,
    truncate_error_message,
)
from video2d3d.audio.exceptions import (
    AudioExtractionError,
    AudioTrackNotFoundError,
    AudioProcessingError,
)
from video2d3d.audio.metadata import AudioMetadata, AudioTrackInfo
from video2d3d.utils.logger import get_logger


_logger = get_logger("audio.tracks")

@dataclass
class TrackExtractionResult:
    """Result of extracting a single audio track.

    Attributes:
        track_index: Index of the extracted track.
        output_path: Path to the extracted audio file.
        codec: Codec used for the output.
        channels: Number of audio channels.
        duration: Duration in seconds.
        success: Whether extraction was successful.
        error_message: Error message if extraction failed.
    """

    track_index: int
    output_path: Optional[Path] = None
    codec: str = "aac"
    channels: int = 2
    duration: float = 0.0
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class TrackPreservationResult:
    """Result of preserving audio tracks from a video.

    Attributes:
        video_path: Path to the source video.
        extracted_tracks: List of TrackExtractionResult for each track.
        preserved_count: Number of successfully preserved tracks.
        failed_count: Number of failed extractions.
        temp_files: List of temporary files created.
    """

    video_path: Path
    extracted_tracks: List[TrackExtractionResult] = field(default_factory=list)
    preserved_count: int = 0
    failed_count: int = 0
    temp_files: List[Path] = field(default_factory=list)

    def get_successful_tracks(self) -> Dict[int, Path]:
        """Get mapping of track indices to their output paths.

        Returns:
            Dictionary mapping track index to output file path.
        """
        return {
            t.track_index: t.output_path
            for t in self.extracted_tracks
            if t.success and t.output_path
        }


class AudioTrackPreserver:
    """Preserve audio tracks from video files.

    This class handles the extraction and preservation of audio tracks
    from source videos, supporting multiple tracks, different codecs,
    and track selection.

    Example usage:
        ```python
        preserver = AudioTrackPreserver()
        result = preserver.preserve_tracks("input.mp4", output_dir="temp/")
        for track_result in result.extracted_tracks:
            if track_result.success:
                print(f"Track {track_result.track_index}: {track_result.output_path}")
        ```
    """

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        format_config: Optional[AudioFormatConfig] = None,
    ) -> None:
        """Initialize the audio track preserver.

        Args:
            config: Audio configuration.
            format_config: Audio format configuration.
        """
        self.config = config or AudioConfig()
        self.format_config = format_config or AudioFormatConfig()
        self._logger = _get_tracks_logger()

        # Check FFmpeg availability
        self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> None:
        """Check if FFmpeg is available."""
        if shutil.which("ffmpeg") is None:
            raise AudioProcessingError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
            )

    def extract_track(
        self,
        video_path: Path | str,
        track_index: int,
        output_path: Path | str,
        copy_codec: bool = True,
    ) -> TrackExtractionResult:
        """Extract a single audio track from a video file.

        Args:
            video_path: Path to the source video.
            track_index: Index of the audio track to extract.
            output_path: Path to save the extracted audio.
            copy_codec: Whether to copy the codec without re-encoding.

        Returns:
            TrackExtractionResult with extraction details.
        """
        video_path = Path(video_path).resolve()
        output_path = Path(output_path).resolve()

        if not video_path.exists():
            return TrackExtractionResult(
                track_index=track_index,
                success=False,
                error_message=f"Video file not found: {video_path}",
            )

        # Verify track exists
        metadata = AudioMetadata.extract_from_video(video_path)
        track_info = metadata.get_track(track_index)

        if track_info is None:
            return TrackExtractionResult(
                track_index=track_index,
                success=False,
                error_message=f"Track {track_index} not found in video",
            )

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-map",
                f"0:a:{track_index}",
            ]

            if copy_codec and not self._needs_reencoding(track_info):
                cmd.extend(["-c:a", "copy"])
            else:
                # Re-encode to configured format
                cmd.extend(self.format_config.to_ffmpeg_args())

            cmd.append(str(output_path))

            self._logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self._logger.error(f"Track extraction failed: {error_msg}")
                return TrackExtractionResult(
                    track_index=track_index,
                    success=False,
                    error_message=f"FFmpeg error: {error_msg}",
                )

            self._logger.info(f"Extracted audio track {track_index} to {output_path.name}")

            return TrackExtractionResult(
                track_index=track_index,
                output_path=output_path,
                codec=self.format_config.codec if not copy_codec else track_info.codec,
                channels=track_info.channels,
                duration=track_info.duration,
                success=True,
            )

        except subprocess.TimeoutExpired:
            error = "Track extraction timed out"
            self._logger.error(error)
            return TrackExtractionResult(
                track_index=track_index,
                success=False,
                error_message=error,
            )
        except Exception as e:
            error = f"Track extraction failed: {e}"
            self._logger.error(error)
            return TrackExtractionResult(
                track_index=track_index,
                success=False,
                error_message=error,
            )

    def _needs_reencoding(self, track_info: AudioTrackInfo) -> bool:
        """Check if a track needs re-encoding.

        Args:
            track_info: Track information.

        Returns:
            True if re-encoding is needed.
        """
        # Need to re-encode if target codec differs
        if self.format_config.codec != track_info.codec:
            return True

        # Need to re-encode if channel count differs
        if self.format_config.channels != track_info.channels:
            return True

        # Need to re-encode if sample rate differs
        if self.format_config.sample_rate != track_info.sample_rate:
            return True

        return False

    def preserve_tracks(
        self,
        video_path: Path | str,
        output_dir: Optional[Path | str] = None,
        tracks: Optional[List[int]] = None,
    ) -> TrackPreservationResult:
        """Preserve specified audio tracks from a video file.

        Args:
            video_path: Path to the source video.
            output_dir: Directory to save extracted tracks. If None, uses temp dir.
            tracks: List of track indices to preserve. If None, preserves all.

        Returns:
            TrackPreservationResult with preservation details.
        """
        video_path = Path(video_path).resolve()

        # Extract metadata
        metadata = AudioMetadata.extract_from_video(video_path)

        if not metadata.has_audio:
            self._logger.warning(f"No audio tracks found in {video_path}")
            return TrackPreservationResult(
                video_path=video_path,
                preserved_count=0,
                failed_count=0,
            )

        # Determine which tracks to preserve
        if tracks is None:
            if self.config.tracks_to_preserve:
                tracks = self.config.tracks_to_preserve
            else:
                tracks = metadata.get_track_indices()

        # Create output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="audio_tracks_"))
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        result = TrackPreservationResult(
            video_path=video_path,
            temp_files=[],
        )

        for track_index in tracks:
            # Verify track exists
            track_info = metadata.get_track(track_index)
            if track_info is None:
                self._logger.warning(f"Track {track_index} not found, skipping")
                result.extracted_tracks.append(
                    TrackExtractionResult(
                        track_index=track_index,
                        success=False,
                        error_message="Track not found",
                    )
                )
                result.failed_count += 1
                continue

            # Determine output path
            ext = self._get_extension_for_codec(self.format_config.codec)
            output_path = output_dir / f"track_{track_index}.{ext}"

            # Extract track
            track_result = self.extract_track(
                video_path=video_path,
                track_index=track_index,
                output_path=output_path,
                copy_codec=self.config.preserve_tracks,
            )

            result.extracted_tracks.append(track_result)
            if track_result.success:
                result.preserved_count += 1
                result.temp_files.append(output_path)
            else:
                result.failed_count += 1

        self._logger.info(
            f"Preserved {result.preserved_count}/{len(tracks)} audio tracks from {video_path.name}"
        )

        return result

    def _get_extension_for_codec(self, codec: str) -> str:
        """Get file extension for a codec.

        Args:
            codec: Codec name.

        Returns:
            File extension without dot.
        """
        extension_map = {
            "aac": "m4a",
            "opus": "opus",
            "mp3": "mp3",
            "flac": "flac",
            "pcm_s16le": "wav",
            "pcm_s24le": "wav",
            "ac3": "ac3",
            "eac3": "eac3",
            "truehd": "thd",
        }
        return extension_map.get(codec, "m4a")

    def cleanup_temp_files(self, files: List[Path]) -> None:
        """Clean up temporary audio files.

        Args:
            files: List of file paths to remove.
        """
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self._logger.debug(f"Removed temporary file: {file_path}")
            except OSError as e:
                self._logger.warning(f"Failed to remove {file_path}: {e}")

    def get_default_track(
        self,
        video_path: Path | str,
        output_path: Path | str,
    ) -> TrackExtractionResult:
        """Extract the default audio track from a video.

        Args:
            video_path: Path to the source video.
            output_path: Path to save the extracted audio.

        Returns:
            TrackExtractionResult with extraction details.
        """
        video_path = Path(video_path).resolve()

        # Get metadata to find default track
        metadata = AudioMetadata.extract_from_video(video_path)

        if not metadata.has_audio:
            return TrackExtractionResult(
                track_index=0,
                success=False,
                error_message="No audio tracks found",
            )

        return self.extract_track(
            video_path=video_path,
            track_index=metadata.default_track_index,
            output_path=output_path,
        )
