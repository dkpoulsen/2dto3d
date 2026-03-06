"""Video upscaler for processing video frames in batch.

This module provides the VideoUpscaler class for upscaling video frames
efficiently, with support for progress tracking and memory management.
"""

from __future__ import annotations

import gc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

import numpy as np

from video2d3d.upscaling.base import BaseUpscaler, UpscaleResult
from video2d3d.upscaling.config import UpscalerConfig
from video2d3d.upscaling.esrgan import RealESRGANUpscaler, DummyUpscaler, create_upscaler
from video2d3d.utils.logger import get_logger


@dataclass
class VideoUpscaleStats:
    """Statistics for video upscaling operations.

    Attributes:
        frames_processed: Number of frames processed.
        total_frames: Total number of frames.
        total_time_ms: Total processing time in milliseconds.
        average_time_ms: Average time per frame.
        original_resolution: Original video resolution.
        output_resolution: Output video resolution.
        total_tiles: Total number of tiles processed.
        memory_peak_mb: Peak memory usage in MB.
    """

    frames_processed: int = 0
    total_frames: int = 0
    total_time_ms: float = 0.0
    average_time_ms: float = 0.0
    original_resolution: Tuple[int, int] = (0, 0)
    output_resolution: Tuple[int, int] = (0, 0)
    total_tiles: int = 0
    memory_peak_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "frames_processed": self.frames_processed,
            "total_frames": self.total_frames,
            "total_time_ms": self.total_time_ms,
            "average_time_ms": self.average_time_ms,
            "original_resolution": self.original_resolution,
            "output_resolution": self.output_resolution,
            "total_tiles": self.total_tiles,
            "memory_peak_mb": self.memory_peak_mb,
        }


class VideoUpscaler:
    """Video frame upscaler with batch processing support.

    This class provides efficient video frame upscaling with:
    - Batch processing for memory efficiency
    - Progress tracking
    - Support for generators to avoid loading all frames into memory
    - Integration with the video processing pipeline

    Example:
        ```python
        config = UpscalerConfig(
            model_type=ModelType.REAL_ESRGAN_X4PLUS,
            use_gpu=True,
            tile_size=512,
        )
        upscaler = VideoUpscaler(config)

        # Process frames from a generator
        for upscaled_frame in upscaler.upscale_frame_generator(frame_generator):
            # Process upscaled frame
            pass

        # Or process all frames at once
        upscaled_frames = upscaler.upscale_frames(frames)
        ```
    """

    def __init__(
        self,
        config: UpscalerConfig,
        use_dummy: bool = False,
    ) -> None:
        """Initialize the video upscaler.

        Args:
            config: Configuration for upscaling.
            use_dummy: If True, use a dummy upscaler for testing.
        """
        self.config = config
        self._logger = get_logger("video_upscaler")
        self._use_dummy = use_dummy
        self._upscaler: Optional[BaseUpscaler] = None
        self._is_initialized = False

    def initialize(self) -> None:
        """Initialize the underlying upscaler model.

        This method loads the model into memory. Call this before
        processing frames for faster first-frame processing.
        """
        if self._is_initialized:
            return

        self._logger.info(f"Initializing upscaler: {self.config.model_type.value}")
        self._upscaler = create_upscaler(self.config, use_dummy=self._use_dummy)
        self._is_initialized = True
        self._logger.info("Upscaler initialized successfully")

    def _ensure_initialized(self) -> None:
        """Ensure the upscaler is initialized."""
        if not self._is_initialized:
            self.initialize()

    @property
    def scale(self) -> int:
        """Get the scale factor."""
        return self.config.effective_scale

    @property
    def is_initialized(self) -> bool:
        """Check if the upscaler is initialized."""
        return self._is_initialized

    def upscale_frame(self, frame: np.ndarray) -> np.ndarray:
        """Upscale a single frame.

        Args:
            frame: Input frame (H, W, C) in RGB format.

        Returns:
            Upscaled frame.
        """
        self._ensure_initialized()

        if self._upscaler is None:
            raise RuntimeError("Upscaler not initialized")

        return self._upscaler.upscale(frame)

    def upscale_frames(
        self,
        frames: List[np.ndarray],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[np.ndarray]:
        """Upscale a list of frames.

        Args:
            frames: List of input frames.
            progress_callback: Optional callback(completed, total).

        Returns:
            List of upscaled frames.
        """
        self._ensure_initialized()

        if self._upscaler is None:
            raise RuntimeError("Upscaler not initialized")

        upscaled_frames = []
        total = len(frames)

        for i, frame in enumerate(frames):
            upscaled = self._upscaler.upscale(frame)
            upscaled_frames.append(upscaled)

            if progress_callback:
                progress_callback(i + 1, total)

            # Periodic cleanup
            if (i + 1) % 100 == 0:
                gc.collect()

        return upscaled_frames

    def upscale_frame_generator(
        self,
        frame_generator: Generator[Tuple[int, np.ndarray], None, None],
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        total_frames: Optional[int] = None,
    ) -> Generator[Tuple[int, np.ndarray, UpscaleResult], None, None]:
        """Upscale frames from a generator.

        This is the most memory-efficient way to process large videos.

        Args:
            frame_generator: Generator yielding (frame_number, frame) tuples.
            progress_callback: Optional callback(frame_number, completed, total).
            total_frames: Total number of frames (for progress tracking).

        Yields:
            Tuples of (frame_number, upscaled_frame, result_info).
        """
        self._ensure_initialized()

        if self._upscaler is None:
            raise RuntimeError("Upscaler not initialized")

        processed = 0

        for frame_number, frame in frame_generator:
            upscaled, result = self._upscaler.upscale(frame, return_info=True)

            processed += 1

            if progress_callback and total_frames:
                progress_callback(frame_number, processed, total_frames)

            yield frame_number, upscaled, result

            # Periodic cleanup
            if processed % 100 == 0:
                gc.collect()

    def upscale_video(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> VideoUpscaleStats:
        """Upscale an entire video file.

        Args:
            input_path: Path to input video.
            output_path: Path to output video.
            progress_callback: Optional callback(stage, current, total).

        Returns:
            Statistics about the upscaling operation.
        """
        from video2d3d.video.frame_extractor import FrameExtractor
        from video2d3d.video.video_writer import VideoOutputWriter

        input_path = Path(input_path)
        output_path = Path(output_path)

        self._logger.info(f"Upscaling video: {input_path} -> {output_path}")

        # Initialize stats
        stats = VideoUpscaleStats()

        # Extract frames
        extractor = FrameExtractor(input_path)
        metadata = extractor.metadata

        stats.total_frames = metadata.frame_count
        stats.original_resolution = (metadata.height, metadata.width)

        # Calculate output resolution
        scale = self.scale
        output_height = metadata.height * scale
        output_width = metadata.width * scale
        stats.output_resolution = (output_height, output_width)

        self._logger.info(
            f"Upscaling {metadata.frame_count} frames from "
            f"{metadata.width}x{metadata.height} to {output_width}x{output_height}"
        )

        # Create video writer
        writer = VideoOutputWriter(
            output_path=output_path,
            width=output_width,
            height=output_height,
            fps=metadata.fps,
            source_video=input_path,
        )

        import time

        start_time = time.perf_counter()

        try:
            writer.open()

            # Process frames
            for frame_number, upscaled_frame, result in self.upscale_frame_generator(
                extractor.extract_frames(),
                progress_callback=lambda fn, c, t: (
                    progress_callback("upscaling", c, t) if progress_callback else None
                ),
                total_frames=metadata.frame_count,
            ):
                # Write upscaled frame
                writer.write_frame(upscaled_frame)
                stats.frames_processed += 1
                stats.total_tiles += result.tiles_processed

                if progress_callback:
                    progress_callback("writing", stats.frames_processed, stats.total_frames)

        finally:
            writer.close()
            extractor.close()

        # Calculate stats
        stats.total_time_ms = (time.perf_counter() - start_time) * 1000
        stats.average_time_ms = (
            stats.total_time_ms / stats.frames_processed if stats.frames_processed > 0 else 0
        )

        self._logger.info(
            f"Video upscaling complete: {stats.frames_processed} frames in "
            f"{stats.total_time_ms / 1000:.2f}s ({stats.average_time_ms:.2f}ms/frame)"
        )

        return stats

    def cleanup(self) -> None:
        """Release resources."""
        if self._upscaler is not None:
            if hasattr(self._upscaler, "cleanup"):
                self._upscaler.cleanup()
            del self._upscaler
            self._upscaler = None
            self._is_initialized = False
            gc.collect()
            self._logger.info("Video upscaler resources released")

    def __enter__(self) -> "VideoUpscaler":
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.cleanup()


def upscale_video(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    config: Optional[UpscalerConfig] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> VideoUpscaleStats:
    """Convenience function to upscale a video.

    Args:
        input_path: Path to input video.
        output_path: Path to output video.
        config: Upscaler configuration. Uses defaults if None.
        progress_callback: Optional callback(stage, current, total).

    Returns:
        Statistics about the upscaling operation.
    """
    if config is None:
        config = UpscalerConfig()

    with VideoUpscaler(config) as upscaler:
        return upscaler.upscale_video(input_path, output_path, progress_callback)


def upscale_frames(
    frames: List[np.ndarray],
    config: Optional[UpscalerConfig] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[np.ndarray]:
    """Convenience function to upscale a list of frames.

    Args:
        frames: List of input frames.
        config: Upscaler configuration. Uses defaults if None.
        progress_callback: Optional callback(completed, total).

    Returns:
        List of upscaled frames.
    """
    if config is None:
        config = UpscalerConfig()

    with VideoUpscaler(config) as upscaler:
        return upscaler.upscale_frames(frames, progress_callback)
