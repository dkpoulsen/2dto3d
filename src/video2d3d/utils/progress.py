"""Real-time progress tracking for video conversion operations.

This module provides comprehensive progress tracking capabilities:
- Multi-stage progress tracking (extract, process, write)
- Rich-based visual progress bars with speed/ETA metrics
- Thread-safe progress updates
- Integration with existing logging infrastructure
- Support for both CLI and programmatic usage

Example usage:
    ```python
    from video2d3d.utils.progress import (
        VideoConversionProgress,
        ProgressStage,
    )

    # Create progress tracker
    progress = VideoConversionProgress(total_frames=1000)

    # Track multi-stage conversion
    with progress:
        # Stage 1: Extract frames
        progress.start_stage(ProgressStage.EXTRACT, total=1000)
        for i in range(1000):
            # ... extract frame ...
            progress.update(1)
        progress.complete_stage()

        # Stage 2: Process frames
        progress.start_stage(ProgressStage.PROCESS, total=1000)
        for i in range(1000):
            # ... process frame ...
            progress.update(1)
        progress.complete_stage()

        # Stage 3: Write output
        progress.start_stage(ProgressStage.WRITE, total=1000)
        for i in range(1000):
            # ... write frame ...
            progress.update(1)
        progress.complete_stage()
    ```
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generator

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.table import Table


DEFAULT_REFRESH_RATE: float = 0.1  # seconds
DEFAULT_BAR_WIDTH: int = 40


class ProgressStage(Enum):
    """Available stages in video conversion pipeline."""

    INIT = "initializing"
    EXTRACT = "extracting"
    PROCESS = "processing"
    DEPTH = "depth_estimation"
    STEREO = "stereo_generation"
    WRITE = "writing"
    FINALIZE = "finalizing"
    COMPLETE = "complete"


@dataclass
class StageMetrics:
    """Metrics for a single processing stage."""

    name: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    start_time: float | None = None
    end_time: float | None = None

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time for this stage."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def items_per_second(self) -> float:
        """Get processing speed (items per second)."""
        elapsed = self.elapsed_seconds
        if elapsed > 0:
            return self.completed / elapsed
        return 0.0

    @property
    def eta_seconds(self) -> float:
        """Get estimated time remaining."""
        speed = self.items_per_second
        remaining = self.total - self.completed
        if speed > 0:
            return remaining / speed
        return 0.0

    @property
    def progress_percent(self) -> float:
        """Get progress percentage (0-100)."""
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "elapsed_seconds": self.elapsed_seconds,
            "items_per_second": self.items_per_second,
            "eta_seconds": self.eta_seconds,
            "progress_percent": self.progress_percent,
        }


@dataclass
class ProgressConfig:
    """Configuration for progress tracking.

    Attributes:
        enabled: Whether progress tracking is enabled.
        show_speed: Show processing speed (frames/sec).
        show_eta: Show estimated time remaining.
        show_elapsed: Show elapsed time.
        show_percent: Show percentage complete.
        refresh_rate: How often to refresh the display (seconds).
        console: Console to use for output (None = new console).
        transient: Whether progress bars disappear after completion.
        expand: Expand progress bar to fill available width.
        show_overall: Show overall progress across all stages.
    """

    enabled: bool = True
    show_speed: bool = True
    show_eta: bool = True
    show_elapsed: bool = True
    show_percent: bool = True
    refresh_rate: float = DEFAULT_REFRESH_RATE
    console: Console | None = None
    transient: bool = False
    expand: bool = True
    show_overall: bool = True


@dataclass
class ConversionStats:
    """Overall statistics for video conversion."""

    total_frames: int = 0
    frames_extracted: int = 0
    frames_processed: int = 0
    frames_written: int = 0
    frames_failed: int = 0
    total_elapsed_seconds: float = 0.0
    stages: dict[str, StageMetrics] = field(default_factory=dict)

    @property
    def overall_speed(self) -> float:
        """Get overall processing speed (frames per second)."""
        if self.total_elapsed_seconds > 0:
            return self.frames_processed / self.total_elapsed_seconds
        return 0.0

    @property
    def success_rate(self) -> float:
        """Get success rate percentage."""
        if self.total_frames == 0:
            return 0.0
        return ((self.total_frames - self.frames_failed) / self.total_frames) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_frames": self.total_frames,
            "frames_extracted": self.frames_extracted,
            "frames_processed": self.frames_processed,
            "frames_written": self.frames_written,
            "frames_failed": self.frames_failed,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "overall_speed": self.overall_speed,
            "success_rate": self.success_rate,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
        }


class VideoConversionProgress:
    """Real-time progress tracker for video conversion operations.

    This class provides a Rich-based progress display with:
    - Multi-stage progress tracking
    - Speed and ETA metrics
    - Visual progress bars
    - Thread-safe updates
    - Summary statistics

    Example:
        ```python
        progress = VideoConversionProgress(total_frames=1000)

        with progress:
            # Extract frames
            progress.start_stage(ProgressStage.EXTRACT, total=1000)
            for frame in frames:
                progress.update(1)
            progress.complete_stage()
        ```
    """

    # Stage display names and descriptions
    STAGE_INFO: dict[ProgressStage, tuple[str, str]] = {
        ProgressStage.INIT: ("Initialize", "Setting up conversion"),
        ProgressStage.EXTRACT: ("Extract", "Reading frames from video"),
        ProgressStage.PROCESS: ("Process", "Processing frames"),
        ProgressStage.DEPTH: ("Depth", "Estimating depth maps"),
        ProgressStage.STEREO: ("Stereo", "Generating stereoscopic views"),
        ProgressStage.WRITE: ("Write", "Writing output video"),
        ProgressStage.FINALIZE: ("Finalize", "Finalizing output"),
        ProgressStage.COMPLETE: ("Complete", "Conversion finished"),
    }

    def __init__(
        self,
        total_frames: int = 0,
        config: ProgressConfig | None = None,
        *,
        input_file: str = "",
        output_file: str = "",
        console: Console | None = None,
    ) -> None:
        """Initialize the progress tracker.

        Args:
            total_frames: Total number of frames to process.
            config: Progress configuration. If None, uses defaults.
            input_file: Input file path (for display).
            output_file: Output file path (for display).
            console: Rich console to use. If None, creates new one.
        """
        self.total_frames = total_frames
        self.config = config or ProgressConfig()
        self.input_file = input_file
        self.output_file = output_file

        # Initialize console
        self._console = console or self.config.console or Console()

        # Progress state
        self._current_stage: ProgressStage = ProgressStage.INIT
        self._stage_metrics: dict[ProgressStage, StageMetrics] = {}
        self._stats = ConversionStats(total_frames=total_frames)

        # Rich progress components
        self._progress: Progress | None = None
        self._current_task: TaskID | None = None
        self._overall_task: TaskID | None = None

        # Thread safety
        self._lock = threading.Lock()
        self._is_active = False
        self._start_time: float | None = None

    def _create_progress(self) -> Progress:
        """Create the Rich progress bar with configured columns."""
        columns = [
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="left"),
            BarColumn(bar_width=None if self.config.expand else DEFAULT_BAR_WIDTH),
        ]

        if self.config.show_percent:
            columns.append(TextColumn("[progress.percentage]{task.percentage:>3.0f}%"))

        columns.append(TextColumn("•", style="dim"))

        if self.config.show_speed:
            columns.append(TextColumn("[cyan]{task.fields[speed]:.1f} fps", justify="right"))

        if self.config.show_eta:
            columns.append(TextColumn("•", style="dim"))
            columns.append(TimeRemainingColumn())

        if self.config.show_elapsed:
            columns.append(TextColumn("•", style="dim"))
            columns.append(TimeElapsedColumn())

        return Progress(
            *columns,
            console=self._console,
            refresh_per_second=1.0 / self.config.refresh_rate,
            transient=self.config.transient,
            expand=self.config.expand,
        )

    def start(self) -> None:
        """Start the progress display."""
        if not self.config.enabled:
            return

        with self._lock:
            if self._is_active:
                return

            self._progress = self._create_progress()
            self._progress.start()
            self._is_active = True
            self._start_time = time.time()

            # Create overall task if enabled
            if self.config.show_overall and self.total_frames > 0:
                self._overall_task = self._progress.add_task(
                    "[bold]Overall Progress",
                    total=self.total_frames,
                    speed=0.0,
                )

    def stop(self) -> None:
        """Stop the progress display."""
        if not self.config.enabled:
            return

        with self._lock:
            if not self._is_active or self._progress is None:
                return

            self._progress.stop()
            self._is_active = False

            if self._start_time is not None:
                self._stats.total_elapsed_seconds = time.time() - self._start_time

    def start_stage(
        self,
        stage: ProgressStage,
        total: int = 0,
        description: str | None = None,
    ) -> None:
        """Start a new processing stage.

        Args:
            stage: The stage to start.
            total: Total items in this stage.
            description: Custom description (uses default if None).
        """
        if not self.config.enabled:
            return

        with self._lock:
            self._current_stage = stage

            # Get stage display info
            name, default_desc = self.STAGE_INFO.get(stage, ("Unknown", "Processing"))
            desc = description or f"{name}: {default_desc}"

            # Create metrics for this stage
            self._stage_metrics[stage] = StageMetrics(
                name=name,
                total=total,
                start_time=time.time(),
            )

            # Ensure progress is running
            if self._progress is None or not self._is_active:
                self.start()

            # Complete previous task if any
            if self._current_task is not None and self._progress is not None:
                self._progress.update(self._current_task, completed=total)

            # Create new task for this stage
            if self._progress is not None:
                self._current_task = self._progress.add_task(
                    desc,
                    total=total if total > 0 else self.total_frames,
                    speed=0.0,
                )

    def update(
        self,
        advance: int = 1,
        failed: int = 0,
        description: str | None = None,
    ) -> None:
        """Update progress for the current stage.

        Args:
            advance: Number of items completed.
            failed: Number of failed items.
            description: Optional new description.
        """
        if not self.config.enabled:
            return

        with self._lock:
            if self._progress is None or self._current_task is None:
                return

            # Update stage metrics
            if self._current_stage in self._stage_metrics:
                metrics = self._stage_metrics[self._current_stage]
                metrics.completed += advance
                metrics.failed += failed

                # Calculate speed
                speed = metrics.items_per_second

                # Update progress bar
                self._progress.update(
                    self._current_task,
                    advance=advance,
                    speed=speed,
                    description=description,
                )

                # Update overall progress
                if self._overall_task is not None:
                    self._progress.update(
                        self._overall_task,
                        advance=advance,
                        speed=self._get_overall_speed(),
                    )

            # Update stats
            self._stats.frames_failed += failed

    def complete_stage(self, message: str | None = None) -> None:
        """Complete the current stage.

        Args:
            message: Optional completion message.
        """
        if not self.config.enabled:
            return

        with self._lock:
            if self._current_stage in self._stage_metrics:
                metrics = self._stage_metrics[self._current_stage]
                metrics.end_time = time.time()

                # Mark as complete in progress
                if self._progress is not None and self._current_task is not None:
                    self._progress.update(
                        self._current_task,
                        completed=metrics.total,
                        description=message or f"[green]✓ {metrics.name} complete",
                    )

            # Update stats based on stage
            if self._current_stage == ProgressStage.EXTRACT:
                if self._current_stage in self._stage_metrics:
                    self._stats.frames_extracted = self._stage_metrics[
                        self._current_stage
                    ].completed
            elif self._current_stage == ProgressStage.PROCESS:
                if self._current_stage in self._stage_metrics:
                    self._stats.frames_processed = self._stage_metrics[
                        self._current_stage
                    ].completed
            elif self._current_stage == ProgressStage.WRITE:
                if self._current_stage in self._stage_metrics:
                    self._stats.frames_written = self._stage_metrics[self._current_stage].completed

    def _get_overall_speed(self) -> float:
        """Calculate overall processing speed."""
        if self._start_time is None:
            return 0.0
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            total_completed = sum(m.completed for m in self._stage_metrics.values())
            # Divide by number of stages to get frames/sec
            num_stages = len(self._stage_metrics) or 1
            return (total_completed / num_stages) / elapsed
        return 0.0

    def get_stats(self) -> ConversionStats:
        """Get current conversion statistics."""
        with self._lock:
            self._stats.stages = {
                stage.value: metrics for stage, metrics in self._stage_metrics.items()
            }
            return self._stats

    def print_summary(self) -> None:
        """Print a summary table of the conversion."""
        stats = self.get_stats()

        table = Table(
            title="[bold]Conversion Summary[/bold]",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Frames", str(stats.total_frames))
        table.add_row("Extracted", str(stats.frames_extracted))
        table.add_row("Processed", str(stats.frames_processed))
        table.add_row("Written", str(stats.frames_written))

        if stats.frames_failed > 0:
            table.add_row("Failed", f"[red]{stats.frames_failed}[/red]")

        table.add_row("Success Rate", f"{stats.success_rate:.1f}%")
        table.add_row("Total Time", f"{stats.total_elapsed_seconds:.1f}s")

        if stats.overall_speed > 0:
            table.add_row("Avg Speed", f"{stats.overall_speed:.1f} fps")

        self._console.print(table)

    def create_callback(self) -> Callable[[int, int], None]:
        """Create a callback function for use with batch processor.

        Returns:
            A callback function that updates progress.
        """

        def callback(completed: int, total: int) -> None:
            # Calculate delta since we track cumulative progress
            self.update(1)

        return callback

    @contextmanager
    def track(
        self,
        iterable: Any,
        stage: ProgressStage,
        total: int | None = None,
        description: str | None = None,
    ) -> Generator[Any, None, None]:
        """Context manager to track iteration over items.

        Args:
            iterable: Items to iterate over.
            stage: Processing stage.
            total: Total items (auto-detected if None).
            description: Stage description.

        Yields:
            Items from the iterable.
        """
        # Try to get total
        if total is None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = 0

        self.start_stage(stage, total=total, description=description)

        try:
            for item in iterable:
                yield item
                self.update(1)
        finally:
            self.complete_stage()

    def __enter__(self) -> VideoConversionProgress:
        """Enter context manager."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.stop()
        if exc_type is None:
            self.print_summary()


class SimpleProgressTracker:
    """Simple progress tracker for basic use cases.

    This provides a lightweight alternative to VideoConversionProgress
    for simple single-stage operations.

    Example:
        ```python
        with SimpleProgressTracker(total=1000, description="Processing") as tracker:
            for frame in frames:
                process(frame)
                tracker.update(1)
        ```
    """

    def __init__(
        self,
        total: int = 0,
        description: str = "Processing",
        console: Console | None = None,
    ) -> None:
        """Initialize the simple tracker.

        Args:
            total: Total items to process.
            description: Description for the progress bar.
            console: Console to use for output.
        """
        self.total = total
        self.description = description
        self._console = console or Console()
        self._progress: Progress | None = None
        self._task: TaskID | None = None
        self._completed = 0
        self._start_time: float | None = None

    def start(self) -> None:
        """Start the progress bar."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{self.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self._console,
        )
        self._progress.start()
        self._task = self._progress.add_task(self.description, total=self.total)
        self._start_time = time.time()

    def update(self, advance: int = 1) -> None:
        """Update progress."""
        if self._progress is not None and self._task is not None:
            self._completed += advance
            self._progress.update(self._task, advance=advance)

    def stop(self) -> None:
        """Stop the progress bar."""
        if self._progress is not None:
            self._progress.stop()

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    @property
    def items_per_second(self) -> float:
        """Get processing speed."""
        elapsed = self.elapsed_seconds
        if elapsed > 0:
            return self._completed / elapsed
        return 0.0

    def __enter__(self) -> SimpleProgressTracker:
        """Enter context manager."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager."""
        self.stop()


# Convenience function for quick progress tracking
def track_progress(
    iterable: Any,
    description: str = "Processing",
    total: int | None = None,
) -> Generator[Any, None, None]:
    """Track progress over an iterable.

    Args:
        iterable: Items to iterate over.
        description: Progress description.
        total: Total items (auto-detected if None).

    Yields:
        Items from the iterable.

    Example:
        ```python
        for frame in track_progress(frames, "Processing frames"):
            process(frame)
        ```
    """
    with SimpleProgressTracker(total=total or len(iterable), description=description) as tracker:
        for item in iterable:
            yield item
            tracker.update(1)


__all__ = [
    "ProgressStage",
    "StageMetrics",
    "ProgressConfig",
    "ConversionStats",
    "VideoConversionProgress",
    "SimpleProgressTracker",
    "track_progress",
]
