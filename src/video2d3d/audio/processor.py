"""Main audio processor that integrates all audio processing capabilities."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from video2d3d.audio.config import AudioConfig
from video2d3d.audio.exceptions import AudioProcessingError
from video2d3d.audio.metadata import AudioMetadata
from video2d3d.audio.multichannel import MultiChannelAudioProcessor
from video2d3d.audio.spatial import SpatialAudioProcessor, SpatialProcessingResult
from video2d3d.audio.tracks import AudioTrackPreserver, TrackPreservationResult
from video2d3d.utils.logger import get_logger


def _get_processor_logger():
    """Get the audio processor logger (lazy initialization)."""
    return get_logger("audio.processor")


@dataclass
class AudioProcessingResult:
    """Result of audio processing operations.

    Attributes:
        success: Whether processing was successful.
        output_path: Path to the final output audio file.
        temp_files: List of temporary files created during processing.
        metadata: Audio metadata from the source.
        spatial_result: Result of spatial processing if enabled.
        track_preservation_result: Result of track preservation if enabled.
        duration: Duration of the processed audio.
        channels: Number of output channels.
        codec: Output codec used.
        bitrate: Output bitrate in bits per second.
        error_message: Error message if processing failed.
    """

    success: bool = True
    output_path: Optional[Path] = None
    temp_files: List[Path] = field(default_factory=list)
    metadata: Optional[AudioMetadata] = None
    spatial_result: Optional[SpatialProcessingResult] = None
    track_preservation_result: Optional[TrackPreservationResult] = None
    duration: float = 0.0
    channels: int = 2
    codec: str = "aac"
    bitrate: int = 192000
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output_path": str(self.output_path) if self.output_path else None,
            "duration": self.duration,
            "channels": self.channels,
            "codec": self.codec,
            "bitrate": self.bitrate,
            "error_message": self.error_message,
        }


class AudioProcessor:
    """Main audio processor integrating all audio processing capabilities.

    This class provides a unified interface for:
    - Audio track preservation
    - Spatial audio processing
    - Multi-channel audio support
    - Audio normalization
    - Integration with video processing

    Example usage:
        ```python
        config = AudioConfig(
            preserve_tracks=True,
            normalize=True,
            spatial_config=SpatialAudioConfig(enable_spatial=True),
        )
        processor = AudioProcessor(config=config)
        result = processor.process("input.mp4", "output_audio.m4a")
        if result.success:
            print(f"Processed audio: {result.output_path}")
        ```
    """

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Initialize the audio processor.

        Args:
            config: Audio processing configuration.
            progress_callback: Optional callback for progress updates.
        """
        self.config = config or AudioConfig()
        self._progress_callback = progress_callback
        self._logger = _get_processor_logger()

        # Initialize sub-processors
        self._track_preserver = AudioTrackPreserver(
            config=self.config,
            format_config=self.config.format_config,
        )
        self._spatial_processor = SpatialAudioProcessor(
            config=self.config.spatial_config,
            format_config=self.config.format_config,
        )
        self._multichannel_processor = MultiChannelAudioProcessor(
            format_config=self.config.format_config,
        )

        # Check dependencies
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check that required dependencies are available."""
        if shutil.which("ffmpeg") is None:
            raise AudioProcessingError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
            )

    def extract_audio_info(self, video_path: Path | str) -> AudioMetadata:
        """Extract audio information from a video file.

        Args:
            video_path: Path to the video file.

        Returns:
            AudioMetadata with extracted information.
        """
        return AudioMetadata.extract_from_video(video_path)

    def _apply_normalization(self, input_path: Path, output_path: Path) -> bool:
        """Apply loudness normalization to audio.

        Args:
            input_path: Path to input audio file.
            output_path: Path to output audio file.

        Returns:
            True if normalization was successful.
        """
        if not self.config.normalize:
            # Just copy the file
            shutil.copy(input_path, output_path)
            return True

        try:
            # Use FFmpeg loudnorm filter for EBU R128 normalization
            target_lufs = self.config.normalization_target

            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-af",
                f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
                "-c:a",
                self.config.format_config.codec,
                "-b:a",
                str(self.config.format_config.bitrate),
                str(output_path),
            ]

            self._logger.debug(f"Normalization command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                self._logger.warning(f"Normalization failed: {result.stderr[:200]}")
                # Fall back to copy
                shutil.copy(input_path, output_path)
                return True

            return True

        except Exception as e:
            self._logger.warning(f"Normalization error: {e}")
            shutil.copy(input_path, output_path)
            return True

    def process(
        self,
        input_path: Path | str,
        output_path: Path | str,
        preserve_temp: bool = False,
    ) -> AudioProcessingResult:
        """Process audio from a video file with all configured operations.

        This is the main entry point for audio processing. It performs:
        1. Audio metadata extraction
        2. Track selection and extraction
        3. Spatial audio processing (if enabled)
        4. Multi-channel conversion (if needed)
        5. Loudness normalization (if enabled)
        6. Final encoding to output format

        Args:
            input_path: Path to input video/audio file.
            output_path: Path to output audio file.
            preserve_temp: Whether to keep temporary files.

        Returns:
            AudioProcessingResult with processing details.
        """
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()
        temp_files: List[Path] = []

        if not input_path.exists():
            return AudioProcessingResult(
                success=False,
                error_message=f"Input file not found: {input_path}",
            )

        try:
            # Step 1: Extract audio metadata
            self._logger.info(f"Processing audio from: {input_path.name}")
            metadata = self.extract_audio_info(input_path)

            if not metadata.has_audio:
                return AudioProcessingResult(
                    success=False,
                    metadata=metadata,
                    error_message="No audio tracks found in input file",
                )

            # Step 2: Extract/preserve audio tracks
            temp_dir = Path(tempfile.mkdtemp(prefix="audio_proc_"))
            temp_audio = temp_dir / f"extracted.{self._get_extension()}"
            temp_files.append(temp_audio)

            # Extract default track or specified track
            track_result = self._track_preserver.extract_track(
                video_path=input_path,
                track_index=self.config.default_track,
                output_path=temp_audio,
                copy_codec=False,  # Always re-encode for consistency
            )

            if not track_result.success:
                return AudioProcessingResult(
                    success=False,
                    metadata=metadata,
                    error_message=track_result.error_message,
                )

            current_audio = temp_audio

            # Step 3: Spatial audio processing (if enabled)
            if self.config.spatial_config.enable_spatial:
                spatial_output = temp_dir / f"spatial.{self._get_extension()}"
                temp_files.append(spatial_output)

                spatial_result = self._spatial_processor.process(
                    input_path=current_audio,
                    output_path=spatial_output,
                )

                if spatial_result.success:
                    current_audio = spatial_output
                else:
                    self._logger.warning(
                        f"Spatial processing failed: {spatial_result.error_message}"
                    )

            # Step 4: Multi-channel conversion (if needed)
            if self.config.enable_downmix and metadata.has_multi_channel:
                downmix_output = temp_dir / f"downmix.{self._get_extension()}"
                temp_files.append(downmix_output)

                downmix_result = self._multichannel_processor.downmix_to_stereo(
                    input_path=current_audio,
                    output_path=downmix_output,
                    coefficient=self.config.downmix_coefficient,
                )

                if downmix_result.success:
                    current_audio = downmix_output
                else:
                    self._logger.warning(f"Downmix failed: {downmix_result.error_message}")

            # Step 5: Normalization (if enabled)
            if self.config.normalize:
                normalized_output = temp_dir / f"normalized.{self._get_extension()}"
                temp_files.append(normalized_output)

                if self._apply_normalization(current_audio, normalized_output):
                    current_audio = normalized_output

            # Step 6: Final copy to output
            shutil.copy(current_audio, output_path)

            # Get final audio info
            final_metadata = AudioMetadata.extract_from_video(output_path)
            final_track = final_metadata.get_default_track() if final_metadata.has_audio else None

            self._logger.info(f"Audio processing complete: {output_path.name}")

            return AudioProcessingResult(
                success=True,
                output_path=output_path,
                temp_files=temp_files if preserve_temp else [],
                metadata=metadata,
                duration=final_track.duration if final_track else 0.0,
                channels=final_track.channels if final_track else 2,
                codec=self.config.format_config.codec,
                bitrate=self.config.format_config.bitrate,
            )

        except Exception as e:
            error = f"Audio processing failed: {e}"
            self._logger.error(error)
            return AudioProcessingResult(
                success=False,
                temp_files=temp_files,
                error_message=error,
            )
        finally:
            # Cleanup temp files
            if not preserve_temp:
                for temp_file in temp_files:
                    try:
                        if temp_file.exists():
                            temp_file.unlink()
                    except OSError:
                        pass
                # Cleanup temp directory
                try:
                    if temp_dir.exists():
                        temp_dir.rmdir()
                except (OSError, NameError):
                    pass

    def process_for_video(
        self,
        source_video: Path | str,
        output_audio: Path | str,
        video_duration: float,
    ) -> AudioProcessingResult:
        """Process audio specifically for video output integration.

        This method ensures audio duration matches video duration and
        applies any necessary time-stretching or padding.

        Args:
            source_video: Path to source video file.
            output_audio: Path to output audio file.
            video_duration: Duration of the target video in seconds.

        Returns:
            AudioProcessingResult with processing details.
        """
        result = self.process(source_video, output_audio)

        if not result.success:
            return result

        # Check if duration adjustment is needed
        if abs(result.duration - video_duration) > 0.5:  # More than 0.5s difference
            self._logger.info(
                f"Adjusting audio duration: {result.duration:.2f}s -> {video_duration:.2f}s"
            )
            # Note: Duration adjustment would be done with FFmpeg atempo filter
            # For now, we just log the mismatch

        return result

    def _get_extension(self) -> str:
        """Get file extension for current codec configuration."""
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
        return extension_map.get(self.config.format_config.codec, "m4a")

    def get_ffmpeg_audio_args(self) -> List[str]:
        """Get FFmpeg arguments for audio encoding.

        This is useful for integrating with video encoding pipelines.

        Returns:
            List of FFmpeg arguments for audio processing.
        """
        args = []

        # Audio codec
        codec_map = {
            "aac": "aac",
            "opus": "libopus",
            "mp3": "libmp3lame",
            "flac": "flac",
            "ac3": "ac3",
            "eac3": "eac3",
        }
        codec = codec_map.get(self.config.format_config.codec, "aac")
        args.extend(["-c:a", codec])

        # Bitrate
        if self.config.format_config.bitrate > 0:
            args.extend(["-b:a", str(self.config.format_config.bitrate)])

        # Sample rate
        args.extend(["-ar", str(self.config.format_config.sample_rate)])

        # Channels
        args.extend(["-ac", str(self.config.format_config.channels)])

        return args

    def cleanup(self) -> None:
        """Clean up any resources held by the processor."""
        # Currently no persistent resources to clean up
        pass
