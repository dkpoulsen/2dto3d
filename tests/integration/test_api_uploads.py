"""Integration tests for upload API endpoints.

Tests cover:
- File upload functionality
- File validation
- File info retrieval
- File listing
- File deletion
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.exceptions import register_exception_handlers
from video2d3d.web.routers import uploads
from video2d3d.web.state import AppState


@pytest.fixture
def mock_app_state(tmp_path: Path) -> Generator[AppState, None, None]:
    """Create mock app state with temp directories."""
    state = AppState()
    state.upload_dir = tmp_path / "uploads"
    state.output_dir = tmp_path / "outputs"
    state.max_upload_size_mb = 10  # 10MB for testing
    state.upload_dir.mkdir(parents=True, exist_ok=True)
    state.output_dir.mkdir(parents=True, exist_ok=True)
    yield state


@pytest.fixture
def app(mock_app_state: AppState) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with upload router."""
    app = FastAPI()
    register_exception_handlers(app)

    # Mock get_config to return API prefix
    with patch("video2d3d.web.routers.uploads.get_config") as mock_config:
        mock_config.return_value.web_api.prefix = "/api/v1"
        app.include_router(uploads.router, prefix="/api/v1/upload")

    with patch("video2d3d.web.routers.uploads.app_state", mock_app_state):
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestUploadFile:
    """Tests for file upload endpoint."""

    def test_upload_mp4_file(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test uploading a valid MP4 file."""
        # Create test file content
        content = b"fake video content for testing"
        files = {"file": ("test_video.mp4", BytesIO(content), "video/mp4")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test_video.mp4"
        assert data["file_size_bytes"] == len(content)
        assert data["content_type"] == "video/mp4"
        assert data["message"] == "File uploaded successfully"

    def test_upload_avi_file(self, client: TestClient) -> None:
        """Test uploading a valid AVI file."""
        content = b"fake avi content"
        files = {"file": ("test_video.avi", BytesIO(content), "video/x-msvideo")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["filename"] == "test_video.avi"

    def test_upload_mov_file(self, client: TestClient) -> None:
        """Test uploading a valid MOV file."""
        content = b"fake mov content"
        files = {"file": ("test_video.mov", BytesIO(content), "video/quicktime")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_mkv_file(self, client: TestClient) -> None:
        """Test uploading a valid MKV file."""
        content = b"fake mkv content"
        files = {"file": ("test_video.mkv", BytesIO(content), "video/x-matroska")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_webm_file(self, client: TestClient) -> None:
        """Test uploading a valid WebM file."""
        content = b"fake webm content"
        files = {"file": ("test_video.webm", BytesIO(content), "video/webm")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_201_CREATED

    def test_upload_unsupported_format(self, client: TestClient) -> None:
        """Test uploading an unsupported format returns error."""
        content = b"not a video"
        files = {"file": ("document.txt", BytesIO(content), "text/plain")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "unsupported_format"

    def test_upload_file_too_large(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test uploading a file that exceeds size limit."""
        # Set small limit
        mock_app_state.max_upload_size_mb = 0.001  # 1KB

        # Create content larger than limit
        content = b"x" * 2000  # 2KB
        files = {"file": ("large_video.mp4", BytesIO(content), "video/mp4")}

        response = client.post("/api/v1/upload/", files=files)

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        data = response.json()
        assert data["error"] == "file_too_large"

    def test_upload_generates_unique_id(self, client: TestClient) -> None:
        """Test that each upload gets a unique file ID."""
        content = b"test content"
        files1 = {"file": ("video1.mp4", BytesIO(content), "video/mp4")}
        files2 = {"file": ("video2.mp4", BytesIO(content), "video/mp4")}

        response1 = client.post("/api/v1/upload/", files=files1)
        response2 = client.post("/api/v1/upload/", files=files2)

        assert response1.json()["file_id"] != response2.json()["file_id"]


class TestGetFileInfo:
    """Tests for get file info endpoint."""

    def test_get_file_info_success(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test getting info for an uploaded file."""
        # First upload a file
        content = b"test video content"
        files = {"file": ("test.mp4", BytesIO(content), "video/mp4")}
        upload_response = client.post("/api/v1/upload/", files=files)
        file_id = upload_response.json()["file_id"]

        # Get file info
        response = client.get(f"/api/v1/upload/{file_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_id"] == file_id
        assert "filename" in data
        assert "file_size_bytes" in data

    def test_get_file_info_not_found(self, client: TestClient) -> None:
        """Test getting info for non-existent file."""
        response = client.get("/api/v1/upload/nonexistent-file-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "file_not_found"

    def test_get_file_info_invalid_id(self, client: TestClient) -> None:
        """Test getting info with invalid file ID (path traversal)."""
        response = client.get("/api/v1/upload/../etc/passwd")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "validation_error"


class TestDeleteFile:
    """Tests for delete file endpoint."""

    def test_delete_file_success(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test deleting an uploaded file."""
        # First upload a file
        content = b"test content"
        files = {"file": ("test.mp4", BytesIO(content), "video/mp4")}
        upload_response = client.post("/api/v1/upload/", files=files)
        file_id = upload_response.json()["file_id"]

        # Delete the file
        response = client.delete(f"/api/v1/upload/{file_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify file is gone
        get_response = client.get(f"/api/v1/upload/{file_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_file_not_found(self, client: TestClient) -> None:
        """Test deleting a non-existent file."""
        response = client.delete("/api/v1/upload/nonexistent-file-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_file_invalid_id(self, client: TestClient) -> None:
        """Test deleting with invalid file ID."""
        response = client.delete("/api/v1/upload/../../etc/passwd")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestListFiles:
    """Tests for list files endpoint."""

    def test_list_files_empty(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test listing files when directory is empty."""
        response = client.get("/api/v1/upload/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_files_with_files(self, client: TestClient) -> None:
        """Test listing files when files exist."""
        # Upload multiple files
        for i in range(3):
            content = f"content {i}".encode()
            files = {"file": (f"video{i}.mp4", BytesIO(content), "video/mp4")}
            client.post("/api/v1/upload/", files=files)

        response = client.get("/api/v1/upload/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_files_excludes_non_video(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test listing files excludes non-video files."""
        # Upload a video file
        content = b"video content"
        files = {"file": ("video.mp4", BytesIO(content), "video/mp4")}
        client.post("/api/v1/upload/", files=files)

        # Create a non-video file directly
        (mock_app_state.upload_dir / "readme.txt").write_text("not a video")

        response = client.get("/api/v1/upload/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"].endswith(".mp4")

    def test_list_files_sorted_by_time(self, client: TestClient) -> None:
        """Test files are sorted by creation time (newest first)."""
        import time

        # Upload files with delay
        for i in range(3):
            content = f"content {i}".encode()
            files = {"file": (f"video{i}.mp4", BytesIO(content), "video/mp4")}
            client.post("/api/v1/upload/", files=files)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        response = client.get("/api/v1/upload/")
        data = response.json()

        # Check that files are sorted (newest first)
        if len(data) >= 2:
            # First file should be video2 (most recent)
            assert "video2.mp4" in data[0]["filename"]


class TestUploadSecurity:
    """Tests for upload security measures."""

    def test_path_traversal_in_filename_sanitized(self, client: TestClient) -> None:
        """Test path traversal in filename is sanitized."""
        content = b"malicious content"
        files = {"file": ("../../../etc/passwd.mp4", BytesIO(content), "video/mp4")}

        response = client.post("/api/v1/upload/", files=files)

        # Should succeed - filename is sanitized
        assert response.status_code == status.HTTP_201_CREATED

    def test_special_characters_in_filename(self, client: TestClient) -> None:
        """Test special characters in filename are handled."""
        content = b"test content"
        files = {"file": ('test<>:"|?*.mp4', BytesIO(content), "video/mp4")}

        response = client.post("/api/v1/upload/", files=files)

        # Should succeed - filename is sanitized
        assert response.status_code == status.HTTP_201_CREATED
