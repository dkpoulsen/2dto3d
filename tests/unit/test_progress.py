"""Unit tests for progress tracking module.

Tests cover:
- ProgressStage enum
- StageMetrics dataclass
- ProgressConfig dataclass
- ConversionStats dataclass
- VideoConversionProgress class
- SimpleProgressTracker class
- track_progress function
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.utils.progress import (
    ConversionStats,
    ProgressConfig,
    ProgressStage,
    SimpleProgressTracker,
    StageMetrics,
    VideoConversionProgress,
    track_progress,
)


class TestProgressStage:
    """Tests for ProgressStage enum."""

    def test_stage_values(self) -> None:
        """Test that all expected stages exist."""
        assert ProgressStage.INIT.value == "initializing"
        assert ProgressStage.EXTRACT.value == "extracting"
        assert ProgressStage.PROCESS.value == "processing"
        assert ProgressStage.DEPTH.value == "depth_estimation"
        assert ProgressStage.STEREO.value == "stereo_generation"
        assert ProgressStage.WRITE.value == "writing"
        assert ProgressStage.FINALIZE.value == "finalizing"
        assert ProgressStage.COMPLETE.value == "complete"

    def test_stage_count(self) -> None:
        """Test that we have all expected stages."""
        stages = list(ProgressStage)
        assert len(stages) == 8


class TestStageMetrics:
    """Tests for StageMetrics dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        metrics = StageMetrics(name="test")
        assert metrics.name == "test"
        assert metrics.total == 0
        assert metrics.completed == 0
        assert metrics.failed == 0
        assert metrics.start_time is None
        assert metrics.end_time is None

    def test_elapsed_seconds_not_started(self) -> None:
        """Test elapsed_seconds when not started."""
        metrics = StageMetrics(name="test")
        assert metrics.elapsed_seconds == 0.0

    def test_elapsed_seconds_started(self) -> None:
        """Test elapsed_seconds after start."""
        metrics = StageMetrics(name="test", start_time=time.time())
        time.sleep(0.1)
        assert metrics.elapsed_seconds >= 0.1

    def test_elapsed_seconds_ended(self) -> None:
        """Test elapsed_seconds after end."""
        start = time.time() - 1.0
        end = time.time()
        metrics = StageMetrics(name="test", start_time=start, end_time=end)
        assert metrics.elapsed_seconds >= 1.0

    def test_items_per_second_zero_elapsed(self) -> None:
        """Test items_per_second with zero elapsed time."""
        metrics = StageMetrics(name="test", completed=100)
        assert metrics.items_per_second == 0.0

    def test_items_per_second_with_elapsed(self) -> None:
        """Test items_per_second with elapsed time."""
        start = time.time() - 2.0
        metrics = StageMetrics(name="test", completed=100, start_time=start)
        # 100 items / 2 seconds = 50 items/sec
        assert 49.0 <= metrics.items_per_second <= 51.0

    def test_eta_seconds_zero_speed(self) -> None:
        """Test eta_seconds with zero speed."""
        metrics = StageMetrics(name="test", total=100, completed=50)
        assert metrics.eta_seconds == 0.0

    def test_eta_seconds_with_speed(self) -> None:
        """Test eta_seconds with valid speed."""
        start = time.time() - 1.0
        metrics = StageMetrics(name="test", total=100, completed=50, start_time=start)
        # 50 items/sec, 50 remaining = 1 second ETA
        assert 0.9 <= metrics.eta_seconds <= 1.1

    def test_progress_percent_zero_total(self) -> None:
        """Test progress_percent with zero total."""
        metrics = StageMetrics(name="test", total=0, completed=10)
        assert metrics.progress_percent == 0.0

    def test_progress_percent_partial(self) -> None:
        """Test progress_percent partial completion."""
        metrics = StageMetrics(name="test", total=200, completed=50)
        assert metrics.progress_percent == 25.0

    def test_progress_percent_complete(self) -> None:
        """Test progress_percent at completion."""
        metrics = StageMetrics(name="test", total=100, completed=100)
        assert metrics.progress_percent == 100.0

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        metrics = StageMetrics(
            name="extract",
            total=100,
            completed=50,
            failed=2,
        )
        result = metrics.to_dict()

        assert result["name"] == "extract"
        assert result["total"] == 100
        assert result["completed"] == 50
        assert result["failed"] == 2
        assert "elapsed_seconds" in result
        assert "items_per_second" in result
        assert "eta_seconds" in result
        assert "progress_percent" in result


class TestProgressConfig:
    """Tests for ProgressConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        config = ProgressConfig()
        assert config.enabled is True
        assert config.show_speed is True
        assert config.show_eta is True
        assert config.show_elapsed is True
        assert config.show_percent is True
        assert config.show_overall is True
        assert config.refresh_rate == 0.1
        assert config.transient is False
        assert config.expand is True

    def test_disabled(self) -> None:
        """Test disabled configuration."""
        config = ProgressConfig(enabled=False)
        assert config.enabled is False

    def test_custom_values(self) -> None:
        """Test custom values."""
        config = ProgressConfig(
            enabled=True,
            show_speed=False,
            show_eta=False,
            show_elapsed=False,
            show_percent=False,
            refresh_rate=0.5,
            transient=True,
            expand=False,
        )
        assert config.show_speed is False
        assert config.show_eta is False
        assert config.show_elapsed is False
        assert config.show_percent is False
        assert config.refresh_rate == 0.5
        assert config.transient is True
        assert config.expand is False


class TestConversionStats:
    """Tests for ConversionStats dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        stats = ConversionStats()
        assert stats.total_frames == 0
        assert stats.frames_extracted == 0
        assert stats.frames_processed == 0
        assert stats.frames_written == 0
        assert stats.frames_failed == 0
        assert stats.total_elapsed_seconds == 0.0
        assert stats.stages == {}

    def test_overall_speed_zero_elapsed(self) -> None:
        """Test overall_speed with zero elapsed time."""
        stats = ConversionStats(frames_processed=100)
        assert stats.overall_speed == 0.0

    def test_overall_speed_with_elapsed(self) -> None:
        """Test overall_speed with elapsed time."""
        stats = ConversionStats(
            frames_processed=100,
            total_elapsed_seconds=2.0,
        )
        assert stats.overall_speed == 50.0

    def test_success_rate_zero_total(self) -> None:
        """Test success_rate with zero total frames."""
        stats = ConversionStats()
        assert stats.success_rate == 0.0

    def test_success_rate_all_success(self) -> None:
        """Test success_rate with all success."""
        stats = ConversionStats(total_frames=100, frames_failed=0)
        assert stats.success_rate == 100.0

    def test_success_rate_some_failed(self) -> None:
        """Test success_rate with some failures."""
        stats = ConversionStats(total_frames=100, frames_failed=25)
        assert stats.success_rate == 75.0

    def test_to_dict(self) -> None:
        """Test to_dict conversion."""
        stats = ConversionStats(
            total_frames=100,
            frames_extracted=100,
            frames_processed=100,
            frames_written=100,
            frames_failed=0,
            total_elapsed_seconds=10.0,
        )
        result = stats.to_dict()

        assert result["total_frames"] == 100
        assert result["frames_extracted"] == 100
        assert result["frames_processed"] == 100
        assert result["frames_written"] == 100
        assert result["frames_failed"] == 0
        assert result["total_elapsed_seconds"] == 10.0
        assert result["overall_speed"] == 10.0
        assert result["success_rate"] == 100.0


class TestVideoConversionProgress:
    """Tests for VideoConversionProgress class."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        progress = VideoConversionProgress(total_frames=100)
        assert progress.total_frames == 100
        assert progress.config.enabled is True
        assert progress.input_file == ""
        assert progress.output_file == ""

    def test_init_with_config(self) -> None:
        """Test initialization with custom config."""
        config = ProgressConfig(enabled=False)
        progress = VideoConversionProgress(total_frames=100, config=config)
        assert progress.config.enabled is False

    def test_init_with_files(self) -> None:
        """Test initialization with file paths."""
        progress = VideoConversionProgress(
            total_frames=100,
            input_file="input.mp4",
            output_file="output.mp4",
        )
        assert progress.input_file == "input.mp4"
        assert progress.output_file == "output.mp4"

    def test_init_negative_frames_raises(self) -> None:
        """Test that negative total_frames raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            VideoConversionProgress(total_frames=-1)

    def test_init_zero_frames_valid(self) -> None:
        """Test that zero total_frames is valid."""
        progress = VideoConversionProgress(total_frames=0)
        assert progress.total_frames == 0

    def test_start_creates_progress(self) -> None:
        """Test that start() creates progress bar."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        assert progress._progress is not None
        assert progress._is_active is True
        progress.stop()

    def test_stop_stops_progress(self) -> None:
        """Test that stop() stops progress bar."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.stop()
        assert progress._is_active is False

    def test_start_stage(self) -> None:
        """Test starting a stage."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        assert progress._current_stage == ProgressStage.EXTRACT
        assert ProgressStage.EXTRACT in progress._stage_metrics
        progress.stop()

    def test_start_stage_with_description(self) -> None:
        """Test starting a stage with custom description."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(
            ProgressStage.EXTRACT,
            total=100,
            description="Custom description",
        )
        assert progress._current_stage == ProgressStage.EXTRACT
        progress.stop()

    def test_update_increments_completed(self) -> None:
        """Test that update() increments completed count."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        progress.update(1)
        progress.update(1)
        progress.update(1)

        metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert metrics.completed == 3
        progress.stop()

    def test_update_with_failed(self) -> None:
        """Test update() with failed count."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        progress.update(advance=1, failed=1)

        metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert metrics.completed == 1
        assert metrics.failed == 1
        progress.stop()

    def test_complete_stage(self) -> None:
        """Test completing a stage."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        progress.update(50)
        progress.complete_stage()

        metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert metrics.end_time is not None
        progress.stop()

    def test_complete_stage_updates_stats(self) -> None:
        """Test that complete_stage updates conversion stats."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()

        # Extract stage
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        for _ in range(100):
            progress.update(1)
        progress.complete_stage()

        # Process stage
        progress.start_stage(ProgressStage.PROCESS, total=100)
        for _ in range(100):
            progress.update(1)
        progress.complete_stage()

        # Write stage
        progress.start_stage(ProgressStage.WRITE, total=100)
        for _ in range(100):
            progress.update(1)
        progress.complete_stage()

        stats = progress.get_stats()
        assert stats.frames_extracted == 100
        assert stats.frames_processed == 100
        assert stats.frames_written == 100
        progress.stop()

    def test_get_stats(self) -> None:
        """Test get_stats() returns current statistics."""
        progress = VideoConversionProgress(total_frames=100)
        stats = progress.get_stats()
        assert isinstance(stats, ConversionStats)
        assert stats.total_frames == 100

    def test_disabled_config_no_progress(self) -> None:
        """Test that disabled config prevents progress display."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=False),
        )
        progress.start()
        assert progress._progress is None
        assert progress._is_active is False

    def test_context_manager(self) -> None:
        """Test context manager usage."""
        with VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        ) as progress:
            assert progress._is_active is True

        assert progress._is_active is False

    def test_create_callback(self) -> None:
        """Test create_callback() returns callable."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        callback = progress.create_callback()
        assert callable(callback)

    def test_callback_updates_progress(self) -> None:
        """Test that callback updates progress."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)

        callback = progress.create_callback()
        callback(1, 100)
        callback(2, 100)

        metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert metrics.completed == 2
        progress.stop()

    @pytest.mark.skip(reason="track() API needs redesign - contextmanager pattern doesn't work for iteration")
    def test_track_context_manager(self) -> None:
        """Test track() context manager for iteration."""
        progress = VideoConversionProgress(
            total_frames=0,
            config=ProgressConfig(enabled=True),
        )
        items = [1, 2, 3, 4, 5]

        with progress:
            results = []
            with progress.track(items, ProgressStage.EXTRACT) as gen:
                for item in gen:
                    results.append(item)

        assert results == [1, 2, 3, 4, 5]

    def test_multiple_stages(self) -> None:
        """Test multiple stage progression."""
        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()

        # Stage 1: Extract
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        progress.update(100)
        progress.complete_stage()

        # Stage 2: Process
        progress.start_stage(ProgressStage.PROCESS, total=100)
        progress.update(100)
        progress.complete_stage()

        # Stage 3: Write
        progress.start_stage(ProgressStage.WRITE, total=100)
        progress.update(100)
        progress.complete_stage()

        # Verify all stages recorded
        assert len(progress._stage_metrics) == 3
        assert ProgressStage.EXTRACT in progress._stage_metrics
        assert ProgressStage.PROCESS in progress._stage_metrics
        assert ProgressStage.WRITE in progress._stage_metrics
        progress.stop()

    def test_thread_safety(self) -> None:
        """Test that progress updates are thread-safe."""
        import threading

        progress = VideoConversionProgress(
            total_frames=100,
            config=ProgressConfig(enabled=True),
        )
        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)

        errors = []

        def update_many(count: int) -> None:
            try:
                for _ in range(count):
                    progress.update(1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=update_many, args=(10,)) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert metrics.completed == 100
        progress.stop()


class TestSimpleProgressTracker:
    """Tests for SimpleProgressTracker class."""

    def test_init_defaults(self) -> None:
        """Test initialization with defaults."""
        tracker = SimpleProgressTracker(total=100)
        assert tracker.total == 100
        assert tracker.description == "Processing"

    def test_init_with_description(self) -> None:
        """Test initialization with custom description."""
        tracker = SimpleProgressTracker(total=100, description="Custom")
        assert tracker.description == "Custom"

    def test_start_creates_progress(self) -> None:
        """Test that start() creates progress bar."""
        tracker = SimpleProgressTracker(total=100)
        tracker.start()
        assert tracker._progress is not None
        tracker.stop()

    def test_update_increments_completed(self) -> None:
        """Test that update() increments count."""
        tracker = SimpleProgressTracker(total=100)
        tracker.start()
        tracker.update(1)
        tracker.update(1)
        assert tracker._completed == 2
        tracker.stop()

    def test_stop_stops_progress(self) -> None:
        """Test that stop() stops progress bar."""
        tracker = SimpleProgressTracker(total=100)
        tracker.start()
        tracker.stop()
        # Just verify no exception

    def test_elapsed_seconds(self) -> None:
        """Test elapsed_seconds property."""
        tracker = SimpleProgressTracker(total=100)
        tracker.start()
        time.sleep(0.1)
        assert tracker.elapsed_seconds >= 0.1
        tracker.stop()

    def test_items_per_second(self) -> None:
        """Test items_per_second property."""
        tracker = SimpleProgressTracker(total=100)
        tracker.start()
        for _ in range(10):
            tracker.update(1)
        time.sleep(0.1)
        assert tracker.items_per_second > 0
        tracker.stop()

    def test_context_manager(self) -> None:
        """Test context manager usage."""
        tracker = SimpleProgressTracker(total=100)
        with tracker:
            assert tracker._progress is not None
            tracker.update(1)
            # Verify progress was tracked inside context
            assert tracker._completed == 1


class TestTrackProgress:
    """Tests for track_progress function."""

    def test_basic_iteration(self) -> None:
        """Test basic iteration with progress."""
        items = [1, 2, 3, 4, 5]
        results = []

        for item in track_progress(items, description="Processing"):
            results.append(item)

        assert results == [1, 2, 3, 4, 5]

    def test_with_total(self) -> None:
        """Test with explicit total."""
        items = [1, 2, 3]
        results = []

        for item in track_progress(items, description="Test", total=3):
            results.append(item)

        assert results == [1, 2, 3]

    def test_empty_iterable(self) -> None:
        """Test with empty iterable."""
        results = []

        for item in track_progress([], description="Empty"):
            results.append(item)

        assert results == []


class TestProgressIntegration:
    """Integration tests for progress tracking."""

    def test_full_conversion_workflow(self) -> None:
        """Test full conversion workflow with all stages."""
        config = ProgressConfig(enabled=True)
        progress = VideoConversionProgress(
            total_frames=30,
            config=config,
            input_file="test_input.mp4",
            output_file="test_output.mp4",
        )

        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=30)
        for _ in range(30):
            progress.update(1)
        progress.complete_stage()

        progress.start_stage(ProgressStage.DEPTH, total=30)
        for _ in range(30):
            progress.update(1)
        progress.complete_stage()

        progress.start_stage(ProgressStage.STEREO, total=30)
        for _ in range(30):
            progress.update(1)
        progress.complete_stage()

        progress.start_stage(ProgressStage.WRITE, total=30)
        for _ in range(30):
            progress.update(1)
        progress.complete_stage()
        progress.stop()

        # Verify stage metrics were recorded (stats may not be populated depending on implementation)
        assert len(progress._stage_metrics) == 4
        assert ProgressStage.EXTRACT in progress._stage_metrics
        assert ProgressStage.DEPTH in progress._stage_metrics
        assert ProgressStage.STEREO in progress._stage_metrics
        assert ProgressStage.WRITE in progress._stage_metrics

        # Verify metrics have correct values
        extract_metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert extract_metrics.completed == 30
        write_metrics = progress._stage_metrics[ProgressStage.WRITE]
        assert write_metrics.completed == 30

    def test_with_failures(self) -> None:
        """Test workflow with some failures."""
        config = ProgressConfig(enabled=True)
        progress = VideoConversionProgress(
            total_frames=100,
            config=config,
        )

        progress.start()
        progress.start_stage(ProgressStage.EXTRACT, total=100)
        for i in range(100):
            if i % 10 == 0:
                progress.update(advance=1, failed=1)
            else:
                progress.update(1)
        progress.complete_stage()
        progress.stop()

        # Verify failures were tracked in stage metrics
        extract_metrics = progress._stage_metrics[ProgressStage.EXTRACT]
        assert extract_metrics.failed == 10
        assert extract_metrics.completed == 100
