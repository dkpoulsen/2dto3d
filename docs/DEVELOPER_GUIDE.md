# 2Dto3D Video Converter - Developer Guide

**Version:** 0.1.0  
**Last Updated:** March 2026

> This guide is intended for developers who want to understand, extend, or contribute to the 2Dto3D Video Converter project.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Modules](#core-modules)
4. [Data Flow](#data-flow)
5. [Extending the System](#extending-the-system)
6. [API Reference](#api-reference)
7. [Testing](#testing)
8. [Debugging](#debugging)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Interface Layer                            │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│     CLI         │    Web API      │   Desktop GUI   │    Web Dashboard      │
│   (cli.py)      │   (web/app.py)  │   (gui/)        │    (frontend/)        │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬────────────┘
         │                 │                 │                    │
         ▼                 ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Core Processing Layer                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Video Handler  │──▶  Depth Engine   │──▶  Stereo Engine  │             │
│  │  (video/)       │  │  (depth/)       │  │  (stereo/)      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│           │                   │                    │                        │
│           ▼                   ▼                    ▼                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Frame Extractor │  │ Depth Processor │  │ Output Encoders │             │
│  │ Video Writer    │  │ Temporal Smooth │  │ SBS/Anaglyph/VR │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │                 │                 │                    │
         ▼                 ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Infrastructure Layer                               │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│   Batch Queue   │   GPU Manager   │  Config System  │   Logging System      │
│  (batch/)       │  (utils/gpu)    │ (utils/config)  │  (utils/logger)       │
├─────────────────┼─────────────────┼─────────────────┼───────────────────────┤
│ Error Recovery  │ Memory Monitor  │  Crash Reporter │   Preset Manager      │
│(utils/error)    │(utils/memory)   │   (crash/)      │   (presets/)          │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

### Processing Pipeline

The video conversion follows a well-defined pipeline:

```mermaid
graph LR
    A[Input Video] --> B[Frame Extraction]
    B --> C[Batch Processor]
    C --> D[Depth Estimation]
    D --> E[Depth Processing]
    E --> F[Temporal Smoothing]
    F --> G[DIBR Engine]
    G --> H[Stereo Encoder]
    H --> I[Video Writer]
    I --> J[Output 3D Video]
```

---

## Project Structure

```
2dto3d/
├── config/                     # Configuration files
│   ├── default.yaml           # Default settings
│   ├── development.yaml       # Development overrides
│   └── production.yaml        # Production overrides
│
├── src/video2d3d/             # Main source code
│   ├── __init__.py
│   ├── __main__.py            # Entry point for python -m
│   ├── cli.py                 # Command-line interface
│   ├── _version.py            # Version information
│   │
│   ├── core/                  # Core processing logic
│   │   ├── __init__.py
│   │   └── batch_processor.py # Parallel batch processing
│   │
│   ├── video/                 # Video I/O handling
│   │   ├── __init__.py
│   │   ├── handler.py         # Main video handler
│   │   ├── frame_extractor.py # Frame extraction from videos
│   │   ├── video_writer.py    # Video output writer
│   │   ├── metadata.py        # Video metadata utilities
│   │   └── exceptions.py      # Video-specific exceptions
│   │
│   ├── depth/                 # Depth estimation modules
│   │   ├── __init__.py
│   │   ├── processor.py       # Depth map post-processing
│   │   ├── temporal.py        # Temporal smoothing
│   │   ├── adadepth.py        # AdaDepth model integration
│   │   ├── zoedepth.py        # ZoeDepth model integration
│   │   ├── ensemble.py        # Depth ensemble methods
│   │   ├── curve.py           # Depth curve adjustments
│   │   └── model_selector.py  # Dynamic model selection
│   │
│   ├── stereo/                # Stereoscopic generation
│   │   ├── __init__.py
│   │   ├── dibr.py            # Depth-Image-Based Rendering
│   │   ├── side_by_side.py    # Side-by-side encoder
│   │   ├── anaglyph.py        # Anaglyph encoder
│   │   ├── interlaced.py      # Interlaced encoder
│   │   ├── checkerboard.py    # Checkerboard encoder
│   │   ├── top_bottom.py      # Top-bottom encoder
│   │   └── vr.py              # VR format encoder
│   │
│   ├── audio/                 # Audio processing
│   │   ├── __init__.py
│   │   ├── processor.py       # Audio processing pipeline
│   │   ├── tracks.py          # Audio track handling
│   │   ├── spatial.py         # Spatial audio
│   │   ├── multichannel.py    # Multichannel audio
│   │   ├── metadata.py        # Audio metadata
│   │   ├── config.py          # Audio configuration
│   │   ├── constants.py       # Audio constants
│   │   └── exceptions.py      # Audio exceptions
│   │
│   ├── web/                   # Web API server
│   │   ├── __init__.py
│   │   ├── app.py             # FastAPI application
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── health.py          # Health check endpoints
│   │   ├── state.py           # Application state
│   │   ├── rate_limit.py      # Rate limiting
│   │   ├── exceptions.py      # API exceptions
│   │   ├── utils.py           # API utilities
│   │   └── routers/           # API routers
│   │       ├── __init__.py
│   │       ├── jobs.py        # Job management
│   │       ├── uploads.py     # File uploads
│   │       ├── downloads.py   # File downloads
│   │       └── crash.py       # Crash reports
│   │
│   ├── batch/                 # Batch processing
│   │   ├── __init__.py
│   │   ├── queue.py           # Job queue management
│   │   ├── models.py          # Batch job models
│   │   ├── config.py          # Batch configuration
│   │   ├── file_discovery.py  # File discovery
│   │   ├── folder_watcher.py  # Folder watching
│   │   ├── exceptions.py      # Batch exceptions
│   │   └── adaptive_sizer.py  # Adaptive batch sizing
│   │
│   ├── gui/                   # Desktop GUI (PyQt)
│   │   ├── __init__.py
│   │   ├── main_window.py     # Main application window
│   │   ├── convert_tab.py     # Conversion tab
│   │   ├── batch_tab.py       # Batch processing tab
│   │   ├── settings_tab.py    # Settings tab
│   │   ├── workers.py         # Background workers
│   │   └── widgets.py         # Custom widgets
│   │
│   ├── preview/               # Preview functionality
│   │   ├── __init__.py
│   │   └── preview_window.py  # Live preview window
│   │
│   ├── utils/                 # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging utilities
│   │   ├── gpu.py             # GPU management
│   │   ├── progress.py        # Progress tracking
│   │   ├── error_recovery.py  # Error recovery utilities
│   │   └── memory_monitor.py  # Memory monitoring
│   │
│   ├── crash/                 # Crash reporting
│   │   ├── __init__.py
│   │   ├── reporter.py        # Crash reporter
│   │   ├── models.py          # Crash report models
│   │   └── state_capture.py   # State capture
│   │
│   ├── benchmark/             # Benchmarking tools
│   │   ├── __init__.py
│   │   ├── runner.py          # Benchmark runner
│   │   ├── results.py         # Benchmark results
│   │   ├── reporting.py       # Result reporting
│   │   └── config.py          # Benchmark config
│   │
│   ├── presets/               # Preset management
│   │   ├── __init__.py
│   │   ├── manager.py         # Preset manager
│   │   ├── storage.py         # Preset storage
│   │   ├── models.py          # Preset models
│   │   └── builtins.py        # Built-in presets
│   │
│   ├── checkpoint/            # Checkpoint/resume
│   │   ├── __init__.py
│   │   ├── manager.py         # Checkpoint manager
│   │   └── models.py          # Checkpoint models
│   │
│   ├── opticalflow/           # Optical flow engine
│   │   ├── __init__.py
│   │   └── engine.py          # Optical flow computation
│   │
│   └── segmentation/          # Segmentation processor
│       ├── __init__.py
│       ├── processor.py       # Segmentation processing
│       └── integrator.py      # Segmentation integration
│
├── frontend/                  # Web dashboard (React/TypeScript)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
│
├── docs/                      # Documentation
│   ├── USER_GUIDE.md         # User documentation
│   └── DEVELOPER_GUIDE.md    # This file
│
├── models/                    # Pre-trained models (downloaded)
├── inputs/                    # Input videos directory
├── outputs/                   # Output videos directory
├── logs/                      # Log files directory
│
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project configuration
├── setup.py                  # Package setup
├── Dockerfile                # GPU Docker image
├── Dockerfile.cpu            # CPU-only Docker image
├── docker-compose.yml        # Docker Compose (GPU)
└── docker-compose.cpu.yml    # Docker Compose (CPU)
```

---

## Core Modules

### 1. Video Module (`src/video2d3d/video/`)

Handles all video input/output operations.

#### Key Components

| Component | Description |
|-----------|-------------|
| `VideoHandler` | Main class for video processing workflow |
| `FrameExtractor` | Extracts individual frames from video files |
| `VideoWriter` | Writes processed frames to output video |
| `VideoMetadata` | Extracts and manages video metadata |

#### Usage Example

```python
from video2d3d.video import FrameExtractor, VideoWriter

# Extract frames from a video
extractor = FrameExtractor("input.mp4")
for frame_idx, frame in extractor.extract_frames():
    # Process frame
    processed_frame = process(frame)
    # Write to output
    break

# Write frames to video
writer = VideoWriter(
    "output.mp4",
    fps=30,
    resolution=(1920, 1080),
    codec="libx264"
)
for frame in processed_frames:
    writer.write_frame(frame)
writer.close()
```

### 2. Depth Module (`src/video2d3d/depth/`)

Handles depth estimation and post-processing.

#### Key Components

| Component | Description |
|-----------|-------------|
| `DepthMapProcessor` | Post-processes depth maps (normalization, filtering) |
| `TemporalSmoother` | Smooths depth across video frames |
| `DepthModelSelector` | Dynamically selects depth models |
| `DepthEnsemble` | Combines multiple depth estimates |

#### Depth Processing Pipeline

```python
from video2d3d.depth import DepthMapProcessor, DepthProcessorConfig

# Configure depth processing
config = DepthProcessorConfig(
    edge_aware_smoothing=True,
    bilateral_filter=True,
    hole_filling=True,
    hole_filling_method="inpaint",
    normalization_method="percentile",
    colormap="turbo"
)

processor = DepthMapProcessor(config=config)

# Process a depth map
processed_depth = processor.process(raw_depth_map, apply_colormap=False)

# Individual operations
normalized = processor.normalize(raw_depth_map, method="min_max")
filtered = processor.apply_bilateral_filter(normalized)
filled = processor.fill_holes(filtered)
colored = processor.apply_colormap(filled, colormap="plasma")
```

### 3. Stereo Module (`src/video2d3d/stereo/`)

Generates stereoscopic 3D views from depth maps.

#### Key Components

| Component | Description |
|-----------|-------------|
| `DIBREngine` | Depth-Image-Based Rendering for stereo generation |
| `SideBySideEncoder` | Left-right stereo format |
| `AnaglyphEncoder` | Red-cyan anaglyph format |
| `InterlacedEncoder` | Row-alternating format |
| `VREncoder` | VR over-under format |

#### DIBR Rendering

```python
from video2d3d.stereo import DIBREngine, DIBRConfig

# Configure DIBR
config = DIBRConfig(
    baseline=0.05,           # Camera separation (3D effect strength)
    focal_length=1.0,        # Virtual focal length
    convergence=0.5,         # Zero parallax distance
    hole_filling="inpaint",  # How to fill disocclusions
    depth_interpretation="inverse"  # MiDaS-style depth
)

engine = DIBREngine(config=config)

# Generate stereo pair
left_view, right_view = engine.render(frame, depth_map)

# Get disparity map for visualization
disparity = engine.compute_disparity(depth_map, image_width=1920)
```

### 4. Core Module (`src/video2d3d/core/`)

Provides parallel batch processing capabilities.

#### Batch Processing

```python
from video2d3d.core import (
    FrameBatchProcessor,
    BatchProcessorConfig,
    ProcessingMode
)

# Configure batch processing
config = BatchProcessorConfig(
    batch_size=8,
    num_workers=4,
    mode=ProcessingMode.MULTIPROCESSING,
    timeout_seconds=300.0,
    max_retries=2,
    preserve_order=True
)

processor = FrameBatchProcessor(config=config)

# Process frames in parallel
def depth_estimation(frame):
    return estimate_depth(frame)

result = processor.process(frames, depth_estimation)

# Access results
for output in result.get_successful_outputs():
    save_output(output)

# Check for errors
for idx, error in result.errors:
    print(f"Frame {idx} failed: {error}")

print(f"Success rate: {result.success_rate:.1f}%")
print(f"Throughput: {result.items_per_second:.1f} fps")
```

### 5. Web API Module (`src/video2d3d/web/`)

REST API server built with FastAPI.

#### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/upload/` | POST | Upload video file |
| `/api/v1/jobs/` | POST | Submit conversion job |
| `/api/v1/jobs/{id}` | GET | Get job status |
| `/api/v1/jobs/{id}/cancel` | POST | Cancel job |
| `/api/v1/download/{id}` | GET | Download result |

#### Starting the Server

```bash
# Command line
video2d3d serve --host 0.0.0.0 --port 8000
```

```python
# Programmatically
from video2d3d.web.app import create_app
import uvicorn

app = create_app()
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6. Batch Module (`src/video2d3d/batch/`)

Manages job queues and batch processing.

```python
from video2d3d.batch import BatchQueue, BatchJobConfig

# Create batch queue
queue = BatchQueue(
    max_concurrent_jobs=1,
    auto_start=True,
    save_state=True
)

# Add job to queue
job_config = BatchJobConfig(
    input_path="video.mp4",
    output_path="video_3d.mp4",
    stereo_format="side_by_side",
    depth_model="midas_small"
)
job_id = queue.add_job(job_config)

# Monitor queue status
status = queue.get_status()
print(f"Pending: {status.pending_jobs}")
print(f"Running: {status.running_jobs}")
print(f"Completed: {status.completed_jobs}")
```

---

## Data Flow

### Frame Processing Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRAME PROCESSING FLOW                      │
└──────────────────────────────────────────────────────────────────┘

Input Video (MP4, AVI, etc.)
         │
         ▼
┌─────────────────────┐
│  Frame Extraction   │  Extract individual frames using OpenCV
│  (FrameExtractor)   │  - Decode video stream
└──────────┬──────────┘  - Yield frames with timestamps
           │
           ▼
┌─────────────────────┐
│   Batch Processing  │  Process frames in parallel batches
│  (BatchProcessor)   │  - Multiprocessing for CPU-bound tasks
└──────────┬──────────┘  - Progress tracking
           │
           ▼
┌─────────────────────┐
│  Depth Estimation   │  Estimate depth using ML models
│  (MiDaS, DPT, etc.) │  - GPU acceleration when available
└──────────┬──────────┘  - Model caching
           │
           ▼
┌─────────────────────┐
│  Depth Processing   │  Post-process depth maps
│ (DepthMapProcessor) │  - Normalization
└──────────┬──────────┘  - Edge-aware smoothing
           │             - Hole filling
           ▼
┌─────────────────────┐
│ Temporal Smoothing  │  Smooth depth across frames
│ (TemporalSmoother)  │  - Consistent depth over time
└──────────┬──────────┘  - Reduces flickering
           │
           ▼
┌─────────────────────┐
│   DIBR Rendering    │  Generate stereo views
│    (DIBREngine)     │  - Compute disparity
└──────────┬──────────┘  - Warp images
           │             - Fill disocclusions
           ▼
┌─────────────────────┐
│  Stereo Encoding    │  Encode stereo format
│ (SBS, Anaglyph, VR) │  - Side-by-side
└──────────┬──────────┘  - Anaglyph
           │             - Interlaced
           ▼             - VR formats
┌─────────────────────┐
│    Video Writing    │  Write output video
│   (VideoWriter)     │  - Encode with FFmpeg
└──────────┬──────────┘  - Preserve audio
           │
           ▼
Output Video (3D MP4, etc.)
```

---

## Extending the System

### Adding a New Depth Model

1. Create a new model adapter in `src/video2d3d/depth/`:

```python
# src/video2d3d/depth/my_model.py

from typing import Optional
import numpy as np
import torch

class MyDepthModel:
    """Custom depth estimation model."""
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cuda"):
        self.device = device
        self.model = self._load_model(model_path)
    
    def _load_model(self, model_path: Optional[str]):
        # Load your model here
        pass
    
    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """Estimate depth from a single frame.
        
        Args:
            frame: Input image (H, W, 3) in RGB format, uint8.
            
        Returns:
            Depth map (H, W) as float32, values in [0, 1] where
            1 = far, 0 = close (inverse depth interpretation).
        """
        # Preprocess
        input_tensor = self._preprocess(frame)
        
        # Run inference
        with torch.no_grad():
            output = self.model(input_tensor)
        
        # Postprocess
        depth = self._postprocess(output)
        
        return depth
```

2. Register the model in `model_selector.py`:

```python
# src/video2d3d/depth/model_selector.py

SUPPORTED_MODELS = {
    # ... existing models ...
    "my_model": {
        "class": "video2d3d.depth.my_model.MyDepthModel",
        "description": "My custom depth model",
        "quality": "custom",
        "speed": "custom",
    }
}
```

3. Add configuration support in `config/default.yaml`:

```yaml
depth_estimation:
  model: my_model  # or midas_small, dpt_large, etc.
```

### Adding a New Stereo Output Format

1. Create a new encoder in `src/video2d3d/stereo/`:

```python
# src/video2d3d/stereo/my_format.py

import numpy as np
from typing import Tuple

class MyFormatEncoder:
    """Encoder for custom stereo format."""
    
    def encode(
        self, 
        left_view: np.ndarray, 
        right_view: np.ndarray
    ) -> np.ndarray:
        """Encode left and right views into custom format.
        
        Args:
            left_view: Left eye view (H, W, 3)
            right_view: Right eye view (H, W, 3)
            
        Returns:
            Encoded stereo image
        """
        # Implement your encoding logic
        encoded = self._custom_encode(left_view, right_view)
        return encoded
    
    def _custom_encode(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        # Your encoding implementation
        pass
```

2. Register in `__init__.py`:

```python
# src/video2d3d/stereo/__init__.py

from video2d3d.stereo.my_format import MyFormatEncoder

__all__ = [
    # ... existing exports ...
    "MyFormatEncoder",
]
```

3. Add CLI support in `cli.py`:

```python
# In convert command
format_choices = [
    "side_by_side", 
    "anaglyph", 
    "interlaced", 
    "my_format"  # Add your format
]
```

### Adding a New CLI Command

```python
# src/video2d3d/cli.py

import click

@click.group()
def cli():
    """2Dto3D Video Converter CLI."""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', required=True, help='Output file path')
@click.option('--option', '-opt', default='default', help='Custom option')
def my_command(input_file: str, output: str, option: str):
    """Description of my custom command.
    
    Extended description with usage examples.
    """
    # Implementation
    click.echo(f"Processing {input_file} -> {output}")
    # ... your logic ...
    click.echo("Done!")

# Register with main CLI group
cli.add_command(my_command)
```

---

## API Reference

### Configuration Classes

#### BatchProcessorConfig

```python
@dataclass
class BatchProcessorConfig:
    batch_size: int = 8          # Items per batch
    num_workers: int = 4         # Parallel workers
    mode: ProcessingMode = ProcessingMode.MULTIPROCESSING
    chunk_size: int = 1          # Items per chunk
    timeout_seconds: float = 300.0
    max_retries: int = 2
    preserve_order: bool = True
    enable_progress: bool = True
```

#### DepthProcessorConfig

```python
@dataclass
class DepthProcessorConfig:
    edge_aware_smoothing: bool = True
    smoothing_radius: int = 3
    bilateral_filter: bool = True
    bilateral_sigma_color: float = 0.1
    bilateral_sigma_space: int = 5
    hole_filling: bool = True
    hole_filling_method: str = "inpaint"  # "inpaint", "nearest", "linear"
    normalization_method: str = "min_max"  # "min_max", "percentile", "histogram_equalization"
    colormap: str = "turbo"
```

#### DIBRConfig

```python
@dataclass
class DIBRConfig:
    baseline: float = 0.05        # Camera separation
    focal_length: float = 1.0     # Virtual focal length
    convergence: float = 0.5      # Zero parallax distance (0-1)
    hole_filling: str = "nearest" # "none", "nearest", "linear", "inpaint"
    depth_interpretation: str = "inverse"  # "inverse" or "direct"
    max_disparity: int = 64       # Maximum disparity in pixels
```

### Exception Classes

| Exception | Description |
|-----------|-------------|
| `BatchProcessorError` | Base error for batch processing |
| `WorkerTimeoutError` | Worker exceeded timeout |
| `DepthProcessingError` | Error in depth processing |
| `DIBRError` | Error in DIBR rendering |
| `VideoProcessingError` | Error in video processing |

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=video2d3d --cov-report=html

# Run specific test file
pytest tests/unit/test_depth_processor.py

# Run specific test
pytest tests/unit/test_depth_processor.py::test_normalization

# Run with verbose output
pytest -v tests/

# Run integration tests only
pytest tests/integration/

# Run with markers
pytest -m "not slow"  # Skip slow tests
pytest -m gpu         # Run GPU tests only
```

### Writing Tests

```python
# tests/unit/test_depth_processor.py

import numpy as np
import pytest
from video2d3d.depth import DepthMapProcessor, DepthProcessorConfig

class TestDepthMapProcessor:
    """Tests for DepthMapProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance for testing."""
        config = DepthProcessorConfig(
            bilateral_filter=True,
            hole_filling=True
        )
        return DepthMapProcessor(config=config)
    
    @pytest.fixture
    def sample_depth_map(self):
        """Create a sample depth map for testing."""
        return np.random.rand(480, 640).astype(np.float32)
    
    def test_normalization(self, processor, sample_depth_map):
        """Test depth map normalization."""
        normalized = processor.normalize(sample_depth_map)
        
        assert normalized.dtype == np.float32
        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0
    
    def test_bilateral_filter(self, processor, sample_depth_map):
        """Test bilateral filtering."""
        filtered = processor.apply_bilateral_filter(sample_depth_map)
        
        assert filtered.shape == sample_depth_map.shape
        assert filtered.dtype == np.float32
    
    def test_invalid_config(self):
        """Test that invalid config raises error."""
        with pytest.raises(ValueError):
            DepthProcessorConfig(
                normalization_method="invalid_method"
            )
```

### Test Fixtures

Place test fixtures in `tests/fixtures/`:

```
tests/fixtures/
├── videos/
│   ├── sample_1s.mp4      # 1-second test video
│   ├── sample_5s.mp4      # 5-second test video
│   └── sample_corrupt.mp4 # Corrupt video for error testing
├── images/
│   ├── test_frame.png
│   └── test_depth.npy
└── configs/
    ├── test_config.yaml
    └── minimal_config.yaml
```

---

## Debugging

### Enable Debug Logging

```bash
# Environment variable
export VIDEO2D3D_LOG_LEVEL=DEBUG

# Or via CLI
video2d3d --verbose convert input.mp4 output.mp4
```

### Log Files

Logs are written to `logs/video2d3d.log` by default.

```bash
# View recent logs
tail -f logs/video2d3d.log

# Search for errors
grep -i error logs/video2d3d.log

# View specific module logs
grep "\[depth\]" logs/video2d3d.log
```

### GPU Debugging

```python
# Check GPU availability
from video2d3d.utils.gpu import get_gpu_info

info = get_gpu_info()
print(f"GPU available: {info.available}")
print(f"GPU name: {info.name}")
print(f"Memory: {info.memory_total} MB")
```

### Performance Profiling

```python
import cProfile
import pstats

from video2d3d.core import FrameBatchProcessor

def profile_batch_processing():
    processor = FrameBatchProcessor()
    # ... processing code ...

# Profile
profiler = cProfile.Profile()
profiler.enable()

profile_batch_processing()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `CUDA out of memory` | GPU memory exhausted | Reduce batch_size, enable auto_batch_size |
| `FFmpeg not found` | FFmpeg not in PATH | Install FFmpeg and add to PATH |
| `Model download failed` | Network issue | Download models manually to `models/` |
| `ImportError` | Module not installed | Run `pip install -e .` |

---

## Performance Optimization

### GPU Memory Management

```python
from video2d3d.utils.gpu import GPUMemoryManager

# Enable memory growth (TensorFlow style)
manager = GPUMemoryManager(memory_fraction=0.8)
manager.configure()

# Check memory usage
usage = manager.get_memory_usage()
print(f"Used: {usage.used} / {usage.total} MB")
```

### Batch Size Tuning

```python
from video2d3d.batch import AdaptiveBatchSizer

# Auto-adjust batch size based on GPU memory
sizer = AdaptiveBatchSizer(
    min_batch_size=1,
    max_batch_size=32,
    target_memory_fraction=0.8
)

batch_size = sizer.get_optimal_batch_size(frame_resolution=(1920, 1080))
```

### Processing Mode Selection

| Mode | Use Case | Performance |
|------|----------|-------------|
| `MULTIPROCESSING` | CPU-bound tasks (depth estimation) | High |
| `THREADING` | I/O-bound tasks (video writing) | Medium |
| `SEQUENTIAL` | Debugging, single-threaded environments | Low |

---

## Development Workflow

### Setting Up a Development Environment

Before contributing to the project, set up a local development environment with all required tooling. The project uses Python 3.9 or later, and all development dependencies are listed in `requirements-dev.txt`.

```bash
# Clone the repository
git clone https://github.com/automaker/2dto3d.git
cd 2dto3d

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install runtime and development dependencies
pip install -r requirements-dev.txt

# Install the package in editable mode
pip install -e .
```

After installation, verify that the core dependencies import correctly and that FFmpeg is available on your `PATH`. FFmpeg is required for all video encoding and decoding operations, and the converter will refuse to start without it.

```bash
# Verify FFmpeg availability
ffmpeg -version
ffprobe -version

# Run a quick smoke test
video2d3d --help
```

### Running the Test Suite

The test suite is organized into unit, integration, and contract tests. Unit tests are fast and run on every commit; integration tests exercise real video files and may download model weights on first run.

```bash
# Run the full test suite with coverage
pytest --cov=src/video2d3d --cov-report=term-missing tests/

# Run only unit tests
pytest tests/unit/ -m "not slow and not gpu"

# Run tests in parallel with pytest-xdist
pytest tests/ -n 4

# Run a single test file
pytest tests/unit/test_depth_curve.py -v
```

Tests marked with the `slow` marker are excluded from the default CI run because they download large model weights or take several minutes to complete. Tests marked with `gpu` require a CUDA-capable device.

### Code Style and Linting

The project enforces formatting with Black, import ordering with isort, and general linting with Ruff. All three tools run in the CI pipeline, and a pull request will fail if formatting does not match.

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Run the linter
ruff check src/ tests/

# Run all checks exactly as CI does
black --check src/ tests/ && ruff check src/ tests/
```

Type hints are required for all public functions. The codebase is fully annotated, and MyPy verifies internal consistency. Run MyPy locally before pushing:

```bash
mypy src/video2d3d
```

## Error Handling Patterns

The codebase follows a layered error handling pattern. Each module defines its own exception hierarchy rooted at a module-specific base class, which in turn derives from a common application error. This allows callers to catch errors at whatever granularity they need.

### Exception Hierarchy

Every module exposes exceptions such as `VideoFileNotFoundError`, `VideoCorruptedError`, and `FrameExtractionError`. All of these derive from the module base, so `except VideoError` catches anything raised by the video pipeline. When writing new code, always raise the most specific exception available and include a human-readable message plus any relevant context.

### Crash Reporting

The crash reporting subsystem captures system state, active jobs, and log excerpts when an unhandled exception occurs. Reports are written as JSON files into a configurable crash directory and can be disabled entirely for embedded deployments.

```bash
# Run the server with crash reporting to a custom directory
VIDEO2D3D_CRASH_DIR=/var/crashes video2d3d serve
```

Callbacks can be registered to receive crash reports programmatically, which is useful for shipping reports to a monitoring service. Callback exceptions are caught and logged so they never interfere with the crash handler itself.

## Configuration Reference

Configuration is loaded from YAML files in the `config/` directory, with environment-specific overrides layered on top of `default.yaml`. The `VIDEO2D3D_ENV` environment variable selects which override file is used.

```bash
# Run with production configuration
VIDEO2D3D_ENV=production video2d3d serve

# Run with development configuration (default)
VIDEO2D3D_ENV=development video2d3d serve
```

Every configuration section maps to a dataclass in `video2d3d.utils.config`. Unknown keys are ignored with a warning, and type mismatches raise a `ValueError` at load time rather than failing silently during processing. When adding a new configuration option, add the field to the dataclass, document it, and add a default so existing configuration files continue to work unchanged.

## Performance Tuning

### Batch Size Selection

The adaptive batch sizer monitors GPU utilization and system memory to adjust batch sizes at runtime. When the GPU is underutilized, the batch size scales up; when memory pressure rises or the GPU is saturated, it scales down. The stability window prevents oscillation by requiring consistent readings before making adjustments.

For dedicated GPU servers, start with the default configuration and observe the logs during a representative workload. If the batch size rarely reaches the maximum, the GPU is not the bottleneck and increasing `max_batch_size` will not help.

### Video Memory Management

Large 4K videos can exhaust GPU memory during stereo generation. The tiling system splits frames into overlapping tiles processed independently, which bounds peak memory at the cost of some duplication at tile boundaries.

```bash
# Process a large video with tiling enabled
video2d3d convert large_video.mp4 --tile-size 512
```

### Profiling

The built-in profiler records per-component timing and can identify bottlenecks. Results include sorted component timings and automatic bottleneck detection based on a configurable threshold percentage of total time.

## Troubleshooting

### Common Issues

Most startup failures are environmental rather than logical. The following checklist covers the majority of reported problems:

```bash
# FFmpeg missing from PATH
which ffmpeg || echo "Install FFmpeg first"

# GPU not visible to PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# Model weights not downloaded
ls ~/.cache/torch/hub/checkpoints/

# Database locked by another process
ls uploads/data/auth.db*
```

### Reading the Logs

Logs are written to the `logs/` directory with daily rotation and gzip compression. Debug-level logging can be enabled through the configuration file or the `VIDEO2D3D_LOG_LEVEL` environment variable. The web API also emits structured request logs with request IDs that correlate API calls with internal processing stages, which is essential when diagnosing slow or failed jobs.

### Getting Help

When filing an issue, include the crash report JSON if one was generated, the relevant log excerpt, and the exact command that was run. Reproduction steps with a small input video dramatically reduce diagnosis time.

## Continuous Integration Pipeline

The CI pipeline runs on every pull request and consists of a linting stage followed by a test matrix. The lint stage is intentionally fast — it completes in under thirty seconds — so formatting mistakes are caught before expensive test jobs start. The test matrix runs the full suite on multiple Python versions in parallel, each with a thirty-minute timeout and a sixty-second per-test timeout to prevent hangs.

Test jobs publish a JUnit XML report and a coverage profile. The coverage profile is checked against a minimum threshold, so new code that ships without tests will fail the build even when all tests pass. Integration tests run in a separate job that is triggered manually or by schedule, since they depend on network access for model downloads.

### Writing Good Tests

Tests in this repository follow several conventions. Each test file mirrors a source file and lives under the same relative path in `tests/`. Fixtures are preferred over setup methods, and shared fixtures live in `tests/conftest.py`. Tests that exercise real image or video code paths should use the real OpenCV rather than mocks — the conftest falls back to mock modules only when the real package is unavailable.

When a test needs a video file, generate it programmatically with `cv2.VideoWriter` into a `tmp_path` fixture rather than committing binary fixtures to the repository. This keeps the checkout small and makes the test's assumptions explicit.

### Dependency Management

Runtime dependencies are pinned to major ranges in `requirements.txt`. Development-only tooling lives in `requirements-dev.txt`, which includes the runtime file. When upgrading a dependency, run the full test suite locally and watch for deprecation warnings — several libraries in the computer vision ecosystem change behavior in minor releases.

Optional heavy dependencies such as `onnxruntime` are required for specific features like Real-ESRGAN upscaling. The code imports them lazily and raises a helpful error message describing the installation command when they are missing.

## Concurrency Model

The converter supports three processing modes selected per workload. Multiprocessing sidesteps the Python GIL for CPU-bound work such as depth estimation on large frames. Threading is appropriate for I/O-bound stages like video writing where the underlying library releases the GIL. Sequential mode exists for debugging and for constrained environments where process spawning is unavailable.

Shared state is protected by locks in the components that accept work from multiple threads — the batch queue, the notification manager, and the preview window. These locks are reentrant so that public methods can safely compose other public methods on the same object. When adding new mutable state to these components, extend the existing lock rather than introducing a second one, as nested acquisitions of independent locks are a common source of deadlocks.

Background threads are daemonized so that a crashed main thread does not hang the process. Long-running loops check a stop event each iteration and exit promptly when shutdown is requested. The web application's lifespan handler stops the batch queue and shuts down crash reporting and notification managers in the reverse order of their initialization.

## Security Considerations

The web API performs authentication with JWTs. A default development secret is built in for local experimentation, but production deployments must set the `JWT_SECRET_KEY` environment variable — the server logs a prominent security warning when the default is in use. Access tokens are short-lived and refresh tokens are long-lived; both include a unique `jti` claim so that repeated logins always produce distinct tokens.

Uploaded files are stored under an ID-prefixed filename to prevent path traversal. File IDs are validated before any filesystem access, and requests containing traversal sequences are rejected with a validation error. Uploads are size-limited, and partial uploads are cleaned up when the limit is exceeded.

The SQLite database used for authentication is created with directory creation on first run. Back up the database alongside the uploads directory when migrating deployments.

## Deployment Notes

The repository includes Docker images for GPU and CPU deployments. The GPU image builds on a CUDA base and expects the NVIDIA container runtime; the CPU image is substantially smaller and suits evaluation deployments.

```bash
# Build the CPU image
docker build -f Dockerfile.cpu -t 2dto3d:cpu .

# Run with mounted volumes for inputs and outputs
docker run --rm -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/outputs:/app/outputs \
  2dto3d:cpu

# Follow the logs
docker logs -f $(docker ps -q --filter ancestor=2dto3d:cpu)
```

For Kubernetes deployments, the `k8s/` directory contains manifests with health probes wired to the `/health` endpoint. Configure resource requests conservatively: depth estimation is GPU-bound, and oversubscribing CPU limits causes more context switching than throughput gain.

## Release Process

Releases cut from `main` after CI passes. The version string lives in the package `__init__` and is surfaced in the CLI banner, the API health endpoint, and the documentation footer — update all occurrences in the same commit. Release notes should list user-visible changes, known issues, and any configuration migrations required.

## Module Deep Dives

### Video Module Internals

The video module wraps FFmpeg and OpenCV behind a consistent Python interface. `FrameExtractor` implements the iterator protocol, yielding `(frame_number, frame)` tuples so callers can process frames lazily without loading an entire video into memory. It supports three sampling strategies: extracting every frame, extracting at a fixed interval, or uniform sampling to a target count. Frame indices are computed once and cached, and a bounded frame buffer smooths out bursts of downstream demand.

`VideoWriter` manages the FFmpeg subprocess lifecycle. It builds the encoder command from a `VideoWriterConfig`, validates dimensions and FPS before starting the process, and streams frames to the process's stdin. Progress callbacks fire per frame, and statistics such as elapsed time and frames per second are accumulated in a `WriterStats` object. Audio from an optional source video can be copied onto the output without re-encoding.

### Depth Module Internals

`DepthMapProcessor` composes individual operations — normalization, smoothing, hole filling, and edge enhancement — into a pipeline. Each operation is a small, independently testable function; the pipeline applies them in a documented order and validates the value range between stages. The `TemporalSmoother` operates across frames rather than within one, implementing exponential moving average, sliding window, and optical-flow-guided variants. Its state carries the previous depth map and a bounded history deque, and `reset()` clears it between video sequences.

Model selection is handled by `DepthModelSelector`, which maps scene classifications to a primary model and an ordered fallback chain. When a model fails to load or produces an inference error, the selector advances through the chain before giving up. Callers that explicitly select a model bypass automatic selection entirely.

### Stereo Generation Internals

The `DIBREngine` performs depth-image-based rendering: it warps the source frame using the depth map, synthesizes the left and right views, and fills disocclusion holes using a background-extension strategy. The configuration controls convergence distance, field of view, and hole-filling aggressiveness. Disparity maps can be exported alongside the stereo pair for debugging, and the anaglyph and side-by-side encoders share the same intermediate views.

### Web API Design

The API follows resource-oriented conventions with a versioned prefix. Routers are registered per resource and include explicit response models, so the generated OpenAPI document is accurate. Exception handlers translate internal errors into a consistent JSON error envelope containing an error code, a human-readable message, and a request ID. Rate limiting is applied per endpoint category through decorators backed by `slowapi`, and the limiter instance lives in application state.

## Extending the System

### Adding a Depth Model

New depth models implement the estimator interface: `load_model`, `estimate_depth`, and the context-manager protocol for cleanup. Register the model in the `DepthModelType` enum and add a branch in the selector's estimator factory. Add an integration test that exercises the model with a mocked torch backend so the CI matrix does not require GPU hardware.

### Adding a CLI Command

Commands are plain functions decorated with `@app.command` on the Typer application in `cli.py`. Prefer composing existing service functions over embedding logic in the command body, and return a non-zero exit code through `typer.Exit` on failure. Console output uses Rich markup for consistent color and alignment across commands.

### Adding a Configuration Option

Add the field to the relevant dataclass with a sensible default, surface it in `default.yaml`, and validate it in `__post_init__` if it has invariants. Export and import round-trip through `to_dict` and `from_dict`, so no extra work is needed for persistence — but do add a test covering the new field's parsing.

## Coding Guidelines

### Naming Conventions

Classes use PascalCase, modules use lowercase with underscores, and constants use uppercase with underscores. Private methods are prefixed with a single underscore. Enum members use uppercase and their values are lowercase strings, which keeps log output readable. When a class has both a configuration dataclass and an implementation class, name them `ThingConfig` and `Thing` respectively so the pairing is obvious in imports.

### Documentation Style

Every module starts with a docstring describing its purpose and its role in the larger pipeline. Public functions include Google-style docstrings covering arguments, return values, and raised exceptions. Inline comments explain *why*, not *what* — the code already says what it does. When a workaround for a third-party library is required, link the relevant issue or changelog entry so future maintainers can evaluate removing it.

### Commit Discipline

Commits follow the conventional commit format: a type prefix such as `fix`, `feat`, or `ci`, a short imperative summary, and a body explaining the motivation when the summary is insufficient. Each commit should leave the tree in a state where the test suite passes. Rebase onto the latest `main` before opening a pull request rather than merging, which keeps the history linear and bisectable.

### Review Expectations

Pull requests should be scoped to a single concern. A change that fixes a bug and refactors the surrounding module is harder to review and revert than two separate changes. Reviewers look for correctness first, then test coverage, then readability. Disagreements about style are resolved by the configured tooling rather than in review comments.

## Additional Resources

- [User Guide](USER_GUIDE.md) - End-user documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server running)
- [GitHub Repository](https://github.com/automaker/2dto3d) - Source code and issues

---

*This developer guide is for 2Dto3D Video Converter version 0.1.0*
