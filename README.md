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

## Docker Deployment

Docker images are available for easy deployment with GPU or CPU support.

### Prerequisites

**For GPU support:**
- Docker 19.03+
- NVIDIA Driver 470+
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

**For CPU-only:**
- Docker 19.03+

### Quick Start with Docker

```bash
# Build the image (choose GPU or CPU)
docker build -t video2d3d:gpu -f Dockerfile .
docker build -t video2d3d:cpu -f Dockerfile.cpu .
```

### Running the API Server

```bash
# GPU mode
docker run --gpus all -p 8000:8000 \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:gpu serve

# CPU mode
docker run -p 8000:8000 \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:cpu serve
```

### Using Docker Compose

```bash
# GPU deployment
docker-compose up -d

# CPU-only deployment
docker-compose -f docker-compose.cpu.yml up -d

# With API profile
docker-compose --profile api up -d

# With batch processing profile
docker-compose --profile batch up -d
```

### Docker Volumes

| Volume | Purpose |
|--------|---------|
| `./inputs:/app/inputs` | Input video files (read-only) |
| `./outputs:/app/outputs` | Converted 3D videos (read-write) |
| `./models:/app/models` | Pre-trained model cache |
| `./logs:/app/logs` | Application logs |
| `./config:/app/config` | Configuration files |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO2D3D_ENV` | `production` | Environment (development/production) |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device IDs |
| `VIDEO2D3D_LOG_LEVEL` | `INFO` | Logging level |
| `BATCH_SIZE` | `4` | Processing batch size |
| `NUM_WORKERS` | `4` | Number of worker processes |
| `API_PORT` | `8000` | API server port |

### Single Video Conversion

```bash
docker run --gpus all \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:gpu convert /app/inputs/video.mp4 /app/outputs/video_3d.mp4
```

### Batch Processing

```bash
docker run --gpus all \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:gpu batch-convert /app/inputs --output-dir /app/outputs
```
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
