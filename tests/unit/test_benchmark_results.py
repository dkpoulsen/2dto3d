"""Unit tests for the benchmark results module."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from video2d3d.benchmark.results import (
    BenchmarkResult,
    BenchmarkResults,
    GPUMetrics,
    MemoryMetrics,
    TimingMetrics,
)


class TestTimingMetrics:
    """Tests for TimingMetrics dataclass."""

    def test_default_values(self):
        """Test default timing values."""
        timing = TimingMetrics(total_time_ms=100.0, inference_time_ms=80.0)

        assert timing.total_time_ms == 100.0
        assert timing.inference_time_ms == 80.0
        assert timing.mean_ms == 0.0
        assert timing.std_ms == 0.0

    def test_fps_calculation_from_mean(self):
        """Test FPS calculation from mean time."""
        timing = TimingMetrics(
            total_time_ms=100.0,
            inference_time_ms=80.0,
            mean_ms=50.0,  # 50ms per frame = 20 FPS
        )

        assert timing.fps == pytest.approx(20.0, rel=0.01)

    def test_fps_calculation_from_total(self):
        """Test FPS calculation from total time when mean is 0."""
        timing = TimingMetrics(
            total_time_ms=100.0,
            inference_time_ms=100.0,
            mean_ms=0.0,
        )

        assert timing.fps == pytest.approx(10.0, rel=0.01)

    def test_fps_zero_when_no_time(self):
        """Test FPS is 0 when both times are 0."""
        timing = TimingMetrics(total_time_ms=0.0, inference_time_ms=0.0)

        assert timing.fps == 0.0


class TestMemoryMetrics:
    """Tests for MemoryMetrics dataclass."""

    def test_default_values(self):
        """Test default memory values."""
        memory = MemoryMetrics()

        assert memory.peak_memory_mb == 0.0
        assert memory.avg_memory_mb == 0.0
        assert memory.gpu_peak_memory_mb == 0.0

    def test_custom_values(self):
        """Test custom memory values."""
        memory = MemoryMetrics(
            peak_memory_mb=1000.0,
            avg_memory_mb=800.0,
            gpu_peak_memory_mb=2000.0,
        )

        assert memory.peak_memory_mb == 1000.0
        assert memory.gpu_peak_memory_mb == 2000.0


class TestGPUMetrics:
    """Tests for GPUMetrics dataclass."""

    def test_default_values(self):
        """Test default GPU values."""
        gpu = GPUMetrics()

        assert gpu.device_name == ""
        assert gpu.device_id == 0
        assert gpu.compute_capability == (0, 0)

    def test_custom_values(self):
        """Test custom GPU values."""
        gpu = GPUMetrics(
            device_name="NVIDIA RTX 3080",
            device_id=0,
            compute_capability=(8, 6),
            total_memory_mb=10240.0,
        )

        assert gpu.device_name == "NVIDIA RTX 3080"
        assert gpu.compute_capability == (8, 6)
        assert gpu.total_memory_mb == 10240.0


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    @pytest.fixture
    def sample_result(self) -> BenchmarkResult:
        """Create a sample benchmark result."""
        return BenchmarkResult(
            name="midas_small_640x480_cuda_bs1",
            model="midas_small",
            resolution=(640, 480),
            device="cuda",
            batch_size=1,
            timing=TimingMetrics(
                total_time_ms=100.0,
                inference_time_ms=80.0,
                mean_ms=50.0,
            ),
            memory=MemoryMetrics(peak_memory_mb=500.0),
        )

    def test_basic_properties(self, sample_result):
        """Test basic result properties."""
        assert sample_result.width == 640
        assert sample_result.height == 480
        assert sample_result.pixels == 307200
        assert sample_result.resolution_label == "640x480"

    def test_to_dict(self, sample_result):
        """Test conversion to dictionary."""
        result_dict = sample_result.to_dict()

        assert result_dict["name"] == "midas_small_640x480_cuda_bs1"
        assert result_dict["model"] == "midas_small"
        assert result_dict["resolution"] == "640x480"
        assert "timestamp" in result_dict
        assert "timing" in result_dict
        assert "memory" in result_dict

    def test_from_dict(self, sample_result):
        """Test creation from dictionary."""
        result_dict = sample_result.to_dict()
        restored = BenchmarkResult.from_dict(result_dict)

        assert restored.name == sample_result.name
        assert restored.model == sample_result.model
        assert restored.resolution == sample_result.resolution
        assert restored.timing.mean_ms == sample_result.timing.mean_ms

    def test_from_dict_with_resolution_string(self):
        """Test from_dict handles resolution as string."""
        data = {
            "name": "test",
            "model": "midas_small",
            "resolution": "1280x720",
            "device": "cuda",
            "timestamp": datetime.now().isoformat(),
        }

        result = BenchmarkResult.from_dict(data)
        assert result.resolution == (1280, 720)

    def test_from_dict_with_nested_dataclasses(self):
        """Test from_dict properly reconstructs nested dataclasses."""
        data = {
            "name": "test",
            "model": "midas_small",
            "resolution": (640, 480),
            "device": "cuda",
            "timestamp": datetime.now().isoformat(),
            "timing": {
                "total_time_ms": 100.0,
                "inference_time_ms": 80.0,
                "mean_ms": 50.0,
                "extra_field": "ignored",  # Should be ignored
            },
            "memory": {
                "peak_memory_mb": 500.0,
            },
            "gpu": {
                "device_name": "RTX 3080",
            },
        }

        result = BenchmarkResult.from_dict(data)
        assert result.timing.mean_ms == 50.0
        assert result.memory.peak_memory_mb == 500.0
        assert result.gpu.device_name == "RTX 3080"


class TestBenchmarkResults:
    """Tests for BenchmarkResults collection class."""

    @pytest.fixture
    def sample_results(self) -> BenchmarkResults:
        """Create sample benchmark results collection."""
        results = BenchmarkResults(config_name="test_config")

        results.add_result(
            BenchmarkResult(
                name="model_a_640x480_cuda",
                model="model_a",
                resolution=(640, 480),
                device="cuda",
                timing=TimingMetrics(
                    total_time_ms=100.0,
                    inference_time_ms=80.0,
                    mean_ms=50.0,
                ),
            )
        )

        results.add_result(
            BenchmarkResult(
                name="model_b_640x480_cuda",
                model="model_b",
                resolution=(640, 480),
                device="cuda",
                timing=TimingMetrics(
                    total_time_ms=200.0,
                    inference_time_ms=160.0,
                    mean_ms=100.0,
                ),
            )
        )

        results.add_result(
            BenchmarkResult(
                name="model_a_1280x720_cuda",
                model="model_a",
                resolution=(1280, 720),
                device="cuda",
                success=False,
                error_message="OOM",
            )
        )

        return results

    def test_add_and_count_results(self, sample_results):
        """Test adding results and counting."""
        assert len(sample_results) == 3

    def test_successful_and_failed_results(self, sample_results):
        """Test filtering by success status."""
        successful = sample_results.successful_results
        failed = sample_results.failed_results

        assert len(successful) == 2
        assert len(failed) == 1
        assert failed[0].error_message == "OOM"

    def test_get_by_model(self, sample_results):
        """Test filtering by model."""
        model_a = sample_results.get_by_model("model_a")
        model_b = sample_results.get_by_model("model_b")

        assert len(model_a) == 2
        assert len(model_b) == 1

    def test_get_by_device(self, sample_results):
        """Test filtering by device."""
        cuda_results = sample_results.get_by_device("cuda")

        assert len(cuda_results) == 3

    def test_get_by_resolution(self, sample_results):
        """Test filtering by resolution."""
        res_640 = sample_results.get_by_resolution((640, 480))
        res_1280 = sample_results.get_by_resolution((1280, 720))

        assert len(res_640) == 2
        assert len(res_1280) == 1

    def test_get_best_by_fps(self, sample_results):
        """Test finding best result by FPS."""
        best = sample_results.get_best_by_fps()

        assert best is not None
        assert best.model == "model_a"  # 20 FPS vs 10 FPS
        assert best.timing.fps == pytest.approx(20.0, rel=0.01)

    def test_get_best_by_fps_empty_results(self):
        """Test get_best_by_fps with no successful results."""
        results = BenchmarkResults()
        results.add_result(
            BenchmarkResult(
                name="failed",
                model="model",
                resolution=(640, 480),
                device="cuda",
                success=False,
            )
        )

        assert results.get_best_by_fps() is None

    def test_get_summary_stats(self, sample_results):
        """Test summary statistics."""
        stats = sample_results.get_summary_stats()

        assert stats["total_benchmarks"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert "model_a" in stats["models_tested"]
        assert "model_b" in stats["models_tested"]
        assert "640x480" in stats["resolutions_tested"]

    def test_compare_models(self, sample_results):
        """Test model comparison."""
        comparison = sample_results.compare_models()

        assert "model_a" in comparison
        assert "model_b" in comparison
        # model_a has one successful result at 20 FPS
        assert comparison["model_a"]["avg_fps"] == pytest.approx(20.0, rel=0.01)
        # model_b has one successful result at 10 FPS
        assert comparison["model_b"]["avg_fps"] == pytest.approx(10.0, rel=0.01)

    def test_save_and_load(self, sample_results):
        """Test saving and loading results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.json"

            sample_results.save(path)
            assert path.exists()

            loaded = BenchmarkResults.load(path)

            assert loaded.config_name == sample_results.config_name
            assert len(loaded) == len(sample_results)
            assert loaded.results[0].name == sample_results.results[0].name

    def test_load_missing_file(self):
        """Test loading from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            BenchmarkResults.load(Path("/nonexistent/path.json"))

    def test_iteration(self, sample_results):
        """Test iterating over results."""
        names = [r.name for r in sample_results]
        assert len(names) == 3
        assert "model_a_640x480_cuda" in names

    def test_indexing(self, sample_results):
        """Test indexing results."""
        assert sample_results[0].name == "model_a_640x480_cuda"
        assert sample_results[1].name == "model_b_640x480_cuda"
