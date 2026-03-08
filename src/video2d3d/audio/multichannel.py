"""Multi-channel audio processing for surround sound support."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from video2d3d.audio.config import AudioChannelLayout, AudioFormatConfig
from video2d3d.audio.exceptions import AudioProcessingError
from video2d3d.audio.metadata import AudioMetadata
from video2d3d.utils.logger import get_logger


def _get_multichannel_logger():
    """Get the multichannel audio logger (lazy initialization)."""
    return get_logger("audio.multichannel")


@dataclass
class DownmixResult:
    """Result of audio downmix operation.

    Attributes:
        success: Whether downmix was successful.
        output_path: Path to the output audio file.
        input_channels: Number of input channels.
        output_channels: Number of output channels.
        input_layout: Input channel layout.
        output_layout: Output channel layout.
        error_message: Error message if downmix failed.
    """

    success: bool = True
    output_path: Optional[Path] = None
    input_channels: int = 6
    output_channels: int = 2
    input_layout: AudioChannelLayout = AudioChannelLayout.SURROUND_5_1
    output_layout: AudioChannelLayout = AudioChannelLayout.STEREO
    error_message: Optional[str] = None


class MultiChannelAudioProcessor:
    """Process multi-channel audio for surround sound support.

    This class handles:
    - Downmixing multi-channel audio to stereo
    - Upmixing stereo to multi-channel (basic)
    - Channel layout conversion
    - Surround sound format handling

    Example usage:
        ```python
        processor = MultiChannelAudioProcessor()
        result = processor.downmix_to_stereo(
            "input_51.ac3",
            "output_stereo.m4a",
            coefficient=0.707
        )
        if result.success:
            print(f"Downmixed {result.input_channels}ch to {result.output_channels}ch")
        ```
    """

    # Standard downmix coefficients
    DOWNMIX_COEFFICIENTS = {
        # Stereo downmix from surround
        "5.1_to_stereo": {
            "center": 0.707,  # -3dB
            "surround": 0.5,  # -6dB
            "lfe": 0.5,  # -6dB (typically omitted or mixed lower)
        },
        "7.1_to_stereo": {
            "center": 0.707,
            "side_surround": 0.5,
            "rear_surround": 0.35,  # -9dB
            "lfe": 0.5,
        },
        "5.1_to_2.1": {
            "center": 0.707,
            "surround": 0.5,
        },
    }

    def __init__(
        self,
        format_config: Optional[AudioFormatConfig] = None,
    ) -> None:
        """Initialize the multi-channel audio processor.

        Args:
            format_config: Audio format configuration for output.
        """
        self.format_config = format_config or AudioFormatConfig()
        self._logger = _get_multichannel_logger()

        # Check FFmpeg availability
        self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> None:
        """Check if FFmpeg is available."""
        if shutil.which("ffmpeg") is None:
            raise AudioProcessingError(
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
            )

    def _build_downmix_filter(
        self,
        input_channels: int,
        output_channels: int,
        coefficient: float = 0.707,
    ) -> str:
        """Build FFmpeg filter for downmixing audio.

        Args:
            input_channels: Number of input channels.
            output_channels: Number of output channels.
            coefficient: Downmix coefficient for non-front channels.

        Returns:
            FFmpeg filter string.
        """
        if output_channels >= input_channels:
            return ""  # No downmix needed

        filters = []

        if input_channels == 6 and output_channels == 2:
            # 5.1 to stereo downmix
            # Standard Dolby downmix: L = FL + 0.707*C + 0.707*RL + 0.707*RR
            #                         R = FR + 0.707*C + 0.707*RL - 0.707*RR
            filters.append(
                f"pan=stereo|"
                f"c0=c0+{coefficient}*c2+{coefficient}*c4|"
                f"c1=c1+{coefficient}*c2+{coefficient}*c5"
            )
        elif input_channels == 8 and output_channels == 2:
            # 7.1 to stereo downmix
            filters.append(
                f"pan=stereo|"
                f"c0=c0+{coefficient}*c2+{coefficient}*c4+{coefficient}*c6|"
                f"c1=c1+{coefficient}*c2+{coefficient}*c5+{coefficient}*c7"
            )
        elif input_channels == 6 and output_channels == 3:
            # 5.1 to 2.1 (stereo + LFE)
            filters.append(f"pan=2.1|c0=c0+{coefficient}*c2|c1=c1+{coefficient}*c2|c2=c3")
        else:
            # Generic downmix using aformat
            filters.append(f"aformat=channel_layouts={output_channels}c")

        return ",".join(filters)

    def _build_upmix_filter(
        self,
        input_channels: int,
        output_channels: int,
    ) -> str:
        """Build FFmpeg filter for upmixing audio.

        Note: This provides basic upmixing, not true spatial upmixing.

        Args:
            input_channels: Number of input channels.
            output_channels: Number of output channels.

        Returns:
            FFmpeg filter string.
        """
        if input_channels >= output_channels:
            return ""  # No upmix needed

        filters = []

        if input_channels == 1 and output_channels == 2:
            # Mono to stereo (duplicate)
            filters.append("aformat=channel_layouts=stereo")
        elif input_channels == 2 and output_channels == 6:
            # Stereo to 5.1 (basic matrix upmix)
            # This is a simple upmix, not ProLogic or similar
            filters.append(
                "pan=5.1|"
                "c0=c0|"  # FL from L
                "c1=c1|"  # FR from R
                "c2=c0+c1|"  # C from L+R
                "c3=0|"  # LFE (empty)
                "c4=c0|"  # BL from L
                "c5=c1"  # BR from R
            )
        elif input_channels == 2 and output_channels == 8:
            # Stereo to 7.1
            filters.append(
                "pan=7.1|"
                "c0=c0|"  # FL from L
                "c1=c1|"  # FR from R
                "c2=c0+c1|"  # C from L+R
                "c3=0|"  # LFE (empty)
                "c4=c0|"  # BL from L
                "c5=c1|"  # BR from R
                "c6=c0|"  # SL from L
                "c7=c1"  # SR from R
            )
        else:
            # Generic channel layout change
            filters.append(f"aformat=channel_layouts={output_channels}c")

        return ",".join(filters)

    def downmix_to_stereo(
        self,
        input_path: Path | str,
        output_path: Path | str,
        coefficient: float = 0.707,
    ) -> DownmixResult:
        """Downmix multi-channel audio to stereo.

        Args:
            input_path: Path to input audio/video file.
            output_path: Path to output audio file.
            coefficient: Downmix coefficient for non-front channels.

        Returns:
            DownmixResult with operation details.
        """
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()

        if not input_path.exists():
            return DownmixResult(
                success=False,
                error_message=f"Input file not found: {input_path}",
            )

        try:
            # Get input audio info
            metadata = AudioMetadata.extract_from_video(input_path)
            if not metadata.has_audio:
                return DownmixResult(
                    success=False,
                    error_message="No audio found in input file",
                )

            track = metadata.get_default_track()
            if track is None:
                return DownmixResult(
                    success=False,
                    error_message="No default audio track found",
                )

            input_channels = track.channels
            input_layout = track.channel_layout_enum

            # Build FFmpeg command
            cmd = ["ffmpeg", "-y", "-i", str(input_path)]

            # Build downmix filter
            filter_chain = self._build_downmix_filter(
                input_channels=input_channels,
                output_channels=2,
                coefficient=coefficient,
            )

            if filter_chain:
                cmd.extend(["-af", filter_chain])

            # Add output format arguments (force stereo)
            output_format = AudioFormatConfig(
                codec=self.format_config.codec,
                bitrate=self.format_config.bitrate,
                sample_rate=self.format_config.sample_rate,
                channels=2,
                channel_layout=AudioChannelLayout.STEREO,
            )
            cmd.extend(output_format.to_ffmpeg_args())

            cmd.append(str(output_path))

            self._logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self._logger.error(f"Downmix failed: {error_msg}")
                return DownmixResult(
                    success=False,
                    input_channels=input_channels,
                    input_layout=input_layout,
                    error_message=f"FFmpeg error: {error_msg}",
                )

            self._logger.info(f"Downmixed {input_channels}ch to 2ch: {output_path.name}")

            return DownmixResult(
                success=True,
                output_path=output_path,
                input_channels=input_channels,
                output_channels=2,
                input_layout=input_layout,
                output_layout=AudioChannelLayout.STEREO,
            )

        except subprocess.TimeoutExpired:
            error = "Downmix operation timed out"
            self._logger.error(error)
            return DownmixResult(success=False, error_message=error)
        except Exception as e:
            error = f"Downmix failed: {e}"
            self._logger.error(error)
            return DownmixResult(success=False, error_message=error)

    def upmix_to_surround(
        self,
        input_path: Path | str,
        output_path: Path | str,
        target_layout: AudioChannelLayout = AudioChannelLayout.SURROUND_5_1,
    ) -> DownmixResult:
        """Upmix audio to surround sound.

        Note: This provides basic channel routing, not true spatial upmixing.

        Args:
            input_path: Path to input audio/video file.
            output_path: Path to output audio file.
            target_layout: Target channel layout.

        Returns:
            DownmixResult with operation details.
        """
        input_path = Path(input_path).resolve()
        output_path = Path(output_path).resolve()

        if not input_path.exists():
            return DownmixResult(
                success=False,
                error_message=f"Input file not found: {input_path}",
            )

        try:
            # Get input audio info
            metadata = AudioMetadata.extract_from_video(input_path)
            if not metadata.has_audio:
                return DownmixResult(
                    success=False,
                    error_message="No audio found in input file",
                )

            track = metadata.get_default_track()
            if track is None:
                return DownmixResult(
                    success=False,
                    error_message="No default audio track found",
                )

            input_channels = track.channels
            input_layout = track.channel_layout_enum
            output_channels = target_layout.channel_count

            # Build FFmpeg command
            cmd = ["ffmpeg", "-y", "-i", str(input_path)]

            # Build upmix filter
            filter_chain = self._build_upmix_filter(
                input_channels=input_channels,
                output_channels=output_channels,
            )

            if filter_chain:
                cmd.extend(["-af", filter_chain])

            # Add output format arguments
            output_format = AudioFormatConfig(
                codec=self.format_config.codec,
                bitrate=self.format_config.bitrate,
                sample_rate=self.format_config.sample_rate,
                channels=output_channels,
                channel_layout=target_layout,
            )
            cmd.extend(output_format.to_ffmpeg_args())

            cmd.append(str(output_path))

            self._logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self._logger.error(f"Upmix failed: {error_msg}")
                return DownmixResult(
                    success=False,
                    input_channels=input_channels,
                    input_layout=input_layout,
                    error_message=f"FFmpeg error: {error_msg}",
                )

            self._logger.info(
                f"Upmixed {input_channels}ch to {output_channels}ch: {output_path.name}"
            )

            return DownmixResult(
                success=True,
                output_path=output_path,
                input_channels=input_channels,
                output_channels=output_channels,
                input_layout=input_layout,
                output_layout=target_layout,
            )

        except subprocess.TimeoutExpired:
            error = "Upmix operation timed out"
            self._logger.error(error)
            return DownmixResult(success=False, error_message=error)
        except Exception as e:
            error = f"Upmix failed: {e}"
            self._logger.error(error)
            return DownmixResult(success=False, error_message=error)

    def convert_channel_layout(
        self,
        input_path: Path | str,
        output_path: Path | str,
        target_layout: AudioChannelLayout,
    ) -> DownmixResult:
        """Convert audio to a different channel layout.

        Args:
            input_path: Path to input audio/video file.
            output_path: Path to output audio file.
            target_layout: Target channel layout.

        Returns:
            DownmixResult with operation details.
        """
        input_path = Path(input_path).resolve()
        metadata = AudioMetadata.extract_from_video(input_path)

        if not metadata.has_audio:
            return DownmixResult(
                success=False,
                error_message="No audio found in input file",
            )

        track = metadata.get_default_track()
        if track is None:
            return DownmixResult(
                success=False,
                error_message="No default audio track found",
            )

        input_channels = track.channels

        if input_channels > target_layout.channel_count:
            return self.downmix_to_stereo(
                input_path,
                output_path,
                coefficient=0.707,
            )
        elif input_channels < target_layout.channel_count:
            return self.upmix_to_surround(
                input_path,
                output_path,
                target_layout=target_layout,
            )
        else:
            # Same channel count, just copy
            import shutil as sh

            sh.copy(input_path, output_path)
            return DownmixResult(
                success=True,
                output_path=output_path,
                input_channels=input_channels,
                output_channels=input_channels,
                input_layout=track.channel_layout_enum,
                output_layout=target_layout,
            )

    def get_optimal_layout(
        self,
        metadata: AudioMetadata,
        prefer_surround: bool = False,
    ) -> AudioChannelLayout:
        """Get optimal channel layout based on source and preferences.

        Args:
            metadata: Audio metadata from source video.
            prefer_surround: Whether to prefer surround sound layouts.

        Returns:
            Recommended AudioChannelLayout.
        """
        if not metadata.has_audio:
            return AudioChannelLayout.STEREO

        track = metadata.get_default_track()
        if track is None:
            return AudioChannelLayout.STEREO

        source_layout = track.channel_layout_enum

        if prefer_surround and source_layout.channel_count >= 6:
            return source_layout

        # Default to stereo for maximum compatibility
        return AudioChannelLayout.STEREO
