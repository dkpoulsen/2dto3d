# =============================================================================
# 2Dto3D Video Converter - GPU Docker Image
# =============================================================================
# Multi-stage build for optimized GPU-enabled Docker image
# Supports NVIDIA CUDA for deep learning acceleration
#
# Build: docker build -t video2d3d:gpu -f Dockerfile .
# Run:   docker run --gpus all -v $(pwd)/inputs:/app/inputs -v $(pwd)/outputs:/app/outputs video2d3d:gpu
# =============================================================================

# Build arguments for version pinning
ARG PYTHON_VERSION=3.10
ARG CUDA_VERSION=12.1.0
ARG UBUNTU_VERSION=22.04
ARG TORCH_VERSION=2.1.0
ARG TORCHVISION_VERSION=0.16.0
ARG CUDA_TAG=cu121

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build
# -----------------------------------------------------------------------------
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS builder

# Re-declare ARGs after FROM
ARG PYTHON_VERSION
ARG TORCH_VERSION
ARG TORCHVISION_VERSION
ARG CUDA_TAG

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA support first (largest dependency)
RUN pip install --no-cache-dir \
    torch==${TORCH_VERSION}+${CUDA_TAG} \
    torchvision==${TORCHVISION_VERSION}+${CUDA_TAG} \
    --index-url https://download.pytorch.org/whl/${CUDA_TAG}

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and install package
COPY pyproject.toml setup.py README.md ./
COPY src/ ./src/
COPY config/ ./config/
RUN pip install --no-cache-dir -e .

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION} AS runtime

# Re-declare ARGs after FROM
ARG PYTHON_VERSION

# Labels for container metadata
LABEL maintainer="Automaker <support@automaker.dev>"
LABEL org.opencontainers.image.title="2Dto3D Video Converter"
LABEL org.opencontainers.image.description="Convert 2D videos to 3D using deep learning depth estimation with GPU support"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/automaker/2dto3d"
LABEL org.opencontainers.image.licenses="MIT"

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies only (smaller image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    ffmpeg \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set Python as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1

# Create non-root user for security
RUN groupadd -r video2d3d && useradd -r -g video2d3d video2d3d

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    VIDEO2D3D_ENV=production \
    CUDA_VISIBLE_DEVICES=0

# Create application directories
WORKDIR /app
RUN mkdir -p /app/inputs /app/outputs /app/logs /app/models /app/config \
    && chown -R video2d3d:video2d3d /app

# Copy application code
COPY --chown=video2d3d:video2d3d src/ /app/src/
COPY --chown=video2d3d:video2d3d config/ /app/config/
COPY --chown=video2d3d:video2d3d pyproject.toml setup.py README.md ./
COPY --chown=video2d3d:video2d3d .env.example /app/.env.example

# Copy entrypoint and healthcheck scripts
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/healthcheck.sh /healthcheck.sh
RUN chmod +x /entrypoint.sh /healthcheck.sh

# Switch to non-root user
USER video2d3d

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /healthcheck.sh || exit 1

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command: show help
CMD ["video2d3d", "--help"]
