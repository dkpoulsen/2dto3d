"""Parallel batch processing for frame-by-frame video operations.

This module provides efficient parallel batch processing capabilities:
- Multiprocessing-based worker pools for CPU-bound tasks
- Configurable batch sizes and worker counts
- Progress tracking and callbacks
- Graceful error handling and recovery
- Memory-efficient processing with chunked batches

Example usage:
    ```python
    from video2d3d.core.batch_processor import (
        BatchProcessorConfig,
        FrameBatchProcessor,
    )

    config = BatchProcessorConfig(batch_size=8, num_workers=4)
    processor = FrameBatchProcessor(config=config)

    def process_frame(frame):
        return processed_frame

    results = processor.process_frames(frames, process_frame)
    ```
"""

from __future__ import annotations

import gc
import multiprocessing as mp
import threading
import time
from collections.abc import Generator, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    TypeVar,
)

import numpy as np

from video2d3d.utils.logger import get_logger, log_exception, log_performance

if TYPE_CHECKING:
    from loguru import Logger


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

DEFAULT_BATCH_SIZE: int = 8
DEFAULT_NUM_WORKERS: int = 4
DEFAULT_CHUNK_SIZE: int = 1
DEFAULT_TIMEOUT_SECONDS: float = 300.0
MAX_WORKERS_LIMIT: int = 32
MIN_BATCH_SIZE: int = 1


class ProcessingMode(Enum):
    """Available processing modes for batch operations."""

    MULTIPROCESSING = "multiprocessing"
    THREADING = "threading"
    SEQUENTIAL = "sequential"


class BatchProcessorError(Exception):
    """Base exception for batch processing errors."""

    def __init__(
        self,
        message: str,
        *,
        batch_index: int | None = None,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.batch_index = batch_index
        self.original_exception = original_exception


class WorkerTimeoutError(BatchProcessorError):
    """Raised when a worker exceeds the timeout limit."""

    pass


class WorkerInitializationError(BatchProcessorError):
    """Raised when worker initialization fails."""

    pass


def _get_batch_logger() -> Logger:
    return get_logger("batch_processor")


@dataclass
class BatchProcessorConfig:
    """Configuration for batch processing operations.

    Attributes:
        batch_size: Number of items to process per batch.
        num_workers: Number of parallel workers.
        mode: Processing mode (multiprocessing, threading, sequential).
        chunk_size: Items per chunk sent to workers.
        timeout_seconds: Maximum time per batch in seconds.
        max_retries: Number of retry attempts for failed batches.
        preserve_order: Whether to preserve input order in output.
        enable_progress: Whether to enable progress tracking.
        progress_callback: Optional callback for progress updates.
        error_callback: Optional callback for error handling.
        use_shared_memory: Use shared memory for large arrays (multiprocessing only).
        gc_threshold: Garbage collection threshold (0 to disable).
    """

    batch_size: int = DEFAULT_BATCH_SIZE
    num_workers: int = DEFAULT_NUM_WORKERS
    mode: ProcessingMode = ProcessingMode.MULTIPROCESSING
    chunk_size: int = DEFAULT_CHUNK_SIZE
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = 2
    preserve_order: bool = True
    enable_progress: bool = True
    progress_callback: Callable[[int, int], None] | None = None
    error_callback: Callable[[Exception, int], None] | None = None
    use_shared_memory: bool = False
    gc_threshold: int = 100

    def __post_init__(self) -> None:
        if self.batch_size < MIN_BATCH_SIZE:
            raise ValueError(f"batch_size must be >= {MIN_BATCH_SIZE}, got {self.batch_size}")

        if self.num_workers < 1:
            raise ValueError(f"num_workers must be >= 1, got {self.num_workers}")

        if self.num_workers > MAX_WORKERS_LIMIT:
            _get_batch_logger().warning(
                f"num_workers ({self.num_workers}) exceeds recommended limit "
                f"({MAX_WORKERS_LIMIT}), may cause resource issues"
            )

        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be > 0, got {self.timeout_seconds}")

        if self.chunk_size < 1:
            raise ValueError(f"chunk_size must be >= 1, got {self.chunk_size}")

        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")

    @classmethod
    def from_processing_config(cls, config: Any) -> BatchProcessorConfig:
        return cls(
            batch_size=getattr(config, "batch_size", DEFAULT_BATCH_SIZE),
            num_workers=getattr(config, "num_workers", DEFAULT_NUM_WORKERS),
        )


@dataclass
class ProcessingResult(Generic[OutputT]):
    """Result of a batch processing operation.

    Attributes:
        outputs: List of processed outputs (None for failed items).
        errors: List of (index, exception) tuples for failed items.
        total_processed: Total number of items processed.
        total_failed: Total number of failed items.
        elapsed_seconds: Total processing time in seconds.
        items_per_second: Processing throughput.
    """

    outputs: list[OutputT | None]
    errors: list[tuple[int, Exception]]
    total_processed: int = 0
    total_failed: int = 0
    elapsed_seconds: float = 0.0
    items_per_second: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return ((self.total_processed - self.total_failed) / self.total_processed) * 100

    def get_successful_outputs(self) -> list[OutputT]:
        return [o for o in self.outputs if o is not None]


class ProgressTracker:
    """Thread-safe progress tracking for batch operations."""

    def __init__(
        self,
        total_items: int,
        callback: Callable[[int, int], None] | None = None,
    ) -> None:
        self.total_items = total_items
        self.callback = callback
        self._completed = 0
        self._failed = 0
        self._lock = threading.Lock()
        self._start_time = time.time()

    def update(self, completed_delta: int = 1, failed_delta: int = 0) -> None:
        with self._lock:
            self._completed += completed_delta
            self._failed += failed_delta

            if self.callback:
                try:
                    self.callback(self._completed, self.total_items)
                except Exception as e:
                    _get_batch_logger().warning(f"Progress callback error: {e}")

    @property
    def completed(self) -> int:
        with self._lock:
            return self._completed

    @property
    def failed(self) -> int:
        with self._lock:
            return self._failed

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self._start_time

    @property
    def items_per_second(self) -> float:
        elapsed = self.elapsed_seconds
        if elapsed > 0:
            return self.completed / elapsed
        return 0.0

    @property
    def progress_percent(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self._completed / self.total_items) * 100


def _worker_process_item(
    process_fn: Callable[[InputT], OutputT],
    item: InputT,
    max_retries: int,
) -> tuple[int, OutputT | None, Exception | None]:
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return (-1, process_fn(item), None)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(0.1 * (attempt + 1))

    return (-1, None, last_error)


class FrameBatchProcessor(Generic[InputT, OutputT]):
    """Parallel batch processor for frame-by-frame operations.

    This class provides efficient parallel processing of frames using
    either multiprocessing (for CPU-bound tasks) or threading (for I/O-bound tasks).

    Example usage:
        ```python
        config = BatchProcessorConfig(
            batch_size=8,
            num_workers=4,
            mode=ProcessingMode.MULTIPROCESSING,
        )
        processor = FrameBatchProcessor(config=config)

        def depth_estimation(frame):
            return estimate_depth(frame)

        result = processor.process(frames, depth_estimation)
        for output in result.get_successful_outputs():
            save_output(output)
        ```
    """

    def __init__(
        self,
        config: BatchProcessorConfig | None = None,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        num_workers: int = DEFAULT_NUM_WORKERS,
        mode: ProcessingMode = ProcessingMode.MULTIPROCESSING,
    ) -> None:
        if config is not None:
            self.config = config
        else:
            self.config = BatchProcessorConfig(
                batch_size=batch_size,
                num_workers=num_workers,
                mode=mode,
            )

        self._logger = _get_batch_logger()
        self._logger.debug(
            f"FrameBatchProcessor initialized: batch_size={self.config.batch_size}, "
            f"workers={self.config.num_workers}, mode={self.config.mode.value}"
        )

    def process(
        self,
        items: Iterable[InputT],
        process_fn: Callable[[InputT], OutputT],
    ) -> ProcessingResult[OutputT]:
        """Process items in parallel batches.

        Args:
            items: Iterable of items to process.
            process_fn: Function to apply to each item.

        Returns:
            ProcessingResult with outputs and statistics.

        Raises:
            BatchProcessorError: If processing fails critically.
        """
        start_time = time.time()
        items_list = list(items)
        total_items = len(items_list)

        if total_items == 0:
            return ProcessingResult(outputs=[], errors=[], total_processed=0)

        self._logger.info(
            f"Starting batch processing: {total_items} items, "
            f"batch_size={self.config.batch_size}, workers={self.config.num_workers}"
        )

        progress = ProgressTracker(
            total_items=total_items,
            callback=self.config.progress_callback if self.config.enable_progress else None,
        )

        if self.config.mode == ProcessingMode.SEQUENTIAL:
            outputs, errors = self._process_sequential(items_list, process_fn, progress)
        elif self.config.mode == ProcessingMode.THREADING:
            outputs, errors = self._process_threaded(items_list, process_fn, progress)
        else:
            outputs, errors = self._process_multiprocessing(items_list, process_fn, progress)

        elapsed = time.time() - start_time
        total_failed = len(errors)
        items_per_second = total_items / elapsed if elapsed > 0 else 0.0

        log_performance(
            "batch_processing",
            elapsed * 1000,
            total_items=total_items,
            batch_size=self.config.batch_size,
            workers=self.config.num_workers,
            mode=self.config.mode.value,
            success_rate=f"{((total_items - total_failed) / total_items * 100):.1f}%",
        )

        return ProcessingResult(
            outputs=outputs,
            errors=errors,
            total_processed=total_items,
            total_failed=total_failed,
            elapsed_seconds=elapsed,
            items_per_second=items_per_second,
        )

    def _process_sequential(
        self,
        items: list[InputT],
        process_fn: Callable[[InputT], OutputT],
        progress: ProgressTracker,
    ) -> tuple[list[OutputT | None], list[tuple[int, Exception]]]:
        outputs: list[OutputT | None] = [None] * len(items)
        errors: list[tuple[int, Exception]] = []

        for idx, item in enumerate(items):
            try:
                outputs[idx] = process_fn(item)
                progress.update(1)
            except Exception as e:
                errors.append((idx, e))
                progress.update(1, failed_delta=1)
                self._handle_error(e, idx)

        return outputs, errors

    def _process_threaded(
        self,
        items: list[InputT],
        process_fn: Callable[[InputT], OutputT],
        progress: ProgressTracker,
    ) -> tuple[list[OutputT | None], list[tuple[int, Exception]]]:
        outputs: list[OutputT | None] = [None] * len(items)
        errors: list[tuple[int, Exception]] = []

        with ThreadPoolExecutor(max_workers=self.config.num_workers) as executor:
            future_to_idx = {
                executor.submit(self._process_item_with_retry, process_fn, item, idx): idx
                for idx, item in enumerate(items)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    outputs[idx] = future.result(timeout=self.config.timeout_seconds)
                    progress.update(1)
                except Exception as e:
                    errors.append((idx, e))
                    progress.update(1, failed_delta=1)
                    self._handle_error(e, idx)

        return outputs, errors

    def _process_multiprocessing(
        self,
        items: list[InputT],
        process_fn: Callable[[InputT], OutputT],
        progress: ProgressTracker,
    ) -> tuple[list[OutputT | None], list[tuple[int, Exception]]]:
        outputs: list[OutputT | None] = [None] * len(items)
        errors: list[tuple[int, Exception]] = []

        mp_context = mp.get_context("spawn")

        with ProcessPoolExecutor(
            max_workers=self.config.num_workers,
            mp_context=mp_context,
        ) as executor:
            future_to_idx = {}
            for idx, item in enumerate(items):
                future = executor.submit(
                    _worker_process_item,
                    process_fn,
                    item,
                    self.config.max_retries,
                )
                future_to_idx[future] = idx

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    _, result, exc = future.result(timeout=self.config.timeout_seconds)
                    if exc is not None:
                        errors.append((idx, exc))
                        progress.update(1, failed_delta=1)
                        self._handle_error(exc, idx)
                    else:
                        outputs[idx] = result
                        progress.update(1)
                except Exception as e:
                    errors.append((idx, e))
                    progress.update(1, failed_delta=1)
                    self._handle_error(e, idx)

        return outputs, errors

    def _process_item_with_retry(
        self,
        process_fn: Callable[[InputT], OutputT],
        item: InputT,
        idx: int,
    ) -> OutputT:
        last_error: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return process_fn(item)
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    self._logger.debug(
                        f"Retrying item {idx} (attempt {attempt + 2}/{self.config.max_retries + 1})"
                    )
                    time.sleep(0.1 * (attempt + 1))

        raise last_error if last_error else RuntimeError("Unknown error")

    def _handle_error(self, error: Exception, idx: int) -> None:
        log_exception(f"Error processing item {idx}", exception=error)

        if self.config.error_callback:
            try:
                self.config.error_callback(error, idx)
            except Exception as e:
                self._logger.warning(f"Error callback failed: {e}")

    def process_in_batches(
        self,
        items: Iterable[InputT],
        process_fn: Callable[[list[InputT]], list[OutputT]],
    ) -> Generator[list[OutputT], None, None]:
        """Process items in batches, yielding results as they complete.

        This is a memory-efficient generator-based approach for large datasets.

        Args:
            items: Iterable of items to process.
            process_fn: Function that processes a batch of items.

        Yields:
            Lists of processed outputs, one per batch.
        """
        batch: list[InputT] = []

        for item in items:
            batch.append(item)
            if len(batch) >= self.config.batch_size:
                yield process_fn(batch)
                batch.clear()

                if self.config.gc_threshold > 0:
                    gc.collect()
        if batch:
            yield process_fn(batch)

    def map(
        self,
        items: Iterable[InputT],
        process_fn: Callable[[InputT], OutputT],
    ) -> Iterator[OutputT]:
        """Apply a function to items in parallel, yielding results lazily.

        Args:
            items: Iterable of items to process.
            process_fn: Function to apply to each item.

        Yields:
            Processed outputs in order.
        """
        items_list = list(items)

        if self.config.mode == ProcessingMode.SEQUENTIAL:
            for item in items_list:
                yield process_fn(item)
            return

        executor_class = (
            ThreadPoolExecutor
            if self.config.mode == ProcessingMode.THREADING
            else ProcessPoolExecutor
        )

        with executor_class(max_workers=self.config.num_workers) as executor:
            futures = [executor.submit(process_fn, item) for item in items_list]

            for future in futures:
                try:
                    yield future.result(timeout=self.config.timeout_seconds)
                except Exception as e:
                    self._handle_error(e, -1)
                    raise


class ChunkedBatchProcessor(FrameBatchProcessor[np.ndarray, np.ndarray]):
    """Specialized batch processor for numpy arrays with chunking support.

    This processor is optimized for processing large numpy arrays (frames)
    with memory-efficient chunking and optional shared memory support.
    """

    def process_frames(
        self,
        frames: Iterable[np.ndarray],
        process_fn: Callable[[np.ndarray], np.ndarray],
    ) -> ProcessingResult[np.ndarray]:
        return self.process(frames, process_fn)

    def process_video_chunks(
        self,
        video_path: str,
        chunk_processor: Callable[[list[np.ndarray]], list[np.ndarray]],
        frames_per_chunk: int = 30,
    ) -> Generator[list[np.ndarray], None, None]:
        """Process video in chunks for memory-efficient large video handling.

        Args:
            video_path: Path to the video file.
            chunk_processor: Function to process a chunk of frames.
            frames_per_chunk: Number of frames per chunk.

        Yields:
            Processed frame chunks.
        """
        from video2d3d.video.frame_extractor import FrameExtractor

        extractor = FrameExtractor(video_path)

        try:
            batch: list[np.ndarray] = []
            for _, frame in extractor.extract_frames():
                batch.append(frame)
                if len(batch) >= frames_per_chunk:
                    yield chunk_processor(batch)
                    batch.clear()
                    gc.collect()

            if batch:
                yield chunk_processor(batch)
        finally:
            extractor.close()


def create_processor(
    batch_size: int = DEFAULT_BATCH_SIZE,
    num_workers: int = DEFAULT_NUM_WORKERS,
    mode: str = "multiprocessing",
    **kwargs: int | float | str | bool | Callable,
) -> FrameBatchProcessor:
    """Create a batch processor with the specified configuration.

    Args:
        batch_size: Number of items per batch.
        num_workers: Number of parallel workers.
        mode: Processing mode ('multiprocessing', 'threading', 'sequential').
        **kwargs: Additional BatchProcessorConfig field values.

    Returns:
        Configured FrameBatchProcessor instance.
    """
    mode_enum = ProcessingMode(mode.lower())
    config = BatchProcessorConfig(
        batch_size=batch_size,
        num_workers=num_workers,
        mode=mode_enum,
        **kwargs,  # type: ignore[arg-type]
    )
    return FrameBatchProcessor(config=config)


def process_in_parallel(
    items: Iterable[InputT],
    process_fn: Callable[[InputT], OutputT],
    batch_size: int = DEFAULT_BATCH_SIZE,
    num_workers: int = DEFAULT_NUM_WORKERS,
) -> ProcessingResult[OutputT]:
    """Process items in parallel with default settings (convenience function).

    Args:
        items: Items to process.
        process_fn: Function to apply to each item.
        batch_size: Number of items per batch.
        num_workers: Number of parallel workers.

    Returns:
        ProcessingResult with outputs and statistics.
    """
    processor = create_processor(batch_size=batch_size, num_workers=num_workers)
    return processor.process(items, process_fn)


__all__ = [
    "BatchProcessorConfig",
    "FrameBatchProcessor",
    "ChunkedBatchProcessor",
    "ProcessingResult",
    "ProgressTracker",
    "ProcessingMode",
    "BatchProcessorError",
    "WorkerTimeoutError",
    "WorkerInitializationError",
    "create_processor",
    "process_in_parallel",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_NUM_WORKERS",
    "MAX_WORKERS_LIMIT",
    "MIN_BATCH_SIZE",
]
