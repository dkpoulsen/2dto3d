"""Efficient frame extraction system with memory management and configurable sampling.

This module provides a comprehensive frame extraction system that:
- Reads video streams efficiently using OpenCV
- Decodes frames with configurable sampling rates
- Handles memory management for large videos
- Supports multiple sampling strategies
- Provides generator-based iteration for memory efficiency

Example usage:
    ```python
    from video2d3d.video import FrameExtractor, SamplingStrategy

    # Extract every 10th frame
    extractor = FrameExtractor("video.mp4", sampling_interval=10)
    for frame_number, frame in extractor.extract_frames():
        process_frame(frame)

    # Extract a specific range of frames
    for frame in extractor.extract_range(start=100, end=200):
        save_frame(frame)

    # Use generator for memory efficiency
    for frame in extractor:
        process_frame(frame)
    ```
"""

from __future__ import annotations

import gc
import threading
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Iterator,
)

import cv2
import numpy as np

from video2d3d.utils.logger import get_logger

from .exceptions import (
    FrameBufferError,
    FrameExtractionError,
    InvalidSamplingStrategyError,
    MemoryLimitExceededError,
    VideoCorruptedError,
    VideoFileNotFoundError,
)
from .handler import VideoInputHandler
from .metadata import VideoMetadata

# Constants
DEFAULT_ESTIMATED_GOP_SIZE = 30  # Typical GOP (Group of Pictures) size
DEFAULT_BUFFER_SIZE = 100
DEFAULT_MAX_MEMORY_MB = 1024.0  # 1GB default


def _get_frame_logger():
    """Get the frame extraction logger (lazy initialization)."""
    return get_logger("frame_extractor")


class SamplingStrategy(Enum):
    """Frame sampling strategies for extraction."""

    ALL = "all"  # Extract all frames
    INTERVAL = "interval"  # Extract every Nth frame
    UNIFORM = "uniform"  # Extract N frames uniformly distributed
    KEYFRAME = "keyframe"  # Extract only keyframes (I-frames)
    CUSTOM = "custom"  # Use custom frame indices


@dataclass
class FrameExtractorConfig:
    """Configuration for frame extraction.

    Attributes:
        sampling_strategy: Strategy for sampling frames.
        sampling_interval: Interval for INTERVAL strategy (extract every Nth frame).
        target_frame_count: Target number of frames for UNIFORM strategy.
        buffer_size: Maximum number of frames to keep in buffer.
        max_memory_mb: Maximum memory usage in megabytes.
        prefetch_count: Number of frames to prefetch ahead.
        resize_width: Optional width to resize frames (0 = no resize).
        resize_height: Optional height to resize frames (0 = no resize).
        convert_to_rgb: Convert BGR to RGB (OpenCV reads as BGR).
        normalize: Normalize pixel values to [0, 1] range.
    """

    sampling_strategy: SamplingStrategy = SamplingStrategy.ALL
    sampling_interval: int = 1
    target_frame_count: int | None = None
    buffer_size: int = DEFAULT_BUFFER_SIZE
    max_memory_mb: float = DEFAULT_MAX_MEMORY_MB
    prefetch_count: int = 10  # Reserved for future use
    resize_width: int = 0
    resize_height: int = 0
    convert_to_rgb: bool = True
    normalize: bool = False

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.sampling_interval < 1:
            raise ValueError(
                f"sampling_interval must be >= 1, got {self.sampling_interval}"
            )
        if self.target_frame_count is not None and self.target_frame_count < 1:
            raise ValueError(
                f"target_frame_count must be >= 1, got {self.target_frame_count}"
            )
        if self.buffer_size < 1:
            raise ValueError(f"buffer_size must be >= 1, got {self.buffer_size}")
        if self.max_memory_mb <= 0:
            raise ValueError(
                f"max_memory_mb must be > 0, got {self.max_memory_mb}"
            )


@dataclass
class FrameInfo:
    """Information about an extracted frame.

    Attributes:
        frame_number: Zero-based frame index in the video.
        timestamp: Timestamp in seconds.
        frame: The frame as a numpy array (or None if not loaded).
        is_keyframe: Whether this is a keyframe (I-frame).
    """

    frame_number: int
    timestamp: float
    frame: np.ndarray | None = None
    is_keyframe: bool = False

    @property
    def is_loaded(self) -> bool:
        """Check if the frame data is loaded."""
        return self.frame is not None


class FrameBuffer:
    """Memory-efficient circular buffer for frame storage.

    This buffer manages frame storage with automatic memory management,
    supporting a maximum size and optional memory limit enforcement.

    Attributes:
        max_size: Maximum number of frames to store.
        max_memory_mb: Maximum memory usage in megabytes.
    """

    def __init__(
        self,
        max_size: int = 100,
        max_memory_mb: float = 1024.0,
    ) -> None:
        """Initialize the frame buffer.

        Args:
            max_size: Maximum number of frames to store.
            max_memory_mb: Maximum memory usage in megabytes.
        """
        self.max_size = max_size
        self.max_memory_mb = max_memory_mb
        self._buffer: dict[int, np.ndarray] = {}
        self._access_order: deque[int] = deque()
        self._lock = threading.Lock()
        self._current_memory_mb: float = 0.0

    def _estimate_frame_size_mb(self, frame: np.ndarray) -> float:
        """Estimate the memory size of a frame in megabytes."""
        return frame.nbytes / (1024 * 1024)

    def _evict_oldest(self) -> None:
        """Evict the oldest frame from the buffer."""
        if not self._access_order:
            return

        oldest_key = self._access_order.popleft()
        if oldest_key in self._buffer:
            frame = self._buffer.pop(oldest_key)
            self._current_memory_mb -= self._estimate_frame_size_mb(frame)

    def put(self, frame_number: int, frame: np.ndarray) -> None:
        """Add a frame to the buffer.

        Args:
            frame_number: Frame index.
            frame: Frame data as numpy array.

        Raises:
            FrameBufferError: If frame exceeds memory limit.
        """
        frame_size_mb = self._estimate_frame_size_mb(frame)

        # Check if single frame exceeds memory limit
        if frame_size_mb > self.max_memory_mb:
            raise FrameBufferError(
                f"Single frame size ({frame_size_mb:.1f}MB) exceeds "
                f"memory limit ({self.max_memory_mb:.1f}MB)",
                buffer_size=len(self._buffer),
            )

        with self._lock:
            # Evict frames until we have space
            while (
                len(self._buffer) >= self.max_size
                or self._current_memory_mb + frame_size_mb > self.max_memory_mb
            ):
                if not self._access_order:
                    break
                self._evict_oldest()

            # Remove old entry if updating existing frame
            if frame_number in self._buffer:
                old_frame = self._buffer[frame_number]
                self._current_memory_mb -= self._estimate_frame_size_mb(old_frame)
                self._access_order.remove(frame_number)

            # Add new frame
            self._buffer[frame_number] = frame
            self._access_order.append(frame_number)
            self._current_memory_mb += frame_size_mb

    def get(self, frame_number: int) -> np.ndarray | None:
        """Get a frame from the buffer.

        Args:
            frame_number: Frame index to retrieve.

        Returns:
            Frame data or None if not in buffer.
        """
        with self._lock:
            return self._buffer.get(frame_number)

    def contains(self, frame_number: int) -> bool:
        """Check if a frame is in the buffer."""
        with self._lock:
            return frame_number in self._buffer

    def clear(self) -> None:
        """Clear all frames from the buffer."""
        with self._lock:
            self._buffer.clear()
            self._access_order.clear()
            self._current_memory_mb = 0.0
            gc.collect()

    @property
    def size(self) -> int:
        """Get the current number of frames in the buffer."""
        return len(self._buffer)

    @property
    def memory_usage_mb(self) -> float:
        """Get the current memory usage in megabytes."""
        return self._current_memory_mb

    def get_stats(self) -> dict[str, Any]:
        """Get buffer statistics."""
        with self._lock:
            return {
                "size": len(self._buffer),
                "max_size": self.max_size,
                "memory_mb": self._current_memory_mb,
                "max_memory_mb": self.max_memory_mb,
                "utilization": len(self._buffer) / self.max_size if self.max_size > 0 else 0,
            }


class FrameExtractor:
    """Efficient frame extractor with memory management and sampling support.

    This class provides comprehensive frame extraction capabilities including:
    - Multiple sampling strategies (all, interval, uniform, keyframe)
    - Memory-efficient buffer management for large videos
    - Generator-based iteration for streaming processing
    - Configurable frame preprocessing (resize, color conversion, normalization)
    - Thread-safe operations

    Example usage:
        ```python
        # Basic usage - extract all frames
        extractor = FrameExtractor("video.mp4")
        for frame_number, frame in extractor.extract_frames():
            print(f"Frame {frame_number}: shape={frame.shape}")

        # With sampling - extract every 10th frame
        extractor = FrameExtractor("video.mp4", sampling_interval=10)
        for frame_number, frame in extractor:
            process_frame(frame)

        # With configuration
        config = FrameExtractorConfig(
            sampling_strategy=SamplingStrategy.UNIFORM,
            target_frame_count=100,
            resize_width=640,
            resize_height=480,
        )
        extractor = FrameExtractor("video.mp4", config=config)
        frames = extractor.extract_all()
        ```
    """

    VALID_STRATEGIES = ["all", "interval", "uniform", "keyframe", "custom"]

    def __init__(
        self,
        video_path: str | Path,
        config: FrameExtractorConfig | None = None,
        *,
        sampling_interval: int = 1,
        target_frame_count: int | None = None,
        resize_width: int = 0,
        resize_height: int = 0,
        convert_to_rgb: bool = True,
        validate_video: bool = True,
    ) -> None:
        """Initialize the frame extractor.

        Args:
            video_path: Path to the video file.
            config: Optional FrameExtractorConfig. If provided, other params ignored.
            sampling_interval: Extract every Nth frame (default: 1 = all frames).
            target_frame_count: Target number of frames for uniform sampling.
            resize_width: Resize frames to this width (0 = no resize).
            resize_height: Resize frames to this height (0 = no resize).
            convert_to_rgb: Convert BGR to RGB (default: True).
            validate_video: Whether to validate the video file first (default: True).

        Raises:
            VideoFileNotFoundError: If the video file doesn't exist.
            VideoCorruptedError: If the video file is corrupted.
        """
        self.video_path = Path(video_path).resolve()

        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            self.config = FrameExtractorConfig(
                sampling_interval=sampling_interval,
                target_frame_count=target_frame_count,
                resize_width=resize_width,
                resize_height=resize_height,
                convert_to_rgb=convert_to_rgb,
            )

        # Initialize video capture and metadata
        self._cap: cv2.VideoCapture | None = None
        self._metadata: VideoMetadata | None = None
        self._frame_indices: list[int] | None = None
        self._current_index: int = 0
        self._lock = threading.Lock()

        # Initialize frame buffer
        self._buffer = FrameBuffer(
            max_size=self.config.buffer_size,
            max_memory_mb=self.config.max_memory_mb,
        )

        # Validate and open video
        if validate_video:
            self._validate_video()
        else:
            self._open_video()

        _get_frame_logger().info(
            f"FrameExtractor initialized for {self.video_path.name}: "
            f"{self.metadata.frame_count} frames, {self.metadata.fps:.2f} fps"
        )

    def _validate_video(self) -> None:
        """Validate the video file and extract metadata."""
        if not self.video_path.exists():
            raise VideoFileNotFoundError(self.video_path)

        handler = VideoInputHandler()
        self._metadata = handler.validate_and_extract(self.video_path, check_readability=True)
        self._open_video()

    def _open_video(self) -> None:
        """Open the video file with OpenCV."""
        self._cap = cv2.VideoCapture(str(self.video_path))

        if not self._cap.isOpened():
            raise VideoCorruptedError(self.video_path, reason="Could not open video with OpenCV")

    @property
    def metadata(self) -> VideoMetadata:
        """Get video metadata."""
        if self._metadata is None:
            if self._cap is None:
                self._open_video()
            # Create basic metadata from capture properties
            self._metadata = VideoMetadata(
                file_path=self.video_path,
                width=int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                height=int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                fps=self._cap.get(cv2.CAP_PROP_FPS),
                frame_count=int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                duration=self._cap.get(cv2.CAP_PROP_FRAME_COUNT)
                / max(self._cap.get(cv2.CAP_PROP_FPS), 1),
            )
        return self._metadata

    def _calculate_frame_indices(self) -> list[int]:
        """Calculate which frame indices to extract based on sampling strategy."""
        total_frames = self.metadata.frame_count

        if self.config.sampling_strategy == SamplingStrategy.ALL:
            return list(range(total_frames))

        elif self.config.sampling_strategy == SamplingStrategy.INTERVAL:
            interval = max(1, self.config.sampling_interval)
            return list(range(0, total_frames, interval))

        elif self.config.sampling_strategy == SamplingStrategy.UNIFORM:
            target = self.config.target_frame_count or 100
            target = min(target, total_frames)
            if target >= total_frames:
                return list(range(total_frames))
            # Uniform distribution
            step = total_frames / target
            return [int(i * step) for i in range(target)]

        elif self.config.sampling_strategy == SamplingStrategy.KEYFRAME:
            # Note: OpenCV doesn't provide direct keyframe detection
            # We estimate based on typical GOP size
            return list(range(0, total_frames, DEFAULT_ESTIMATED_GOP_SIZE))

        else:
            raise InvalidSamplingStrategyError(
                str(self.config.sampling_strategy),
                valid_strategies=self.VALID_STRATEGIES,
            )

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply preprocessing to a frame.

        Args:
            frame: Raw frame from video.

        Returns:
            Preprocessed frame.
        """
        # Resize if configured
        if self.config.resize_width > 0 or self.config.resize_height > 0:
            width = self.config.resize_width or frame.shape[1]
            height = self.config.resize_height or frame.shape[0]
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

        # Convert BGR to RGB
        if self.config.convert_to_rgb:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        if self.config.normalize:
            frame = frame.astype(np.float32) / 255.0

        return frame

    def _read_frame_at(self, frame_number: int) -> np.ndarray:
        """Read a frame at a specific index.

        Args:
            frame_number: Zero-based frame index.

        Returns:
            Frame as numpy array.

        Raises:
            FrameExtractionError: If frame cannot be read.
        """
        if self._cap is None:
            raise FrameExtractionError(
                self.video_path, frame_number, "Video capture not initialized"
            )

        # Check buffer first
        cached = self._buffer.get(frame_number)
        if cached is not None:
            return cached

        # Seek to frame
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self._cap.read()

        if not ret or frame is None:
            raise FrameExtractionError(
                self.video_path,
                frame_number,
                f"Failed to read frame at index {frame_number}",
            )

        # Preprocess
        frame = self._preprocess_frame(frame)

        # Cache in buffer
        try:
            self._buffer.put(frame_number, frame)
        except FrameBufferError as e:
            _get_frame_logger().warning(f"Buffer error: {e}")

        return frame

    def _estimate_memory_requirement(self, frame_count: int) -> float:
        """Estimate memory requirement for extracting frames.

        Args:
            frame_count: Number of frames to extract.

        Returns:
            Estimated memory in megabytes.
        """
        width = self.config.resize_width or self.metadata.width
        height = self.config.resize_height or self.metadata.height
        channels = 3
        bytes_per_element = 4 if self.config.normalize else 1
        bytes_per_frame = width * height * channels * bytes_per_element
        return (bytes_per_frame * frame_count) / (1024 * 1024)

    def extract_frames(
        self,
        start_frame: int = 0,
        end_frame: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """Extract frames as a generator.

        This is the most memory-efficient way to process frames, as only
        one frame is loaded at a time.

        Args:
            start_frame: Starting frame index (inclusive).
            end_frame: Ending frame index (exclusive). None = last frame.
            progress_callback: Optional callback(completed, total) for progress tracking.

        Yields:
            Tuples of (frame_number, frame).

        Example:
            ```python
            for frame_num, frame in extractor.extract_frames(0, 100):
                print(f"Processing frame {frame_num}")
            ```
        """
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()

        end_frame = end_frame or self.metadata.frame_count
        total_frames = len([i for i in self._frame_indices if start_frame <= i < end_frame])
        completed = 0

        for frame_number in self._frame_indices:
            if frame_number < start_frame:
                continue
            if frame_number >= end_frame:
                break

            try:
                frame = self._read_frame_at(frame_number)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_frames)
                yield frame_number, frame
            except FrameExtractionError as e:
                _get_frame_logger().warning(f"Skipping frame {frame_number}: {e}")
                continue

    def extract_range(
        self,
        start_frame: int,
        end_frame: int,
    ) -> list[np.ndarray]:
        """Extract a range of frames into a list.

        Warning: This loads all frames into memory. For large ranges,
        use extract_frames() generator instead.

        Args:
            start_frame: Starting frame index (inclusive).
            end_frame: Ending frame index (exclusive).

        Returns:
            List of frames.

        Raises:
            MemoryLimitExceededError: If estimated memory exceeds limit.
        """
        frame_count = end_frame - start_frame
        estimated_memory = self._estimate_memory_requirement(frame_count)

        if estimated_memory > self.config.max_memory_mb:
            raise MemoryLimitExceededError(
                self.video_path,
                required_mb=estimated_memory,
                available_mb=self.config.max_memory_mb,
            )

        frames = []
        for _, frame in self.extract_frames(start_frame, end_frame):
            frames.append(frame)
        return frames

    def extract_all(self) -> list[np.ndarray]:
        """Extract all frames according to the sampling strategy.

        Warning: This loads all frames into memory. For large videos,
        use extract_frames() generator instead.

        Returns:
            List of frames.

        Raises:
            MemoryLimitExceededError: If estimated memory exceeds limit.
        """
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()

        frame_count = len(self._frame_indices)
        estimated_memory = self._estimate_memory_requirement(frame_count)

        if estimated_memory > self.config.max_memory_mb:
            raise MemoryLimitExceededError(
                self.video_path,
                required_mb=estimated_memory,
                available_mb=self.config.max_memory_mb,
            )

        return [frame for _, frame in self.extract_frames()]

    def get_frame(self, frame_number: int) -> np.ndarray:
        """Get a single frame by index.

        Args:
            frame_number: Zero-based frame index.

        Returns:
            Frame as numpy array.

        Raises:
            FrameExtractionError: If frame cannot be read.
        """
        if frame_number < 0 or frame_number >= self.metadata.frame_count:
            raise FrameExtractionError(
                self.video_path,
                frame_number,
                f"Frame index out of range [0, {self.metadata.frame_count})",
            )

        return self._read_frame_at(frame_number)

    def get_frame_info(self, frame_number: int) -> FrameInfo:
        """Get frame information without loading the frame data.

        Args:
            frame_number: Zero-based frame index.

        Returns:
            FrameInfo with metadata.
        """
        if frame_number < 0 or frame_number >= self.metadata.frame_count:
            raise FrameExtractionError(
                self.video_path,
                frame_number,
                f"Frame index out of range [0, {self.metadata.frame_count})",
            )

        timestamp = frame_number / self.metadata.fps if self.metadata.fps > 0 else 0.0

        return FrameInfo(
            frame_number=frame_number,
            timestamp=timestamp,
            is_keyframe=False,  # We don't have keyframe info from OpenCV
        )

    def get_sample_indices(self) -> list[int]:
        """Get the list of frame indices that will be extracted."""
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()
        return self._frame_indices.copy()

    def seek(self, frame_number: int) -> None:
        """Seek to a specific frame for iteration.

        Args:
            frame_number: Frame index to seek to.
        """
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()

        # Find position in frame indices
        try:
            self._current_index = self._frame_indices.index(frame_number)
        except ValueError:
            raise FrameExtractionError(
                self.video_path,
                frame_number,
                "Frame not in sample indices",
            )

    def tell(self) -> int:
        """Get current frame position in iteration."""
        if self._frame_indices is None or self._current_index >= len(self._frame_indices):
            return -1
        return self._frame_indices[self._current_index]

    def clear_buffer(self) -> None:
        """Clear the frame buffer to free memory."""
        self._buffer.clear()

    def get_buffer_stats(self) -> dict[str, Any]:
        """Get buffer statistics."""
        return self._buffer.get_stats()

    def __iter__(self) -> Iterator[tuple[int, np.ndarray]]:
        """Iterate over extracted frames."""
        self._current_index = 0
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()

        for frame_number in self._frame_indices:
            try:
                frame = self._read_frame_at(frame_number)
                yield frame_number, frame
            except FrameExtractionError as e:
                _get_frame_logger().warning(f"Skipping frame {frame_number}: {e}")
                continue

    def __len__(self) -> int:
        """Get the number of frames that will be extracted."""
        if self._frame_indices is None:
            self._frame_indices = self._calculate_frame_indices()
        return len(self._frame_indices)

    def __enter__(self) -> FrameExtractor:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self) -> None:
        """Release resources."""
        with self._lock:
            if self._cap is not None:
                self._cap.release()
                self._cap = None
            self._buffer.clear()
            _get_frame_logger().debug("FrameExtractor resources released")


def extract_frames(
    video_path: str | Path,
    sampling_interval: int = 1,
    start_frame: int = 0,
    end_frame: int | None = None,
) -> Generator[tuple[int, np.ndarray], None, None]:
    """Convenience function to extract frames from a video.

    Args:
        video_path: Path to the video file.
        sampling_interval: Extract every Nth frame.
        start_frame: Starting frame index.
        end_frame: Ending frame index (None = last frame).

    Yields:
        Tuples of (frame_number, frame).

    Example:
        ```python
        for frame_num, frame in extract_frames("video.mp4", sampling_interval=10):
            print(f"Frame {frame_num}: {frame.shape}")
        ```
    """
    config = FrameExtractorConfig(
        sampling_strategy=SamplingStrategy.INTERVAL,
        sampling_interval=sampling_interval,
    )

    with FrameExtractor(video_path, config=config) as extractor:
        yield from extractor.extract_frames(start_frame, end_frame)


def extract_frame_at(video_path: str | Path, frame_number: int) -> np.ndarray:
    """Convenience function to extract a single frame.

    Args:
        video_path: Path to the video file.
        frame_number: Frame index to extract.

    Returns:
        Frame as numpy array.
    """
    with FrameExtractor(video_path, validate_video=False) as extractor:
        return extractor.get_frame(frame_number)
