"""Unit tests for profiling utilities.

Tests cover:
- Profiler class functionality
- Component statistics tracking
- Pipeline profiler
- Decorator and context manager utilities
- Thread safety
"""

from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def reset_profiler_registry() -> Generator[None, None, None]:
    """Reset profiler registry before and after each test."""
    # Reset before test
    if "video2d3d.utils.profiler" in sys.modules:
        from video2d3d.utils.profiler import _profilers

        _profilers.clear()

    yield

    # Reset after test
    if "video2d3d.utils.profiler" in sys.modules:
        from video2d3d.utils.profiler import _profilers

        _profilers.clear()


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock logger module."""
    with patch("video2d3d.utils.profiler.get_logger") as mock_get_logger:
        mock_log = MagicMock()
        mock_get_logger.return_value = mock_log
        yield mock_log


@pytest.fixture
def mock_log_performance() -> Generator[MagicMock, None, None]:
    """Mock log_performance function."""
    with patch("video2d3d.utils.profiler.log_performance") as mock:
        yield mock


class TestComponentStats:
    """Tests for ComponentStats dataclass."""

    def test_component_stats_creation(self) -> None:
        """Test creating ComponentStats."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test_component")
        assert stats.name == "test_component"
        assert stats.total_time_ms == 0.0
        assert stats.call_count == 0
        assert stats.min_time_ms == float("inf")
        assert stats.max_time_ms == 0.0

    def test_add_measurement(self) -> None:
        """Test adding measurements updates stats correctly."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test")
        stats.add_measurement(10.0)
        stats.add_measurement(20.0)
        stats.add_measurement(15.0)

        assert stats.call_count == 3
        assert stats.total_time_ms == 45.0
        assert stats.avg_time_ms == 15.0
        assert stats.min_time_ms == 10.0
        assert stats.max_time_ms == 20.0

    def test_avg_time_empty(self) -> None:
        """Test avg_time returns 0 when no measurements."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test")
        assert stats.avg_time_ms == 0.0

    def test_std_dev_calculation(self) -> None:
        """Test standard deviation calculation."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test")
        # Add consistent values (std dev should be 0)
        stats.add_measurement(10.0)
        stats.add_measurement(10.0)
        assert stats.std_dev_ms == 0.0

        # Add varied values
        stats2 = ComponentStats(name="test2")
        stats2.add_measurement(10.0)
        stats2.add_measurement(20.0)
        assert stats2.std_dev_ms > 0

    def test_median_calculation(self) -> None:
        """Test median calculation."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test")
        stats.add_measurement(10.0)
        stats.add_measurement(20.0)
        stats.add_measurement(30.0)
        assert stats.median_time_ms == 20.0

        stats2 = ComponentStats(name="test2")
        stats2.add_measurement(10.0)
        stats2.add_measurement(20.0)
        stats2.add_measurement(30.0)
        stats2.add_measurement(40.0)
        assert stats2.median_time_ms == 25.0  # Average of 20 and 30

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test_component")
        stats.add_measurement(10.5)
        result = stats.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test_component"
        assert result["call_count"] == 1
        assert result["total_time_ms"] == 10.5


class TestProfilerResult:
    """Tests for ProfilerResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating ProfilerResult."""
        from video2d3d.utils.profiler import ProfilerResult

        result = ProfilerResult(session_name="test_session")
        assert result.session_name == "test_session"
        assert len(result.components) == 0
        assert result.total_time_ms == 0.0

    def test_total_time_seconds(self) -> None:
        """Test total_time_seconds property."""
        from video2d3d.utils.profiler import ProfilerResult

        result = ProfilerResult(session_name="test", total_time_ms=1500.0)
        assert result.total_time_seconds == 1.5

    def test_get_sorted_components(self) -> None:
        """Test components are sorted by total time."""
        from video2d3d.utils.profiler import ComponentStats, ProfilerResult

        stats1 = ComponentStats(name="fast")
        stats1.add_measurement(10.0)

        stats2 = ComponentStats(name="slow")
        stats2.add_measurement(100.0)

        result = ProfilerResult(
            session_name="test",
            components={"fast": stats1, "slow": stats2},
        )

        sorted_comps = result.get_sorted_components()
        assert sorted_comps[0].name == "slow"
        assert sorted_comps[1].name == "fast"

    def test_get_bottlenecks(self) -> None:
        """Test bottleneck detection."""
        from video2d3d.utils.profiler import ComponentStats, ProfilerResult

        stats1 = ComponentStats(name="small")
        stats1.add_measurement(10.0)

        stats2 = ComponentStats(name="large")
        stats2.add_measurement(90.0)  # 90% of total

        result = ProfilerResult(
            session_name="test",
            components={"small": stats1, "large": stats2},
            total_time_ms=100.0,
        )

        bottlenecks = result.get_bottlenecks(threshold_percent=15.0)
        assert len(bottlenecks) == 1
        assert bottlenecks[0].name == "large"

    def test_to_dict(self) -> None:
        """Test serialization to dictionary."""
        from video2d3d.utils.profiler import ComponentStats, ProfilerResult

        stats = ComponentStats(name="test")
        stats.add_measurement(50.0)

        result = ProfilerResult(
            session_name="session",
            components={"test": stats},
            total_time_ms=50.0,
            start_time=1000.0,
            end_time=1050.0,
        )

        d = result.to_dict()
        assert d["session_name"] == "session"
        assert "components" in d
        assert "bottlenecks" in d


class TestProfiler:
    """Tests for Profiler class."""

    def test_profiler_creation(self) -> None:
        """Test creating a Profiler instance."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test_session")
        assert profiler.session_name == "test_session"
        assert profiler.auto_log is True

    def test_profiler_start_stop(self) -> None:
        """Test start and stop methods."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)
        profiler.start()
        assert profiler._start_time is not None

        result = profiler.stop()
        assert profiler._end_time is not None
        assert result.session_name == "test"

    def test_measure_context_manager(self) -> None:
        """Test measure context manager records timing."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        with profiler.measure("operation1"):
            time.sleep(0.01)

        stats = profiler.get_stats("operation1")
        assert stats is not None
        assert stats.call_count == 1
        assert stats.total_time_ms >= 10.0  # At least 10ms

    def test_multiple_measurements(self) -> None:
        """Test multiple measurements accumulate correctly."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        for _ in range(3):
            with profiler.measure("repeated_op"):
                time.sleep(0.005)

        stats = profiler.get_stats("repeated_op")
        assert stats is not None
        assert stats.call_count == 3

    def test_record_manual(self) -> None:
        """Test manually recording a measurement."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)
        profiler.record("manual_op", 42.5)

        stats = profiler.get_stats("manual_op")
        assert stats is not None
        assert stats.total_time_ms == 42.5

    def test_record_negative_time_raises_error(self) -> None:
        """Test record raises ValueError for negative time."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        with pytest.raises(ValueError, match="negative"):
            profiler.record("op", -10.0)

    def test_add_measurement_negative_time_raises_error(self) -> None:
        """Test add_measurement raises ValueError for negative time."""
        from video2d3d.utils.profiler import ComponentStats

        stats = ComponentStats(name="test")

        with pytest.raises(ValueError, match="negative"):
            stats.add_measurement(-5.0)

    def test_get_result(self) -> None:
        """Test get_result returns complete ProfilerResult."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        with profiler.measure("op1"):
            pass
        with profiler.measure("op2"):
            pass

        result = profiler.get_result()
        assert result.session_name == "test"
        assert len(result.components) == 2

    def test_get_summary(self) -> None:
        """Test get_summary returns formatted string."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        with profiler.measure("operation"):
            pass

        summary = profiler.get_summary()
        assert "Profiler Summary: test" in summary
        assert "operation" in summary

    def test_reset(self) -> None:
        """Test reset clears all data."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("test", auto_log=False)

        with profiler.measure("op"):
            pass

        assert len(profiler._components) == 1
        profiler.reset()
        assert len(profiler._components) == 0

    def test_create_child(self) -> None:
        """Test creating a child profiler."""
        from video2d3d.utils.profiler import Profiler

        parent = Profiler("parent", auto_log=False)
        child = parent.create_child("child")

        assert child.session_name == "parent.child"
        assert child.parent is parent


class TestProfilerRegistry:
    """Tests for global profiler registry."""

    def test_get_profiler_creates_new(self) -> None:
        """Test get_profiler creates new profiler."""
        from video2d3d.utils.profiler import get_profiler

        profiler = get_profiler("new_session")
        assert profiler is not None
        assert profiler.session_name == "new_session"

    def test_get_profiler_returns_existing(self) -> None:
        """Test get_profiler returns existing profiler."""
        from video2d3d.utils.profiler import get_profiler

        profiler1 = get_profiler("session")
        profiler2 = get_profiler("session")

        assert profiler1 is profiler2

    def test_clear_profiler(self) -> None:
        """Test clear_profiler removes profiler."""
        from video2d3d.utils.profiler import clear_profiler, get_profiler

        get_profiler("to_clear")
        result = clear_profiler("to_clear")
        assert result is True

        result2 = clear_profiler("nonexistent")
        assert result2 is False

    def test_get_all_profilers(self) -> None:
        """Test get_all_profilers returns all registered profilers."""
        from video2d3d.utils.profiler import get_all_profilers, get_profiler

        get_profiler("session1")
        get_profiler("session2")

        all_profilers = get_all_profilers()
        assert "session1" in all_profilers
        assert "session2" in all_profilers


class TestProfileComponent:
    """Tests for profile_component decorator."""

    def test_decorator_profiles_function(self, mock_log_performance: MagicMock) -> None:
        """Test decorator profiles decorated function."""
        from video2d3d.utils.profiler import profile_component

        @profile_component("test_func")
        def my_function() -> str:
            time.sleep(0.005)
            return "result"

        result = my_function()
        assert result == "result"

        # Check that performance was logged
        mock_log_performance.assert_called()

    def test_decorator_preserves_function_name(self) -> None:
        """Test decorator preserves original function name."""
        from video2d3d.utils.profiler import profile_component

        @profile_component()
        def my_function() -> None:
            pass

        assert my_function.__name__ == "my_function"


class TestProfileBlock:
    """Tests for profile_block context manager."""

    def test_profile_block_profiles_code(
        self, mock_logger: MagicMock, mock_log_performance: MagicMock
    ) -> None:
        """Test profile_block profiles code block."""
        from video2d3d.utils.profiler import profile_block

        with profile_block("test_block"):
            time.sleep(0.005)

        # Check that the block was profiled
        mock_logger.info.assert_called()


class TestPipelineProfiler:
    """Tests for PipelineProfiler class."""

    def test_pipeline_profiler_stages(self) -> None:
        """Test pipeline profiler tracks stages."""
        from video2d3d.utils.profiler import PipelineProfiler

        pipeline = PipelineProfiler("test_pipeline", auto_log=False)
        pipeline.start()

        with pipeline.stage("stage1"):
            time.sleep(0.005)

        with pipeline.stage("stage2"):
            time.sleep(0.005)

        result = pipeline.stop()

        assert len(result.components) == 2
        assert "stage1" in result.components
        assert "stage2" in result.components

    def test_pipeline_get_report(self) -> None:
        """Test pipeline get_report returns formatted report."""
        from video2d3d.utils.profiler import PipelineProfiler

        pipeline = PipelineProfiler("test_pipeline", auto_log=False)
        pipeline.start()

        with pipeline.stage("stage1"):
            pass

        pipeline.stop()

        report = pipeline.get_report()
        assert "test_pipeline" in report
        assert "stage1" in report


class TestTimedExecution:
    """Tests for timed_execution function."""

    def test_timed_execution_returns_result_and_time(self, mock_log_performance: MagicMock) -> None:
        """Test timed_execution returns result and timing."""
        from video2d3d.utils.profiler import timed_execution

        def slow_function(x: int) -> int:
            time.sleep(0.01)
            return x * 2

        result, time_ms = timed_execution("slow_func", slow_function, 5)

        assert result == 10
        assert time_ms >= 10.0
        mock_log_performance.assert_called()


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_measurements(self) -> None:
        """Test concurrent measurements don't cause race conditions."""
        import threading

        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("concurrent_test", auto_log=False)
        errors: list[Exception] = []

        def measure_task() -> None:
            try:
                for _ in range(100):
                    with profiler.measure("concurrent_op"):
                        pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=measure_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        stats = profiler.get_stats("concurrent_op")
        assert stats is not None
        assert stats.call_count == 1000  # 10 threads * 100 calls
