"""Comprehensive benchmark suite for 2Dto3D video converter.

This module provides tools for measuring and comparing performance across
different models, resolutions, and hardware configurations.

Example usage:
    ```python
    from video2d3d.benchmark import BenchmarkRunner, BenchmarkConfig
    from video2d3d.benchmark.reporting import MarkdownReporter

    # Run a quick benchmark
    config = BenchmarkConfig(models=["midas_small", "dpt_hybrid"])
    runner = BenchmarkRunner(config)
    results = runner.run()

    # Generate report
    reporter = MarkdownReporter()
    report = reporter.generate(results)
    print(report)
    ```
"""

from video2d3d.benchmark.config import (
    BenchmarkConfig,
    BenchmarkCategory,
    ResolutionPreset,
    QuickBenchmarkConfig,
    FullBenchmarkConfig,
)
from video2d3d.benchmark.runner import BenchmarkRunner
from video2d3d.benchmark.results import (
    BenchmarkResult,
    BenchmarkResults,
)
from video2d3d.benchmark.reporting import (
    ReportGenerator,
    MarkdownReporter,
    JSONReporter,
    CSVReporter,
    generate_report,
)

__all__ = [
    # Core classes
    "BenchmarkRunner",
    "BenchmarkConfig",
    # Config presets
    "QuickBenchmarkConfig",
    "FullBenchmarkConfig",
    # Enums
    "BenchmarkCategory",
    "ResolutionPreset",
    # Results
    "BenchmarkResult",
    "BenchmarkResults",
    # Reporting
    "ReportGenerator",
    "MarkdownReporter",
    "JSONReporter",
    "CSVReporter",
    "generate_report",
]
