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

import os
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
    AudioProcessingError,
    FFmpegProcessError,
    InvalidVideoDimensionsError,
    VideoWriteError,
)


def _get_writer_logger():
    """Get the video writer logger (lazy initialization)."""
    return get_logger("video_writer")


class VideoCodec(Enum):
    """Supported video codecs for encoding."""

    H264 = "libx264"
    H265 = "libx265"
    VP9 = "libvpx-vp9"
    AV1 = "libaom-av1"
    MPEG4 = "mpeg4"
    PRORES = "prores_ks"
    MJPEG = "mjpeg"


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
    "libx264": {
        "preset": "medium",
        "crf": 23,
        "pixel_format": "yuv420p",
    },
    "libx265": {
        "preset": "medium",
        "crf": 28,
        "pixel_format": "yuv420p",
    },
    "libvpx-vp9": {
        "crf": 31,
        "pixel_format": "yuv420p",
        "deadline": "good",
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
        metadata: Video metadata to embed.
        faststart: Move atom to start of file (for web streaming).
        threads: Number of encoding threads (0 = auto).
        hwaccel: Enable hardware acceleration if available.
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
    metadata: dict[str, str] = field(default_factory=dict)
    faststart: bool = True
    threads: int = 0
    hwaccel: bool = False

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

        # Validate CRF range
        if self.crf is not None:
            if self.codec in ("libx264", "libx265"):
                if not 0 <= self.crf <= 51:
                    raise ValueError(f"CRF must be 0-51 for {self.codec}, got {self.crf}")
            elif self.codec == "libvpx-vp9":
                if not 0 <= self.crf <= 63:
                    raise ValueError(f"CRF must be 0-63 for VP9, got {self.crf}")

        # Validate preset
        valid_presets = [p.value for p in Preset]
        if self.preset and self.preset not in valid_presets:
            raise ValueError(
                f"Invalid preset '{self.preset}'. Valid presets: {', '.join(valid_presets)}"
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
        self.width = width
        self.height = height
        self.fps = fps
        self.source_video = Path(source_video) if source_video else None
        self.input_pixel_format = input_pixel_format
        self._progress_callback = progress_callback
        self._total_frames = total_frames or 0
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
        cmd.extend(["-c:v", self.config.codec])

        # Codec-specific options
        if self.config.codec in ("libx264", "libx265"):
            if self.config.preset:
                cmd.extend(["-preset", self.config.preset])
            if self.config.crf is not None and self.config.bitrate is None:
                cmd.extend(["-crf", str(self.config.crf)])
            elif self.config.bitrate is not None:
                cmd.extend(["-b:v", str(self.config.bitrate)])
            if self.config.codec == "libx265":
                cmd.extend(["-tag:v", "hvc1"])  # Better compatibility

        elif self.config.codec == "libvpx-vp9":
            if self.config.crf is not None:
                cmd.extend(["-crf", str(self.config.crf)])
            cmd.extend(["-b:v", "0"])  # Use CRF mode

        elif self.config.codec == "prores_ks":
            profile = CODEC_DEFAULTS.get("prores_ks", {}).get("profile", 3)
            cmd.extend(["-profile:v", str(profile)])

        elif self.config.codec == "mjpeg":
            cmd.extend(["-q:v", str(CODEC_DEFAULTS.get("mjpeg", {}).get("q", 5))])

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

    def _extract_audio(self) -> None:
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
