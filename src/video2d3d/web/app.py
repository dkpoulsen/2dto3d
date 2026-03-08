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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from video2d3d import __version__
from video2d3d.batch import BatchQueueConfig, BatchVideoQueue
from video2d3d.crash import init_crash_reporting, set_crash_reporter_queue, shutdown_crash_reporting
from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger
from video2d3d.web.exceptions import register_exception_handlers

# Import health monitoring utilities
from video2d3d.web.health import get_comprehensive_health, get_gpu_status
from video2d3d.web.rate_limit import setup_rate_limiting

# Import routers (will be created)
from video2d3d.web.routers import auth, crash, downloads, jobs, notifications, uploads

# Import schemas and exceptions
from video2d3d.web.schemas import (
    APIInfoResponse,
    ComprehensiveHealthResponse,
    HealthCheckResponse,
)
from video2d3d.web.state import app_state

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

    # Hook up notification callbacks
    from video2d3d.web.notification_manager import get_notification_manager

    notification_manager = get_notification_manager()

    def on_job_completed(job):
        notification_manager.on_job_completed(job)

    def on_job_error(job, error):
        notification_manager.on_job_failed(job, error)

    queue.on_completion(on_job_completed)
    queue.on_error(on_job_error)

    queue.start()

    logger.info(f"Batch queue initialized with {batch_config.max_concurrent_jobs} workers")

    return queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting 2Dto3D API server...")

    # Initialize crash reporting first
    config = get_config()
    crash_dir = Path(config.web_api.upload_dir).parent / "crashes"
    init_crash_reporting(
        app_version=__version__,
        app_start_time=app_state.start_time,
    )
    logger.info(f"Crash reporting initialized. Reports saved to {crash_dir}")

    # Create directories
    create_upload_dirs()

    # Initialize queue
    app_state.queue = initialize_queue()

    # Update crash reporter with queue reference
    if app_state.queue:
        set_crash_reporter_queue(app_state.queue)

    logger.info("API server ready")

    yield

    # Shutdown
    logger.info("Shutting down API server...")

    # Shutdown crash reporting
    shutdown_crash_reporting()

    if app_state.queue:
        app_state.queue.stop(wait=True)
        logger.info("Batch queue stopped")


def create_app(
    title: str = "2Dto3D Video Converter API",
    description: str = """# 2Dto3D Video Converter API

Convert 2D videos to immersive 3D using state-of-the-art deep learning depth estimation.

## Overview

This REST API provides endpoints for:
- **Upload**: Upload 2D video files for processing
- **Jobs**: Submit, monitor, and manage video conversion jobs
- **Download**: Retrieve converted 3D video files

## Key Features

- 🎬 Support for multiple video formats (MP4, AVI, MOV, MKV, WebM)
- 🧠 Multiple depth estimation models (MiDaS Small, MiDaS Hybrid, DPT Large, DPT Hybrid)
- 👓 Multiple 3D output formats (Side-by-Side, Anaglyph, Interlaced, VR)
- ⚡ GPU acceleration support
- 🔄 Batch processing with queue management
- 📊 Real-time job progress tracking

## Getting Started

1. Upload a video file using `POST /api/v1/upload/`
2. Submit a conversion job using `POST /api/v1/jobs/`
3. Monitor job progress using `GET /api/v1/jobs/{job_id}`
4. Download the result using `GET /api/v1/download/{file_id}`

## Authentication

This API uses JWT-based authentication. Most endpoints require a valid access token.

### Getting Started with Authentication

1. Register a new account using `POST /api/v1/auth/register`
2. Login using `POST /api/v1/auth/login` to get access and refresh tokens
3. Include the access token in the `Authorization` header as `Bearer <token>`
4. Use `POST /api/v1/auth/refresh` to get new tokens when the access token expires

### Token Types

- **Access Token**: Short-lived token (30 minutes default) for API requests
- **Refresh Token**: Long-lived token (7 days default) for obtaining new access tokens
""",
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

    # Define API tags with descriptions
    tags_metadata = [
        {
            "name": "Info",
            "description": "API information and service metadata.",
        },
        {
            "name": "Authentication",
            "description": "User authentication endpoints. Register, login, and manage JWT tokens. "
            "Includes role-based access control for protected resources.",
        },
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring service status.",
        },
        {
            "name": "Upload",
            "description": "Upload 2D video files for conversion. Manage uploaded files.",
        },
        {
            "name": "Jobs",
            "description": "Submit, monitor, and manage video conversion jobs. "
            "Includes batch processing, job cancellation, and retry functionality.",
        },
        {
            "name": "Download",
            "description": "Download converted 3D video files. List and manage downloadable results.",
        },
        {
            "name": "Queue",
            "description": "Monitor and manage the processing queue. View queue statistics.",
        },
        {
            "name": "Crash Reports",
            "description": "View and manage crash reports for debugging and diagnostics. "
            "Includes crash history, system state at crash time, and manual reporting.",
        },
        {
            "name": "Notifications",
            "description": "Manage in-app notifications for job events, system alerts, "
            "and webhook configurations. Includes notification preferences and history.",
        },
    ]

    # Create FastAPI app with lifespan
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "2Dto3D API Support",
            "url": "https://github.com/automaker/2dto3d",
            "email": "support@automaker.dev",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=tags_metadata,
        servers=[
            {
                "url": "/",
                "description": "Current server",
            },
            {
                "url": "http://localhost:8000",
                "description": "Local development server",
            },
        ],
        terms_of_service="https://github.com/automaker/2dto3d/blob/main/LICENSE",
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

    # Set up rate limiting
    limiter = setup_rate_limiting(app)
    if limiter:
        app_state.limiter = limiter

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
    app.include_router(
        crash.router,
        prefix=f"{api_prefix}/crash-reports",
        tags=["Crash Reports"],
    )
    app.include_router(
        notifications.router,
        prefix=f"{api_prefix}/notifications",
        tags=["Notifications"],
    )
    app.include_router(
        auth.router,
        prefix=f"{api_prefix}/auth",
        tags=["Authentication"],
    )

    # Health check endpoint (basic)
    @app.get(
        "/health",
        response_model=HealthCheckResponse,
        tags=["Health"],
        summary="Basic health check",
    )
    async def health_check():
        """Check basic API health status.

        Returns a simplified health check response for quick health monitoring.
        For detailed health information, use `/health/detailed`.
        """
        gpu_status = get_gpu_status()
        queue_running = app_state.queue.is_running if app_state.queue else False

        # Determine basic health status string
        # Report "healthy" only if queue is running (primary health indicator)
        status = "healthy" if queue_running else "unhealthy"

        return HealthCheckResponse(
            status=status,
            version=__version__,
            uptime_seconds=app_state.uptime_seconds,
            queue_running=queue_running,
            gpu_available=gpu_status.available,
        )

    # Comprehensive health check endpoint
    @app.get(
        "/health/detailed",
        response_model=ComprehensiveHealthResponse,
        tags=["Health"],
        summary="Comprehensive health check",
    )
    async def health_check_detailed():
        """Check comprehensive API health status.

        Returns detailed health information including:
        - GPU status (availability, memory usage, utilization)
        - System memory usage
        - Queue statistics (depth, job counts, success rate)
        - Individual component health checks
        - Overall health status (healthy, degraded, unhealthy)
        """
        return get_comprehensive_health(
            queue=app_state.queue,
            version=__version__,
            uptime_seconds=app_state.uptime_seconds,
        )

    # Root endpoint - serve frontend or API info
    frontend_dist = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    frontend_index = frontend_dist / "index.html"

    if frontend_index.exists():
        # Serve frontend
        @app.get("/", include_in_schema=False)
        async def root():
            """Serve the web dashboard."""
            return FileResponse(str(frontend_index))

    else:
        # Serve API info when frontend not built
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

    # OpenAPI YAML export endpoint (for external tools like Postman, Insomnia)
    @app.get(
        "/openapi.yaml",
        include_in_schema=False,
    )
    async def get_openapi_yaml():
        """Get OpenAPI specification in YAML format."""
        import yaml

        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
            tags=tags_metadata,
        )
        yaml_content = yaml.dump(openapi_schema, default_flow_style=False)
        return Response(
            content=yaml_content,
            media_type="application/yaml",
        )

    # Export API spec endpoint
    @app.get(
        f"{api_prefix}/spec",
        tags=["Info"],
        summary="Get OpenAPI specification",
        description="Get the complete OpenAPI specification for this API in JSON format. "
        "Useful for importing into API clients like Postman, Insomnia, or generating SDKs.",
    )
    async def export_openapi_spec():
        """Export OpenAPI specification for external tools."""
        return get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
            tags=tags_metadata,
        )

    # Serve static frontend files (if built)
    if frontend_dist.exists() and frontend_dist.is_dir():
        # Mount static assets
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        logger.info(f"Serving frontend from {frontend_dist}")

        # Serve index.html for all non-API routes (SPA routing)
        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            """Serve the SPA for all non-API routes."""
            # Check if requesting a static file that exists
            file_path = frontend_dist / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))

            # For all other routes, serve index.html (SPA routing)
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))

            return {"error": "Frontend not built. Run 'npm run build' in frontend/"}

    logger.info(f"FastAPI app created with prefix: {api_prefix}")

    return app


# Create default app instance
app = create_app()


__all__ = [
    "app",
    "create_app",
]
