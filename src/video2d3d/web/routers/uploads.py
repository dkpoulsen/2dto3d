"""Upload router for handling video file uploads.

This module provides endpoints for:
- Uploading video files
- Checking upload status
- Listing uploaded files
- Deleting uploaded files
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from video2d3d.utils.config import get_config
from video2d3d.utils.logger import get_logger
from video2d3d.web.exceptions import (
    FileNotFoundError,
    FileSizeExceededError,
    FileUploadError,
    UnsupportedFormatError,
    ValidationError,
)
from video2d3d.web.schemas import DownloadInfoResponse, ErrorResponse, UploadResponse
from video2d3d.web.state import app_state
from video2d3d.web.utils import (
    SUPPORTED_VIDEO_EXTENSIONS,
    find_file_by_id,
    get_content_type,
    sanitize_filename,
    validate_file_id,
)

logger = get_logger("web.upload")

router = APIRouter()

# Configuration
_config = get_config()
API_PREFIX = _config.web_api.prefix


def validate_file_extension(filename: str) -> str:
    """Validate file extension and return normalized extension.

    Args:
        filename: Original filename.

    Returns:
        Normalized lowercase extension.

    Raises:
        UnsupportedFormatError: If extension is not supported.
    """
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_VIDEO_EXTENSIONS:
        raise UnsupportedFormatError(
            format=ext or "unknown",
            supported_formats=list(SUPPORTED_VIDEO_EXTENSIONS),
        )
    return ext


@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a video file",
    description="Upload a 2D video file for conversion to 3D. "
    "Maximum file size is configured in the API settings.",
    responses={
        201: {"description": "File uploaded successfully"},
        400: {"model": ErrorResponse, "description": "Invalid file or upload error"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)
async def upload_file(
    file: UploadFile = File(..., description="Video file to upload"),
) -> UploadResponse:
    """Upload a video file for processing.

    Args:
        file: Uploaded file object.

    Returns:
        Upload response with file ID and metadata.

    Raises:
        FileSizeExceededError: If file exceeds size limit.
        UnsupportedFormatError: If file format is not supported.
        FileUploadError: If upload fails.
    """
    # Validate file extension
    try:
        extension = validate_file_extension(file.filename or "unknown")
    except UnsupportedFormatError:
        logger.warning(f"Rejected upload with unsupported format: {file.filename}")
        raise

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Create safe filename (keep original name for listings, prefixed by ID)
    safe_filename = sanitize_filename(file.filename or "video")
    stored_filename = f"{file_id}_{safe_filename}"
    file_path = app_state.upload_dir / stored_filename

    # Track file size
    total_size = 0
    max_size_bytes = app_state.max_upload_size_mb * 1024 * 1024

    try:
        # Write file in chunks to handle large files
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break

                total_size += len(chunk)

                # Check size limit
                if total_size > max_size_bytes:
                    # Clean up partial file
                    f.close()
                    file_path.unlink(missing_ok=True)
                    logger.warning(
                        f"Upload rejected: {safe_filename} exceeds size limit "
                        f"({total_size / (1024 * 1024):.2f} MB > {app_state.max_upload_size_mb} MB)"
                    )
                    raise FileSizeExceededError(
                        max_size_mb=app_state.max_upload_size_mb,
                        actual_size_mb=total_size / (1024 * 1024),
                    )

                f.write(chunk)

        logger.info(
            f"Uploaded file {safe_filename} -> {file_id} ({total_size / (1024 * 1024):.2f} MB)"
        )

        return UploadResponse(
            file_id=file_id,
            filename=safe_filename,
            file_size_bytes=total_size,
            content_type=get_content_type(extension),
            upload_time=datetime.now(),
            message="File uploaded successfully",
        )

    except FileSizeExceededError:
        raise
    except Exception as e:
        # Clean up on error
        file_path.unlink(missing_ok=True)
        logger.error(f"Upload failed for {safe_filename}: {e}")
        raise FileUploadError(
            message="Failed to upload file",
            filename=safe_filename,
            reason=str(e),
        )
    finally:
        await file.close()


@router.get(
    "/{file_id}",
    response_model=DownloadInfoResponse,
    summary="Get uploaded file info",
    description="Get information about an uploaded file.",
    responses={
        200: {"description": "File info"},
        400: {"model": ErrorResponse, "description": "Invalid file ID"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def get_file_info(file_id: str) -> DownloadInfoResponse:
    """Get information about an uploaded file.

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
        logger.warning(f"Invalid file_id requested: {file_id}")
        raise ValidationError(
            message="Invalid file ID format",
            field="file_id",
            value=file_id,
        )

    # Find file by ID
    file_path = find_file_by_id(
        app_state.upload_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path:
        logger.debug(f"File not found: {file_id}")
        raise FileNotFoundError(file_id=file_id)

    stat = file_path.stat()

    return DownloadInfoResponse(
        file_id=file_id,
        filename=file_path.name,
        file_size_bytes=stat.st_size,
        content_type=get_content_type(file_path.suffix.lower()),
        download_url=f"{API_PREFIX}/download/{file_id}",
        created_at=datetime.fromtimestamp(stat.st_ctime),
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded file",
    description="Delete an uploaded file.",
    responses={
        204: {"description": "File deleted"},
        400: {"model": ErrorResponse, "description": "Invalid file ID"},
        404: {"model": ErrorResponse, "description": "File not found"},
    },
)
async def delete_file(file_id: str) -> None:
    """Delete an uploaded file.

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

    # Find file by ID
    file_path = find_file_by_id(
        app_state.upload_dir,
        file_id,
        extensions=SUPPORTED_VIDEO_EXTENSIONS,
    )

    if not file_path:
        raise FileNotFoundError(file_id=file_id)

    try:
        file_path.unlink()
        logger.info(f"Deleted uploaded file: {file_id}")
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file",
        )


@router.get(
    "/",
    response_model=list[DownloadInfoResponse],
    summary="List uploaded files",
    description="List all uploaded files.",
)
async def list_files() -> list[DownloadInfoResponse]:
    """List all uploaded files.

    Returns:
        List of uploaded file information.
    """
    files = []

    if not app_state.upload_dir.exists():
        return files

    for file_path in app_state.upload_dir.iterdir():
        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()
        if extension not in SUPPORTED_VIDEO_EXTENSIONS:
            continue

        # Extract file ID (filename without extension)
        file_id = file_path.stem
        stat = file_path.stat()

        files.append(
            DownloadInfoResponse(
                file_id=file_id,
                filename=file_path.name,
                file_size_bytes=stat.st_size,
                content_type=get_content_type(extension),
                download_url=f"{API_PREFIX}/download/{file_id}",
                created_at=datetime.fromtimestamp(stat.st_ctime),
            )
        )

    # Sort by creation time, newest first
    files.sort(key=lambda x: x.created_at, reverse=True)

    return files


__all__ = ["router"]
