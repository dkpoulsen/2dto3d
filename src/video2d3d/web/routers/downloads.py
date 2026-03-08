"""Downloads router for serving result files.

This module provides endpoints for:
- Downloading converted 3D video files
- Getting download info
- Listing available downloads
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger
from video2d3d.web.exceptions import FileNotFoundError, ValidationError
from video2d3d.web.schemas import DownloadInfoResponse, ErrorResponse
from video2d3d.web.state import app_state
from video2d3d.web.utils import (
    SUPPORTED_VIDEO_EXTENSIONS,
    find_file_by_id,
    get_content_type,
    validate_file_id,
)

logger = get_logger("web.download")

router = APIRouter()

# Configuration
_config = get_config()
API_PREFIX = _config.web_api.prefix


@router.get(
    "/{file_id}",
    summary="Download a result file",
    description="Download a converted 3D video file by its ID.",
    responses={
        200: {"description": "File download", "content": {"video/mp4": {}}},
        400: {"model": ErrorResponse, "description": "Invalid file ID"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def download_file(file_id: str):
    """Download a result file.

    Args:
        file_id: Unique file identifier.

    Returns:
        File response for download.

    Raises:
        ValidationError: If file_id is invalid.
        FileNotFoundError: If file doesn't exist.
    """
    # Validate file_id to prevent path traversal
    if not validate_file_id(file_id):
        logger.warning(f"Invalid file_id for download: {file_id}")
        raise ValidationError(
            message="Invalid file ID format",
            field="file_id",
            value=file_id,
        )

    # Find the file
    file_path = find_file_by_id(
        app_state.output_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path or not file_path.exists():
        logger.debug(f"Download file not found: {file_id}")
        raise FileNotFoundError(file_id=file_id)

    # Get content type
    content_type = get_content_type(file_path.suffix.lower())

    logger.info(f"Downloading file: {file_path.name}")

    # Return file response
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=file_path.name,
    )


@router.get(
    "/{file_id}/info",
    response_model=DownloadInfoResponse,
    summary="Get download info",
    description="Get information about a downloadable file.",
    responses={
        200: {"description": "File info"},
        400: {"model": ErrorResponse, "description": "Invalid file ID"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def get_download_info(file_id: str) -> DownloadInfoResponse:
    """Get information about a downloadable file.

    Args:
        file_id: Unique file identifier.

    Returns:
        File information.

    Raises:
        ValidationError: If file_id is invalid.
        FileNotFoundError: If file doesn't exist.
    """
    # Validate file_id to prevent path traversal
    if not validate_file_id(file_id):
        logger.warning(f"Invalid file_id for info request: {file_id}")
        raise ValidationError(
            message="Invalid file ID format",
            field="file_id",
            value=file_id,
        )

    # Find the file
    file_path = find_file_by_id(
        app_state.output_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path or not file_path.exists():
        raise FileNotFoundError(file_id=file_id)

    stat = file_path.stat()
    content_type = get_content_type(file_path.suffix.lower())

    return DownloadInfoResponse(
        file_id=file_id,
        filename=file_path.name,
        file_size_bytes=stat.st_size,
        content_type=content_type,
        download_url=f"{API_PREFIX}/download/{file_id}",
        created_at=datetime.fromtimestamp(stat.st_ctime),
    )


@router.get(
    "/",
    response_model=list[DownloadInfoResponse],
    summary="List available downloads",
    description="List all available result files for download.",
)
async def list_downloads() -> list[DownloadInfoResponse]:
    """List all available downloads.

    Returns:
        List of downloadable file information.
    """
    files = []

    if not app_state.output_dir.exists():
        return files

    for file_path in app_state.output_dir.iterdir():
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()
        if extension not in SUPPORTED_VIDEO_EXTENSIONS:
            continue

        stat = file_path.stat()
        content_type = get_content_type(extension)

        files.append(
            DownloadInfoResponse(
                file_id=file_path.stem,
                filename=file_path.name,
                file_size_bytes=stat.st_size,
                content_type=content_type,
                download_url=f"{API_PREFIX}/download/{file_path.stem}",
                created_at=datetime.fromtimestamp(stat.st_ctime),
            )
        )

    # Sort by creation time, newest first
    files.sort(key=lambda x: x.created_at, reverse=True)

    return files


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a result file",
    description="Delete a converted result file.",
    responses={
        204: {"description": "File deleted"},
        400: {"model": ErrorResponse, "description": "Invalid file ID"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def delete_download(file_id: str) -> None:
    """Delete a result file.

    Args:
        file_id: Unique file identifier.

    Raises:
        ValidationError: If file_id is invalid.
        FileNotFoundError: If file doesn't exist.
    """
    # Validate file_id to prevent path traversal
    if not validate_file_id(file_id):
        logger.warning(f"Invalid file_id for deletion: {file_id}")
        raise ValidationError(
            message="Invalid file ID format",
            field="file_id",
            value=file_id,
        )

    # Find the file
    file_path = find_file_by_id(
        app_state.output_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path or not file_path.exists():
        raise FileNotFoundError(file_id=file_id)

    try:
        file_path.unlink()
        logger.info(f"Deleted result file: {file_path.name}")
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )


__all__ = ["router"]
