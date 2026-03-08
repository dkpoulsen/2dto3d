"""Benchmark report generation module.

This module provides tools for generating benchmark reports in various
formats including Markdown, JSON, and CSV.
"""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


class ReportGenerator(ABC):
    """Abstract base class for report generators."""

    @abstractmethod
    def generate(self, results: BenchmarkResults) -> str:
        """Generate a report from benchmark results.

        Args:
            results: Benchmark results to report on.

        Returns:
            Generated report as a string.
        """
        pass

    @abstractmethod
    def save(self, results: BenchmarkResults, path: Path) -> None:
        """Save a report to a file.

        Args:
            results: Benchmark results to report on.
            path: Path to save the report to.
        """
        pass


class MarkdownReporter(ReportGenerator):
    """Generate Markdown reports from benchmark results."""

    def __init__(
        self,
        include_system_info: bool = True,
        include_summary: bool = True,
        include_comparison: bool = True,
        include_details: bool = True,
    ) -> None:
        """Initialize the Markdown reporter.

        Args:
            include_system_info: Include system information section.
            include_summary: Include summary statistics section.
            include_comparison: Include model comparison section.
            include_details: Include detailed results section.
        """
        self.include_system_info = include_system_info
        self.include_summary = include_summary
        self.include_comparison = include_comparison
        self.include_details = include_details

    def generate(self, results: BenchmarkResults) -> str:
        """Generate a Markdown report."""
        lines: list[str] = []

        # Title
        lines.append("# Benchmark Results")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # System Information
        if self.include_system_info and results.system_info:
            lines.extend(self._generate_system_info(results))

        # Summary Statistics
        if self.include_summary:
            lines.extend(self._generate_summary(results))

        # Model Comparison
        if self.include_comparison:
            lines.extend(self._generate_comparison(results))

        # Detailed Results
        if self.include_details:
            lines.extend(self._generate_details(results))

        # Failed Benchmarks
        if results.failed_results:
            lines.extend(self._generate_failures(results))

        return "\n".join(lines)

    def _generate_system_info(self, results: BenchmarkResults) -> list[str]:
        """Generate system information section."""
        lines = [
            "## System Information",
            "",
        ]
        info = results.system_info

        lines.append(f"- **Platform**: {info.get('platform', 'Unknown')}")
        lines.append(f"- **Python**: {info.get('python_version', 'Unknown')}")
        lines.append(f"- **CPU**: {info.get('cpu_name', 'Unknown')}")
        lines.append(f"- **CPU Cores**: {info.get('cpu_count', 'Unknown')}")
        lines.append(f"- **RAM**: {info.get('ram_total_gb', 0):.1f} GB")
        lines.append(f"- **PyTorch**: {info.get('torch_version', 'Unknown')}")

        cuda_available = info.get("cuda_available", False)
        lines.append(f"- **CUDA Available**: {'Yes' if cuda_available else 'No'}")

        if cuda_available:
            lines.append(f"- **CUDA Version**: {info.get('cuda_version', 'Unknown')}")

        gpus = info.get("gpus", [])
        if gpus:
            lines.append("")
            lines.append("### GPUs")
            lines.append("")
            for gpu in gpus:
                lines.append(
                    f"- {gpu['name']} ({gpu['total_memory_mb']:.0f} MB, "
                    f"SM {gpu['compute_capability']})"
                )

        lines.append("")
        return lines

    def _generate_summary(self, results: BenchmarkResults) -> list[str]:
        """Generate summary statistics section."""
        lines = [
            "## Summary",
            "",
        ]
        stats = results.get_summary_stats()

        lines.append(f"- **Total Benchmarks**: {stats['total_benchmarks']}")
        lines.append(f"- **Successful**: {stats['successful']}")
        lines.append(f"- **Failed**: {stats['failed']}")
        lines.append(f"- **Total Duration**: {stats['total_duration_seconds']:.1f}s")
        lines.append("")

        if stats["successful"] > 0:
            fps = stats["fps"]
            lines.append("### Performance Summary")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Mean FPS | {fps['mean']:.2f} |")
            lines.append(f"| Min FPS | {fps['min']:.2f} |")
            lines.append(f"| Max FPS | {fps['max']:.2f} |")
            lines.append("")

            lines.append(f"- **Models Tested**: {', '.join(stats['models_tested'])}")
            lines.append(f"- **Resolutions Tested**: {', '.join(stats['resolutions_tested'])}")
            lines.append("")

        return lines

    def _generate_comparison(self, results: BenchmarkResults) -> list[str]:
        """Generate model comparison section."""
        comparison = results.compare_models()
        if not comparison:
            return []

        lines = [
            "## Model Comparison",
            "",
            "| Model | Avg FPS | Avg Inference (ms) | Avg Memory (MB) |",
            "|-------|---------|-------------------|-----------------|",
        ]

        # Sort by FPS (descending)
        sorted_models = sorted(
            comparison.items(),
            key=lambda x: x[1]["avg_fps"],
            reverse=True,
        )

        for model, metrics in sorted_models:
            lines.append(
                f"| {model} | {metrics['avg_fps']:.2f} | "
                f"{metrics['avg_inference_ms']:.2f} | "
                f"{metrics['avg_peak_memory_mb']:.1f} |"
            )

        lines.append("")
        return lines

    def _generate_details(self, results: BenchmarkResults) -> list[str]:
        """Generate detailed results section."""
        lines = [
            "## Detailed Results",
            "",
        ]

        # Group by model
        models = sorted(set(r.model for r in results.successful_results))

        for model in models:
            model_results = results.get_by_model(model)
            if not model_results:
                continue

            lines.append(f"### {model}")
            lines.append("")
            lines.append(
                "| Resolution | Device | Batch | FPS | Avg (ms) | Std (ms) | Memory (MB) |"
            )
            lines.append("|------------|--------|-------|-----|----------|---------|-------------|")

            for r in model_results:
                lines.append(
                    f"| {r.resolution_label} | {r.device} | {r.batch_size} | "
                    f"{r.timing.fps:.2f} | {r.timing.mean_ms:.2f} | "
                    f"{r.timing.std_ms:.2f} | {r.memory.peak_memory_mb:.1f} |"
                )

            lines.append("")

        return lines

    def _generate_failures(self, results: BenchmarkResults) -> list[str]:
        """Generate failed benchmarks section."""
        lines = [
            "## Failed Benchmarks",
            "",
        ]

        for r in results.failed_results:
            lines.append(f"- **{r.name}**: {r.error_message}")

        lines.append("")
        return lines

    def save(self, results: BenchmarkResults, path: Path) -> None:
        """Save the Markdown report to a file."""
        report = self.generate(results)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(report)


class JSONReporter(ReportGenerator):
    """Generate JSON reports from benchmark results."""

    def __init__(self, pretty: bool = True) -> None:
        """Initialize the JSON reporter.

        Args:
            pretty: Whether to format JSON with indentation.
        """
        self.pretty = pretty

    def generate(self, results: BenchmarkResults) -> str:
        """Generate a JSON report."""
        data = {
            "config_name": results.config_name,
            "start_time": results.start_time.isoformat(),
            "end_time": results.end_time.isoformat() if results.end_time else None,
            "system_info": results.system_info,
            "summary": results.get_summary_stats(),
            "model_comparison": results.compare_models(),
            "results": [r.to_dict() for r in results.results],
        }

        indent = 2 if self.pretty else None
        return json.dumps(data, indent=indent)

    def save(self, results: BenchmarkResults, path: Path) -> None:
        """Save the JSON report to a file."""
        report = self.generate(results)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(report)


class CSVReporter(ReportGenerator):
    """Generate CSV reports from benchmark results."""

    def __init__(
        self,
        include_timing: bool = True,
        include_memory: bool = True,
        include_gpu: bool = True,
    ) -> None:
        """Initialize the CSV reporter.

        Args:
            include_timing: Include timing columns.
            include_memory: Include memory columns.
            include_gpu: Include GPU columns.
        """
        self.include_timing = include_timing
        self.include_memory = include_memory
        self.include_gpu = include_gpu

    def generate(self, results: BenchmarkResults) -> str:
        """Generate a CSV report."""
        rows = []
        headers = [
            "name",
            "model",
            "resolution",
            "device",
            "batch_size",
            "success",
            "error_message",
        ]

        if self.include_timing:
            headers.extend(
                [
                    "fps",
                    "total_time_ms",
                    "inference_time_ms",
                    "mean_ms",
                    "std_ms",
                    "min_ms",
                    "max_ms",
                    "median_ms",
                    "p95_ms",
                    "p99_ms",
                ]
            )

        if self.include_memory:
            headers.extend(
                [
                    "peak_memory_mb",
                    "avg_memory_mb",
                    "gpu_peak_memory_mb",
                    "gpu_avg_memory_mb",
                ]
            )

        if self.include_gpu:
            headers.extend(
                [
                    "gpu_device_name",
                    "gpu_device_id",
                    "gpu_compute_capability",
                    "gpu_total_memory_mb",
                ]
            )

        for r in results.results:
            row = [
                r.name,
                r.model,
                r.resolution_label,
                r.device,
                r.batch_size,
                r.success,
                r.error_message or "",
            ]

            if self.include_timing:
                row.extend(
                    [
                        f"{r.timing.fps:.2f}",
                        f"{r.timing.total_time_ms:.2f}",
                        f"{r.timing.inference_time_ms:.2f}",
                        f"{r.timing.mean_ms:.2f}",
                        f"{r.timing.std_ms:.2f}",
                        f"{r.timing.min_ms:.2f}",
                        f"{r.timing.max_ms:.2f}",
                        f"{r.timing.median_ms:.2f}",
                        f"{r.timing.p95_ms:.2f}",
                        f"{r.timing.p99_ms:.2f}",
                    ]
                )

            if self.include_memory:
                row.extend(
                    [
                        f"{r.memory.peak_memory_mb:.1f}",
                        f"{r.memory.avg_memory_mb:.1f}",
                        f"{r.memory.gpu_peak_memory_mb:.1f}",
                        f"{r.memory.gpu_avg_memory_mb:.1f}",
                    ]
                )

            if self.include_gpu:
                row.extend(
                    [
                        r.gpu.device_name,
                        r.gpu.device_id,
                        f"{r.gpu.compute_capability[0]}.{r.gpu.compute_capability[1]}",
                        f"{r.gpu.total_memory_mb:.1f}",
                    ]
                )

            rows.append(row)

        # Build CSV string using csv.writer for proper escaping
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        return output.getvalue()

    def save(self, results: BenchmarkResults, path: Path) -> None:
        """Save the CSV report to a file."""
        report = self.generate(results)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(report)


def generate_report(
    results: BenchmarkResults,
    format: str = "markdown",
    output_path: Optional[Union[Path, str]] = None,
) -> str:
    """Generate a report in the specified format.

    Args:
        results: Benchmark results to report on.
        format: Output format ('markdown', 'md', 'json', 'csv').
        output_path: Optional path to save the report.

    Returns:
        Generated report as a string.

    Raises:
        ValueError: If format is not supported.
    """
    format_lower = format.lower()

    if format_lower in ("markdown", "md"):
        reporter: ReportGenerator = MarkdownReporter()
    elif format_lower == "json":
        reporter = JSONReporter()
    elif format_lower == "csv":
        reporter = CSVReporter()
    else:
        valid_formats = ["markdown", "md", "json", "csv"]
        raise ValueError(
            f"Unknown report format: '{format}'. " f"Valid formats are: {', '.join(valid_formats)}"
        )

    report = reporter.generate(results)

    if output_path:
        reporter.save(results, Path(output_path))

    return report


__all__ = [
    "ReportGenerator",
    "MarkdownReporter",
    "JSONReporter",
    "CSVReporter",
    "generate_report",
]
