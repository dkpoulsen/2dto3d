"""Audio processing configuration dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AudioChannelLayout(Enum):
    """Supported audio channel layouts."""

    MONO = "mono"  # 1 channel
    STEREO = "stereo"  # 2 channels (L, R)
    STEREO_2_1 = "2.1"  # 3 channels (L, R, LFE)
    QUAD = "quad"  # 4 channels (L, R, BL, BR)
    SURROUND_5_0 = "5.0"  # 5 channels (L, R, C, BL, BR)
    SURROUND_5_1 = "5.1"  # 6 channels (L, R, C, LFE, BL, BR)
    SURROUND_7_0 = "7.0"  # 7 channels (L, R, C, BL, BR, SL, SR)
    SURROUND_7_1 = "7.1"  # 8 channels (L, R, C, LFE, BL, BR, SL, SR)

    @classmethod
    def from_channel_count(cls, count: int) -> AudioChannelLayout:
        """Get channel layout from channel count.

        Args:
            count: Number of audio channels.

        Returns:
            Corresponding AudioChannelLayout.
        """
        layout_map = {
            1: cls.MONO,
            2: cls.STEREO,
            3: cls.STEREO_2_1,
            4: cls.QUAD,
            5: cls.SURROUND_5_0,
            6: cls.SURROUND_5_1,
            7: cls.SURROUND_7_0,
            8: cls.SURROUND_7_1,
        }
        return layout_map.get(count, cls.STEREO)

    @property
    def channel_count(self) -> int:
        """Get the number of channels for this layout."""
        count_map = {
            AudioChannelLayout.MONO: 1,
            AudioChannelLayout.STEREO: 2,
            AudioChannelLayout.STEREO_2_1: 3,
            AudioChannelLayout.QUAD: 4,
            AudioChannelLayout.SURROUND_5_0: 5,
            AudioChannelLayout.SURROUND_5_1: 6,
            AudioChannelLayout.SURROUND_7_0: 7,
            AudioChannelLayout.SURROUND_7_1: 8,
        }
        return count_map[self]

    def to_ffmpeg_layout(self) -> str:
        """Get FFmpeg channel layout string."""
        layout_map = {
            AudioChannelLayout.MONO: "mono",
            AudioChannelLayout.STEREO: "stereo",
            AudioChannelLayout.STEREO_2_1: "2.1",
            AudioChannelLayout.QUAD: "quad",
            AudioChannelLayout.SURROUND_5_0: "5.0",
            AudioChannelLayout.SURROUND_5_1: "5.1",
            AudioChannelLayout.SURROUND_7_0: "7.0",
            AudioChannelLayout.SURROUND_7_1: "7.1",
        }
        return layout_map[self]


class SpatialAudioFormat(Enum):
    """Supported spatial audio formats."""

    NONE = "none"  # No spatial processing
    BINAURAL = "binaural"  # Stereo binaural (HRTF)
    AMBISONICS_1ST = "ambisonics_1st"  # First-order Ambisonics (4 channels)
    AMBISONICS_2ND = "ambisonics_2nd"  # Second-order Ambisonics (9 channels)
    AMBISONICS_3RD = "ambisonics_3rd"  # Third-order Ambisonics (16 channels)
    DOLBY_ATMOS = "dolby_atmos"  # Dolby Atmos (requires specific encoder)
    MPEG_H = "mpeg_h"  # MPEG-H 3D Audio

    @property
    def is_ambisonics(self) -> bool:
        """Check if this is an Ambisonics format."""
        return self in (
            SpatialAudioFormat.AMBISONICS_1ST,
            SpatialAudioFormat.AMBISONICS_2ND,
            SpatialAudioFormat.AMBISONICS_3RD,
        )

    @property
    def requires_encoding(self) -> bool:
        """Check if this format requires special encoding."""
        return self in (
            SpatialAudioFormat.DOLBY_ATMOS,
            SpatialAudioFormat.MPEG_H,
        )


@dataclass
class AudioFormatConfig:
    """Configuration for audio format settings.

    Attributes:
        codec: Audio codec (e.g., 'aac', 'opus', 'mp3', 'flac').
        bitrate: Audio bitrate in bits per second (e.g., 192000 for 192kbps).
        sample_rate: Audio sample rate in Hz (e.g., 48000).
        channels: Number of audio channels.
        channel_layout: Channel layout for multi-channel audio.
        quality: Quality preset for variable bitrate codecs ('low', 'medium', 'high').
    """

    codec: str = "aac"
    bitrate: int = 192000
    sample_rate: int = 48000
    channels: int = 2
    channel_layout: AudioChannelLayout = AudioChannelLayout.STEREO
    quality: str = "medium"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_codecs = [
            "aac",
            "opus",
            "mp3",
            "flac",
            "pcm_s16le",
            "pcm_s24le",
            "ac3",
            "eac3",
            "truehd",
        ]
        if self.codec not in valid_codecs:
            raise ValueError(
                f"Invalid codec '{self.codec}'. Valid codecs: {', '.join(valid_codecs)}"
            )

        valid_qualities = ["low", "medium", "high"]
        if self.quality not in valid_qualities:
            raise ValueError(
                f"Invalid quality '{self.quality}'. Valid qualities: {', '.join(valid_qualities)}"
            )

        if self.bitrate <= 0:
            raise ValueError(f"Bitrate must be positive, got {self.bitrate}")

        if self.sample_rate <= 0:
            raise ValueError(f"Sample rate must be positive, got {self.sample_rate}")

        if self.channels <= 0:
            raise ValueError(f"Channels must be positive, got {self.channels}")

    def to_ffmpeg_args(self) -> list[str]:
        """Convert to FFmpeg command-line arguments.

        Returns:
            List of FFmpeg arguments for audio encoding.
        """
        args = []

        # Codec
        codec_map = {
            "aac": "aac",
            "opus": "libopus",
            "mp3": "libmp3lame",
            "flac": "flac",
            "pcm_s16le": "pcm_s16le",
            "pcm_s24le": "pcm_s24le",
            "ac3": "ac3",
            "eac3": "eac3",
            "truehd": "truehd",
        }
        args.extend(["-c:a", codec_map.get(self.codec, self.codec)])

        # Bitrate or quality
        if self.codec in ("flac", "pcm_s16le", "pcm_s24le", "truehd"):
            # Lossless codecs don't use bitrate
            pass
        elif self.bitrate > 0:
            args.extend(["-b:a", str(self.bitrate)])
        else:
            # Quality-based encoding
            quality_map = {
                "aac": {"low": "5", "medium": "3", "high": "1"},
                "opus": {"low": "64k", "medium": "96k", "high": "128k"},
                "mp3": {"low": "4", "medium": "2", "high": "0"},
            }
            if self.codec in quality_map:
                args.extend(["-q:a", quality_map[self.codec][self.quality]])

        # Sample rate
        args.extend(["-ar", str(self.sample_rate)])

        # Channels
        args.extend(["-ac", str(self.channels)])

        # Channel layout
        args.extend(["-channel_layout", self.channel_layout.to_ffmpeg_layout()])

        return args

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "codec": self.codec,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "channel_layout": self.channel_layout.value,
            "quality": self.quality,
        }


@dataclass
class SpatialAudioConfig:
    """Configuration for 3D spatial audio processing.

    Attributes:
        enable_spatial: Whether to enable spatial audio processing.
        spatial_format: Target spatial audio format.
        room_size: Room simulation size ('small', 'medium', 'large', 'cathedral').
        room_damping: Room damping factor (0.0 - 1.0).
        listener_position: 3D position of listener (x, y, z).
        source_position: 3D position of audio source (x, y, z).
        hrtf_file: Path to custom HRTF file for binaural rendering.
        enable_reflections: Enable early reflections simulation.
        reflection_delay: Reflection delay in milliseconds.
        reverb_amount: Reverb amount (0.0 - 1.0).
        preserve_original: Also include original stereo mix.
    """

    enable_spatial: bool = False
    spatial_format: SpatialAudioFormat = SpatialAudioFormat.BINAURAL
    room_size: str = "medium"
    room_damping: float = 0.5
    listener_position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    source_position: tuple[float, float, float] = (0.0, 0.0, 1.0)
    hrtf_file: str | None = None
    enable_reflections: bool = True
    reflection_delay: float = 20.0
    reverb_amount: float = 0.3
    preserve_original: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_room_sizes = ["small", "medium", "large", "cathedral"]
        if self.room_size not in valid_room_sizes:
            raise ValueError(
                f"Invalid room_size '{self.room_size}'. Valid sizes: {', '.join(valid_room_sizes)}"
            )

        if not 0.0 <= self.room_damping <= 1.0:
            raise ValueError(f"room_damping must be between 0.0 and 1.0, got {self.room_damping}")

        if self.reflection_delay < 0:
            raise ValueError(f"reflection_delay must be non-negative, got {self.reflection_delay}")

        if not 0.0 <= self.reverb_amount <= 1.0:
            raise ValueError(f"reverb_amount must be between 0.0 and 1.0, got {self.reverb_amount}")

    def to_ffmpeg_filter(self) -> str:
        """Generate FFmpeg filter chain for spatial audio.

        Returns:
            FFmpeg filter chain string.
        """
        if not self.enable_spatial:
            return ""

        filters = []

        if self.spatial_format == SpatialAudioFormat.BINAURAL:
            # Binaural (HRTF) rendering
            # Use sofalizer filter if HRTF file is provided, otherwise use simple stereo widening
            if self.hrtf_file:
                filters.append(f"sofalizer=sofa={self.hrtf_file}:gain=1")
            else:
                # Simple binaural simulation using haas filter and stereo widening
                x, y, z = self.source_position
                # Calculate azimuth and elevation
                import math

                azimuth = math.degrees(math.atan2(x, z))
                math.degrees(math.atan2(y, math.sqrt(x * x + z * z)))

                # Use atrim and adelay for simple spatialization
                # Left ear delay for sounds from the right, right ear delay for sounds from the left
                delay_ms = abs(azimuth) * 0.1  # ~0.1ms per degree
                if azimuth > 0:  # Sound from right
                    filters.append(f"adelay={delay_ms:.1f}|0")
                else:  # Sound from left
                    filters.append(f"adelay=0|{delay_ms:.1f}")

                # Add room simulation
                if self.enable_reflections:
                    room_sizes = {"small": 5, "medium": 15, "large": 30, "cathedral": 100}
                    room_sizes.get(self.room_size, 15)
                    filters.append(f"aecho=1.0:0.7:{self.reflection_delay}:{self.reverb_amount}")

        elif self.spatial_format.is_ambisonics:
            # Ambisonics encoding
            # Convert to Ambisonics B-format
            order_map = {
                SpatialAudioFormat.AMBISONICS_1ST: "1",
                SpatialAudioFormat.AMBISONICS_2ND: "2",
                SpatialAudioFormat.AMBISONICS_3RD: "3",
            }
            order_map[self.spatial_format]
            # Note: Full Ambisonics requires external tools like SPARTA or IEM plugins
            # Here we provide a basic stereo-to-B-format conversion
            filters.append(f"aformat=channel_layouts={self.spatial_format.value}")

        return ",".join(filters) if filters else ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enable_spatial": self.enable_spatial,
            "spatial_format": self.spatial_format.value,
            "room_size": self.room_size,
            "room_damping": self.room_damping,
            "listener_position": self.listener_position,
            "source_position": self.source_position,
            "hrtf_file": self.hrtf_file,
            "enable_reflections": self.enable_reflections,
            "reflection_delay": self.reflection_delay,
            "reverb_amount": self.reverb_amount,
            "preserve_original": self.preserve_original,
        }


@dataclass
class AudioConfig:
    """Main audio processing configuration.

    Attributes:
        preserve_tracks: Whether to preserve original audio tracks.
        format_config: Audio format configuration.
        spatial_config: Spatial audio configuration.
        normalize: Whether to normalize audio levels.
        normalization_target: Target loudness in LUFS (e.g., -14 for streaming).
        tracks_to_preserve: List of track indices to preserve (None = all).
        default_track: Default track index for single-track output.
        enable_downmix: Enable downmixing multi-channel to stereo.
        downmix_coefficient: Downmix coefficient (0.5 - 1.0).
    """

    preserve_tracks: bool = True
    format_config: AudioFormatConfig = field(default_factory=AudioFormatConfig)
    spatial_config: SpatialAudioConfig = field(default_factory=SpatialAudioConfig)
    normalize: bool = True
    normalization_target: float = -14.0
    tracks_to_preserve: list[int] | None = None
    default_track: int = 0
    enable_downmix: bool = False
    downmix_coefficient: float = 0.707  # -3dB

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.normalization_target < -70 or self.normalization_target > 0:
            raise ValueError(
                f"normalization_target must be between -70 and 0 LUFS, got {self.normalization_target}"
            )

        if not 0.0 <= self.downmix_coefficient <= 1.0:
            raise ValueError(
                f"downmix_coefficient must be between 0.0 and 1.0, got {self.downmix_coefficient}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "preserve_tracks": self.preserve_tracks,
            "format_config": self.format_config.to_dict(),
            "spatial_config": self.spatial_config.to_dict(),
            "normalize": self.normalize,
            "normalization_target": self.normalization_target,
            "tracks_to_preserve": self.tracks_to_preserve,
            "default_track": self.default_track,
            "enable_downmix": self.enable_downmix,
            "downmix_coefficient": self.downmix_coefficient,
        }
