"""Profiling tools for identifying bottlenecks in the processing pipeline.

This module provides per-component timing analysis and profiling utilities:
- Profiler class for tracking component timings
- Context manager and decorator for easy profiling
- Statistics aggregation and reporting
- Memory usage tracking integration

Example usage:
    ```python
    from video2d3d.utils.profiler import Profiler, profile_component

    # Using the profiler directly
    profiler = Profiler("video_conversion")
    with profiler.measure("depth_estimation"):
        # ... depth estimation code ...
        pass
    with profiler.measure("stereo_generation"):
        # ... stereo generation code ...
        pass
    print(profiler.get_summary())

    # Using the decorator
    @profile_component("depth_estimation")
    def estimate_depth(frame):
        # ... code ...
        pass

    # Using the context manager
    with profile_block("stereo_generation"):
        # ... code ...
        pass
    ```
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import wraps
from statistics import mean, median, stdev
from threading import Lock
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    TypeVar,
    Union,
)

from video2d3d.utils.logger import get_logger, log_performance

if TYPE_CHECKING:
    from loguru import Logger


F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class ComponentStats:
    """Statistics for a single profiled component.

    Attributes:
        name: Component name.
        total_time_ms: Total accumulated time in milliseconds.
        call_count: Number of times the component was called.
        min_time_ms: Minimum execution time.
        max_time_ms: Maximum execution time.
        times: List of individual execution times (for calculating stdev).
    """

    name: str
    total_time_ms: float = 0.0
    call_count: int = 0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    times: List[float] = field(default_factory=list)

    @property
    def avg_time_ms(self) -> float:
        """Average execution time in milliseconds."""
        if self.call_count == 0:
            return 0.0
        return self.total_time_ms / self.call_count

    @property
    def std_dev_ms(self) -> float:
        """Standard deviation of execution times in milliseconds."""
        if len(self.times) < 2:
            return 0.0
        return stdev(self.times)

    @property
    def median_time_ms(self) -> float:
        """Median execution time in milliseconds."""
        if not self.times:
            return 0.0
        return median(self.times)

    def add_measurement(self, time_ms: float) -> None:
        """Add a new timing measurement.

        Args:
            time_ms: Execution time in milliseconds.
        """
        self.total_time_ms += time_ms
        self.call_count += 1
        self.min_time_ms = min(self.min_time_ms, time_ms)
        self.max_time_ms = max(self.max_time_ms, time_ms)
        self.times.append(time_ms)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "total_time_ms": round(self.total_time_ms, 3),
            "call_count": self.call_count,
            "avg_time_ms": round(self.avg_time_ms, 3),
            "min_time_ms": round(self.min_time_ms, 3) if self.min_time_ms != float("inf") else 0,
            "max_time_ms": round(self.max_time_ms, 3),
            "median_time_ms": round(self.median_time_ms, 3),
            "std_dev_ms": round(self.std_dev_ms, 3),
        }


@dataclass
class ProfilerResult:
    """Complete profiling result for a session.

    Attributes:
        session_name: Name of the profiling session.
        components: Dictionary of component name to stats.
        total_time_ms: Total elapsed time for the session.
        start_time: Unix timestamp of session start.
        end_time: Unix timestamp of session end.
    """

    session_name: str
    components: Dict[str, ComponentStats] = field(default_factory=dict)
    total_time_ms: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0

    @property
    def total_time_seconds(self) -> float:
        """Total time in seconds."""
        return self.total_time_ms / 1000

    def get_sorted_components(self) -> List[ComponentStats]:
        """Get components sorted by total time (descending)."""
        return sorted(
            self.components.values(),
            key=lambda c: c.total_time_ms,
            reverse=True,
        )

    def get_bottlenecks(self, threshold_percent: float = 10.0) -> List[ComponentStats]:
        """Get components that exceed the threshold percentage of total time.

        Args:
            threshold_percent: Minimum percentage of total time to be considered a bottleneck.

        Returns:
            List of components exceeding the threshold.
        """
        if self.total_time_ms == 0:
            return []

        threshold_ms = self.total_time_ms * (threshold_percent / 100)
        return [c for c in self.components.values() if c.total_time_ms >= threshold_ms]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_name": self.session_name,
            "total_time_ms": round(self.total_time_ms, 3),
            "total_time_seconds": round(self.total_time_seconds, 3),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "components": {name: stats.to_dict() for name, stats in self.components.items()},
            "bottlenecks": [b.name for b in self.get_bottlenecks()],
        }


class Profiler:
    """Thread-safe profiler for tracking component execution times.

    This class provides per-component timing analysis with support for
    nested measurements and statistical aggregation.

    Example usage:
        ```python
        profiler = Profiler("video_conversion")

        # Measure a single operation
        with profiler.measure("depth_estimation"):
            depth_map = estimate_depth(frame)

        # Multiple measurements
        for frame in frames:
            with profiler.measure("frame_processing"):
                process_frame(frame)

        # Get results
        summary = profiler.get_summary()
        print(summary)

        # Export as dictionary
        result = profiler.get_result()
        ```
    """

    def __init__(
        self,
        session_name: str,
        auto_log: bool = True,
        parent: Optional["Profiler"] = None,
    ) -> None:
        """Initialize the profiler.

        Args:
            session_name: Name for this profiling session.
            auto_log: Whether to automatically log performance metrics.
            parent: Optional parent profiler for nested profiling.
        """
        self.session_name = session_name
        self.auto_log = auto_log
        self.parent = parent

        self._components: Dict[str, ComponentStats] = {}
        self._lock = Lock()
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._logger = get_logger("profiler")

        # Stack for nested measurements
        self._measurement_stack: List[str] = []

    def start(self) -> "Profiler":
        """Start the profiling session.

        Returns:
            Self for chaining.
        """
        self._start_time = time.time()
        self._logger.debug(f"Profiler '{self.session_name}' started")
        return self

    def stop(self) -> ProfilerResult:
        """Stop the profiling session and get results.

        Returns:
            ProfilerResult with all collected statistics.
        """
        self._end_time = time.time()
        result = self.get_result()
        self._logger.debug(f"Profiler '{self.session_name}' stopped: {result.total_time_ms:.2f}ms")

        if self.auto_log:
            log_performance(
                f"profiler_session_{self.session_name}",
                result.total_time_ms,
                components=len(result.components),
                total_calls=sum(c.call_count for c in result.components.values()),
            )

        return result

    @contextmanager
    def measure(self, component_name: str) -> Generator[None, None, None]:
        """Context manager to measure execution time of a component.

        Args:
            component_name: Name of the component to measure.

        Yields:
            None

        Example:
            ```python
            with profiler.measure("depth_estimation"):
                depth_map = estimate_depth(frame)
            ```
        """
        start_time = time.perf_counter()
        self._measurement_stack.append(component_name)

        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            self._measurement_stack.pop()

            with self._lock:
                if component_name not in self._components:
                    self._components[component_name] = ComponentStats(name=component_name)
                self._components[component_name].add_measurement(elapsed_ms)

            if self.auto_log:
                log_performance(
                    f"component_{component_name}",
                    elapsed_ms,
                    session=self.session_name,
                    depth=len(self._measurement_stack),
                )

    def record(self, component_name: str, time_ms: float) -> None:
        """Record a timing measurement manually.

        Args:
            component_name: Name of the component.
            time_ms: Execution time in milliseconds.
        """
        with self._lock:
            if component_name not in self._components:
                self._components[component_name] = ComponentStats(name=component_name)
            self._components[component_name].add_measurement(time_ms)

    def get_stats(self, component_name: str) -> Optional[ComponentStats]:
        """Get statistics for a specific component.

        Args:
            component_name: Name of the component.

        Returns:
            ComponentStats if found, None otherwise.
        """
        return self._components.get(component_name)

    def get_result(self) -> ProfilerResult:
        """Get the complete profiling result.

        Returns:
            ProfilerResult with all collected statistics.
        """
        with self._lock:
            components_copy = {k: v for k, v in self._components.items()}

        total_ms = sum(c.total_time_ms for c in components_copy.values())

        return ProfilerResult(
            session_name=self.session_name,
            components=components_copy,
            total_time_ms=total_ms,
            start_time=self._start_time or 0.0,
            end_time=self._end_time or 0.0,
        )

    def get_summary(self, top_n: int = 10) -> str:
        """Get a human-readable summary of profiling results.

        Args:
            top_n: Number of top components to include.

        Returns:
            Formatted string summary.
        """
        result = self.get_result()
        sorted_components = result.get_sorted_components()[:top_n]

        lines = [
            f"\n{'=' * 60}",
            f"Profiler Summary: {self.session_name}",
            f"{'=' * 60}",
            f"Total Time: {result.total_time_ms:.2f}ms ({result.total_time_seconds:.3f}s)",
            f"Components: {len(result.components)}",
            "",
            f"{'Component':<30} {'Calls':>8} {'Total(ms)':>12} {'Avg(ms)':>10} {'%':>6}",
            f"{'-' * 70}",
        ]

        for comp in sorted_components:
            percent = (
                (comp.total_time_ms / result.total_time_ms * 100) if result.total_time_ms > 0 else 0
            )
            lines.append(
                f"{comp.name:<30} {comp.call_count:>8} {comp.total_time_ms:>12.2f} "
                f"{comp.avg_time_ms:>10.2f} {percent:>5.1f}%"
            )

        lines.append(f"{'=' * 60}")

        # Bottleneck analysis
        bottlenecks = result.get_bottlenecks(threshold_percent=15.0)
        if bottlenecks:
            lines.append("\nPotential Bottlenecks (>15% of total time):")
            for b in bottlenecks:
                percent = (
                    (b.total_time_ms / result.total_time_ms * 100)
                    if result.total_time_ms > 0
                    else 0
                )
                lines.append(f"  - {b.name}: {percent:.1f}% ({b.total_time_ms:.2f}ms)")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all profiling data."""
        with self._lock:
            self._components.clear()
            self._start_time = None
            self._end_time = None
        self._logger.debug(f"Profiler '{self.session_name}' reset")

    def create_child(self, name: str) -> "Profiler":
        """Create a child profiler for nested profiling.

        Args:
            name: Name for the child profiler.

        Returns:
            Child Profiler instance.
        """
        child_name = f"{self.session_name}.{name}"
        return Profiler(session_name=child_name, auto_log=self.auto_log, parent=self)


# Global profiler registry for multi-threaded access
_profilers: Dict[str, Profiler] = {}
_profilers_lock = Lock()


def get_profiler(session_name: str, create: bool = True) -> Optional[Profiler]:
    """Get or create a profiler by session name.

    Args:
        session_name: Name of the profiling session.
        create: Whether to create a new profiler if not found.

    Returns:
        Profiler instance if found or created, None otherwise.
    """
    with _profilers_lock:
        if session_name not in _profilers:
            if create:
                _profilers[session_name] = Profiler(session_name)
            else:
                return None
        return _profilers[session_name]


def clear_profiler(session_name: str) -> bool:
    """Clear a profiler from the registry.

    Args:
        session_name: Name of the profiling session.

    Returns:
        True if profiler was removed, False if not found.
    """
    with _profilers_lock:
        if session_name in _profilers:
            del _profilers[session_name]
            return True
        return False


def get_all_profilers() -> Dict[str, Profiler]:
    """Get all registered profilers.

    Returns:
        Dictionary of session name to Profiler.
    """
    with _profilers_lock:
        return dict(_profilers)


# Decorator for profiling functions
def profile_component(
    component_name: Optional[str] = None,
    profiler_name: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator to profile a function.

    Args:
        component_name: Name for the component (defaults to function name).
        profiler_name: Name of the profiler to use (creates new if None).

    Returns:
        Decorated function.

    Example:
        ```python
        @profile_component("depth_estimation")
        def estimate_depth(frame):
            # ... code ...
            return depth_map
        ```
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = component_name or func.__name__
            profiler = (
                get_profiler(profiler_name) if profiler_name else Profiler(name, auto_log=False)
            )

            with profiler.measure(name):
                result = func(*args, **kwargs)

            # Log the measurement
            stats = profiler.get_stats(name)
            if stats:
                log_performance(
                    f"function_{name}",
                    stats.avg_time_ms,
                    calls=stats.call_count,
                )

            return result

        return wrapper  # type: ignore

    return decorator


# Context manager for profiling code blocks
@contextmanager
def profile_block(
    component_name: str,
    profiler_name: Optional[str] = None,
) -> Generator[Profiler, None, None]:
    """Context manager to profile a code block.

    Args:
        component_name: Name for the component.
        profiler_name: Name of the profiler to use (creates temporary if None).

    Yields:
        Profiler instance.

    Example:
        ```python
        with profile_block("video_processing") as profiler:
            process_video(input_path, output_path)
        print(profiler.get_summary())
        ```
    """
    profiler = (
        get_profiler(profiler_name) if profiler_name else Profiler(component_name, auto_log=False)
    )
    profiler.start()

    with profiler.measure(component_name):
        yield profiler

    result = profiler.stop()
    get_logger("profiler").info(f"Block '{component_name}' completed: {result.total_time_ms:.2f}ms")


# Pipeline profiler for multi-stage processing
class PipelineProfiler:
    """Specialized profiler for pipeline-style processing.

    This class provides a convenient interface for profiling multi-stage
    processing pipelines with automatic stage timing.

    Example:
        ```python
        pipeline = PipelineProfiler("video_conversion")

        with pipeline.stage("frame_extraction"):
            frames = extract_frames(video)

        with pipeline.stage("depth_estimation"):
            depth_maps = estimate_depths(frames)

        with pipeline.stage("stereo_generation"):
            stereo_frames = generate_stereo(frames, depth_maps)

        print(pipeline.get_report())
        ```
    """

    def __init__(self, name: str, auto_log: bool = True) -> None:
        """Initialize the pipeline profiler.

        Args:
            name: Name for the pipeline.
            auto_log: Whether to automatically log stage performance.
        """
        self.name = name
        self._profiler = Profiler(name, auto_log=auto_log)
        self._stage_times: List[float] = []
        self._logger = get_logger("pipeline_profiler")

    def start(self) -> "PipelineProfiler":
        """Start the pipeline profiling.

        Returns:
            Self for chaining.
        """
        self._profiler.start()
        return self

    def stop(self) -> ProfilerResult:
        """Stop the pipeline and get results.

        Returns:
            ProfilerResult with all stage statistics.
        """
        return self._profiler.stop()

    @contextmanager
    def stage(self, stage_name: str) -> Generator[None, None, None]:
        """Context manager for a pipeline stage.

        Args:
            stage_name: Name of the processing stage.

        Yields:
            None
        """
        stage_start = time.perf_counter()
        self._logger.debug(f"Pipeline '{self.name}' entering stage: {stage_name}")

        with self._profiler.measure(stage_name):
            yield

        stage_time = (time.perf_counter() - stage_start) * 1000
        self._stage_times.append(stage_time)
        self._logger.debug(
            f"Pipeline '{self.name}' completed stage: {stage_name} ({stage_time:.2f}ms)"
        )

    def get_report(self) -> str:
        """Get a detailed pipeline performance report.

        Returns:
            Formatted report string.
        """
        result = self._profiler.get_result()
        summary = self._profiler.get_summary()

        # Add pipeline-specific analysis
        lines = [summary]
        lines.append("\nPipeline Flow Analysis:")

        sorted_stages = result.get_sorted_components()
        for i, stage in enumerate(sorted_stages):
            percent = (
                (stage.total_time_ms / result.total_time_ms * 100)
                if result.total_time_ms > 0
                else 0
            )
            lines.append(f"  {i + 1}. {stage.name}: {stage.total_time_ms:.2f}ms ({percent:.1f}%)")

        return "\n".join(lines)

    def get_result(self) -> ProfilerResult:
        """Get the profiling result.

        Returns:
            ProfilerResult with all statistics.
        """
        return self._profiler.get_result()


# Convenience function for quick profiling
def timed_execution(
    name: str,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, float]:
    """Execute a function and return the result with timing.

    Args:
        name: Name for the operation.
        func: Function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Tuple of (result, time_ms).

    Example:
        ```python
        result, time_ms = timed_execution("depth_estimation", estimate_depth, frame)
        print(f"Depth estimation took {time_ms:.2f}ms")
        ```
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    log_performance(name, elapsed_ms)

    return result, elapsed_ms


__all__ = [
    # Classes
    "Profiler",
    "PipelineProfiler",
    "ComponentStats",
    "ProfilerResult",
    # Decorators
    "profile_component",
    # Context managers
    "profile_block",
    # Functions
    "get_profiler",
    "clear_profiler",
    "get_all_profilers",
    "timed_execution",
]
