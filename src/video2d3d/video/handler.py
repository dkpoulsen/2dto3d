"""Video input handler for validating and extracting metadata from video files."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typing import Any
import cv2
import numpy as np
from loguru import logger

from video2d3d.utils.config import VideoInputConfig, get_config

from .exceptions import (
    VideoCodecNotSupportedError,
    VideoCorruptedError,
    VideoError,
    VideoFileNotFoundError,
    VideoFormatNotSupportedError,
    VideoMetadataExtractionError,
    VideoValidationError,
)
from .metadata import VideoMetadata


# Magic bytes (file signatures) for video format detection
MAGIC_BYTES: dict[str, list[bytes]] = {
    "mp4": [b"\x00\x00\x00\x1cftyp", b"\x00\x00\x00\x20ftyp", b"ftyp"],
    "avi": [b"RIFF"],
    "mov": [b"moov", b"mdat", b"wide", b"free", b"ftyp"],
    "mkv": [b"\x1a\x45\xdf\xa3"],  # EBML header
    "webm": [b"\x1a\x45\xdf\xa3"],  # EBML header (same as MKV)
}

# OpenCV FourCC codec mapping
FOURCC_TO_CODEC: dict[int, str] = {
    cv2.VideoWriter_fourcc(*"H264"): "h264",
    cv2.VideoWriter_fourcc(*"avc1"): "h264",
    cv2.VideoWriter_fourcc(*"X264"): "h264",
    cv2.VideoWriter_fourcc(*"mp4v"): "mpeg4",
    cv2.VideoWriter_fourcc(*"DIVX"): "divx",
    cv2.VideoWriter_fourcc(*"XVID"): "xvid",
    cv2.VideoWriter_fourcc(*"MJPG"): "mjpeg",
    cv2.VideoWriter_fourcc(*"HEVC"): "hevc",
    cv2.VideoWriter_fourcc(*"VP80"): "vp8",
    cv2.VideoWriter_fourcc(*"VP90"): "vp9",
}


class VideoInputHandler:
    """
    Handles video file input validation and metadata extraction.

    This class provides robust video file handling with support for:
    - Format validation using file extensions and magic bytes
    - Metadata extraction using OpenCV and FFmpeg
    - Comprehensive error handling for corrupted/unsupported files
    - Configurable validation rules

    Example usage:
        ```python
        from video2d3d.video import VideoInputHandler

        handler = VideoInputHandler()
        metadata = handler.validate_and_extract("video.mp4")
        print(f"Resolution: {metadata.width}x{metadata.height}")
        print(f"Duration: {metadata.duration_formatted}")
        ```
    """

    def __init__(
        self,
        config: VideoInputConfig | None = None,
        strict_validation: bool = True,
    ) -> None:
        """
        Initialize VideoInputHandler.

        Args:
            config: Video input configuration. If None, uses global config.
            strict_validation: If True, fails on any validation error.
                             If False, records errors but continues.
        """
        self.config = config or get_config().video_input
        self.strict_validation = strict_validation
        self._cap: cv2.VideoCapture | None = None

    def validate_file_exists(self, file_path: Path) -> None:
        """
        Validate that the video file exists.

        Args:
            file_path: Path to the video file.

        Raises:
            VideoFileNotFoundError: If the file does not exist.
        """
        if not file_path.exists():
            logger.error(f"Video file not found: {file_path}")
            raise VideoFileNotFoundError(file_path)

        if not file_path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise VideoFileNotFoundError(file_path)

    def validate_format(self, file_path: Path) -> str:
        """
        Validate the video format based on file extension.

        Args:
            file_path: Path to the video file.

        Returns:
            The detected format (lowercase).

        Raises:
            VideoFormatNotSupportedError: If format is not supported.
        """
        extension = file_path.suffix.lower().lstrip(".")
        if not extension:
            logger.error(f"No file extension found: {file_path}")
            raise VideoFormatNotSupportedError(
                file_path,
                format="unknown",
                supported_formats=self.config.supported_formats,
            )

        if extension not in self.config.supported_formats:
            logger.error(f"Unsupported video format: {extension}")
            raise VideoFormatNotSupportedError(
                file_path,
                format=extension,
                supported_formats=self.config.supported_formats,
            )

        logger.debug(f"Format validation passed: {extension}")
        return extension

    def validate_magic_bytes(self, file_path: Path, expected_format: str) -> bool:
        """
        Validate file format using magic bytes (file signature).

        Args:
            file_path: Path to the video file.
            expected_format: Expected format based on extension.

        Returns:
            True if magic bytes match, False otherwise.
        """
        if expected_format not in MAGIC_BYTES:
            # Format doesn't have magic byte validation defined
            logger.debug(f"No magic byte validation for format: {expected_format}")
            return True

        try:
            with open(file_path, "rb") as f:
                header = f.read(32)  # Read first 32 bytes

            expected_signatures = MAGIC_BYTES[expected_format]
            for signature in expected_signatures:
                if header.startswith(signature) or signature in header[:12]:
                    logger.debug(f"Magic bytes validated for {expected_format}: {file_path}")
                    return True

            logger.warning(
                f"Magic bytes mismatch for {file_path}. "
                f"Expected {expected_format} signature not found."
            )
            return False
        except OSError as e:
            logger.warning(f"Could not read file header for magic bytes check: {e}")
            return False

    def open_video(self, file_path: Path) -> cv2.VideoCapture:
        """
        Open the video file with OpenCV.

        Args:
            file_path: Path to the video file.

        Returns:
            OpenCV VideoCapture object.

        Raises:
            VideoCorruptedError: If the video cannot be opened.
        """
        cap = cv2.VideoCapture(str(file_path))

        if not cap.isOpened():
            cap.release()
            logger.error(f"Failed to open video file: {file_path}")
            raise VideoCorruptedError(file_path, reason="OpenCV could not open the file")

        return cap

    def extract_opencv_metadata(self, cap: cv2.VideoCapture, file_path: Path) -> VideoMetadata:
        """
        Extract video metadata using OpenCV.

        Args:
            cap: OpenCV VideoCapture object.
            file_path: Path to the video file.

        Returns:
            VideoMetadata with extracted information.

        Raises:
            VideoMetadataExtractionError: If critical metadata cannot be extracted.
        """
        errors: list[str] = []

        # Extract basic properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Extract codec
        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = FOURCC_TO_CODEC.get(fourcc_int, "")
        if not codec:
            # Try to decode FourCC code
            try:
                codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)])
                codec = codec.strip("\x00").lower()
            except (ValueError, TypeError):
                codec = "unknown"

        # Calculate duration
        duration = 0.0
        if fps > 0 and frame_count > 0:
            duration = frame_count / fps
        elif fps == 0:
            errors.append("Could not determine frame rate (FPS is 0)")

        # Validate critical metadata
        if width <= 0:
            errors.append("Invalid video width (0 or negative)")
        if height <= 0:
            errors.append("Invalid video height (0 or negative)")
        if frame_count <= 0:
            errors.append("No frames detected in video")

        # Check resolution limits
        if width > self.config.max_width:
            errors.append(f"Video width ({width}) exceeds maximum ({self.config.max_width})")
        if height > self.config.max_height:
            errors.append(f"Video height ({height}) exceeds maximum ({self.config.max_height})")

        # Get file size
        file_size = file_path.stat().st_size if file_path.exists() else 0

        metadata = VideoMetadata(
            file_path=file_path,
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration=duration,
            codec=codec,
            format=file_path.suffix.lower().lstrip("."),
            file_size=file_size,
            is_valid=len(errors) == 0,
            validation_errors=errors,
        )

        if errors and self.strict_validation:
            logger.error(f"Video validation failed: {file_path}")
            raise VideoValidationError(file_path, errors)

        return metadata

    def extract_ffmpeg_metadata(self, file_path: Path) -> dict[str, str]:
        """
        Extract detailed metadata using FFmpeg.

        This method uses FFmpeg to extract additional metadata that OpenCV
        might miss, such as bitrate, audio information, etc.

        Args:
            file_path: Path to the video file.

        Returns:
            Dictionary with FFmpeg-extracted metadata.
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"FFprobe failed for {file_path}: {result.stderr}")
                return {}

            import json

            return json.loads(result.stdout)  # type: ignore[no-any-return]

        except FileNotFoundError:
            logger.warning("FFprobe not found. Install FFmpeg for extended metadata.")
            return {}
        except subprocess.TimeoutExpired:
            logger.warning(f"FFprobe timed out for {file_path}")
            return {}
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse FFprobe output: {e}")
            return {}

    def enrich_metadata_with_ffmpeg(
        self, metadata: VideoMetadata, ffprobe_data: dict
    ) -> VideoMetadata:
        """
        Enrich VideoMetadata with FFmpeg-extracted information.

        Args:
            metadata: Existing VideoMetadata from OpenCV.
            ffprobe_data: Data extracted from FFprobe.

        Returns:
            Enriched VideoMetadata.
        """
        if not ffprobe_data:
            return metadata

        # Extract format-level information
        format_info = ffprobe_data.get("format", {})
        if format_info:
            if "bit_rate" in format_info:
                try:
                    metadata.bitrate = int(format_info["bit_rate"])
                except (ValueError, TypeError):
                    pass

        # Extract stream information
        streams = ffprobe_data.get("streams", [])
        for stream in streams:
            codec_type = stream.get("codec_type", "")

            if codec_type == "video" and not metadata.codec:
                # Use FFmpeg codec if OpenCV didn't detect it
                metadata.codec = stream.get("codec_name", metadata.codec)

            elif codec_type == "audio":
                metadata.has_audio = True
                metadata.audio_codec = stream.get("codec_name", "")
                if "sample_rate" in stream:
                    try:
                        metadata.audio_sample_rate = int(stream["sample_rate"])
                    except (ValueError, TypeError):
                        pass
                if "channels" in stream:
                    try:
                        metadata.audio_channels = int(stream["channels"])
                    except (ValueError, TypeError):
                        pass

        return metadata

    def validate_readability(self, cap: cv2.VideoCapture, file_path: Path) -> None:
        """
        Validate that video frames can actually be read.

        Args:
            cap: OpenCV VideoCapture object.
            file_path: Path to the video file.

        Raises:
            VideoCorruptedError: If frames cannot be read.
        """
        ret, frame = cap.read()

        if not ret or frame is None:
            logger.error(f"Cannot read frames from video: {file_path}")
            raise VideoCorruptedError(file_path, reason="Failed to read first frame from video")

        # Reset to beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        logger.debug(f"Frame read test passed: {file_path}")

    def validate_and_extract(
        self, video_path: str | Path, check_readability: bool = True
    ) -> VideoMetadata:
        """
        Validate a video file and extract its metadata.

        This is the main entry point for video validation. It performs
        all validation steps and extracts comprehensive metadata.

        Args:
            video_path: Path to the video file.
            check_readability: If True, attempts to read a frame to verify
                             the video is not corrupted.

        Returns:
            VideoMetadata containing all extracted information.

        Raises:
            VideoFileNotFoundError: If file does not exist.
            VideoFormatNotSupportedError: If format is not supported.
            VideoCorruptedError: If video is corrupted or unreadable.
            VideoValidationError: If validation fails (in strict mode).
        """
        file_path = Path(video_path).resolve()
        logger.info(f"Validating video: {file_path}")

        # Step 1: Check file exists
        self.validate_file_exists(file_path)

        # Step 2: Validate format by extension
        video_format = self.validate_format(file_path)

        # Step 3: Validate magic bytes
        if not self.validate_magic_bytes(file_path, video_format):
            if self.strict_validation:
                raise VideoCorruptedError(
                    file_path,
                    reason="File signature does not match expected format",
                )

        # Step 4: Open with OpenCV
        cap = self.open_video(file_path)
        self._cap = cap

        try:
            # Step 5: Check readability
            if check_readability:
                self.validate_readability(cap, file_path)

            # Step 6: Extract metadata with OpenCV
            metadata = self.extract_opencv_metadata(cap, file_path)

            # Step 7: Enrich with FFmpeg metadata
            ffprobe_data = self.extract_ffmpeg_metadata(file_path)
            if ffprobe_data:
                metadata = self.enrich_metadata_with_ffmpeg(metadata, ffprobe_data)

            logger.info(
                f"Video validated: {metadata.width}x{metadata.height}, "
                f"{metadata.fps:.2f}fps, {metadata.duration_formatted}"
            )

            return metadata

        finally:
            # Always release the capture
            cap.release()
            self._cap = None

    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """
        Get a specific frame from the currently open video.

        Note: This requires validate_and_extract to be called first
        to open the video.

        Args:
            frame_number: Zero-based frame index.

        Returns:
            Frame as numpy array, or None if frame cannot be read.
        """
        if self._cap is None or not self._cap.isOpened():
            logger.error("No video currently open. Call validate_and_extract first.")
            return None

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self._cap.read()

        if not ret or frame is None:
            logger.warning(f"Could not read frame {frame_number}")
            return None

        return frame

    def is_codec_supported(self, codec: str) -> bool:
        """
        Check if a video codec is supported.

        Args:
            codec: Codec name to check.

        Returns:
            True if codec is supported.
        """
        # Common supported codecs
        supported = {
            "h264",
            "avc1",
            "hevc",
            "h265",
            "vp8",
            "vp9",
            "mpeg4",
            "divx",
            "xvid",
            "mjpeg",
        }
        return codec.lower() in supported

    def __enter__(self) -> "VideoInputHandler":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Context manager exit - cleanup resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None


def validate_video(video_path: str | Path, strict: bool = True) -> VideoMetadata:
    """
    Convenience function to validate a video file.

    Args:
        video_path: Path to the video file.
        strict: If True, raises on validation errors.

    Returns:
        VideoMetadata with extracted information.

    Raises:
        VideoError or subclass on validation failure.
    """
    handler = VideoInputHandler(strict_validation=strict)
    return handler.validate_and_extract(video_path)
