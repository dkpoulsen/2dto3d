"""Spatial audio processing using FFmpeg filters."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from video2d3d.audio.config import AudioFormatConfig, SpatialAudioConfig, SpatialAudioFormat
from video2d3d.audio.exceptions import SpatialAudioError
from video2d3d.utils.logger import get_logger


def _get_spatial_logger():
    """Get the spatial audio logger (lazy initialization)."""
    return get_logger("audio.spatial")


@dataclass
class SpatialProcessingResult:
    """Result of spatial audio processing.

    Attributes:
        success: Whether processing was successful.
        output_path: Path to the output audio file.
        spatial_format: The spatial format used.
        channels: Number of output channels.
        duration: Duration of the processed audio.
        error_message: Error message if processing failed.
    """

    success: bool = True
    output_path: Optional[Path] = None
    spatial_format: SpatialAudioFormat = SpatialAudioFormat.NONE
    channels: int = 2
    duration: float = 0.0
    error_message: Optional[str] = None


class SpatialAudioProcessor:
    """Process audio for 3D spatial audio output.

    This class handles the conversion of stereo audio to various spatial
    audio formats including binaural (HRTF), Ambisonics, and other 3D formats.

    Example usage:
        ```python
        config = SpatialAudioConfig(
            enable_spatial=True,
            spatial_format=SpatialAudioFormat.BINAURAL,
            room_size="medium",
        )
        processor = SpatialAudioProcessor(config=config)
        result = processor.process("input_audio.aac", "output_spatial.m4a")
        if result.success:
            print(f"Spatial audio saved to: {result.output_path}")
        ```
    """

    # Room size presets (in meters)
    ROOM_PRESETS = {
        "small": {"size": 5, "damping": 0.8},
        "medium": {"size": 15, "damping": 0.5},
        "large": {"size": 30, "damping": 0.3},
        "cathedral": {"size": 100, "damping": 0.1},
    }

    def __init__(
        self,
        config: Optional[SpatialAudioConfig] = None,
        format_config: Optional[AudioFormatConfig] = None,
    ) -> None:
        """Initialize the spatial audio processor.

        Args:
            config: Spatial audio configuration.
            format_config: Audio format configuration for output.
        """
        self.config = config or SpatialAudioConfig()
        self.format_config = format_config or AudioFormatConfig()
        self._logger = _get_spatial_logger()

        # Check FFmpeg availability
        self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> None:
        """Check if FFmpeg is available."""
        if shutil.which("ffmpeg") is None:
            raise SpatialAudioError(
                "initialization",
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.",
            )

    def _build_binaural_filter(self) -> List[str]:
        """Build FFmpeg filter chain for binaural rendering.

        Returns:
            List of FFmpeg filter arguments.
        """
        filters = []

        # Get room preset
        room = self.ROOM_PRESETS.get(self.config.room_size, self.ROOM_PRESETS["medium"])

        # Calculate interaural time difference (ITD) based on source position
        x, y, z = self.config.source_position
        import math

        # Azimuth angle in degrees (-180 to 180)
        azimuth = math.degrees(math.atan2(x, z))
        # Elevation angle in degrees (-90 to 90)
        elevation = math.degrees(math.atan2(y, math.sqrt(x * x + z * z)))

        self._logger.debug(f"Calculated azimuth: {azimuth:.1f}°, elevation: {elevation:.1f}°")

        # Simple binaural simulation using delay and filtering
        # ITD is approximately 0.7ms max for human head
        max_itd_ms = 0.7
        itd_left = max_itd_ms * max(0, -math.sin(math.radians(azimuth)))
        itd_right = max_itd_ms * max(0, math.sin(math.radians(azimuth)))

        # Apply delays based on source position
        # For a source on the left, right ear gets delayed
        if abs(azimuth) > 1:  # More than 1 degree off-center
            # Use adelay filter (delays in milliseconds)
            delay_left = int(itd_left * 10)  # Convert to centiseconds for adelay
            delay_right = int(itd_right * 10)
            filters.append(f"adelay={delay_left}c:{delay_right}c")

        # Apply head shadow effect using low-pass filter on the far ear
        # This simulates the head blocking high frequencies
        if self.config.room_size != "small":
            # Add slight room reverb for larger spaces
            reverb_amount = int(self.config.reverb_amount * 100)
            filters.append("aecho=1.0:0.6:20:0.3")

        return filters

    def _build_ambisonics_filter(self) -> List[str]:
        """Build FFmpeg filter chain for Ambisonics encoding.

        Returns:
            List of FFmpeg filter arguments.
        """
        filters = []

        # Get channel count based on Ambisonics order
        channel_counts = {
            SpatialAudioFormat.AMBISONICS_1ST: 4,  # W, Y, Z, X
            SpatialAudioFormat.AMBISONICS_2ND: 9,  # + R, S, T, U, V
            SpatialAudioFormat.AMBISONICS_3RD: 16,  # + K, L, M, N, O, P, Q
        }
        channels = channel_counts.get(self.config.spatial_format, 4)

        # For basic stereo-to-Ambisonics conversion
        # We use a simple approach: distribute stereo into Ambisonics B-format
        # This is not a proper spatializer, but provides compatibility

        # Set output channel layout
        filters.append(f"aformat=channel_layouts={channels}c")

        return filters

    def _build_spatial_filter_chain(self) -> str:
        """Build the complete spatial audio filter chain.

        Returns:
            FFmpeg filter chain string.
        """
        if not self.config.enable_spatial:
            return ""

        filters = []

        if self.config.spatial_format == SpatialAudioFormat.BINAURAL:
            filters.extend(self._build_binaural_filter())
        elif self.config.spatial_format.is_ambisonics:
            filters.extend(self._build_ambisonics_filter())

        # Add loudness normalization if enabled
        # (handled separately in main processor)

        return ",".join(filters) if filters else ""

    def process(
        self,
        input_path: Path | str,
        output_path: Path | str,
        additional_filters: Optional[List[str]] = None,
    ) -> SpatialProcessingResult:
        """Process audio with spatial audio effects.

        Args:
            input_path: Path to input audio/video file.
            output_path: Path to output audio file.
            additional_filters: Additional FFmpeg filters to apply.

        Returns:
            SpatialProcessingResult with processing details.
        """
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()

        if not input_path.exists():
            return SpatialProcessingResult(
                success=False,
                error_message=f"Input file not found: {input_path}",
            )

        try:
            # Build FFmpeg command
            cmd = ["ffmpeg", "-y", "-i", str(input_path)]

            # Build filter chain
            filters = []
            spatial_filter = self._build_spatial_filter_chain()
            if spatial_filter:
                filters.append(spatial_filter)

            if additional_filters:
                filters.extend(additional_filters)

            if filters:
                cmd.extend(["-af", ",".join(filters)])

            # Add output format arguments
            cmd.extend(self.format_config.to_ffmpeg_args())

            # Output file
            cmd.append(str(output_path))

            self._logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self._logger.error(f"FFmpeg failed: {error_msg}")
                return SpatialProcessingResult(
                    success=False,
                    error_message=f"FFmpeg error: {error_msg}",
                )

            # Get output duration
            duration = self._get_audio_duration(output_path)

            self._logger.info(f"Spatial audio processing complete: {output_path.name}")

            return SpatialProcessingResult(
                success=True,
                output_path=output_path,
                spatial_format=self.config.spatial_format,
                channels=self.format_config.channels,
                duration=duration,
            )

        except subprocess.TimeoutExpired:
            error = "Spatial audio processing timed out"
            self._logger.error(error)
            return SpatialProcessingResult(
                success=False,
                error_message=error,
            )
        except Exception as e:
            error = f"Spatial audio processing failed: {e}"
            self._logger.error(error)
            return SpatialProcessingResult(
                success=False,
                error_message=error,
            )

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration using FFprobe.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, ValueError):
            pass
        return 0.0

    def process_video_audio(
        self,
        video_path: Path | str,
        output_audio_path: Path | str,
    ) -> SpatialProcessingResult:
        """Extract and process video audio track with spatial effects.

        Args:
            video_path: Path to input video file.
            output_audio_path: Path to output audio file.

        Returns:
            SpatialProcessingResult with processing details.
        """
        return self.process(video_path, output_audio_path)

    def get_output_channel_count(self) -> int:
        """Get the expected output channel count for the current configuration.

        Returns:
            Number of output channels.
        """
        if not self.config.enable_spatial:
            return self.format_config.channels

        channel_map = {
            SpatialAudioFormat.BINAURAL: 2,
            SpatialAudioFormat.AMBISONICS_1ST: 4,
            SpatialAudioFormat.AMBISONICS_2ND: 9,
            SpatialAudioFormat.AMBISONICS_3RD: 16,
            SpatialAudioFormat.DOLBY_ATMOS: 8,  # Typically 7.1.4 bed
            SpatialAudioFormat.MPEG_H: 8,
        }
        return channel_map.get(self.config.spatial_format, 2)
