"""Benchmark runner for measuring performance across models and configurations.

This module provides the main BenchmarkRunner class for executing benchmarks
and collecting performance metrics.
"""

from __future__ import annotations

import gc
import platform
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from video2d3d.benchmark.config import BenchmarkConfig, BenchmarkCategory
from video2d3d.benchmark.results import (
    BenchmarkResult,
    BenchmarkResults,
    GPUMetrics,
    MemoryMetrics,
    TimingMetrics,
)
from video2d3d.utils.logger import get_logger
from video2d3d.utils.gpu import (
    is_cuda_available,
    get_gpu_info,
    get_all_gpu_info,
    get_memory_usage,
    clear_gpu_memory,
)

if TYPE_CHECKING:
    pass


def _get_benchmark_logger():
    """Get the benchmark logger (lazy initialization)."""
    return get_logger("benchmark")


class BenchmarkRunner:
    """Runner for executing performance benchmarks.

    This class handles the execution of benchmarks across different models,
    resolutions, and hardware configurations.

    Example usage:
        ```python
        from video2d3d.benchmark import BenchmarkRunner, BenchmarkConfig

        # Create runner with configuration
        config = BenchmarkConfig(models=["midas_small"])
        runner = BenchmarkRunner(config)

        # Run benchmarks
        results = runner.run()

        # Access results
        print(results.get_summary_stats())
        ```
    """

    def __init__(
        self,
        config: Optional[BenchmarkConfig] = None,
    ) -> None:
        """Initialize the benchmark runner.

        Args:
            config: Benchmark configuration. Uses defaults if None.
        """
        self.config = config or BenchmarkConfig()
        self._logger = _get_benchmark_logger()
        self._results = BenchmarkResults(config_name="benchmark")
        self._estimator_cache: dict[str, Any] = {}
        self._seed_initialized = False
        self._progress_callback: Optional[callable] = None

    def set_progress_callback(self, callback: Optional[callable]) -> None:
        """Set a callback function for progress updates.

        Args:
            callback: Function that takes (current, total, message) arguments.
                      Set to None to disable progress reporting.
        """
        self._progress_callback = callback

    def _get_system_info(self) -> dict[str, Any]:
        """Collect system information for the benchmark report."""
        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": platform.python_version(),
            "cpu_count": self._get_cpu_count(),
            "cpu_name": self._get_cpu_name(),
            "ram_total_gb": self._get_total_ram_gb(),
            "torch_version": self._get_torch_version(),
            "cuda_available": is_cuda_available(),
            "cuda_version": self._get_cuda_version(),
            "gpus": [],
        }

        # Add GPU information
        if is_cuda_available():
            gpu_infos = get_all_gpu_info()
            info["gpus"] = [
                {
                    "name": gpu.name,
                    "device_id": gpu.device_id,
                    "total_memory_mb": gpu.total_memory_mb,
                    "compute_capability": f"{gpu.compute_capability[0]}.{gpu.compute_capability[1]}",
                }
                for gpu in gpu_infos
            ]

        return info

    def _get_cpu_count(self) -> int:
        """Get CPU core count."""
        try:
            import os

            return os.cpu_count() or 1
        except Exception:
            return 1

    def _get_cpu_name(self) -> str:
        """Get CPU name."""
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            elif platform.system() == "Darwin":
                import subprocess

                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip()
        except Exception:
            pass
        return "Unknown CPU"

    def _get_total_ram_gb(self) -> float:
        """Get total RAM in GB."""
        try:
            import psutil

            return psutil.virtual_memory().total / (1024**3)
        except Exception:
            return 0.0

    def _get_torch_version(self) -> str:
        """Get PyTorch version."""
        try:
            import torch

            return torch.__version__
        except Exception:
            return "N/A"

    def _get_cuda_version(self) -> str:
        """Get CUDA version."""
        try:
            if is_cuda_available():
                import torch

                return torch.version.cuda or "N/A"
        except Exception:
            pass
        return "N/A"

    def _initialize_seed(self) -> None:
        """Initialize random seed for reproducible benchmarks."""
        if not self._seed_initialized:
            np.random.seed(self.config.seed)
            self._seed_initialized = True

    def _generate_test_image(self, width: int, height: int) -> np.ndarray:
        """Generate a test image for benchmarking.

        Args:
            width: Image width.
            height: Image height.

        Returns:
            Test image as numpy array.
        """
        self._initialize_seed()
        # Generate RGB image - each call generates different data but reproducibly
        image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return image

    def _get_or_create_estimator(self, model: str, device: str) -> Any:
        """Get or create a depth estimator for the given model.

        Args:
            model: Model name.
            device: Device to use.

        Returns:
            Depth estimator instance.
        """
        cache_key = f"{model}_{device}"
        if cache_key in self._estimator_cache:
            return self._estimator_cache[cache_key]

        try:
            from video2d3d.depth.model_selector import (
                DepthModelSelector,
                DepthModelConfig,
                DepthModelType,
            )

            # Convert model name to DepthModelType
            model_type = DepthModelType.from_string(model)

            config = DepthModelConfig(
                primary_model=model_type,
                device=device,
            )
            estimator = DepthModelSelector(config=config)

            # Warm up the model with a small image
            warmup_image = self._generate_test_image(64, 64)
            estimator.estimate_depth(warmup_image)

            self._estimator_cache[cache_key] = estimator
            return estimator

        except Exception as e:
            self._logger.error(f"Failed to create estimator for {model}: {e}")
            raise

    def _measure_memory(self) -> tuple[float, float]:
        """Measure current memory usage.

        Returns:
            Tuple of (process_memory_mb, gpu_memory_mb).
        """
        process_mb = 0.0
        gpu_mb = 0.0

        try:
            import psutil

            process = psutil.Process()
            process_mb = process.memory_info().rss / (1024**2)
        except Exception:
            pass

        if is_cuda_available():
            try:
                used, _, _ = get_memory_usage()
                gpu_mb = used
            except Exception:
                pass

        return process_mb, gpu_mb

    def _run_single_benchmark(
        self,
        model: str,
        resolution: tuple[int, int],
        device: str,
        batch_size: int = 1,
    ) -> BenchmarkResult:
        """Run a single benchmark configuration.

        Args:
            model: Model name to benchmark.
            resolution: Image resolution (width, height).
            device: Device to use.
            batch_size: Batch size for processing.

        Returns:
            BenchmarkResult with timing and memory metrics.
        """
        width, height = resolution
        name = f"{model}_{width}x{height}_{device}_bs{batch_size}"

        self._logger.info(
            f"Running benchmark: {name} "
            f"(warmup={self.config.warmup_iterations}, "
            f"iter={self.config.test_iterations})"
        )

        result = BenchmarkResult(
            name=name,
            model=model,
            resolution=resolution,
            device=device,
            batch_size=batch_size,
            timestamp=datetime.now(),
        )

        try:
            # Generate test images
            test_images = [self._generate_test_image(width, height) for _ in range(batch_size)]

            # Measure memory before
            mem_before_process, mem_before_gpu = self._measure_memory()

            # Create estimator
            estimator = self._get_or_create_estimator(model, device)

            # Warmup iterations
            warmup_times = []
            for _ in range(self.config.warmup_iterations):
                start = time.perf_counter()
                for img in test_images:
                    estimator.estimate_depth(img)
                elapsed = (time.perf_counter() - start) * 1000
                warmup_times.append(elapsed)

            # Clear GPU memory between warmup and test
            if device.startswith("cuda"):
                clear_gpu_memory()

            # Test iterations
            iteration_times = []
            inference_times = []
            memory_samples_process = []
            memory_samples_gpu = []

            for _ in range(self.config.test_iterations):
                # Measure memory
                proc_mem, gpu_mem = self._measure_memory()
                memory_samples_process.append(proc_mem)
                memory_samples_gpu.append(gpu_mem)

                # Run inference
                start_total = time.perf_counter()
                start_inference = time.perf_counter()

                for img in test_images:
                    estimator.estimate_depth(img)

                inference_time = (time.perf_counter() - start_inference) * 1000
                total_time = (time.perf_counter() - start_total) * 1000

                iteration_times.append(total_time)
                inference_times.append(inference_time)

            # Measure memory after
            mem_after_process, mem_after_gpu = self._measure_memory()

            # Calculate statistics
            if iteration_times:
                result.timing = TimingMetrics(
                    total_time_ms=sum(iteration_times),
                    inference_time_ms=statistics.mean(inference_times),
                    mean_ms=statistics.mean(iteration_times),
                    std_ms=statistics.stdev(iteration_times) if len(iteration_times) > 1 else 0,
                    min_ms=min(iteration_times),
                    max_ms=max(iteration_times),
                    median_ms=statistics.median(iteration_times),
                    p95_ms=self._percentile(iteration_times, 95),
                    p99_ms=self._percentile(iteration_times, 99),
                )

            if memory_samples_process:
                result.memory = MemoryMetrics(
                    peak_memory_mb=max(memory_samples_process),
                    avg_memory_mb=statistics.mean(memory_samples_process),
                    memory_before_mb=mem_before_process,
                    memory_after_mb=mem_after_process,
                    gpu_peak_memory_mb=max(memory_samples_gpu) if memory_samples_gpu else 0,
                    gpu_avg_memory_mb=statistics.mean(memory_samples_gpu)
                    if memory_samples_gpu
                    else 0,
                )

            # Add GPU metrics if available
            if device.startswith("cuda") and is_cuda_available():
                gpu_info = get_gpu_info()
                if gpu_info:
                    result.gpu = GPUMetrics(
                        device_name=gpu_info.name,
                        device_id=gpu_info.device_id,
                        compute_capability=gpu_info.compute_capability,
                        total_memory_mb=gpu_info.total_memory_mb,
                    )

            result.success = True
            self._logger.info(
                f"Benchmark {name} completed: "
                f"{result.timing.fps:.2f} FPS, "
                f"{result.timing.mean_ms:.2f}ms avg"
            )

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            self._logger.error(f"Benchmark {name} failed: {e}")

        finally:
            # Cleanup
            gc.collect()
            if device.startswith("cuda"):
                clear_gpu_memory()

        return result

    def _percentile(self, data: list[float], percentile: int) -> float:
        """Calculate percentile of a list.

        Args:
            data: List of values.
            percentile: Percentile to calculate (0-100).

        Returns:
            Percentile value.
        """
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (len(sorted_data) - 1) * percentile / 100
        lower = int(index)
        upper = lower + 1
        if upper >= len(sorted_data):
            return sorted_data[-1]
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

    def _report_progress(self, current: int, total: int, message: str) -> None:
        """Report progress via callback if set."""
        if self._progress_callback:
            try:
                self._progress_callback(current, total, message)
            except Exception:
                pass  # Don't let progress callback errors break benchmarks

    def _run_model_comparison(self) -> list[BenchmarkResult]:
        """Run model comparison benchmarks."""
        results = []
        default_resolution = self.config.all_resolutions[0]
        device = self.config.devices[0]

        for model in self.config.models:
            result = self._run_single_benchmark(
                model=model,
                resolution=default_resolution,
                device=device,
                batch_size=1,
            )
            results.append(result)

        return results

    def _run_resolution_scaling(self) -> list[BenchmarkResult]:
        """Run resolution scaling benchmarks."""
        results = []
        default_model = self.config.models[0]
        device = self.config.devices[0]

        for resolution in self.config.all_resolutions:
            result = self._run_single_benchmark(
                model=default_model,
                resolution=resolution,
                device=device,
                batch_size=1,
            )
            results.append(result)

        return results

    def _run_hardware_comparison(self) -> list[BenchmarkResult]:
        """Run hardware comparison benchmarks (CPU vs GPU)."""
        results = []
        default_model = self.config.models[0]
        default_resolution = self.config.all_resolutions[0]

        for device in self.config.devices:
            # Skip CUDA if not available
            if device in ("cuda", "auto") and not is_cuda_available():
                self._logger.warning(f"Skipping device '{device}' - CUDA not available")
                continue

            result = self._run_single_benchmark(
                model=default_model,
                resolution=default_resolution,
                device=device if device != "auto" else "cuda",
                batch_size=1,
            )
            results.append(result)

        return results

    def _run_batch_processing(self) -> list[BenchmarkResult]:
        """Run batch processing benchmarks."""
        results = []
        default_model = self.config.models[0]
        default_resolution = self.config.all_resolutions[0]
        device = self.config.devices[0]

        for batch_size in self.config.batch_sizes:
            result = self._run_single_benchmark(
                model=default_model,
                resolution=default_resolution,
                device=device if device != "auto" else "cuda",
                batch_size=batch_size,
            )
            results.append(result)

        return results

    def _run_full_pipeline(self) -> list[BenchmarkResult]:
        """Run full pipeline benchmarks (depth + stereo generation)."""
        results = []

        for model in self.config.models:
            for resolution in self.config.all_resolutions[:2]:  # Limit resolutions
                for device in self.config.devices:
                    result = self._run_single_benchmark(
                        model=model,
                        resolution=resolution,
                        device=device if device != "auto" else "cuda",
                        batch_size=1,
                    )
                    result.name = f"full_{result.name}"
                    results.append(result)

        return results

    def run(
        self,
        categories: Optional[list[BenchmarkCategory]] = None,
    ) -> BenchmarkResults:
        """Run all configured benchmarks.

        Args:
            categories: Specific categories to run. If None, uses config.

        Returns:
            BenchmarkResults containing all benchmark data.
        """
        self._logger.info("Starting benchmark suite")

        # Initialize results
        self._results = BenchmarkResults(
            config_name=f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now(),
            system_info=self._get_system_info(),
        )

        categories = categories or self.config.categories

        try:
            # Run each category
            if BenchmarkCategory.MODEL_COMPARISON in categories:
                self._logger.info("Running model comparison benchmarks")
                for result in self._run_model_comparison():
                    self._results.add_result(result)

            if BenchmarkCategory.RESOLUTION_SCALING in categories:
                self._logger.info("Running resolution scaling benchmarks")
                for result in self._run_resolution_scaling():
                    self._results.add_result(result)

            if BenchmarkCategory.HARDWARE_COMPARISON in categories:
                self._logger.info("Running hardware comparison benchmarks")
                for result in self._run_hardware_comparison():
                    self._results.add_result(result)

            if BenchmarkCategory.BATCH_PROCESSING in categories:
                self._logger.info("Running batch processing benchmarks")
                for result in self._run_batch_processing():
                    self._results.add_result(result)

            if BenchmarkCategory.FULL_PIPELINE in categories:
                self._logger.info("Running full pipeline benchmarks")
                for result in self._run_full_pipeline():
                    self._results.add_result(result)

        finally:
            self._results.end_time = datetime.now()

            # Cleanup estimators
            for estimator in self._estimator_cache.values():
                try:
                    if hasattr(estimator, "close"):
                        estimator.close()
                except Exception:
                    pass
            self._estimator_cache.clear()

            # Save results if configured
            if self.config.save_intermediate:
                self._save_results()

        self._logger.info(
            f"Benchmark suite completed: "
            f"{len(self._results.successful_results)}/{len(self._results)} successful"
        )

        return self._results

    def _save_results(self) -> None:
        """Save benchmark results to file."""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"benchmark_{timestamp}.json"

        self._results.save(output_path)
        self._logger.info(f"Results saved to {output_path}")

    def run_quick(self) -> BenchmarkResults:
        """Run a quick benchmark for fast validation.

        This runs a minimal set of benchmarks.

        Returns:
            BenchmarkResults from quick benchmark.
        """
        from video2d3d.benchmark.config import QuickBenchmarkConfig

        original_config = self.config
        self.config = QuickBenchmarkConfig()

        try:
            return self.run()
        finally:
            self.config = original_config


__all__ = ["BenchmarkRunner"]
