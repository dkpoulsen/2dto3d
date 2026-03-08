"""Unit tests for the benchmark reporting module."""

from __future__ import annotations

import csv
import io
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from video2d3d.benchmark.reporting import (
    CSVReporter,
    JSONReporter,
    MarkdownReporter,
    generate_report,
)
from video2d3d.benchmark.results import (
    BenchmarkResult,
    BenchmarkResults,
    GPUMetrics,
    MemoryMetrics,
    TimingMetrics,
)


@pytest.fixture
def sample_results() -> BenchmarkResults:
    """Create sample benchmark results for testing."""
    results = BenchmarkResults(
        config_name="test_benchmark",
        system_info={
            "platform": "Linux",
            "python_version": "3.10.0",
            "cpu_name": "Test CPU",
            "cpu_count": 8,
            "ram_total_gb": 16.0,
            "torch_version": "2.0.0",
            "cuda_available": True,
            "cuda_version": "11.8",
            "gpus": [
                {
                    "name": "Test GPU",
                    "device_id": 0,
                    "total_memory_mb": 8192.0,
                    "compute_capability": "8.6",
                }
            ],
        },
    )

    results.add_result(
        BenchmarkResult(
            name="model_a_640x480_cuda",
            model="model_a",
            resolution=(640, 480),
            device="cuda",
            batch_size=1,
            timing=TimingMetrics(
                total_time_ms=100.0,
                inference_time_ms=80.0,
                mean_ms=50.0,
                std_ms=5.0,
                min_ms=45.0,
                max_ms=60.0,
                median_ms=50.0,
                p95_ms=58.0,
                p99_ms=59.5,
            ),
            memory=MemoryMetrics(peak_memory_mb=500.0, avg_memory_mb=400.0),
            gpu=GPUMetrics(device_name="Test GPU", device_id=0, total_memory_mb=8192.0),
        )
    )

    results.add_result(
        BenchmarkResult(
            name="model_b_640x480_cuda",
            model="model_b",
            resolution=(640, 480),
            device="cuda",
            batch_size=1,
            timing=TimingMetrics(
                total_time_ms=200.0,
                inference_time_ms=160.0,
                mean_ms=100.0,
                std_ms=10.0,
            ),
            memory=MemoryMetrics(peak_memory_mb=600.0),
        )
    )

    results.add_result(
        BenchmarkResult(
            name="model_a_640x480_cuda_failed",
            model="model_a",
            resolution=(640, 480),
            device="cuda",
            success=False,
            error_message="Out of memory",
        )
    )

    results.end_time = datetime.now()
    return results


class TestMarkdownReporter:
    """Tests for MarkdownReporter."""

    def test_generate_full_report(self, sample_results):
        """Test generating a full markdown report."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_results)

        assert "# Benchmark Results" in report
        assert "## System Information" in report
        assert "## Summary" in report
        assert "## Model Comparison" in report
        assert "## Detailed Results" in report
        assert "## Failed Benchmarks" in report

    def test_generate_without_system_info(self, sample_results):
        """Test generating report without system info."""
        reporter = MarkdownReporter(include_system_info=False)
        report = reporter.generate(sample_results)

        assert "## System Information" not in report
        assert "## Summary" in report

    def test_generate_without_details(self, sample_results):
        """Test generating report without detailed results."""
        reporter = MarkdownReporter(include_details=False)
        report = reporter.generate(sample_results)

        assert "## Detailed Results" not in report
        assert "## System Information" in report

    def test_system_info_section(self, sample_results):
        """Test system information section content."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_results)

        assert "Linux" in report
        assert "3.10.0" in report
        assert "Test CPU" in report
        assert "Test GPU" in report
        assert "CUDA Available**: Yes" in report

    def test_summary_section(self, sample_results):
        """Test summary section content."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_results)

        assert "Total Benchmarks" in report
        assert "3" in report  # Total count
        assert "2" in report  # Successful count
        assert "1" in report  # Failed count

    def test_model_comparison_section(self, sample_results):
        """Test model comparison section."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_results)

        assert "model_a" in report
        assert "model_b" in report
        assert "Avg FPS" in report

    def test_failed_benchmarks_section(self, sample_results):
        """Test failed benchmarks section."""
        reporter = MarkdownReporter()
        report = reporter.generate(sample_results)

        assert "Out of memory" in report

    def test_save_to_file(self, sample_results):
        """Test saving report to file."""
        reporter = MarkdownReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.md"
            reporter.save(sample_results, path)

            assert path.exists()
            content = path.read_text()
            assert "# Benchmark Results" in content


class TestJSONReporter:
    """Tests for JSONReporter."""

    def test_generate_pretty_json(self, sample_results):
        """Test generating pretty-printed JSON."""
        reporter = JSONReporter(pretty=True)
        report = reporter.generate(sample_results)

        # Should be valid JSON
        data = json.loads(report)

        assert data["config_name"] == "test_benchmark"
        assert "system_info" in data
        assert "summary" in data
        assert "model_comparison" in data
        assert len(data["results"]) == 3

    def test_generate_compact_json(self, sample_results):
        """Test generating compact JSON."""
        reporter = JSONReporter(pretty=False)
        report = reporter.generate(sample_results)

        # Should be valid JSON but compact
        data = json.loads(report)
        assert data["config_name"] == "test_benchmark"

        # Compact should not have indentation
        assert "\n  " not in report or len(report) < 2000

    def test_json_structure(self, sample_results):
        """Test JSON output structure."""
        reporter = JSONReporter()
        report = reporter.generate(sample_results)
        data = json.loads(report)

        assert "config_name" in data
        assert "start_time" in data
        assert "end_time" in data
        assert "system_info" in data
        assert "summary" in data
        assert "model_comparison" in data
        assert "results" in data

    def test_save_to_file(self, sample_results):
        """Test saving JSON report to file."""
        reporter = JSONReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.json"
            reporter.save(sample_results, path)

            assert path.exists()

            with open(path) as f:
                data = json.load(f)
            assert data["config_name"] == "test_benchmark"


class TestCSVReporter:
    """Tests for CSVReporter."""

    def test_generate_full_csv(self, sample_results):
        """Test generating full CSV report."""
        reporter = CSVReporter()
        report = reporter.generate(sample_results)

        reader = csv.reader(io.StringIO(report))
        rows = list(reader)

        assert len(rows) == 4  # Header + 3 results
        assert "name" in rows[0]
        assert "model" in rows[0]
        assert "fps" in rows[0]

    def test_generate_without_timing(self, sample_results):
        """Test CSV without timing columns."""
        reporter = CSVReporter(include_timing=False)
        report = reporter.generate(sample_results)

        reader = csv.reader(io.StringIO(report))
        headers = next(reader)

        assert "fps" not in headers
        assert "mean_ms" not in headers
        assert "name" in headers

    def test_generate_without_memory(self, sample_results):
        """Test CSV without memory columns."""
        reporter = CSVReporter(include_memory=False)
        report = reporter.generate(sample_results)

        reader = csv.reader(io.StringIO(report))
        headers = next(reader)

        assert "peak_memory_mb" not in headers
        assert "gpu_peak_memory_mb" not in headers

    def test_generate_without_gpu(self, sample_results):
        """Test CSV without GPU columns."""
        reporter = CSVReporter(include_gpu=False)
        report = reporter.generate(sample_results)

        reader = csv.reader(io.StringIO(report))
        headers = next(reader)

        assert "gpu_device_name" not in headers

    def test_csv_escapes_special_characters(self, sample_results):
        """Test that CSV properly escapes special characters."""
        # Add a result with special characters
        sample_results.add_result(
            BenchmarkResult(
                name='test,with"quotes',
                model="model_a",
                resolution=(640, 480),
                device="cuda",
            )
        )

        reporter = CSVReporter()
        report = reporter.generate(sample_results)

        # Parse and verify
        reader = csv.reader(io.StringIO(report))
        rows = list(reader)

        # Find the row with special characters
        names = [row[0] for row in rows]
        assert 'test,with"quotes' in names

    def test_csv_handles_newlines(self, sample_results):
        """Test that CSV handles newlines in error messages."""
        sample_results.add_result(
            BenchmarkResult(
                name="test_newline",
                model="model_a",
                resolution=(640, 480),
                device="cuda",
                success=False,
                error_message="Line 1\nLine 2",
            )
        )

        reporter = CSVReporter()
        report = reporter.generate(sample_results)

        # Should be parseable despite newlines
        reader = csv.reader(io.StringIO(report))
        rows = list(reader)
        assert len(rows) == 5  # Header + 4 results

    def test_save_to_file(self, sample_results):
        """Test saving CSV report to file."""
        reporter = CSVReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.csv"
            reporter.save(sample_results, path)

            assert path.exists()
            content = path.read_text()
            assert "name" in content


class TestGenerateReportFunction:
    """Tests for the generate_report convenience function."""

    def test_generate_markdown(self, sample_results):
        """Test generating markdown report."""
        report = generate_report(sample_results, format="markdown")
        assert "# Benchmark Results" in report

    def test_generate_markdown_alias(self, sample_results):
        """Test 'md' alias for markdown."""
        report = generate_report(sample_results, format="md")
        assert "# Benchmark Results" in report

    def test_generate_json(self, sample_results):
        """Test generating JSON report."""
        report = generate_report(sample_results, format="json")
        data = json.loads(report)
        assert data["config_name"] == "test_benchmark"

    def test_generate_csv(self, sample_results):
        """Test generating CSV report."""
        report = generate_report(sample_results, format="csv")
        reader = csv.reader(io.StringIO(report))
        rows = list(reader)
        assert len(rows) == 4

    def test_invalid_format(self, sample_results):
        """Test that invalid format raises error."""
        with pytest.raises(ValueError, match="Unknown report format"):
            generate_report(sample_results, format="invalid")

    def test_format_case_insensitive(self, sample_results):
        """Test that format is case insensitive."""
        report_upper = generate_report(sample_results, format="MARKDOWN")
        report_lower = generate_report(sample_results, format="markdown")
        assert report_upper == report_lower

    def test_save_to_path(self, sample_results):
        """Test saving report to path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.md"
            report = generate_report(sample_results, format="markdown", output_path=path)

            assert path.exists()
            assert "# Benchmark Results" in report

    def test_save_with_string_path(self, sample_results):
        """Test saving report with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "report.md")
            generate_report(sample_results, format="markdown", output_path=path)

            assert Path(path).exists()
