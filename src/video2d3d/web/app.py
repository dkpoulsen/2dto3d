"""FastAPI application factory and configuration.

This module creates and configures the FastAPI application with:
- CORS middleware
- Exception handlers
- Request ID middleware
- API routers
- Lifecycle management for the batch queue
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from video2d3d import __version__
from video2d3d.batch import BatchQueueConfig, BatchVideoQueue
from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger

# Import schemas and exceptions
from video2d3d.web.schemas import (
    APIInfoResponse,
    ErrorResponse,
    HealthCheckResponse,
)

# Import routers (will be created)
from video2d3d.web.routers import downloads, jobs, uploads

from video2d3d.web.state import AppState, app_state
from video2d3d.web.exceptions import register_exception_handlers



logger = get_logger("web.api")


def create_upload_dirs() -> None:
    """Create upload and output directories if they don't exist."""
    app_state.upload_dir.mkdir(parents=True, exist_ok=True)
    app_state.output_dir.mkdir(parents=True, exist_ok=True)


def initialize_queue() -> BatchVideoQueue:
    """Initialize the batch processing queue."""
    config = get_config()

    # Create batch queue configuration
    batch_config = BatchQueueConfig(
        max_concurrent_jobs=config.processing.batch_size,
        output_directory=app_state.output_dir,
        auto_start=True,
        save_state=True,
        skip_existing=False,  # For API, we want to process even if output exists
    )

    # Create queue with a placeholder processor
    # The actual processor will be set based on the conversion implementation
    def placeholder_processor(input_path: Path, output_path: Path):
        """Placeholder processor - actual conversion logic to be implemented."""
        from video2d3d.batch.models import BatchJobResult

        logger.warning(
            f"Placeholder processor called: {input_path} -> {output_path}. "
            "Actual conversion not yet implemented."
        )
        return BatchJobResult(
            success=True,
            output_path=output_path,
            metadata={"note": "placeholder"},
        )

    queue = BatchVideoQueue(config=batch_config, processor=placeholder_processor)
    queue.start()

    logger.info(f"Batch queue initialized with {batch_config.max_concurrent_jobs} workers")

    return queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting 2Dto3D API server...")

    # Create directories
    create_upload_dirs()

    # Initialize queue
    app_state.queue = initialize_queue()

    logger.info("API server ready")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    if app_state.queue:
        app_state.queue.stop(wait=True)
        logger.info("Batch queue stopped")


def create_app(
    title: str = "2Dto3D Video Converter API",
    description: str = "REST API for converting 2D videos to 3D using deep learning depth estimation",
    version: str = __version__,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        title: API title for documentation.
        description: API description.
        version: API version.

    Returns:
        Configured FastAPI application instance.
    """
    # Load configuration
    config = get_config()

    # Update app state from config
    app_state.max_upload_size_mb = config.web_api.max_upload_size
    app_state.upload_dir = Path(config.web_api.upload_dir)

    # Create FastAPI app with lifespan
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.web_api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add unique request ID to each request."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        return response

    # Add timing middleware
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        """Add processing time header to responses."""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        return response

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    api_prefix = config.web_api.prefix

    app.include_router(
        uploads.router,
        prefix=f"{api_prefix}/upload",
        tags=["Upload"],
    )
    app.include_router(
        jobs.router,
        prefix=f"{api_prefix}/jobs",
        tags=["Jobs"],
    )
    app.include_router(
        downloads.router,
        prefix=f"{api_prefix}/download",
        tags=["Download"],
    )

    # Health check endpoint
    @app.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Health check",
    )
    async def health_check():
        """Check API health status."""
        return HealthCheckResponse(
            status="healthy",
            version=__version__,
            uptime_seconds=app_state.uptime_seconds,
            queue_running=app_state.queue.is_running if app_state.queue else False,
            gpu_available=False,  # TODO: Check actual GPU availability
        )

    # Root endpoint with API info
    @app.get(
        "/",
        response_model=APIInfoResponse,
        tags=["Info"],
        summary="API information",
    )
    async def root():
        """Get API information and available endpoints."""
        return APIInfoResponse(
            version=__version__,
        )

    # Queue status endpoint at root level
    @app.get(
        f"{api_prefix}/queue",
        response_model=dict,
        tags=["Queue"],
        summary="Queue statistics",
    )
    async def queue_stats():
        """Get batch queue statistics."""
        if not app_state.queue:
            return {"error": "Queue not initialized"}

        stats = app_state.queue.get_stats()
        return stats.to_dict()

    logger.info(f"FastAPI app created with prefix: {api_prefix}")

    return app


# Create default app instance
app = create_app()


__all__ = [
    "app",
    "create_app",
]
