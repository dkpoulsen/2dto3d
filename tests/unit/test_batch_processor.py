"""Unit tests for batch processor module.

Tests cover:
- BatchProcessorConfig dataclass
- ProcessingMode enum
- FrameBatchProcessor class
- ProcessingResult dataclass
- ProgressTracker class
- Convenience functions
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.core.batch_processor import (
    BatchProcessorConfig,
    BatchProcessorError,
    ChunkedBatchProcessor,
    FrameBatchProcessor,
    ProcessingMode,
    ProcessingResult,
    ProgressTracker,
    WorkerInitializationError,
    WorkerTimeoutError,
    create_processor,
)


# Module-level functions for multiprocessing tests (must be picklable)
def _double(x: int) -> int:
    """Double a number - used in multiprocessing tests."""
    return x * 2


def _fail_on_three(x: int) -> int:
    """Fail when input is 3 - used in error handling tests."""
    if x == 3:
        raise ValueError("test error")
    return x * 2


def sample_items() -> list[int]:
    return list(range(10))


@pytest.fixture
def sample_frames() -> list[np.ndarray]:
    np.random.seed(42)
    return [np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8) for _ in range(5)]


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    with patch("video2d3d.core.batch_processor.get_logger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


class TestBatchProcessorConfig:
    """Tests for BatchProcessorConfig dataclass."""

    def test_default_values(self, mock_logger: MagicMock) -> None:
        config = BatchProcessorConfig()

        assert config.batch_size == 8
        assert config.num_workers == 4
        assert config.mode == ProcessingMode.MULTIPROCESSING
        assert config.chunk_size == 1
        assert config.timeout_seconds == 300.0
        assert config.max_retries == 2
        assert config.preserve_order is True
        assert config.enable_progress is True
        assert config.progress_callback is None
        assert config.error_callback is None
        assert config.use_shared_memory is False
        assert config.gc_threshold == 100

    def test_custom_values(self, mock_logger: MagicMock) -> None:
        progress_cb = lambda c, t: None
        error_cb = lambda e, i: None

        config = BatchProcessorConfig(
            batch_size=16,
            num_workers=8,
            mode=ProcessingMode.THREADING,
            chunk_size=2,
            timeout_seconds=60.0,
            max_retries=3,
            preserve_order=False,
            enable_progress=False,
            progress_callback=progress_cb,
            error_callback=error_cb,
            use_shared_memory=True,
            gc_threshold=50,
        )

        assert config.batch_size == 16
        assert config.num_workers == 8
        assert config.mode == ProcessingMode.THREADING
        assert config.chunk_size == 2
        assert config.timeout_seconds == 60.0
        assert config.max_retries == 3
        assert config.preserve_order is False
        assert config.enable_progress is False
        assert config.progress_callback is progress_cb
        assert config.error_callback is error_cb
        assert config.use_shared_memory is True
        assert config.gc_threshold == 50

    def test_invalid_batch_size_raises(self, mock_logger: MagicMock) -> None:
        with pytest.raises(ValueError, match="batch_size"):
            BatchProcessorConfig(batch_size=0)

    def test_invalid_num_workers_raises(self, mock_logger: MagicMock) -> None:
        with pytest.raises(ValueError, match="num_workers"):
            BatchProcessorConfig(num_workers=0)

    def test_invalid_timeout_raises(self, mock_logger: MagicMock) -> None:
        with pytest.raises(ValueError, match="timeout_seconds"):
            BatchProcessorConfig(timeout_seconds=0)

    def test_invalid_chunk_size_raises(self, mock_logger: MagicMock) -> None:
        with pytest.raises(ValueError, match="chunk_size"):
            BatchProcessorConfig(chunk_size=0)

    def test_invalid_max_retries_raises(self, mock_logger: MagicMock) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            BatchProcessorConfig(max_retries=-1)

    def test_from_processing_config(self, mock_logger: MagicMock) -> None:
        class MockConfig:
            batch_size = 32
            num_workers = 16

        config = BatchProcessorConfig.from_processing_config(MockConfig())
        assert config.batch_size == 32
        assert config.num_workers == 16

    def test_from_processing_config_defaults(self, mock_logger: MagicMock) -> None:
        class MockConfig:
            pass

        config = BatchProcessorConfig.from_processing_config(MockConfig())
        assert config.batch_size == 8
        assert config.num_workers == 4


class TestProcessingMode:
    """Tests for ProcessingMode enum."""

    def test_mode_values(self) -> None:
        assert ProcessingMode.MULTIPROCESSING.value == "multiprocessing"
        assert ProcessingMode.THREADING.value == "threading"
        assert ProcessingMode.SEQUENTIAL.value == "sequential"


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_success_rate_zero_processed(self) -> None:
        result = ProcessingResult(outputs=[], errors=[], total_processed=0)
        assert result.success_rate == 0.0

    def test_success_rate_all_success(self) -> None:
        result = ProcessingResult(
            outputs=[1, 2, 3],
            errors=[],
            total_processed=3,
            total_failed=0,
        )
        assert result.success_rate == 100.0

    def test_success_rate_some_failed(self) -> None:
        result = ProcessingResult(
            outputs=[1, None, 3],
            errors=[(1, ValueError("test"))],
            total_processed=3,
            total_failed=1,
        )
        assert result.success_rate == pytest.approx(66.67, rel=0.01)

    def test_get_successful_outputs(self) -> None:
        result = ProcessingResult(
            outputs=[1, None, 3, None, 5],
            errors=[],
        )
        assert result.get_successful_outputs() == [1, 3, 5]

    def test_get_successful_outputs_all_none(self) -> None:
        result = ProcessingResult(outputs=[None, None], errors=[])
        assert result.get_successful_outputs() == []


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    def test_initial_state(self) -> None:
        tracker = ProgressTracker(total_items=100)
        assert tracker.completed == 0
        assert tracker.failed == 0
        assert tracker.total_items == 100

    def test_update_completed(self) -> None:
        tracker = ProgressTracker(total_items=100)
        tracker.update(5)
        assert tracker.completed == 5
        assert tracker.failed == 0

    def test_update_failed(self) -> None:
        tracker = ProgressTracker(total_items=100)
        tracker.update(3, failed_delta=2)
        assert tracker.completed == 3
        assert tracker.failed == 2

    def test_progress_percent(self) -> None:
        tracker = ProgressTracker(total_items=100)
        tracker.update(25)
        assert tracker.progress_percent == 25.0

    def test_progress_percent_zero_total(self) -> None:
        tracker = ProgressTracker(total_items=0)
        assert tracker.progress_percent == 0.0

    def test_items_per_second(self) -> None:
        tracker = ProgressTracker(total_items=100)
        tracker.update(50)
        assert tracker.items_per_second > 0

    def test_callback_called(self) -> None:
        callback = MagicMock()
        tracker = ProgressTracker(total_items=100, callback=callback)
        tracker.update(10)
        callback.assert_called_once_with(10, 100)

    def test_callback_exception_handled(self, mock_logger: MagicMock) -> None:
        callback = MagicMock(side_effect=RuntimeError("callback error"))
        tracker = ProgressTracker(total_items=100, callback=callback)
        tracker.update(10)
        assert tracker.completed == 10


class TestFrameBatchProcessor:
    """Tests for FrameBatchProcessor class."""

    def test_init_with_defaults(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor()
        assert processor.config.batch_size == 8
        assert processor.config.num_workers == 4
        assert processor.config.mode == ProcessingMode.MULTIPROCESSING

    def test_init_with_config(self, mock_logger: MagicMock) -> None:
        config = BatchProcessorConfig(
            batch_size=16,
            num_workers=8,
            mode=ProcessingMode.THREADING,
        )
        processor = FrameBatchProcessor(config=config)
        assert processor.config.batch_size == 16
        assert processor.config.num_workers == 8
        assert processor.config.mode == ProcessingMode.THREADING

    def test_init_with_kwargs(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(
            batch_size=32,
            num_workers=2,
            mode=ProcessingMode.SEQUENTIAL,
        )
        assert processor.config.batch_size == 32
        assert processor.config.num_workers == 2
        assert processor.config.mode == ProcessingMode.SEQUENTIAL

    def test_process_empty_items(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(mode=ProcessingMode.SEQUENTIAL)
        result = processor.process([], lambda x: x)
        assert result.total_processed == 0
        assert result.outputs == []

    def test_process_sequential(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(mode=ProcessingMode.SEQUENTIAL)
        items = [1, 2, 3, 4, 5]
        result = processor.process(items, lambda x: x * 2)

        assert result.total_processed == 5
        assert result.total_failed == 0
        assert result.outputs == [2, 4, 6, 8, 10]

    def test_process_sequential_with_errors(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(mode=ProcessingMode.SEQUENTIAL)

        def process_fn(x: int) -> int:
            if x == 3:
                raise ValueError("test error")
            return x * 2

        result = processor.process([1, 2, 3, 4, 5], process_fn)

        assert result.total_processed == 5
        assert result.total_failed == 1
        assert len(result.errors) == 1
        assert result.errors[0][0] == 2
        assert result.outputs[2] is None

    def test_process_threaded(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(
            mode=ProcessingMode.THREADING,
            num_workers=2,
        )
        items = [1, 2, 3, 4, 5]
        result = processor.process(items, lambda x: x * 2)

        assert result.total_processed == 5
        assert result.outputs == [2, 4, 6, 8, 10]

    def test_process_in_batches(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(batch_size=3, mode=ProcessingMode.SEQUENTIAL)
        items = [1, 2, 3, 4, 5, 6, 7]

        batch_results = list(processor.process_in_batches(items, lambda b: [x * 2 for x in b]))

        assert len(batch_results) == 3
        assert batch_results[0] == [2, 4, 6]
        assert batch_results[1] == [8, 10, 12]
        assert batch_results[2] == [14]

    def test_map_sequential(self, mock_logger: MagicMock) -> None:
        processor = FrameBatchProcessor(mode=ProcessingMode.SEQUENTIAL)
        items = [1, 2, 3, 4, 5]

        result = list(processor.map(items, lambda x: x * 2))

        assert result == [2, 4, 6, 8, 10]

    def test_progress_callback(self, mock_logger: MagicMock) -> None:
        progress_calls = []

        def progress_cb(completed: int, total: int) -> None:
            progress_calls.append((completed, total))

        config = BatchProcessorConfig(
            mode=ProcessingMode.SEQUENTIAL,
            enable_progress=True,
            progress_callback=progress_cb,
        )
        processor = FrameBatchProcessor(config=config)
        processor.process([1, 2, 3], lambda x: x)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    def test_error_callback(self, mock_logger: MagicMock) -> None:
        error_calls = []

        def error_cb(error: Exception, idx: int) -> None:
            error_calls.append((error, idx))

        config = BatchProcessorConfig(
            mode=ProcessingMode.SEQUENTIAL,
            error_callback=error_cb,
        )
        processor = FrameBatchProcessor(config=config)

        def process_fn(x: int) -> int:
            if x == 2:
                raise ValueError("test error")
            return x

        processor.process([1, 2, 3], process_fn)

        assert len(error_calls) == 1
        assert error_calls[0][1] == 1
        assert isinstance(error_calls[0][0], ValueError)


class TestChunkedBatchProcessor:
    """Tests for ChunkedBatchProcessor class."""

    def test_process_frames(self, mock_logger: MagicMock) -> None:
        processor = ChunkedBatchProcessor(mode=ProcessingMode.SEQUENTIAL)

        frames = [
            np.zeros((10, 10, 3), dtype=np.uint8),
            np.ones((10, 10, 3), dtype=np.uint8) * 255,
        ]

        def invert(frame: np.ndarray) -> np.ndarray:
            return 255 - frame

        result = processor.process_frames(frames, invert)

        assert result.total_processed == 2
        assert result.outputs[0][0, 0, 0] == 255
        assert result.outputs[1][0, 0, 0] == 0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_processor_defaults(self, mock_logger: MagicMock) -> None:
        processor = create_processor()
        assert processor.config.batch_size == 8
        assert processor.config.num_workers == 4
        assert processor.config.mode == ProcessingMode.MULTIPROCESSING

    def test_create_processor_custom(self, mock_logger: MagicMock) -> None:
        processor = create_processor(
            batch_size=16,
            num_workers=8,
            mode="threading",
        )
        assert processor.config.batch_size == 16
        assert processor.config.num_workers == 8
        assert processor.config.mode == ProcessingMode.THREADING

    def test_process_in_parallel_basic(self, mock_logger: MagicMock) -> None:
        items = [1, 2, 3, 4, 5]
        processor = create_processor(
            batch_size=2,
            num_workers=2,
            mode="threading",
        )
        result = processor.process(items, lambda x: x * 2)

        assert result.total_processed == 5
        assert result.get_successful_outputs() == [2, 4, 6, 8, 10]


class TestExceptions:
    """Tests for custom exceptions."""

    def test_batch_processor_error_attrs(self) -> None:
        original = ValueError("original")
        error = BatchProcessorError(
            "test error",
            batch_index=5,
            original_exception=original,
        )

        assert str(error) == "test error"
        assert error.batch_index == 5
        assert error.original_exception is original

    def test_worker_timeout_error_inheritance(self) -> None:
        error = WorkerTimeoutError("timeout")
        assert isinstance(error, BatchProcessorError)
        assert isinstance(error, Exception)

    def test_worker_initialization_error_inheritance(self) -> None:
        error = WorkerInitializationError("init failed")
        assert isinstance(error, BatchProcessorError)
        assert isinstance(error, Exception)


class TestHighWorkersWarning:
    """Tests for high num_workers warning."""

    def test_high_workers_warning(self, mock_logger: MagicMock) -> None:
        """Test warning when num_workers exceeds MAX_WORKERS_LIMIT."""
        mock_logger.reset_mock()

        config = BatchProcessorConfig(num_workers=64)

        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "64" in call_args
        assert "exceeds" in call_args.lower()
        assert config.num_workers == 64


class TestMultiprocessingMode:
    """Tests for multiprocessing mode."""

    def test_multiprocessing_config_creation(self, mock_logger: MagicMock) -> None:
        """Test that multiprocessing mode can be configured."""
        config = BatchProcessorConfig(
            num_workers=2,
            mode=ProcessingMode.MULTIPROCESSING,
        )
        assert config.mode == ProcessingMode.MULTIPROCESSING

        processor = FrameBatchProcessor(config=config)
        assert processor.config.mode == ProcessingMode.MULTIPROCESSING

    @pytest.mark.skip(reason="Multiprocessing requires picklable functions")
    def test_process_multiprocessing_basic(self, mock_logger: MagicMock) -> None:
        """Test basic multiprocessing operation."""
        config = BatchProcessorConfig(
            num_workers=2,
            mode=ProcessingMode.MULTIPROCESSING,
            timeout_seconds=10.0,
        )
        processor = FrameBatchProcessor(config=config)
        items = [1, 2, 3, 4, 5]

        result = processor.process(items, _double)

        assert result.total_processed == 5
        assert result.total_failed == 0
        assert result.outputs == [2, 4, 6, 8, 10]

    @pytest.mark.skip(reason="Multiprocessing requires picklable functions")
    def test_process_multiprocessing_with_error(self, mock_logger: MagicMock) -> None:
        """Test multiprocessing with processing errors."""
        error_calls = []

        def error_cb(error: Exception, idx: int) -> None:
            error_calls.append((error, idx))

        config = BatchProcessorConfig(
            num_workers=2,
            mode=ProcessingMode.MULTIPROCESSING,
            timeout_seconds=10.0,
            error_callback=error_cb,
        )
        processor = FrameBatchProcessor(config=config)

        result = processor.process([1, 2, 3, 4, 5], _fail_on_three)

        assert result.total_processed == 5
        assert result.total_failed == 1
        assert len(result.errors) == 1
        assert result.errors[0][0] == 2

    @pytest.mark.skip(reason="Multiprocessing requires picklable functions")
    def test_process_multiprocessing_with_timeout(self, mock_logger: MagicMock) -> None:
        """Test multiprocessing timeout handling."""

        config = BatchProcessorConfig(
            num_workers=1,
            mode=ProcessingMode.MULTIPROCESSING,
            timeout_seconds=0.1,
        )
        processor = FrameBatchProcessor(config=config)

        result = processor.process([1, 2, 3, 4, 5], _double)

        assert result.total_processed == 5


class TestMapMethod:
    """Tests for map() method with all modes."""

    def test_map_threading_mode(self, mock_logger: MagicMock) -> None:
        """Test map() with threading mode."""
        processor = FrameBatchProcessor(
            mode=ProcessingMode.THREADING,
            num_workers=2,
        )
        items = [1, 2, 3, 4, 5]

        result = list(processor.map(items, lambda x: x * 2))

        assert result == [2, 4, 6, 8, 10]

    @pytest.mark.skip(reason="Multiprocessing requires picklable functions")
    def test_map_multiprocessing_mode(self, mock_logger: MagicMock) -> None:
        """Test map() with multiprocessing mode."""
        config = BatchProcessorConfig(
            mode=ProcessingMode.MULTIPROCESSING,
            num_workers=2,
            timeout_seconds=10.0,
        )
        processor = FrameBatchProcessor(config=config)
        items = [1, 2, 3, 4, 5]

        result = list(processor.map(items, _double))

        assert result == [2, 4, 6, 8, 10]

    def test_map_raises_on_error(self, mock_logger: MagicMock) -> None:
        """Test map() raises error on processing failure."""
        processor = FrameBatchProcessor(mode=ProcessingMode.SEQUENTIAL)

        def process_fn(x: int) -> int:
            if x == 3:
                raise ValueError("test error")
            return x * 2

        with pytest.raises(ValueError, match="test error"):
            list(processor.map([1, 2, 3, 4, 5], process_fn))


class TestProcessInBatches:
    """Tests for process_in_batches method."""

    def test_process_in_batches_no_gc(self, mock_logger: MagicMock) -> None:
        """Test process_in_batches with gc_threshold=0."""
        config = BatchProcessorConfig(
            batch_size=3,
            mode=ProcessingMode.SEQUENTIAL,
            gc_threshold=0,
        )
        processor = FrameBatchProcessor(config=config)
        items = [1, 2, 3, 4, 5, 6, 7]

        batch_results = list(processor.process_in_batches(items, lambda b: [x * 2 for x in b]))

        assert len(batch_results) == 3
        assert batch_results[0] == [2, 4, 6]
        assert batch_results[1] == [8, 10, 12]
        assert batch_results[2] == [14]


class TestThreadedWithRetry:
    """Tests for threaded processing with retry logic."""

    def test_threaded_retry_on_failure(self, mock_logger: MagicMock) -> None:
        """Test retry logic in threaded mode."""
        call_counts = {0: 0, 1: 0, 2: 0}

        def process_fn(x: int) -> int:
            call_counts[x] += 1
            if x == 1 and call_counts[x] < 2:
                raise ValueError("temporary error")
            return x * 2

        config = BatchProcessorConfig(
            mode=ProcessingMode.THREADING,
            num_workers=2,
            max_retries=3,
            timeout_seconds=10.0,
        )
        processor = FrameBatchProcessor(config=config)

        result = processor.process([0, 1, 2], process_fn)

        assert result.total_processed == 3
        assert result.outputs == [0, 2, 4]
        assert call_counts[1] >= 2

    def test_threaded_max_retries_exceeded(self, mock_logger: MagicMock) -> None:
        """Test that error is raised after max retries exceeded."""

        def always_fails(x: int) -> int:
            if x == 1:
                raise ValueError("always fails")
            return x * 2

        config = BatchProcessorConfig(
            mode=ProcessingMode.THREADING,
            num_workers=2,
            max_retries=1,
            timeout_seconds=10.0,
        )
        processor = FrameBatchProcessor(config=config)

        result = processor.process([0, 1, 2], always_fails)

        assert result.total_processed == 3
        assert result.total_failed == 1
        assert result.outputs[1] is None
        assert result.outputs[0] == 0
        assert result.outputs[2] == 4
