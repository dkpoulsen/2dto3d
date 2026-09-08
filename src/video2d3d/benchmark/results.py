"""Benchmark results data structures.

This module defines data structures for storing and manipulating
benchmark results, including timing, memory, and GPU metrics.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TimingMetrics:
    """Timing-related metrics for a benchmark run."""

    total_time_ms: float
    inference_time_ms: float
    preprocessing_time_ms: float = 0.0
    postprocessing_time_ms: float = 0.0

    # Statistical measures (populated from multiple iterations)
    mean_ms: float = 0.0
    std_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0  # 95th percentile
    p99_ms: float = 0.0  # 99th percentile

    @property
    def fps(self) -> float:
        """Calculate frames per second based on mean time."""
        if self.mean_ms > 0:
            return 1000.0 / self.mean_ms
        if self.total_time_ms > 0:
            return 1000.0 / self.total_time_ms
        return 0.0


@dataclass
class MemoryMetrics:
    """Memory-related metrics for a benchmark run."""

    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    memory_before_mb: float = 0.0
    memory_after_mb: float = 0.0

    # GPU-specific memory (if applicable)
    gpu_peak_memory_mb: float = 0.0
    gpu_avg_memory_mb: float = 0.0
    gpu_memory_allocated_mb: float = 0.0
    gpu_memory_reserved_mb: float = 0.0


@dataclass
class GPUMetrics:
    """GPU-specific metrics for a benchmark run."""

    device_name: str = ""
    device_id: int = 0
    compute_capability: tuple[int, int] = (0, 0)
    total_memory_mb: float = 0.0
    utilization_percent: float = 0.0
    temperature_celsius: float = 0.0
    power_draw_watts: float = 0.0


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run.

    Attributes:
        name: Human-readable name for this benchmark.
        model: Model name used.
        resolution: Image resolution (width, height).
        device: Device used (cuda, cpu, etc.).
        batch_size: Batch size used.
        timing: Timing metrics.
        memory: Memory metrics.
        gpu: GPU metrics (if applicable).
        success: Whether the benchmark completed successfully.
        error_message: Error message if benchmark failed.
        timestamp: When the benchmark was run.
        metadata: Additional metadata about the benchmark.
    """

    name: str
    model: str
    resolution: tuple[int, int]
    device: str
    batch_size: int = 1
    timing: TimingMetrics = field(
        default_factory=lambda: TimingMetrics(total_time_ms=0.0, inference_time_ms=0.0)
    )
    memory: MemoryMetrics = field(default_factory=MemoryMetrics)
    gpu: GPUMetrics = field(default_factory=GPUMetrics)
    success: bool = True
    error_message: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def width(self) -> int:
        """Get image width."""
        return self.resolution[0]

    @property
    def height(self) -> int:
        """Get image height."""
        return self.resolution[1]

    @property
    def pixels(self) -> int:
        """Get total pixels in resolution."""
        return self.width * self.height

    @property
    def resolution_label(self) -> str:
        """Get human-readable resolution label."""
        return f"{self.width}x{self.height}"

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["resolution"] = f"{self.width}x{self.height}"
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BenchmarkResult:
        """Create result from dictionary."""
        # Parse timestamp
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        # Parse resolution
        if isinstance(data.get("resolution"), str):
            width, height = map(int, data["resolution"].split("x"))
            data["resolution"] = (width, height)

        # Parse nested dataclasses (ignoring unknown fields)
        if "timing" in data and isinstance(data["timing"], dict):
            valid = {f.name for f in fields(TimingMetrics)}
            data["timing"] = TimingMetrics(
                **{k: v for k, v in data["timing"].items() if k in valid}
            )
        if "memory" in data and isinstance(data["memory"], dict):
            valid = {f.name for f in fields(MemoryMetrics)}
            data["memory"] = MemoryMetrics(
                **{k: v for k, v in data["memory"].items() if k in valid}
            )
        if "gpu" in data and isinstance(data["gpu"], dict):
            valid = {f.name for f in fields(GPUMetrics)}
            data["gpu"] = GPUMetrics(**{k: v for k, v in data["gpu"].items() if k in valid})

        return cls(**data)


@dataclass
class BenchmarkResults:
    """Collection of benchmark results with analysis capabilities.

    Attributes:
        results: List of individual benchmark results.
        config_name: Name of the benchmark configuration.
        start_time: When the benchmark suite started.
        end_time: When the benchmark suite ended.
        system_info: System information (OS, CPU, GPU, etc.).
    """

    results: list[BenchmarkResult] = field(default_factory=list)
    config_name: str = "default"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    system_info: dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result to the collection."""
        self.results.append(result)

    def __len__(self) -> int:
        """Return number of results."""
        return len(self.results)

    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)

    def __getitem__(self, index: int) -> BenchmarkResult:
        """Get result by index."""
        return self.results[index]

    @property
    def successful_results(self) -> list[BenchmarkResult]:
        """Get only successful results."""
        return [r for r in self.results if r.success]

    @property
    def failed_results(self) -> list[BenchmarkResult]:
        """Get only failed results."""
        return [r for r in self.results if not r.success]

    @property
    def total_duration_seconds(self) -> float:
        """Get total duration of all benchmarks in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def get_by_model(self, model: str) -> list[BenchmarkResult]:
        """Get results for a specific model."""
        return [r for r in self.results if r.model == model]

    def get_by_device(self, device: str) -> list[BenchmarkResult]:
        """Get results for a specific device."""
        return [r for r in self.results if r.device == device]

    def get_by_resolution(self, resolution: tuple[int, int]) -> list[BenchmarkResult]:
        """Get results for a specific resolution."""
        return [r for r in self.results if r.resolution == resolution]

    def get_best_by_fps(self) -> BenchmarkResult | None:
        """Get the result with the best (highest) FPS."""
        successful = self.successful_results
        if not successful:
            return None
        return max(successful, key=lambda r: r.timing.fps)

    def get_summary_stats(self) -> dict[str, Any]:
        """Get summary statistics for all results."""
        successful = self.successful_results
        if not successful:
            return {
                "total_benchmarks": len(self.results),
                "successful": 0,
                "failed": len(self.failed_results),
            }

        fps_values = [r.timing.fps for r in successful]
        inference_times = [r.timing.inference_time_ms for r in successful]

        return {
            "total_benchmarks": len(self.results),
            "successful": len(successful),
            "failed": len(self.failed_results),
            "total_duration_seconds": self.total_duration_seconds,
            "fps": {
                "mean": statistics.mean(fps_values) if fps_values else 0,
                "std": statistics.stdev(fps_values) if len(fps_values) > 1 else 0,
                "min": min(fps_values) if fps_values else 0,
                "max": max(fps_values) if fps_values else 0,
            },
            "inference_time_ms": {
                "mean": statistics.mean(inference_times) if inference_times else 0,
                "std": statistics.stdev(inference_times) if len(inference_times) > 1 else 0,
                "min": min(inference_times) if inference_times else 0,
                "max": max(inference_times) if inference_times else 0,
            },
            "models_tested": list({r.model for r in successful}),
            "resolutions_tested": list({r.resolution_label for r in successful}),
            "devices_tested": list({r.device for r in successful}),
        }

    def compare_models(self) -> dict[str, dict[str, float]]:
        """Compare performance across models.

        Returns:
            Dictionary mapping model names to their average metrics.
        """
        model_stats: dict[str, dict[str, list[float]]] = {}

        for result in self.successful_results:
            if result.model not in model_stats:
                model_stats[result.model] = {
                    "fps": [],
                    "inference_time_ms": [],
                    "peak_memory_mb": [],
                }

            model_stats[result.model]["fps"].append(result.timing.fps)
            model_stats[result.model]["inference_time_ms"].append(result.timing.inference_time_ms)
            model_stats[result.model]["peak_memory_mb"].append(result.memory.peak_memory_mb)

        # Calculate averages
        comparison: dict[str, dict[str, float]] = {}
        for model, metrics in model_stats.items():
            comparison[model] = {
                "avg_fps": statistics.mean(metrics["fps"]) if metrics["fps"] else 0,
                "avg_inference_ms": (
                    statistics.mean(metrics["inference_time_ms"])
                    if metrics["inference_time_ms"]
                    else 0
                ),
                "avg_peak_memory_mb": (
                    statistics.mean(metrics["peak_memory_mb"]) if metrics["peak_memory_mb"] else 0
                ),
            }

        return comparison

    def save(self, path: Path) -> None:
        """Save results to a JSON file."""
        data = {
            "config_name": self.config_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "system_info": self.system_info,
            "results": [r.to_dict() for r in self.results],
        }

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> BenchmarkResults:
        """Load results from a JSON file.

        Args:
            path: Path to the JSON file.

        Returns:
            BenchmarkResults instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            json.JSONDecodeError: If file is not valid JSON.
            KeyError: If required fields are missing.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Benchmark results file not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Safely parse datetime fields
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = None
        if data.get("end_time"):
            end_time = datetime.fromisoformat(data["end_time"])

        results = cls(
            config_name=data.get("config_name", "unknown"),
            start_time=start_time,
            end_time=end_time,
            system_info=data.get("system_info", {}),
            results=[BenchmarkResult.from_dict(r) for r in data.get("results", [])],
        )

        return results


__all__ = [
    "TimingMetrics",
    "MemoryMetrics",
    "GPUMetrics",
    "BenchmarkResult",
    "BenchmarkResults",
]
