# 2Dto3D Video Converter

Convert 2D videos to 3D using deep learning depth estimation.

## Features

- **Depth Estimation**: Uses state-of-the-art deep learning models (MiDaS, DPT) for accurate depth prediction
- **Multiple 3D Formats**: Supports side-by-side, anaglyph, interlaced, and VR output formats
- **GPU Acceleration**: CUDA support for fast processing
- **Batch Processing**: Process multiple videos efficiently
- **Configurable**: YAML-based configuration for all processing parameters

## Requirements

- Python 3.9 or higher
- FFmpeg (installed and in PATH)
- CUDA-compatible GPU (recommended, but CPU processing is supported)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/automaker/2dto3d.git
cd 2dto3d
```

### 2. Create virtual environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using conda
conda create -n video2d3d python=3.10
conda activate video2d3d
```

### 3. Install dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Or install with development tools
pip install -r requirements-dev.txt

# Or install in editable mode
pip install -e .
```

### 4. Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

## Quick Start

### Command Line Interface

```bash
# Show help
video2d3d --help

# Convert a video to side-by-side 3D
video2d3d convert input.mp4 output_3d.mp4 --format side_by_side

# Convert to anaglyph 3D (red-cyan glasses)
video2d3d convert input.mp4 output_anaglyph.mp4 --format anaglyph

# Use a specific model
video2d3d convert input.mp4 output.mp4 --model dpt_large

# CPU-only processing
video2d3d convert input.mp4 output.mp4 --no-gpu
```

### Python API

```python
from video2d3d.utils.config import load_config
from video2d3d.video import VideoProcessor

# Load configuration
config = load_config(environment="production")

# Process a video
processor = VideoProcessor(config)
processor.convert("input.mp4", "output_3d.mp4")
```

## Configuration

Configuration is managed via YAML files in the `config/` directory:

- `default.yaml` - Default settings
- `development.yaml` - Development environment overrides
- `production.yaml` - Production environment overrides

Set the environment with the `VIDEO2D3D_ENV` environment variable:

```bash
export VIDEO2D3D_ENV=production  # or development
```

### Key Configuration Options

```yaml
# config/default.yaml

processing:
  batch_size: 4
  use_gpu: true
  num_workers: 4

depth_estimation:
  model: midas_small
  output_width: 384
  output_height: 384

stereo_generation:
  format: side_by_side
  baseline: 0.05
```

## Project Structure

```
2dto3d/
├── config/                 # Configuration files
│   ├── default.yaml
│   ├── development.yaml
│   └── production.yaml
├── src/video2d3d/         # Source code
│   ├── __init__.py
│   ├── cli.py             # Command-line interface
│   ├── core/              # Core functionality
│   ├── video/             # Video I/O handling
│   ├── depth/             # Depth estimation
│   ├── stereo/            # Stereoscopic generation
│   └── utils/             # Utilities
├── tests/                  # Test suite
├── models/                 # Pre-trained models (downloaded)
├── inputs/                 # Input videos
├── outputs/                # Output videos
├── logs/                   # Log files
├── docs/                   # Documentation
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.py               # Package setup
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=video2d3d --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Available Models

| Model | Description | Quality | Speed |
|-------|-------------|---------|-------|
| midas_small | MiDaS v2.1 Small | Medium | Fast |
| midas_hybrid | MiDaS v3.1 Hybrid | Good | Medium |
| dpt_large | DPT Large | Best | Slow |
| dpt_hybrid | DPT Hybrid | Good | Medium |

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
