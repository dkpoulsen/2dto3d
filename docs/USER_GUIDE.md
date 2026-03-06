# 2Dto3D Video Converter - User Guide

**Version:** 0.1.0  
**Last Updated:** March 2026

> **⚠️ Development Status**: This project is under active development. The core video conversion functionality is currently a placeholder while the infrastructure (CLI, API, batch processing, configuration) is fully functional. API endpoints and batch processing are operational and ready for integration.
## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Command Line Interface (CLI)](#command-line-interface-cli)
5. [Web API](#web-api)
6. [Docker Deployment](#docker-deployment)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)

---

## Introduction

2Dto3D Video Converter is a powerful tool that converts standard 2D videos into immersive 3D stereoscopic videos using state-of-the-art deep learning depth estimation models.

### Key Features

- **AI-Powered Depth Estimation**: Uses advanced neural networks (MiDaS, DPT, AdaBins) to generate accurate depth maps from 2D footage
- **Multiple 3D Output Formats**: Supports side-by-side, anaglyph, interlaced, and VR formats
- **GPU Acceleration**: CUDA support for fast video processing
- **Batch Processing**: Process multiple videos with queue management and folder watching
- **REST API**: Full-featured API for integration with other applications
- **Flexible Configuration**: YAML-based configuration for all processing parameters
- **Error Recovery**: Automatic retry with configurable backoff strategies

### Supported Input Formats

- MP4, AVI, MOV, MKV, WebM, FLV

### Supported 3D Output Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| `side_by_side` | Left-right stereoscopic view | VR headsets, 3D TVs |
| `anaglyph` | Red-cyan color separation | Standard 3D glasses |
| `interlaced` | Row-alternating | Passive 3D displays |
| `vr` | Over-under format | VR applications |

---

## Installation

### Prerequisites

- **Python 3.9+** (3.10 or 3.11 recommended)
- **FFmpeg** - Required for video processing
- **CUDA-compatible GPU** (optional, but recommended for performance)

### Step 1: Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the archive
3. Add the `bin` directory to your system PATH

Verify installation:
```bash
ffmpeg -version
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/automaker/2dto3d.git
cd 2dto3d
```

### Step 3: Create Virtual Environment

**Using venv:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# On Windows: .venv\Scripts\activate
```

**Using conda:**
```bash
conda create -n video2d3d python=3.10
conda activate video2d3d
```

### Step 4: Install Dependencies

**For basic usage:**
```bash
pip install -r requirements.txt
pip install -e .
```

**For development:**
```bash
pip install -r requirements-dev.txt
pip install -e .
```

**For web API support:**
```bash
pip install -e ".[web]"
```

### Step 5: Verify Installation

```bash
video2d3d --version
video2d3d info
```

---

## Configuration

Configuration is managed via YAML files in the `config/` directory:

| File | Purpose |
|------|---------|
| `default.yaml` | Default settings (base configuration) |
| `development.yaml` | Development environment overrides |
| `production.yaml` | Production environment overrides |

### Setting the Environment

```bash
export VIDEO2D3D_ENV=production  # or development
```

### Custom Configuration Path

```bash
export VIDEO2D3D_CONFIG_PATH=/path/to/custom/config.yaml
```

### Key Configuration Sections

#### Processing Settings

```yaml
processing:
  batch_size: 4              # Frames to process per batch
  num_workers: 4             # Parallel worker threads
  use_gpu: true              # Enable GPU acceleration
  gpu_device: -1             # -1 for auto-select, 0 for first GPU
  max_memory_percent: 80     # Memory usage limit
  mixed_precision: true      # Faster processing with FP16
  auto_batch_size: true      # Adjust batch size based on GPU memory
  min_batch_size: 1          # Minimum batch size when auto-adjusting
  max_batch_size: 32         # Maximum batch size when auto-adjusting
  memory_fraction: 0.8       # Maximum fraction of GPU memory to use
  fallback_to_cpu: true      # Use CPU if GPU fails
  cudnn_benchmark: true      # Enable cuDNN benchmark for optimal kernels
```
#### Depth Estimation

```yaml
depth_estimation:
  model: midas_small         # Options: midas_small, midas_hybrid, dpt_large, dpt_hybrid, adabins_nyu, adabins_kitti
  model_path: ""             # Custom model path (optional)
  auto_download: true        # Download model if not found
  output_width: 384          # Depth map resolution
  output_height: 384
  min_depth: 0.0             # Depth range normalization
  max_depth: 1.0
  temporal_consistency: true # Smooth depth across frames
  temporal_smoothing_factor: 0.5
  
  # Model selector for advanced use
  model_selector:
    primary_model: adabins_nyu
    fallback_model: midas_small
    enable_auto_fallback: true
```

#### Depth Processing

```yaml
depth_processing:
  edge_aware_smoothing: true
  smoothing_radius: 3
  bilateral_filter: true
  bilateral_sigma_color: 0.1
  bilateral_sigma_space: 5
  hole_filling: true
  hole_filling_method: "inpaint"  # Options: inpaint, nearest, linear
```
#### Stereo Generation

```yaml
stereo_generation:
  format: side_by_side       # Output format
  baseline: 0.05             # Camera separation (normalized)
  focal_length: 1.0          # Virtual focal length
  convergence: 0.5           # Convergence plane
```

#### Video Output

```yaml
video_output:
  format: mp4
  codec: libx264
  preset: medium             # ultrafast to veryslow
  crf: 23                    # Quality (0-51, lower = better)
```

#### Web API

```yaml
web_api:
  enabled: false
  host: "0.0.0.0"
  port: 8000
  prefix: "/api/v1"
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"
  max_upload_size: 500       # MB
  upload_dir: "uploads"
  
  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60
    requests_per_hour: 1000
    upload_requests_per_minute: 10
    storage_uri: "memory://"
    whitelist_ips: []
```

#### Batch Queue

```yaml
batch_queue:
  max_concurrent_jobs: 1
  auto_start: true
  retry_failed: true
  max_retries: 3
  retry_delay_seconds: 5.0
  job_timeout_seconds: 3600
  output_naming_pattern: "{name}_3d{ext}"
  skip_existing: true
  save_state: true
  state_file: "logs/batch_queue_state.json"
```

#### Error Recovery

```yaml
error_recovery:
  max_retries: 3
  retry_delay_seconds: 0.1
  backoff_factor: 2.0
  max_retry_delay_seconds: 30.0
  backoff_strategy: exponential  # Options: fixed, linear, exponential, fibonacci
  enable_cpu_fallback: true
  skip_on_max_retries: false
```
### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO2D3D_ENV` | `development` | Environment name |
| `VIDEO2D3D_CONFIG_PATH` | - | Custom config file path |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device IDs |
| `VIDEO2D3D_LOG_LEVEL` | `INFO` | Logging level |

---

## Command Line Interface (CLI)

### Global Options

```bash
video2d3d [OPTIONS] COMMAND [ARGS]

Options:
  --version, -v     Show version and exit
  --verbose         Enable DEBUG level logging
  --log-level TEXT  Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  --log-file TEXT   Custom log file path
```

### Convert Command

Convert a single 2D video to 3D:

```bash
video2d3d convert INPUT_FILE OUTPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE` - Path to input 2D video (required)
- `OUTPUT_FILE` - Path to output 3D video (required)

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--format, -f` | `side_by_side` | 3D output format |
| `--model, -m` | `midas_small` | Depth estimation model |
| `--gpu/--no-gpu` | `--gpu` | Enable/disable GPU |
| `--preview, -p` | `false` | Show live preview during processing |
| `--no-progress` | `false` | Disable progress display |
| `--config, -c` | - | Custom config file path |

**Examples:**

```bash
# Basic conversion
video2d3d convert input.mp4 output_3d.mp4

# Convert to anaglyph format
video2d3d convert input.mp4 output_anaglyph.mp4 --format anaglyph

# Use DPT Large model for best quality
video2d3d convert input.mp4 output.mp4 --model dpt_large

# CPU-only processing with preview
video2d3d convert input.mp4 output.mp4 --no-gpu --preview

# Custom configuration
video2d3d convert input.mp4 output.mp4 --config ./my_config.yaml
```

> **⚠️ Note**: The `convert` command currently runs as a placeholder. The full video conversion implementation is in development. The API server and batch processing infrastructure are fully operational.
### Batch Convert Command

Process multiple videos:

```bash
video2d3d batch-convert INPUT [OPTIONS]
```

**Arguments:**
- `INPUT` - File path, directory, or wildcard pattern

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--output-dir, -o` | - | Output directory |
| `--pattern, -p` | - | Wildcard pattern (e.g., `*.mp4`) |
| `--recursive/--no-recursive` | `--recursive` | Search subdirectories |
| `--format, -f` | `side_by_side` | Output format |
| `--model, -m` | `midas_small` | Depth model |
| `--concurrent, -c` | `1` | Number of concurrent jobs |
| `--skip-existing/--no-skip-existing` | `--skip-existing` | Skip existing outputs |
| `--watch, -w` | `false` | Watch for new files |
| `--list, -l` | - | File containing video paths |

**Examples:**

```bash
# Convert all videos in a directory
video2d3d batch-convert ./videos --output-dir ./output

# Process with pattern matching
video2d3d batch-convert ./videos --pattern "*.mp4" --output-dir ./output

# Process from a file list
video2d3d batch-convert --list videos.txt --output-dir ./output

# Watch mode (continuous processing)
video2d3d batch-convert ./videos --watch --output-dir ./output

# High-performance batch processing
video2d3d batch-convert ./videos --concurrent 4 --model midas_small
```

### Queue Status Command

Monitor batch processing queue:

```bash
video2d3d queue-status [OPTIONS]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--state-file, -s` | `logs/batch_queue_state.json` | Queue state file |
| `--watch, -w` | `false` | Continuous monitoring |
| `--clear` | `false` | Clear completed jobs |

**Examples:**

```bash
# Check queue status
video2d3d queue-status

# Monitor continuously
video2d3d queue-status --watch
```

### List Models Command

Display available depth estimation models:

```bash
video2d3d list-models
```

**Output:**
| Model | Description | Quality | Speed |
|-------|-------------|---------|-------|
| `midas_small` | MiDaS v2.1 Small - Fast, good for preview | Medium | Fast |
| `midas_hybrid` | MiDaS v3.1 Hybrid - Balanced quality/speed | Good | Medium |
| `dpt_large` | DPT Large - Highest quality | Best | Slow |
| `dpt_hybrid` | DPT Hybrid - Good quality, faster than large | Good | Medium |
| `adabins_nyu` | AdaBins NYU - Best for indoor scenes | Best | Slow |
| `adabins_kitti` | AdaBins KITTI - Best for outdoor scenes | Best | Slow |

> **Note**: The default model is configured as `midas_small` for fast preview. For production use, consider `adabins_nyu` (indoor) or `adabins_kitti` (outdoor) for best quality.
### List Formats Command

Display available 3D output formats:

```bash
video2d3d list-formats
```

### Info Command

Display system information and configuration:

```bash
video2d3d info
```

### Serve Command

Start the REST API server:

```bash
video2d3d serve [OPTIONS]
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `--host, -h` | `0.0.0.0` | Server host |
| `--port, -p` | `8000` | Server port |
| `--reload, -r` | `false` | Auto-reload (development) |
| `--workers, -w` | `1` | Worker processes |
| `--log-level, -l` | `info` | Server log level |

**Examples:**

```bash
# Start server on default port
video2d3d serve

# Development mode with auto-reload
video2d3d serve --reload

# Production with multiple workers
video2d3d serve --workers 4 --port 8080
```

---

## Web API

### Starting the Server

```bash
video2d3d serve --host 0.0.0.0 --port 8000
```

### API Documentation

Once the server is running, access the interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v1/spec

### API Endpoints

#### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "queue_running": true,
  "gpu_available": true
}
```

#### Detailed Health Check

```http
GET /health/detailed
```

Returns comprehensive health information including GPU status, memory usage, and queue statistics.

#### Upload Video

```http
POST /api/v1/upload/
Content-Type: multipart/form-data

file: <video_file>
```

**Response:**
```json
{
  "file_id": "abc123",
  "filename": "video.mp4",
  "size_bytes": 104857600,
  "upload_url": "/api/v1/upload/abc123"
}
```

#### Submit Job

```http
POST /api/v1/jobs/
Content-Type: application/json

{
  "input_file_id": "abc123",
  "output_filename": "video_3d.mp4",
  "priority": "normal",
  "config": {
    "stereo_format": "side_by_side",
    "depth_model": "midas_small",
    "use_gpu": true,
    "quality_preset": "balanced"
  },
  "callback_url": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "job_id": "job_123",
  "status": "pending",
  "message": "Job submitted successfully",
  "status_url": "/api/v1/jobs/job_123"
}
```

#### Get Job Status

```http
GET /api/v1/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "job_123",
  "status": "running",
  "priority": "normal",
  "input_filename": "video.mp4",
  "output_filename": "video_3d.mp4",
  "progress": 45.5,
  "current_stage": "depth_estimation",
  "created_at": "2026-03-06T10:00:00Z",
  "started_at": "2026-03-06T10:00:05Z",
  "elapsed_time_seconds": 120,
  "estimated_remaining_seconds": 150
}
```

#### List Jobs

```http
GET /api/v1/jobs/?status=running&page=1&page_size=50
```

#### Cancel Job

```http
POST /api/v1/jobs/{job_id}/cancel
```

#### Retry Job

```http
POST /api/v1/jobs/{job_id}/retry
```
#### Remove Job

```http
DELETE /api/v1/jobs/{job_id}
```

Removes a completed, failed, or cancelled job from the queue. Cannot remove running jobs.

#### Batch Submit Jobs

```http
POST /api/v1/jobs/batch
Content-Type: application/json

{
  "input_file_ids": ["abc123", "def456"],
  "priority": "normal",
  "config": {
    "stereo_format": "side_by_side",
    "depth_model": "midas_small"
  }
}
```

Submit multiple conversion jobs in a single request.

#### Download Result

```http
GET /api/v1/queue
```

**Response:**
```json
{
  "total_jobs": 10,
  "pending_jobs": 2,
  "running_jobs": 1,
  "completed_jobs": 6,
  "failed_jobs": 1,
  "cancelled_jobs": 0,
  "skipped_jobs": 0,
  "success_rate_percent": 85.7,
  "total_frames_processed": 15000,
  "total_processing_time_seconds": 3600,
  "average_processing_time_seconds": 120
}
```

#### Detailed Queue Statistics

```http
GET /api/v1/jobs/stats/queue
```

Returns detailed queue statistics from the jobs router, including processing metrics.
### API Rate Limiting

The API implements rate limiting:

| Endpoint Type | Limit |
|--------------|-------|
| General API | 60 requests/minute |
| File Upload | 10 requests/minute |
| Hourly Limit | 1000 requests/hour |

Rate limit headers are included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

### Using curl

```bash
# Upload a video
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"

# Submit a job
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "input_file_id": "abc123",
    "config": {
      "stereo_format": "side_by_side",
      "depth_model": "midas_small"
    }
  }'

# Check job status
curl "http://localhost:8000/api/v1/jobs/job_123"

# Download result
curl -O "http://localhost:8000/api/v1/download/xyz789"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Upload video
with open("video.mp4", "rb") as f:
    response = requests.post(f"{BASE_URL}/upload/", files={"file": f})
    file_id = response.json()["file_id"]

# Submit job
response = requests.post(
    f"{BASE_URL}/jobs/",
    json={
        "input_file_id": file_id,
        "config": {
            "stereo_format": "side_by_side",
            "depth_model": "midas_small"
        }
    }
)
job_id = response.json()["job_id"]

# Poll for completion
import time
while True:
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    status = response.json()["status"]
    if status in ["completed", "failed", "cancelled"]:
        break
    time.sleep(5)

# Download result
result = requests.get(f"{BASE_URL}/download/{response.json()['result']['output_file_id']}")
with open("output_3d.mp4", "wb") as f:
    f.write(result.content)
```

---

## Docker Deployment

### Prerequisites

**For GPU support:**
- Docker 19.03+
- NVIDIA Driver 470+
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

**For CPU-only:**
- Docker 19.03+

### Building Images

```bash
# GPU-enabled image
docker build -t video2d3d:gpu -f Dockerfile .

# CPU-only image
docker build -t video2d3d:cpu -f Dockerfile.cpu .
```

### Running Containers

**Single video conversion (GPU):**
```bash
docker run --gpus all \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:gpu convert /app/inputs/video.mp4 /app/outputs/video_3d.mp4
```

**Single video conversion (CPU):**
```bash
docker run \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:cpu convert /app/inputs/video.mp4 /app/outputs/video_3d.mp4
```

**API Server (GPU):**
```bash
docker run --gpus all -p 8000:8000 \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/models:/app/models \
  video2d3d:gpu serve
```

**Batch processing:**
```bash
docker run --gpus all \
  -v $(pwd)/inputs:/app/inputs \
  -v $(pwd)/outputs:/app/outputs \
  video2d3d:gpu batch-convert /app/inputs --output-dir /app/outputs
```

### Docker Compose

**GPU deployment:**
```bash
docker-compose up -d
```

**CPU-only deployment:**
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

**With API profile:**
```bash
docker-compose --profile api up -d
```

**With batch processing profile:**
```bash
docker-compose --profile batch up -d
```

### Volume Mounts

| Volume | Purpose |
|--------|---------|
| `./inputs:/app/inputs` | Input video files |
| `./outputs:/app/outputs` | Converted 3D videos |
| `./models:/app/models` | Pre-trained model cache |
| `./logs:/app/logs` | Application logs |
| `./config:/app/config` | Configuration files |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO2D3D_ENV` | `production` | Environment mode |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU device IDs |
| `VIDEO2D3D_LOG_LEVEL` | `INFO` | Logging level |
| `BATCH_SIZE` | `4` | Processing batch size |
| `NUM_WORKERS` | `4` | Worker processes |
| `API_PORT` | `8000` | API server port |

---

## Troubleshooting

### Common Issues

#### 1. "FFmpeg not found"

**Symptom:** Error message about FFmpeg not being installed or not in PATH.

**Solution:**
```bash
# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows - add FFmpeg to PATH
```

Verify:
```bash
ffmpeg -version
```

#### 2. "CUDA out of memory"

**Symptom:** GPU memory errors during processing.

**Solutions:**

1. Reduce batch size:
```bash
video2d3d convert input.mp4 output.mp4 --config config_low_mem.yaml
```

2. Enable auto batch sizing (in config):
```yaml
processing:
  auto_batch_size: true
  min_batch_size: 1
  memory_fraction: 0.6
```

3. Use CPU fallback:
```bash
video2d3d convert input.mp4 output.mp4 --no-gpu
```

#### 3. "Model download failed"

**Symptom:** Unable to download depth estimation models.

**Solution:**
1. Check internet connection
2. Download models manually to `models/` directory
3. Use a smaller model:
```bash
video2d3d convert input.mp4 output.mp4 --model midas_small
```

#### 4. "Permission denied" errors

**Symptom:** Cannot write to output directory.

**Solution:**
```bash
# Check permissions
ls -la outputs/

# Fix permissions
chmod 755 outputs/
```

#### 5. "ImportError: No module named 'video2d3d'"

**Symptom:** Python cannot find the module.

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall
pip install -e .
```

#### 6. Slow processing

**Symptom:** Video conversion takes too long.

**Solutions:**

1. Enable GPU:
```bash
video2d3d convert input.mp4 output.mp4 --gpu
```

2. Use faster model:
```bash
video2d3d convert input.mp4 output.mp4 --model midas_small
```

3. Reduce output resolution (in config):
```yaml
depth_estimation:
  output_width: 256
  output_height: 256
```

#### 7. Queue not starting

**Symptom:** Jobs stuck in pending state.

**Solution:**
1. Check queue status:
```bash
video2d3d queue-status
```

2. Verify GPU availability:
```bash
nvidia-smi
```

3. Check logs:
```bash
tail -f logs/video2d3d.log
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
video2d3d --verbose convert input.mp4 output.mp4
```

Or:
```bash
VIDEO2D3D_LOG_LEVEL=DEBUG video2d3d convert input.mp4 output.mp4
```

### Checking GPU Status

```bash
# NVIDIA GPU
nvidia-smi

# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### Log Files

Logs are stored in `logs/video2d3d.log` by default.

```bash
# View recent logs
tail -f logs/video2d3d.log

# Search for errors
grep -i error logs/video2d3d.log
```

---

## Best Practices

### Choosing the Right Model

| Use Case | Recommended Model | Reason |
|----------|------------------|--------|
| Quick preview | `midas_small` | Fastest processing |
| General use | `midas_hybrid` | Good balance |
| High quality (indoor) | `adabins_nyu` | Best for indoor scenes |
| High quality (outdoor) | `adabins_kitti` | Best for outdoor scenes |
| High quality (general) | `dpt_large` | Best depth accuracy |
| Medium quality, good speed | `dpt_hybrid` | Quality with reasonable speed |
### Optimizing Performance

1. **Use GPU when available** - 10-50x faster than CPU
2. **Enable mixed precision** - Faster with minimal quality loss
3. **Adjust batch size** - Larger batches are more efficient on GPU
4. **Use appropriate resolution** - Higher resolution = slower processing

### Recommended Settings by Use Case

**Quick Testing:**
```yaml
depth_estimation:
  model: midas_small
  output_width: 256
  output_height: 256

processing:
  batch_size: 8
```

**Production Quality (Indoor):**
```yaml
depth_estimation:
  model: adabins_nyu
  output_width: 384
  output_height: 384
  temporal_consistency: true

processing:
  batch_size: 4
  mixed_precision: true

video_output:
  preset: slow
  crf: 18
```

**Production Quality (Outdoor):**
```yaml
depth_estimation:
  model: adabins_kitti
  output_width: 384
  output_height: 384
  temporal_consistency: true

processing:
  batch_size: 4
  mixed_precision: true

video_output:
  preset: slow
  crf: 18
```

**Fast Processing:**
```yaml
depth_estimation:
  model: midas_small
  temporal_consistency: false

processing:
  batch_size: 16
  auto_batch_size: true

video_output:
  preset: fast
  crf: 28
```

### Batch Processing Tips

1. **Use `--skip-existing`** to avoid reprocessing
2. **Set appropriate concurrency** based on GPU memory
3. **Use watch mode** for automated workflows
4. **Monitor with `queue-status`** during large batches

### Storage Recommendations

1. **Input videos**: Fast SSD storage
2. **Output directory**: Sufficient space (3D videos can be larger)
3. **Model cache**: Persistent volume for Docker deployments

### Security Considerations

1. **API in production**: Use reverse proxy with TLS
2. **Rate limiting**: Enable for public deployments
3. **File validation**: Input files are validated automatically
4. **Resource limits**: Set memory limits for containers

---

## FAQ

### General Questions

**Q: What video resolutions are supported?**

A: The tool supports resolutions up to 4K (3840x2160). Higher resolutions require more GPU memory and processing time.

**Q: How long does conversion take?**

A: Processing time depends on:
- Video length and resolution
- Selected depth model
- GPU vs CPU processing
- Batch size settings

Typical speeds (1080p video, GPU):
- `midas_small`: ~2-5x realtime
- `dpt_large`: ~0.5-1x realtime

**Q: Can I process multiple videos at once?**

A: Yes, use `batch-convert` command or submit multiple jobs via the API.

**Q: What are the system requirements?**

A: Minimum:
- 8GB RAM
- 10GB disk space
- Python 3.9+

Recommended:
- 16GB+ RAM
- NVIDIA GPU with 8GB+ VRAM
- SSD storage

### Technical Questions

**Q: How does depth estimation work?**

A: The tool uses deep neural networks trained on stereo image pairs to predict depth from single images. These depth maps are then used to generate stereoscopic views.

**Q: Can I use my own depth model?**

A: Yes, specify a custom model path in configuration:
```yaml
depth_estimation:
  model_path: /path/to/custom/model.pt
```

**Q: Why is my output video larger than input?**

A: 3D videos contain two views (left and right), which can double the file size. Use higher CRF values for compression:
```yaml
video_output:
  crf: 28  # Higher = smaller file, lower quality
```

**Q: How do I improve depth quality?**

A: 
1. Use a higher-quality model (`dpt_large`)
2. Increase depth resolution
3. Enable temporal consistency
4. Use edge-aware smoothing

### Troubleshooting Questions

**Q: Why is my video not recognized?**

A: Ensure the format is supported (MP4, AVI, MOV, MKV, WebM) and FFmpeg can decode it:
```bash
ffmpeg -i your_video.mp4
```

**Q: Why does processing stop midway?**

A: Check:
1. GPU memory (reduce batch size)
2. Disk space
3. Log files for errors

**Q: How do I report bugs?**

A: Open an issue on GitHub with:
- Command used
- Error message
- Log file excerpt
- System information (`video2d3d info`)

---

## Getting Help

- **Documentation**: [GitHub Repository](https://github.com/automaker/2dto3d)
- **Issues**: [GitHub Issues](https://github.com/automaker/2dto3d/issues)
- **API Documentation**: http://localhost:8000/docs (when server is running)

---

*This user guide is for 2Dto3D Video Converter version 0.1.0*
