"""Shared utilities for the web API module.

This module provides common functions and constants used across
multiple routers and modules in the web API.
"""

from __future__ import annotations

import re
from pathlib import Path

# Supported video file extensions
SUPPORTED_VIDEO_EXTENSIONS = frozenset({".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"})

# MIME type mapping for video files
MIME_TYPES: dict[str, str] = {
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".flv": "video/x-flv",
}

# Video extensions accepted for uploads and job submission.
SUPPORTED_VIDEO_EXTENSIONS: set[str] = set(MIME_TYPES.keys())


def get_content_type(extension: str) -> str:
    """Get MIME type for file extension.

    Args:
        extension: File extension (lowercase, with dot).

    Returns:
        MIME type string.
    """
    return MIME_TYPES.get(extension, "application/octet-stream")


def is_supported_video_extension(extension: str) -> bool:
    """Check if a file extension is a supported video format.

    Args:
        extension: File extension (with or without leading dot).

    Returns:
        True if the extension is supported.
    """
    ext = extension.lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    return ext in SUPPORTED_VIDEO_EXTENSIONS


def validate_file_id(file_id: str) -> bool:
    """Validate a file ID to prevent path traversal attacks.

    A valid file ID should be:
    - A valid UUID format, or
    - Alphanumeric with underscores and hyphens only

    Args:
        file_id: The file ID to validate.

    Returns:
        True if the file ID is valid.
    """
    if not file_id:
        return False

    # Check for path traversal attempts
    if ".." in file_id or "/" in file_id or "\\" in file_id:
        return False

    # Check for null bytes
    if "\x00" in file_id:
        return False

    # UUID pattern
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    if uuid_pattern.match(file_id):
        return True

    # Alphanumeric with underscores and hyphens (for custom IDs)
    safe_pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
    return bool(safe_pattern.match(file_id))


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal and invalid characters.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename safe for filesystem use.
    """
    # Remove path separators
    safe_name = filename.replace("/", "_").replace("\\", "_")

    # Remove null bytes
    safe_name = safe_name.replace("\x00", "")

    # Remove other potentially dangerous characters
    dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, "_")

    # Limit length
    max_length = 255
    if len(safe_name) > max_length:
        name, ext = Path(safe_name).stem, Path(safe_name).suffix
        safe_name = name[: max_length - len(ext)] + ext

    return safe_name


def find_file_by_id(
    directory: Path, file_id: str, extensions: set[str] | None = None
) -> Path | None:
    """Find a file by its ID in a directory.

    Args:
        directory: Directory to search in.
        file_id: File identifier (UUID or custom ID).
        extensions: Optional set of allowed extensions (with dots).

    Returns:
        Path to the file if found, None otherwise.
    """
    if not directory.exists():
        return None

    # Look for files matching the ID
    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue

        # Check if stem matches file_id
        if file_path.stem == file_id:
            if extensions is None or file_path.suffix.lower() in extensions:
                return file_path

        # Also check if the file_id is a prefix (for generated names)
        if file_path.stem.startswith(file_id) and len(file_path.stem) > len(file_id):
            # Only match if followed by underscore (e.g., "uuid_3d")
            remainder = file_path.stem[len(file_id) :]
            if remainder.startswith("_"):
                if extensions is None or file_path.suffix.lower() in extensions:
                    return file_path

    return None


__all__ = [
    "SUPPORTED_VIDEO_EXTENSIONS",
    "MIME_TYPES",
    "get_content_type",
    "is_supported_video_extension",
    "validate_file_id",
    "sanitize_filename",
    "find_file_by_id",
]
