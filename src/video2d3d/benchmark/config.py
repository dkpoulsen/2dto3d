"""Configuration for the benchmark suite.

This module defines the configuration options for running benchmarks,
including model selection, resolution presets, and hardware settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class BenchmarkCategory(Enum):
    """Categories for benchmark tests."""

    MODEL_COMPARISON = "model_comparison"
    RESOLUTION_SCALING = "resolution_scaling"
    HARDWARE_COMPARISON = "hardware_comparison"
    BATCH_PROCESSING = "batch_processing"
    FULL_PIPELINE = "full_pipeline"


class ResolutionPreset(Enum):
    """Predefined resolution presets for benchmarks."""

    SD_480P = (640, 480)
    HD_720P = (1280, 720)
    FHD_1080P = (1920, 1080)
    QHD_1440P = (2560, 1440)
    UHD_4K = (3840, 2160)

    @property
    def width(self) -> int:
        """Get the width of this resolution."""
        return self.value[0]

    @property
    def height(self) -> int:
        """Get the height of this resolution."""
        return self.value[1]

    @property
    def label(self) -> str:
        """Get a human-readable label for this resolution."""
        labels = {
            ResolutionPreset.SD_480P: "480p (SD)",
            ResolutionPreset.HD_720P: "720p (HD)",
            ResolutionPreset.FHD_1080P: "1080p (FHD)",
            ResolutionPreset.QHD_1440P: "1440p (QHD)",
            ResolutionPreset.UHD_4K: "2160p (4K)",
        }
        return labels[self]


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs.

    Attributes:
        models: List of model names to benchmark.
        resolutions: List of resolutions to test (as (width, height) tuples).
        resolution_presets: List of resolution presets to use.
        devices: List of devices to test ('cuda', 'cpu', 'auto').
        warmup_iterations: Number of warmup iterations before timing.
        test_iterations: Number of test iterations for averaging.
        batch_sizes: List of batch sizes to test for batch processing.
        output_dir: Directory to save benchmark results.
        save_intermediate: Whether to save intermediate results.
        generate_report: Whether to generate a report after benchmarking.
        report_format: Output format for the report ('markdown', 'json', 'csv').
        include_memory: Whether to include memory usage metrics.
        include_gpu_metrics: Whether to include GPU-specific metrics.
        timeout_seconds: Maximum time per benchmark in seconds.
        categories: Benchmark categories to run.
        custom_test_images: Optional list of custom test image paths.
        seed: Random seed for reproducible benchmarks.
    """

    models: list[str] = field(
        default_factory=lambda: [
            "midas_small",
            "midas_hybrid",
            "dpt_large",
            "dpt_hybrid",
        ]
    )
    resolutions: list[tuple[int, int]] = field(
        default_factory=lambda: [
            (640, 480),
            (1280, 720),
            (1920, 1080),
        ]
    )
    resolution_presets: list[ResolutionPreset] = field(
        default_factory=lambda: [
            ResolutionPreset.SD_480P,
            ResolutionPreset.HD_720P,
            ResolutionPreset.FHD_1080P,
        ]
    )
    devices: list[str] = field(default_factory=lambda: ["auto"])
    warmup_iterations: int = 3
    test_iterations: int = 10
    batch_sizes: list[int] = field(default_factory=lambda: [1, 2, 4, 8])
    output_dir: Path = field(default_factory=lambda: Path("logs/benchmarks"))
    save_intermediate: bool = True
    generate_report: bool = True
    report_format: str = "markdown"
    include_memory: bool = True
    include_gpu_metrics: bool = True
    timeout_seconds: float = 300.0
    categories: list[BenchmarkCategory] = field(
        default_factory=lambda: [
            BenchmarkCategory.MODEL_COMPARISON,
            BenchmarkCategory.RESOLUTION_SCALING,
        ]
    )
    custom_test_images: Optional[list[Path]] = None
    seed: int = 42

    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        # Ensure output_dir is a Path
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Convert custom_test_images to Paths if needed
        if self.custom_test_images is not None:
            self.custom_test_images = [
                Path(p) if isinstance(p, str) else p for p in self.custom_test_images
            ]

        # Validate iterations
        if self.warmup_iterations < 0:
            raise ValueError("warmup_iterations must be >= 0")
        if self.test_iterations < 1:
            raise ValueError("test_iterations must be >= 1")

        # Validate timeout
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def all_resolutions(self) -> list[tuple[int, int]]:
        """Get all resolutions to test (both explicit and presets)."""
        resolution_set = set(self.resolutions)
        for preset in self.resolution_presets:
            resolution_set.add(preset.value)
        return sorted(resolution_set, key=lambda r: r[0] * r[1])

    def get_model_display_names(self) -> dict[str, str]:
        """Get display names for models."""
        return {
            "midas_small": "MiDaS v2.1 Small",
            "midas_hybrid": "MiDaS v3.1 Hybrid",
            "dpt_large": "DPT Large",
            "dpt_hybrid": "DPT Hybrid",
            "adabins_nyu": "AdaBins NYU",
            "adabins_kitti": "AdaBins KITTI",
            "zoedepth_n": "ZoeDepth N",
            "zoedepth_k": "ZoeDepth K",
            "zoedepth_nk": "ZoeDepth NK",
        }


@dataclass
class QuickBenchmarkConfig:
    """Quick benchmark configuration for fast testing.

    This preset runs minimal benchmarks for quick validation.
    Use BenchmarkRunner.run_quick() which handles this automatically.
    Note: This is a standalone config, not inheriting from BenchmarkConfig
    to avoid dataclass field inheritance issues.
    """

    # Override defaults with quick benchmark values
    models: list[str] = field(default_factory=lambda: ["midas_small"])
    resolutions: list[tuple[int, int]] = field(default_factory=lambda: [(640, 480)])
    resolution_presets: list[ResolutionPreset] = field(
        default_factory=lambda: [ResolutionPreset.SD_480P]
    )
    devices: list[str] = field(default_factory=lambda: ["auto"])
    warmup_iterations: int = 1
    test_iterations: int = 3
    batch_sizes: list[int] = field(default_factory=lambda: [1])
    output_dir: Path = field(default_factory=lambda: Path("logs/benchmarks"))
    save_intermediate: bool = True
    generate_report: bool = True
    report_format: str = "markdown"
    include_memory: bool = True
    include_gpu_metrics: bool = True
    timeout_seconds: float = 60.0
    categories: list[BenchmarkCategory] = field(
        default_factory=lambda: [BenchmarkCategory.MODEL_COMPARISON]
    )
    custom_test_images: Optional[list[Path]] = None
    seed: int = 42

    @property
    def all_resolutions(self) -> list[tuple[int, int]]:
        """Get all resolutions to test (both explicit and presets)."""
        resolution_set = set(self.resolutions)
        for preset in self.resolution_presets:
            resolution_set.add(preset.value)
        return sorted(resolution_set, key=lambda r: r[0] * r[1])


@dataclass
class FullBenchmarkConfig:
    """Full benchmark configuration for comprehensive testing.

    This preset runs all models across all resolutions.
    Use this by passing these values to BenchmarkConfig constructor.
    Note: This is a standalone config, not inheriting from BenchmarkConfig
    to avoid dataclass field inheritance issues.
    """

    # Override defaults with full benchmark values
    models: list[str] = field(
        default_factory=lambda: [
            "midas_small",
            "midas_hybrid",
            "dpt_large",
            "dpt_hybrid",
        ]
    )
    resolutions: list[tuple[int, int]] = field(default_factory=lambda: [])
    resolution_presets: list[ResolutionPreset] = field(
        default_factory=lambda: list(ResolutionPreset)
    )
    devices: list[str] = field(default_factory=lambda: ["auto"])
    warmup_iterations: int = 5
    test_iterations: int = 20
    batch_sizes: list[int] = field(default_factory=lambda: [1, 2, 4, 8, 16])
    output_dir: Path = field(default_factory=lambda: Path("logs/benchmarks"))
    save_intermediate: bool = True
    generate_report: bool = True
    report_format: str = "markdown"
    include_memory: bool = True
    include_gpu_metrics: bool = True
    timeout_seconds: float = 600.0
    categories: list[BenchmarkCategory] = field(default_factory=lambda: list(BenchmarkCategory))
    custom_test_images: Optional[list[Path]] = None
    seed: int = 42

    @property
    def all_resolutions(self) -> list[tuple[int, int]]:
        """Get all resolutions to test (both explicit and presets)."""
        resolution_set = set(self.resolutions)
        for preset in self.resolution_presets:
            resolution_set.add(preset.value)
        return sorted(resolution_set, key=lambda r: r[0] * r[1])


__all__ = [
    "BenchmarkConfig",
    "BenchmarkCategory",
    "ResolutionPreset",
    "QuickBenchmarkConfig",
    "FullBenchmarkConfig",
]
