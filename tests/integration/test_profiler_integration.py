"""Integration tests for profiler usage in processing pipeline.

Tests the profiler's integration with actual processing workflows,
demonstrating real-world usage patterns for video conversion pipeline.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def reset_profiler_registry() -> Generator[None, None, None]:
    """Reset profiler registry before and after each test."""
    import sys

    # Reset before test
    if "video2d3d.utils.profiler" in sys.modules:
        from video2d3d.utils.profiler import _profilers

        _profilers.clear()

    yield

    # Reset after test
    if "video2d3d.utils.profiler" in sys.modules:
        from video2d3d.utils.profiler import _profilers

        _profilers.clear()


class TestProfilerPipelineIntegration:
    """Integration tests for profiler with pipeline-style processing."""

    def test_video_conversion_pipeline_profiling(self) -> None:
        """Test profiling a simulated video conversion pipeline."""
        from video2d3d.utils.profiler import PipelineProfiler

        pipeline = PipelineProfiler("video_conversion", auto_log=False)
        pipeline.start()

        # Simulate frame extraction stage
        with pipeline.stage("frame_extraction"):
            time.sleep(0.01)  # Simulate work

        # Simulate depth estimation stage
        with pipeline.stage("depth_estimation"):
            time.sleep(0.02)  # Simulate more work

        # Simulate stereo generation stage
        with pipeline.stage("stereo_generation"):
            time.sleep(0.015)  # Simulate work

        # Simulate encoding stage
        with pipeline.stage("encoding"):
            time.sleep(0.005)  # Simulate less work

        result = pipeline.stop()

        # Verify all stages were tracked
        assert len(result.components) == 4
        assert "frame_extraction" in result.components
        assert "depth_estimation" in result.components
        assert "stereo_generation" in result.components
        assert "encoding" in result.components

        # Verify depth estimation is likely the bottleneck
        bottlenecks = result.get_bottlenecks(threshold_percent=20.0)
        bottleneck_names = [b.name for b in bottlenecks]
        assert "depth_estimation" in bottleneck_names

        # Verify total time is reasonable
        assert result.total_time_ms >= 45  # At least sum of sleeps

        # Verify report generation
        report = pipeline.get_report()
        assert "video_conversion" in report
        assert "Pipeline Flow Analysis" in report

    def test_nested_profiling_with_child_profilers(self) -> None:
        """Test creating nested profilers for sub-components."""
        from video2d3d.utils.profiler import Profiler

        parent = Profiler("parent_pipeline", auto_log=False)

        with parent.measure("main_operation"):
            time.sleep(0.01)

            # Create child profiler for sub-operations
            child = parent.create_child("sub_operations")
            with child.measure("sub_op_1"):
                time.sleep(0.005)

            with child.measure("sub_op_2"):
                time.sleep(0.005)

        parent_result = parent.get_result()

        # Verify parent tracked main operation
        assert "main_operation" in parent_result.components

        # Verify child has correct name
        assert child.session_name == "parent_pipeline.sub_operations"

        # Verify child tracked sub-operations
        child_result = child.get_result()
        assert "sub_op_1" in child_result.components
        assert "sub_op_2" in child_result.components


class TestProfilerBatchProcessingIntegration:
    """Integration tests for profiler with batch processing."""

    def test_batch_processing_profiling(self) -> None:
        """Test profiling batch processing of multiple items."""
        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("batch_processing", auto_log=False)

        # Simulate processing multiple frames
        num_frames = 10
        for i in range(num_frames):
            with profiler.measure("frame_processing"):
                time.sleep(0.001 * (1 + i % 3))  # Variable processing time

        result = profiler.get_result()
        stats = result.components.get("frame_processing")

        assert stats is not None
        assert stats.call_count == num_frames
        assert stats.total_time_ms > 0
        assert stats.avg_time_ms > 0
        assert stats.min_time_ms <= stats.max_time_ms

    def test_parallel_component_profiling(self) -> None:
        """Test profiling multiple components running in parallel."""
        from concurrent.futures import ThreadPoolExecutor

        from video2d3d.utils.profiler import Profiler

        profiler = Profiler("parallel_processing", auto_log=False)

        def process_component(name: str, duration_ms: float) -> None:
            with profiler.measure(name):
                time.sleep(duration_ms / 1000)

        # Process multiple components in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(process_component, "component_a", 10),
                executor.submit(process_component, "component_b", 15),
                executor.submit(process_component, "component_c", 20),
            ]
            for future in futures:
                future.result()

        result = profiler.get_result()

        # All components should be tracked
        assert len(result.components) == 3
        assert "component_a" in result.components
        assert "component_b" in result.components
        assert "component_c" in result.components


class TestProfilerWithDecoratorsIntegration:
    """Integration tests for profiler decorators in realistic scenarios."""

    def test_profile_component_decorator_integration(self) -> None:
        """Test profile_component decorator in realistic workflow."""
        from unittest.mock import patch

        from video2d3d.utils.profiler import profile_component

        processed_items: list[int] = []

        @profile_component("data_processing")
        def process_item(item: int) -> int:
            time.sleep(0.001)
            processed_items.append(item)
            return item * 2

        with patch("video2d3d.utils.profiler.log_performance"):
            results = []
            for i in range(5):
                results.append(process_item(i))

        assert results == [0, 2, 4, 6, 8]
        assert len(processed_items) == 5


class TestProfilerMemoryBoundedIntegration:
    """Integration tests for memory-bounded time storage."""

    def test_memory_bounded_with_many_measurements(self) -> None:
        """Test that memory is bounded when many measurements are taken."""
        from video2d3d.utils.profiler import ComponentStats, MAX_STORED_TIMES

        stats = ComponentStats(name="test")

        # Add many more measurements than the limit
        num_measurements = MAX_STORED_TIMES * 2
        for i in range(num_measurements):
            stats.add_measurement(float(i))

        # call_count should still be accurate
        assert stats.call_count == num_measurements

        # times list should be bounded
        assert len(stats.times) <= MAX_STORED_TIMES

        # Statistics should still be calculable
        assert stats.total_time_ms > 0
        assert stats.avg_time_ms > 0


class TestProfilerGlobalRegistryIntegration:
    """Integration tests for global profiler registry."""

    def test_shared_profiler_across_functions(self) -> None:
        """Test using shared profiler from registry across functions."""
        from video2d3d.utils.profiler import (
            clear_profiler,
            get_profiler,
            get_all_profilers,
        )

        # Get shared profiler
        profiler1 = get_profiler("shared_profiler")

        # Use profiler in one function
        with profiler1.measure("operation_a"):
            time.sleep(0.005)

        # Get same profiler in another context
        profiler2 = get_profiler("shared_profiler")
        with profiler2.measure("operation_b"):
            time.sleep(0.005)

        # Both operations should be in the same profiler
        result = profiler2.get_result()
        assert len(result.components) == 2
        assert "operation_a" in result.components
        assert "operation_b" in result.components

        # Verify registry contains the profiler
        all_profilers = get_all_profilers()
        assert "shared_profiler" in all_profilers

        # Clean up
        assert clear_profiler("shared_profiler") is True
        all_profilers = get_all_profilers()
        assert "shared_profiler" not in all_profilers


class TestProfilerReportIntegration:
    """Integration tests for profiler report generation."""

    def test_comprehensive_report_generation(self) -> None:
        """Test generating comprehensive report from realistic workload."""
        from video2d3d.utils.profiler import PipelineProfiler

        pipeline = PipelineProfiler("comprehensive_test", auto_log=False)
        pipeline.start()

        # Simulate realistic processing stages with multiple calls
        for _ in range(5):
            with pipeline.stage("frame_decode"):
                time.sleep(0.002)

        for _ in range(5):
            with pipeline.stage("depth_estimation"):
                time.sleep(0.005)

        for _ in range(5):
            with pipeline.stage("stereo_render"):
                time.sleep(0.003)

        with pipeline.stage("video_encode"):
            time.sleep(0.01)

        result = pipeline.stop()
        report = pipeline.get_report()

        # Verify report structure
        assert "comprehensive_test" in report
        assert "Pipeline Flow Analysis" in report
        assert "frame_decode" in report
        assert "depth_estimation" in report
        assert "stereo_render" in report
        assert "video_encode" in report

        # Verify statistics
        assert result.components["frame_decode"].call_count == 5
        assert result.components["depth_estimation"].call_count == 5
        assert result.components["stereo_render"].call_count == 5
        assert result.components["video_encode"].call_count == 1

        # Verify summary includes timing info
        assert "Total Time:" in report
        assert "Components:" in report
