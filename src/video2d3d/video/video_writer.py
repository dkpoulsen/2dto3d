"""Robust video output writer using FFmpeg for encoding processed frames.

This module provides a comprehensive video writing system that:
- Encodes processed frames back into video files using FFmpeg
- Supports configurable codecs, bitrates, and quality settings
- Preserves audio tracks from source videos
- Implements proper resource cleanup with context managers
- Handles various pixel formats and color spaces

Example usage:
    ```python
    from video2d3d.video import VideoOutputWriter, VideoWriterConfig

    # Basic usage
    writer = VideoOutputWriter("output.mp4", width=1920, height=1080, fps=30)
    for frame in processed_frames:
        writer.write_frame(frame)
    writer.close()

    # With configuration
    config = VideoWriterConfig(
        codec="libx264",
        preset="medium",
        crf=23,
        pixel_format="yuv420p",
    )
    writer = VideoOutputWriter("output.mp4", config=config, width=1920, height=1080)
    writer.write_frames(processed_frames)
    writer.close()

    # Using context manager
    with VideoOutputWriter("output.mp4", width=1920, height=1080, fps=30) as writer:
        writer.write_frames(processed_frames)

    # With audio preservation from source
    with VideoOutputWriter("output.mp4", source_video="input.mp4",
                           width=1920, height=1080) as writer:
        writer.write_frames(processed_frames)
    ```
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import numpy as np

from video2d3d.utils.logger import get_logger

from .exceptions import (
    FFmpegProcessError,
    InvalidVideoDimensionsError,
    VideoWriteError,
)


def _get_writer_logger():
    """Get the video writer logger (lazy initialization)."""
    return get_logger("video_writer")


class VideoCodec(Enum):
    """Supported video codecs for encoding.

    Categories:
    - Standard codecs: H264, H265/HEVC, VP9, MPEG4, MJPEG, PRORES
    - AV1 codecs: AV1_AOM (libaom), AV1_SVT (SVT-AV1), AV1_RAV1E (Rav1e)
    - HEVC variants: HEVC_LIB, HEVC_NVENC, HEVC_VAAPI, HEVC_QSV
    - VR-optimized: HEVC_VR, AV1_VR (optimized for VR content)
    """

    # Standard codecs
    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    MPEG4 = "mpeg4"
    PRORES = "prores_ks"
    MJPEG = "mjpeg"

    # AV1 codecs (next-generation, royalty-free)
    AV1_AOM = "libaom-av1"  # AOMedia Video 1 (libaom)
    AV1_SVT = "libsvtav1"  # SVT-AV1 (Scalable Video Technology)
    AV1_RAV1E = "librav1e"  # Rav1e (Rust-based encoder)

    # HEVC/H.265 hardware-accelerated variants
    HEVC_LIB = "libx265"  # Software encoder (alias for H265)
    HEVC_NVENC = "hevc_nvenc"  # NVIDIA GPU hardware encoding
    HEVC_VAAPI = "hevc_vaapi"  # VAAPI (Intel/AMD on Linux)
    HEVC_QSV = "hevc_qsv"  # Intel Quick Sync Video
    HEVC_VIDEOTOOLBOX = "hevc_videotoolbox"  # macOS VideoToolbox

    # VR-optimized codec presets
    HEVC_VR = "hevc_vr"  # HEVC optimized for VR (high quality, 10-bit)
    AV1_VR = "av1_vr"  # AV1 optimized for VR content

    # VP9 variants
    VP9_LIBVPX = "libvpx-vp9"  # libvpx VP9 encoder


class Preset(Enum):
    """Encoding presets for speed/quality tradeoff."""

    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"


class PixelFormat(Enum):
    """Common pixel formats for video encoding."""

    YUV420P = "yuv420p"  # Most compatible, 4:2:0 chroma subsampling
    YUV422P = "yuv422p"  # 4:2:2 chroma subsampling
    YUV444P = "yuv444p"  # No chroma subsampling
    YUV420P10LE = "yuv420p10le"  # 10-bit 4:2:0
    YUV422P10LE = "yuv422p10le"  # 10-bit 4:2:2
    YUV444P10LE = "yuv444p10le"  # 10-bit 4:4:4
    RGB24 = "rgb24"  # RGB, no compression


# Codec-specific defaults
CODEC_DEFAULTS: dict[str, dict[str, Any]] = {
    # Standard codecs
    "libx264": {
        "preset": "medium",
        "crf": 23,
        "pixel_format": "yuv420p",
        "tune": None,
        "profile": None,
        "level": None,
    },
    "libx265": {
        "preset": "medium",
        "crf": 28,
        "pixel_format": "yuv420p",
        "tune": None,
        "profile": None,
        "x265_params": {},
    },
    "libvpx-vp9": {
        "crf": 31,
        "pixel_format": "yuv420p",
        "deadline": "good",
        "cpu_used": 4,
    },
    "mpeg4": {
        "q": 5,
        "pixel_format": "yuv420p",
    },
    "prores_ks": {
        "profile": 3,  # ProRes 422
        "pixel_format": "yuv422p10le",
    },
    "mjpeg": {
        "q": 5,
        "pixel_format": "yuv420p",
    },
    # AV1 codecs
    "libaom-av1": {
        "crf": 30,
        "pixel_format": "yuv420p",
        "cpu_used": 4,  # Speed preset (0-8, higher = faster)
        "lag_in_frames": 35,
        "usage_realtime": False,
    },
    "libsvtav1": {
        "crf": 30,
        "pixel_format": "yuv420p",
        "preset": 6,  # SVT-AV1 preset (0-13, higher = faster)
        "tile_columns": 0,
        "tile_rows": 0,
    },
    "librav1e": {
        "qp": 30,
        "pixel_format": "yuv420p",
        "speed": 6,  # Speed preset (0-10, higher = faster)
        "tile_columns": 0,
        "tile_rows": 0,
    },
    # HEVC hardware-accelerated variants
    "hevc_nvenc": {
        "preset": "p4",  # NVENC preset (p1-p7)
        "cq": 23,  # Constant quality
        "pixel_format": "yuv420p",
        "rc": "vbr",  # Rate control
        "profile": "main",
    },
    "hevc_vaapi": {
        "qp": 23,
        "pixel_format": "yuv420p",
        "profile": "main",
    },
    "hevc_qsv": {
        "preset": "medium",
        "global_quality": 23,
        "pixel_format": "yuv420p",
        "profile": "main",
    },
    "hevc_videotoolbox": {
        "q": 23,
        "pixel_format": "yuv420p",
        "profile": "main",
    },
    # VR-optimized presets
    "hevc_vr": {
        "preset": "slow",
        "crf": 20,
        "pixel_format": "yuv420p10le",  # 10-bit for better gradients
        "tune": "grain",  # Preserve detail for VR
        "x265_params": {
            "frame-threads": 2,
            "pmode": 1,
            "pme": 1,
            "aq-mode": 3,
        },
    },
    "av1_vr": {
        "crf": 25,
        "pixel_format": "yuv420p10le",
        "cpu_used": 3,
        "lag_in_frames": 50,
        "usage_realtime": False,
    },
}


@dataclass
class VideoWriterConfig:
    """Configuration for video output writing.

    Attributes:
        codec: Video codec to use (e.g., 'libx264', 'libx265').
        preset: Encoding preset (speed/quality tradeoff).
        crf: Constant Rate Factor (quality). Lower = better quality, larger file.
             Valid range depends on codec. For H.264: 0-51, default 23.
        bitrate: Target bitrate in bits per second. Mutually exclusive with crf.
        pixel_format: Output pixel format.
        container_format: Container format (e.g., 'mp4', 'mkv', 'avi').
        copy_audio: Whether to copy audio from source video.
        audio_codec: Audio codec for re-encoding (if not copying).
        audio_bitrate: Audio bitrate in bits per second.
        audio_sample_rate: Audio sample rate in Hz.
        audio_channels: Number of audio channels.
        enable_spatial_audio: Enable 3D spatial audio processing.
        spatial_audio_format: Spatial audio format ('binaural', 'ambisonics_1st', 'ambisonics_2nd').
        preserve_all_audio_tracks: Preserve all audio tracks from source.
        audio_normalization: Enable loudness normalization (EBU R128).
        audio_normalization_target: Target loudness in LUFS.
        metadata: Video metadata to embed.
        faststart: Move atom to start of file (for web streaming).
        threads: Number of encoding threads (0 = auto).
        hwaccel: Enable hardware acceleration if available.

        # Custom codec options (NEW)
        tune: Codec tuning option (e.g., 'film', 'animation', 'grain' for x264/x265).
        profile: Codec profile (e.g., 'main', 'high', 'main10').
        level: Codec level (e.g., '4.0', '5.1').
        codec_params: Additional codec-specific parameters as dict.
        x265_params: x265-specific parameters (for libx265/hevc_vr).
        av1_params: AV1-specific parameters (for libaom-av1, libsvtav1).
        vr_mode: Enable VR-specific encoding optimizations.
    """

    codec: str = "libx264"
    preset: str = "medium"
    crf: int | None = 23
    bitrate: int | None = None
    pixel_format: str = "yuv420p"
    container_format: str = "mp4"
    copy_audio: bool = True
    audio_codec: str = "aac"
    audio_bitrate: int = 192000
    audio_sample_rate: int = 48000
    audio_channels: int = 2
    # Advanced audio processing options
    enable_spatial_audio: bool = False
    spatial_audio_format: str = "binaural"  # 'binaural', 'ambisonics_1st', 'ambisonics_2nd'
    preserve_all_audio_tracks: bool = False
    audio_normalization: bool = True
    audio_normalization_target: float = -14.0  # LUFS
    # Other options
    metadata: dict[str, str] = field(default_factory=dict)
    faststart: bool = True
    threads: int = 0
    hwaccel: bool = False
    # Custom codec options (NEW)
    tune: str | None = None
    profile: str | None = None
    level: str | None = None
    codec_params: dict[str, Any] = field(default_factory=dict)
    x265_params: dict[str, Any] = field(default_factory=dict)
    av1_params: dict[str, Any] = field(default_factory=dict)
    vr_mode: bool = False

    def __post_init__(self) -> None:
        """Validate and apply codec defaults after initialization."""
        # Apply codec defaults for missing values (but not if bitrate is explicitly set)
        if self.codec in CODEC_DEFAULTS:
            defaults = CODEC_DEFAULTS[self.codec]
            if self.preset is None and "preset" in defaults:
                self.preset = defaults["preset"]
            # Only apply CRF default if bitrate is not set (mutually exclusive)
            if self.crf is None and self.bitrate is None and "crf" in defaults:
                self.crf = defaults["crf"]
            if self.pixel_format is None and "pixel_format" in defaults:
                self.pixel_format = defaults["pixel_format"]
            # Apply tune from defaults if not set
            if self.tune is None and "tune" in defaults:
                self.tune = defaults["tune"]
            # Apply profile from defaults if not set
            if self.profile is None and "profile" in defaults:
                self.profile = defaults["profile"]
            # Apply x265_params from defaults if empty
            if not self.x265_params and "x265_params" in defaults:
                self.x265_params = defaults["x265_params"].copy()
            # Apply av1_params from defaults if empty
            if not self.av1_params and "av1_params" in defaults:
                self.av1_params = defaults["av1_params"].copy()
            # Apply codec_params from defaults if empty
            if not self.codec_params and "codec_params" in defaults:
                self.codec_params = defaults["codec_params"].copy()

        # Validate CRF range based on codec
        if self.crf is not None:
            # H.264/HEVC codecs (0-51 CRF range)
            h264_hevc_codecs = (
                "libx264",
                "libx265",
                "hevc_vr",
                "hevc_nvenc",
                "hevc_vaapi",
                "hevc_qsv",
                "hevc_videotoolbox",
            )
            if self.codec in h264_hevc_codecs:
                if not 0 <= self.crf <= 51:
                    raise ValueError(f"CRF must be 0-51 for {self.codec}, got {self.crf}")
            # VP9/AV1 codecs (0-63 CRF range)
            elif self.codec in ("libvpx-vp9", "vp9_libvpx", "libaom-av1", "libsvtav1", "av1_vr"):
                if not 0 <= self.crf <= 63:
                    raise ValueError(f"CRF must be 0-63 for {self.codec}, got {self.crf}")
            # librav1e uses QP, not CRF - warn if CRF is set
            elif self.codec == "librav1e":
                import warnings

                warnings.warn(
                    "librav1e uses QP (Quantization Parameter), not CRF. "
                    "Set av1_params['qp'] instead for best results.",
                    UserWarning,
                    stacklevel=2,
                )

        # Validate preset for standard codecs
        valid_presets = [p.value for p in Preset]
        if self.preset and self.preset not in valid_presets:
            # Allow numeric presets for SVT-AV1 and NVENC
            if self.codec in ("libsvtav1", "hevc_nvenc"):
                try:
                    preset_num = int(self.preset)
                    if self.codec == "libsvtav1" and not 0 <= preset_num <= 13:
                        raise ValueError(f"SVT-AV1 preset must be 0-13, got {preset_num}")
                    if self.codec == "hevc_nvenc" and not 1 <= preset_num <= 7:
                        raise ValueError(f"NVENC preset must be p1-p7, got {self.preset}")
                except ValueError:
                    raise ValueError(f"Invalid preset '{self.preset}' for {self.codec}")
            else:
                raise ValueError(
                    f"Invalid preset '{self.preset}'. Valid presets: {', '.join(valid_presets)}"
                )

        # Validate spatial audio format
        valid_spatial_formats = ["binaural", "ambisonics_1st", "ambisonics_2nd", "ambisonics_3rd"]
        if self.spatial_audio_format not in valid_spatial_formats:
            raise ValueError(
                f"Invalid spatial_audio_format '{self.spatial_audio_format}'. "
                f"Valid formats: {', '.join(valid_spatial_formats)}"
            )

        # Validate audio normalization target
        if not -70 <= self.audio_normalization_target <= 0:
            raise ValueError(
                f"audio_normalization_target must be between -70 and 0 LUFS, "
                f"got {self.audio_normalization_target}"
            )

    def get_file_extension(self) -> str:
        """Get the file extension for the container format."""
        extensions = {
            "mp4": ".mp4",
            "mkv": ".mkv",
            "avi": ".avi",
            "mov": ".mov",
            "webm": ".webm",
        }
        return extensions.get(self.container_format, f".{self.container_format}")

    def get_audio_config(self) -> AudioConfig:
        """Get audio configuration for the AudioProcessor.

        Returns:
            AudioConfig instance based on this video writer config.
        """
        from video2d3d.audio.config import (
            AudioConfig,
            AudioFormatConfig,
            SpatialAudioConfig,
            SpatialAudioFormat,
        )

        # Map spatial format string to enum
        spatial_format_map = {
            "binaural": SpatialAudioFormat.BINAURAL,
            "ambisonics_1st": SpatialAudioFormat.AMBISONICS_1ST,
            "ambisonics_2nd": SpatialAudioFormat.AMBISONICS_2ND,
            "ambisonics_3rd": SpatialAudioFormat.AMBISONICS_3RD,
        }

        return AudioConfig(
            preserve_tracks=self.preserve_all_audio_tracks,
            format_config=AudioFormatConfig(
                codec=self.audio_codec,
                bitrate=self.audio_bitrate,
                sample_rate=self.audio_sample_rate,
                channels=self.audio_channels,
            ),
            spatial_config=SpatialAudioConfig(
                enable_spatial=self.enable_spatial_audio,
                spatial_format=spatial_format_map.get(
                    self.spatial_audio_format, SpatialAudioFormat.BINAURAL
                ),
            ),
            normalize=self.audio_normalization,
            normalization_target=self.audio_normalization_target,
        )


@dataclass
class WriterStats:
    """Statistics for video writing operations."""

    frames_written: int = 0
    bytes_written: int = 0
    start_time: float | None = None
    end_time: float | None = None
    average_fps: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "frames_written": self.frames_written,
            "bytes_written": self.bytes_written,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "average_fps": self.average_fps,
        }


class VideoOutputWriter:
    """Robust video output writer using FFmpeg.

    This class provides comprehensive video writing capabilities including:
    - Configurable codec, bitrate, and quality settings
    - Audio track preservation from source videos
    - Context manager support for proper resource cleanup
    - Support for various pixel formats and color spaces
    - Streaming frame-by-frame writing for memory efficiency

    Example usage:
        ```python
        # Basic usage
        with VideoOutputWriter("output.mp4", width=1920, height=1080, fps=30) as writer:
            for frame in processed_frames:
                writer.write_frame(frame)

        # With configuration
        config = VideoWriterConfig(codec="libx265", preset="slow", crf=20)
        with VideoOutputWriter("output.mp4", config=config,
                               width=1920, height=1080) as writer:
            writer.write_frames(processed_frames)

        # With audio preservation
        with VideoOutputWriter("output.mp4", source_video="input.mp4",
                               width=1920, height=1080) as writer:
            writer.write_frames(processed_frames)
        ```
    """

    def __init__(
        self,
        output_path: str | Path,
        config: VideoWriterConfig | None = None,
        *,
        width: int,
        height: int,
        fps: float = 30.0,
        source_video: str | Path | None = None,
        input_pixel_format: str = "rgb24",
        progress_callback: Callable[[int, int], None] | None = None,
        total_frames: int | None = None,
    ) -> None:
        """Initialize the video output writer.

        Args:
            output_path: Path to the output video file.
            config: VideoWriterConfig with encoding settings. If None, uses defaults.
            width: Output video width in pixels.
            height: Output video height in pixels.
            fps: Frames per second for the output video.
            source_video: Optional source video to copy audio from.
            input_pixel_format: Pixel format of input frames (default: rgb24).
            progress_callback: Optional callback(completed, total) for progress tracking.
            total_frames: Total number of frames to be written (for progress tracking).

        Raises:
            InvalidVideoDimensionsError: If width or height are invalid.
            VideoWriteError: If FFmpeg is not available.
        """
        self.output_path = Path(output_path).resolve()
        self.config = config or VideoWriterConfig()

        # Validate dimensions and FPS before anything else
        if width <= 0 or height <= 0:
            raise InvalidVideoDimensionsError(width, height)
        if fps <= 0:
            raise ValueError(f"FPS must be positive, got {fps}")

        self.width = width
        self.height = height
        self.fps = fps
        self.source_video = Path(source_video) if source_video else None
        self.input_pixel_format = input_pixel_format
        self._progress_callback = progress_callback
        self._total_frames = total_frames or 0

        # Initialize instance attributes
        self._is_open: bool = False
        self._process: subprocess.Popen | None = None
        self._frames_written: int = 0
        self._temp_audio_file: Path | None = None
        self._stats: WriterStats = WriterStats()

        # Check FFmpeg availability
        self._check_ffmpeg_available()

    def _check_ffmpeg_available(self) -> None:
        """Check if FFmpeg is available in the system PATH."""
        if shutil.which("ffmpeg") is None:
            raise VideoWriteError(
                self.output_path,
                "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.",
            )

    def _build_ffmpeg_command(
        self,
        output_path: Path,
        include_audio: bool = False,
    ) -> list[str]:
        """Build the FFmpeg command for video encoding.

        Args:
            output_path: Path to the output file.
            include_audio: Whether to include audio in the final output.

        Returns:
            List of command arguments for FFmpeg.
        """
        cmd = ["ffmpeg", "-y"]  # Overwrite output file

        # Input from stdin (raw video frames)
        cmd.extend(
            [
                "-f",
                "rawvideo",
                "-vcodec",
                "rawvideo",
                "-s",
                f"{self.width}x{self.height}",
                "-pix_fmt",
                self.input_pixel_format,
                "-r",
                str(self.fps),
                "-i",
                "-",  # Read from stdin
            ]
        )

        # Add audio input if preserving audio
        if include_audio and self.source_video and self._temp_audio_file:
            cmd.extend(["-i", str(self._temp_audio_file)])

        # Video encoding settings
        cmd.extend(["-c:v", self._get_actual_codec()])

        # Codec-specific options
        self._add_codec_options(cmd)

        # Pixel format
        cmd.extend(["-pix_fmt", self.config.pixel_format])

        # Threading
        if self.config.threads > 0:
            cmd.extend(["-threads", str(self.config.threads)])

        # Audio settings
        if include_audio and self.source_video and self._temp_audio_file:
            if self.config.copy_audio:
                cmd.extend(["-c:a", "copy"])
            else:
                cmd.extend(
                    [
                        "-c:a",
                        self.config.audio_codec,
                        "-b:a",
                        str(self.config.audio_bitrate),
                        "-ar",
                        str(self.config.audio_sample_rate),
                        "-ac",
                        str(self.config.audio_channels),
                    ]
                )

        # Metadata
        for key, value in self.config.metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])

        # Faststart for web streaming (MP4 only)
        if self.config.faststart and self.config.container_format == "mp4":
            cmd.append("-movflags")
            cmd.append("+faststart")

        # Output file
        cmd.append(str(output_path))

        _get_writer_logger().debug(f"FFmpeg command: {' '.join(cmd)}")
        return cmd

    def _get_actual_codec(self) -> str:
        """Get the actual FFmpeg codec name for encoding.

        Maps VR-optimized preset names to their actual codec implementations.
        """
        codec_map = {
            "hevc_vr": "libx265",  # VR-optimized HEVC uses libx265
            "av1_vr": "libaom-av1",  # VR-optimized AV1 uses libaom
        }
        return codec_map.get(self.config.codec, self.config.codec)

    def _add_codec_options(self, cmd: list[str]) -> None:
        """Add codec-specific options to the FFmpeg command.

        Args:
            cmd: The FFmpeg command list to append options to.
        """
        actual_codec = self._get_actual_codec()

        # H.264 / x264
        if actual_codec == "libx264":
            self._add_x264_options(cmd)

        # H.265 / HEVC / x265
        elif actual_codec == "libx265":
            self._add_x265_options(cmd)

        # VP9
        elif actual_codec == "libvpx-vp9":
            self._add_vp9_options(cmd)

        # AV1 codecs
        elif actual_codec == "libaom-av1":
            self._add_aom_av1_options(cmd)
        elif actual_codec == "libsvtav1":
            self._add_svtav1_options(cmd)
        elif actual_codec == "librav1e":
            self._add_rav1e_options(cmd)

        # HEVC hardware-accelerated
        elif actual_codec == "hevc_nvenc":
            self._add_nvenc_hevc_options(cmd)
        elif actual_codec == "hevc_vaapi":
            self._add_vaapi_hevc_options(cmd)
        elif actual_codec == "hevc_qsv":
            self._add_qsv_hevc_options(cmd)
        elif actual_codec == "hevc_videotoolbox":
            self._add_videotoolbox_hevc_options(cmd)

        # ProRes
        elif actual_codec == "prores_ks":
            profile = CODEC_DEFAULTS.get("prores_ks", {}).get("profile", 3)
            cmd.extend(["-profile:v", str(profile)])

        # MJPEG
        elif actual_codec == "mjpeg":
            cmd.extend(["-q:v", str(CODEC_DEFAULTS.get("mjpeg", {}).get("q", 5))])

        # MPEG4
        elif actual_codec == "mpeg4":
            cmd.extend(["-q:v", str(CODEC_DEFAULTS.get("mpeg4", {}).get("q", 5))])

        # Apply any custom codec_params
        for key, value in self.config.codec_params.items():
            cmd.extend([f"-{key}", str(value)])

    def _add_x264_options(self, cmd: list[str]) -> None:
        """Add x264-specific options."""
        if self.config.preset:
            cmd.extend(["-preset", self.config.preset])
        if self.config.crf is not None and self.config.bitrate is None:
            cmd.extend(["-crf", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])
        if self.config.tune:
            cmd.extend(["-tune", self.config.tune])
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])
        if self.config.level:
            cmd.extend(["-level", self.config.level])

    def _add_x265_options(self, cmd: list[str]) -> None:
        """Add x265-specific options."""
        if self.config.preset:
            cmd.extend(["-preset", self.config.preset])
        if self.config.crf is not None and self.config.bitrate is None:
            cmd.extend(["-crf", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])
        if self.config.tune:
            cmd.extend(["-tune", self.config.tune])
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])

        # Add x265-params
        params = []
        if self.config.vr_mode or self.config.codec == "hevc_vr":
            # VR-optimized settings
            params.append("frame-threads=2")
            params.append("pmode=1")
            params.append("pme=1")
            params.append("aq-mode=3")
        # Add custom x265 params
        for key, value in self.config.x265_params.items():
            params.append(f"{key}={value}")
        if params:
            cmd.extend(["-x265-params", ":".join(params)])

        # Better compatibility for HEVC
        cmd.extend(["-tag:v", "hvc1"])

    def _add_vp9_options(self, cmd: list[str]) -> None:
        """Add VP9-specific options."""
        if self.config.crf is not None:
            cmd.extend(["-crf", str(self.config.crf)])
        cmd.extend(["-b:v", "0"])  # Use CRF mode

        # VP9 speed/quality tradeoff
        deadline = CODEC_DEFAULTS.get("libvpx-vp9", {}).get("deadline", "good")
        cpu_used = CODEC_DEFAULTS.get("libvpx-vp9", {}).get("cpu_used", 4)
        cmd.extend(["-deadline", deadline])
        cmd.extend(["-cpu-used", str(cpu_used)])

    def _add_aom_av1_options(self, cmd: list[str]) -> None:
        """Add libaom-av1 specific options."""
        if self.config.crf is not None:
            cmd.extend(["-crf", str(self.config.crf)])
        cmd.extend(["-b:v", "0"])  # Use CRF mode

        # CPU used (speed preset, 0-8, higher = faster but lower quality)
        cpu_used = self.config.av1_params.get(
            "cpu_used", CODEC_DEFAULTS.get("libaom-av1", {}).get("cpu_used", 4)
        )
        cmd.extend(["-cpu-used", str(cpu_used)])

        # Lag in frames (lookahead)
        lag_in_frames = self.config.av1_params.get(
            "lag_in_frames", CODEC_DEFAULTS.get("libaom-av1", {}).get("lag_in_frames", 35)
        )
        cmd.extend(["-lag-in-frames", str(lag_in_frames)])

        # VR mode optimizations
        if self.config.vr_mode or self.config.codec == "av1_vr":
            cmd.extend(["-lag-in-frames", "50"])
            cmd.extend(["-cpu-used", "3"])

    def _add_svtav1_options(self, cmd: list[str]) -> None:
        """Add SVT-AV1 specific options."""
        if self.config.crf is not None:
            cmd.extend(["-crf", str(self.config.crf)])

        # SVT-AV1 preset (0-13, higher = faster)
        preset = (
            self.config.preset
            if self.config.preset
            else str(CODEC_DEFAULTS.get("libsvtav1", {}).get("preset", 6))
        )
        cmd.extend(["-preset", preset])

    def _add_rav1e_options(self, cmd: list[str]) -> None:
        """Add Rav1e specific options."""
        # Rav1e uses -qp instead of -crf
        qp = self.config.av1_params.get("qp", CODEC_DEFAULTS.get("librav1e", {}).get("qp", 30))
        cmd.extend(["-qp", str(qp)])

        # Speed preset (0-10, higher = faster)
        speed = self.config.av1_params.get(
            "speed", CODEC_DEFAULTS.get("librav1e", {}).get("speed", 6)
        )
        cmd.extend(["-speed", str(speed)])

    def _add_nvenc_hevc_options(self, cmd: list[str]) -> None:
        """Add NVIDIA NVENC HEVC options."""
        # NVENC preset (p1-p7)
        preset = self.config.preset if self.config.preset else "p4"
        cmd.extend(["-preset", preset])

        # Rate control
        rc = CODEC_DEFAULTS.get("hevc_nvenc", {}).get("rc", "vbr")
        cmd.extend(["-rc", rc])

        # Quality (cq for constant quality)
        if self.config.crf is not None:
            cmd.extend(["-cq", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])

        # Profile
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])

    def _add_vaapi_hevc_options(self, cmd: list[str]) -> None:
        """Add VAAPI HEVC options."""
        if self.config.crf is not None:
            cmd.extend(["-qp", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])

    def _add_qsv_hevc_options(self, cmd: list[str]) -> None:
        """Add Intel QSV HEVC options."""
        preset = self.config.preset if self.config.preset else "medium"
        cmd.extend(["-preset", preset])

        if self.config.crf is not None:
            cmd.extend(["-global_quality", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])

    def _add_videotoolbox_hevc_options(self, cmd: list[str]) -> None:
        """Add macOS VideoToolbox HEVC options."""
        if self.config.crf is not None:
            cmd.extend(["-q:v", str(self.config.crf)])
        elif self.config.bitrate is not None:
            cmd.extend(["-b:v", str(self.config.bitrate)])
        if self.config.profile:
            cmd.extend(["-profile:v", self.config.profile])

        """Extract audio from source video to a temporary file."""
        if not self.source_video or not self.source_video.exists():
            _get_writer_logger().warning(
                f"Source video not found for audio extraction: {self.source_video}"
            )
            return

        try:
            # Create temporary file for audio
            temp_dir = self.output_path.parent
            self._temp_audio_file = Path(tempfile.mktemp(suffix=".aac", dir=temp_dir))

            # Extract audio using FFmpeg
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(self.source_video),
                "-vn",  # No video
                "-c:a",
                "copy",  # Copy audio without re-encoding
                str(self._temp_audio_file),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=60,
            )

            if result.returncode != 0:
                _get_writer_logger().warning(
                    f"Failed to extract audio: {result.stderr.decode('utf-8', errors='ignore')}"
                )
                self._temp_audio_file = None
            else:
                _get_writer_logger().debug(
                    f"Audio extracted to temporary file: {self._temp_audio_file}"
                )

        except subprocess.TimeoutExpired:
            _get_writer_logger().warning("Audio extraction timed out")
            self._temp_audio_file = None
        except Exception as e:
            _get_writer_logger().warning(f"Failed to extract audio: {e}")
            self._temp_audio_file = None

    def open(self) -> None:
        """Open the video writer and start the FFmpeg process.

        This method initializes the FFmpeg subprocess that will encode
        the video frames. It must be called before writing any frames.
        """
        if self._is_open:
            _get_writer_logger().warning("Video writer is already open")
            return

        try:
            # Extract audio from source if needed
            has_audio = False
            if self.source_video:
                self._extract_audio()
                has_audio = self._temp_audio_file is not None

            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(self.output_path, include_audio=has_audio)

            # Start FFmpeg process
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self._is_open = True
            _get_writer_logger().info(f"Video writer opened: {self.output_path.name}")

        except Exception as e:
            raise VideoWriteError(
                self.output_path,
                f"Failed to start FFmpeg process: {e}",
            ) from e

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a single frame to the video.

        Args:
            frame: Frame as numpy array with shape (height, width, channels).
                   The frame should match the initialized width, height, and
                   be in the format specified by input_pixel_format.

        Raises:
            VideoWriteError: If the frame cannot be written.
        """
        if not self._is_open:
            self.open()

        if self._process is None or self._process.stdin is None:
            raise VideoWriteError(self.output_path, "FFmpeg process not initialized")

        # Validate frame dimensions
        if frame.shape[0] != self.height or frame.shape[1] != self.width:
            raise VideoWriteError(
                self.output_path,
                f"Frame dimensions {frame.shape[:2]} don't match "
                f"expected ({self.height}, {self.width})",
            )

        try:
            # Write frame to FFmpeg stdin
            self._process.stdin.write(frame.tobytes())
            self._frames_written += 1

            # Call progress callback if set
            if self._progress_callback:
                self._progress_callback(self._frames_written, self._total_frames)

            # Log progress periodically
            if self._frames_written % 100 == 0:
                _get_writer_logger().debug(
                    f"Written {self._frames_written} frames to {self.output_path.name}"
                )

        except BrokenPipeError:
            # FFmpeg process died, get error message
            stderr = (
                self._process.stderr.read().decode("utf-8", errors="ignore")
                if self._process.stderr
                else ""
            )
            raise FFmpegProcessError(
                self.output_path,
                return_code=self._process.returncode,
                stderr_output=stderr,
            ) from None
        except Exception as e:
            raise VideoWriteError(
                self.output_path,
                f"Failed to write frame {self._frames_written}: {e}",
            ) from e

    def write_frames(self, frames: list[np.ndarray] | np.ndarray) -> int:
        """Write multiple frames to the video.

        Args:
            frames: List or array of frames. Each frame should have shape
                   (height, width, channels).

        Returns:
            Number of frames written.

        Raises:
            VideoWriteError: If frames cannot be written.
        """
        if isinstance(frames, np.ndarray) and frames.ndim == 4:
            # Batch of frames as 4D array (N, H, W, C)
            for i in range(frames.shape[0]):
                self.write_frame(frames[i])
        else:
            # List of frames
            for frame in frames:
                self.write_frame(frame)

        return self._frames_written

    def close(self) -> WriterStats:
        """Close the video writer and finalize the output file.

        This method closes the FFmpeg process and cleans up temporary files.
        It should be called after all frames have been written.

        Returns:
            WriterStats with statistics about the writing operation.
        """
        if not self._is_open:
            return self._stats

        try:
            # Close stdin to signal end of input
            if self._process and self._process.stdin:
                self._process.stdin.close()

            # Wait for FFmpeg to finish
            if self._process:
                return_code = self._process.wait()

                if return_code != 0:
                    stderr = (
                        self._process.stderr.read().decode("utf-8", errors="ignore")
                        if self._process.stderr
                        else ""
                    )
                    raise FFmpegProcessError(
                        self.output_path,
                        return_code=return_code,
                        stderr_output=stderr,
                    )

            # Update stats
            self._stats.frames_written = self._frames_written
            if self.output_path.exists():
                self._stats.bytes_written = self.output_path.stat().st_size

            _get_writer_logger().info(
                f"Video writer closed: {self.output_path.name}, "
                f"{self._frames_written} frames, {self._stats.bytes_written / 1024 / 1024:.2f} MB"
            )

        except FFmpegProcessError:
            raise
        except Exception as e:
            raise VideoWriteError(
                self.output_path,
                f"Failed to finalize video: {e}",
            ) from e
        finally:
            # Cleanup
            self._process = None
            self._is_open = False

            # Remove temporary audio file
            if self._temp_audio_file and self._temp_audio_file.exists():
                try:
                    self._temp_audio_file.unlink()
                    _get_writer_logger().debug(
                        f"Removed temporary audio file: {self._temp_audio_file}"
                    )
                except OSError as e:
                    _get_writer_logger().warning(f"Failed to remove temporary audio file: {e}")
                finally:
                    self._temp_audio_file = None

        return self._stats

    def get_stats(self) -> WriterStats:
        """Get current writing statistics."""
        return self._stats

    @property
    def is_open(self) -> bool:
        """Check if the writer is open and ready to write frames."""
        return self._is_open

    @property
    def frames_written(self) -> int:
        """Get the number of frames written so far."""
        return self._frames_written

    def __enter__(self) -> VideoOutputWriter:
        """Context manager entry."""
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - cleanup resources."""
        if exc_type is not None:
            _get_writer_logger().error(
                f"Closing video writer due to error: {exc_type.__name__}: {exc_val}"
            )
        self.close()


def create_video_writer(
    output_path: str | Path,
    width: int,
    height: int,
    fps: float = 30.0,
    codec: str = "libx264",
    preset: str = "medium",
    crf: int = 23,
    source_video: str | Path | None = None,
    **kwargs: Any,
) -> VideoOutputWriter:
    """Convenience function to create a video writer with common settings.

    Args:
        output_path: Path to the output video file.
        width: Output video width in pixels.
        height: Output video height in pixels.
        fps: Frames per second.
        codec: Video codec (default: libx264).
        preset: Encoding preset (default: medium).
        crf: Constant Rate Factor (default: 23).
        source_video: Optional source video to copy audio from.
        **kwargs: Additional arguments passed to VideoWriterConfig.

    Returns:
        Configured VideoOutputWriter instance.

    Example:
        ```python
        writer = create_video_writer("output.mp4", 1920, 1080, fps=30)
        writer.write_frames(frames)
        writer.close()
        ```
    """
    config = VideoWriterConfig(
        codec=codec,
        preset=preset,
        crf=crf,
        **kwargs,
    )
    return VideoOutputWriter(
        output_path=output_path,
        config=config,
        width=width,
        height=height,
        fps=fps,
        source_video=source_video,
    )


def create_vr_video_writer(
    output_path: str | Path,
    width: int,
    height: int,
    fps: float = 30.0,
    codec: str = "hevc_vr",
    quality: str = "high",
    source_video: str | Path | None = None,
    **kwargs: Any,
) -> VideoOutputWriter:
    """Create a VR-optimized video writer.

    This convenience function creates a VideoOutputWriter pre-configured
    for VR content with optimal settings for 360° video.

    Args:
        output_path: Path to the output video file.
        width: Output video width in pixels.
        height: Output video height in pixels.
        fps: Frames per second.
        codec: VR codec - 'hevc_vr' (recommended) or 'av1_vr'.
        quality: Quality preset - 'fast', 'balanced', or 'high'.
        source_video: Optional source video to copy audio from.
        **kwargs: Additional arguments passed to VideoWriterConfig.

    Returns:
        Configured VideoOutputWriter instance for VR.

    Example:
        ```python
        # High-quality VR video
        writer = create_vr_video_writer("vr_output.mp4", 3840, 1080, fps=30, quality="high")
        writer.write_frames(frames)
        writer.close()
        ```
    """
    quality_settings = {
        "fast": {"crf": 25, "preset": "fast"},
        "balanced": {"crf": 22, "preset": "medium"},
        "high": {"crf": 18, "preset": "slow"},
    }

    settings = quality_settings.get(quality, quality_settings["balanced"])

    config = VideoWriterConfig(
        codec=codec,
        preset=settings["preset"],
        crf=settings["crf"],
        pixel_format="yuv420p10le",  # 10-bit for better VR gradients
        vr_mode=True,
        metadata={
            "spherical": "1",
            "stitched": "1",
            "projection": "equirectangular",
        },
        **kwargs,
    )

    return VideoOutputWriter(
        output_path=output_path,
        config=config,
        width=width,
        height=height,
        fps=fps,
        source_video=source_video,
    )


def create_av1_video_writer(
    output_path: str | Path,
    width: int,
    height: int,
    fps: float = 30.0,
    codec: str = "libaom-av1",
    speed: int = 4,
    crf: int = 30,
    source_video: str | Path | None = None,
    **kwargs: Any,
) -> VideoOutputWriter:
    """Create an AV1 video writer with optimal settings.

    AV1 is a royalty-free, next-generation codec offering excellent
    compression efficiency at the cost of slower encoding speed.

    Args:
        output_path: Path to the output video file.
        width: Output video width in pixels.
        height: Output video height in pixels.
        fps: Frames per second.
        codec: AV1 codec - 'libaom-av1', 'libsvtav1', or 'librav1e'.
        speed: Encoding speed (0-8 for libaom, 0-13 for SVT-AV1).
               Lower = slower but better quality.
        crf: Constant Rate Factor (0-63, lower = better quality).
        source_video: Optional source video to copy audio from.
        **kwargs: Additional arguments passed to VideoWriterConfig.

    Returns:
        Configured VideoOutputWriter instance for AV1.

    Example:
        ```python
        # High-quality AV1 encoding
        writer = create_av1_video_writer("output.webm", 1920, 1080, speed=2, crf=25)
        writer.write_frames(frames)
        writer.close()
        ```
    """
    config = VideoWriterConfig(
        codec=codec,
        crf=crf,
        pixel_format="yuv420p",
        av1_params={"cpu_used": speed},
        **kwargs,
    )

    return VideoOutputWriter(
        output_path=output_path,
        config=config,
        width=width,
        height=height,
        fps=fps,
        source_video=source_video,
    )


def create_hevc_video_writer(
    output_path: str | Path,
    width: int,
    height: int,
    fps: float = 30.0,
    hwaccel: str | None = None,
    preset: str = "medium",
    crf: int = 28,
    source_video: str | Path | None = None,
    **kwargs: Any,
) -> VideoOutputWriter:
    """Create an HEVC/H.265 video writer with optional hardware acceleration.

    HEVC provides better compression than H.264 with support for hardware
    acceleration on modern GPUs.

    Args:
        output_path: Path to the output video file.
        width: Output video width in pixels.
        height: Output video height in pixels.
        fps: Frames per second.
        hwaccel: Hardware acceleration type - 'nvenc' (NVIDIA),
                 'vaapi' (Intel/AMD Linux), 'qsv' (Intel),
                 'videotoolbox' (macOS), or None for software encoding.
        preset: Encoding preset (ultrafast to veryslow).
        crf: Constant Rate Factor (0-51, lower = better quality).
        source_video: Optional source video to copy audio from.
        **kwargs: Additional arguments passed to VideoWriterConfig.

    Returns:
        Configured VideoOutputWriter instance for HEVC.

    Example:
        ```python
        # Software HEVC encoding
        writer = create_hevc_video_writer("output.mp4", 1920, 1080, preset="slow", crf=20)

        # NVIDIA hardware-accelerated encoding
        writer = create_hevc_video_writer("output.mp4", 1920, 1080, hwaccel="nvenc")

        writer.write_frames(frames)
        writer.close()
        ```
    """
    # Map hwaccel option to codec
    codec_map = {
        None: "libx265",
        "nvenc": "hevc_nvenc",
        "vaapi": "hevc_vaapi",
        "qsv": "hevc_qsv",
        "videotoolbox": "hevc_videotoolbox",
    }

    codec = codec_map.get(hwaccel, "libx265")

    config = VideoWriterConfig(
        codec=codec,
        preset=preset,
        crf=crf,
        pixel_format="yuv420p",
        hwaccel=hwaccel is not None,
        **kwargs,
    )

    return VideoOutputWriter(
        output_path=output_path,
        config=config,
        width=width,
        height=height,
        fps=fps,
        source_video=source_video,
    )
