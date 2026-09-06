"""Integration tests for download API endpoints.

Tests cover:
- File download
- Download info retrieval
- Download listing
- File deletion
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.exceptions import register_exception_handlers
from video2d3d.web.routers import downloads
from video2d3d.web.state import AppState


@pytest.fixture
def mock_app_state(tmp_path: Path) -> Generator[AppState, None, None]:
    """Create mock app state with temp directories."""
    state = AppState()
    state.upload_dir = tmp_path / "uploads"
    state.output_dir = tmp_path / "outputs"
    state.max_upload_size_mb = 100
    state.upload_dir.mkdir(parents=True, exist_ok=True)
    state.output_dir.mkdir(parents=True, exist_ok=True)
    yield state


@pytest.fixture
def app(mock_app_state: AppState) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with download router."""
    app = FastAPI()
    register_exception_handlers(app)

    # Mock get_config
    with patch("video2d3d.web.routers.downloads.get_config") as mock_config:
        mock_config.return_value.web_api.prefix = "/api/v1"
        app.include_router(downloads.router, prefix="/api/v1/download")

    with patch("video2d3d.web.routers.downloads.app_state", mock_app_state):
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestDownloadFile:
    """Tests for file download endpoint."""

    def test_download_file_success(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test successful file download."""
        # Create a test output file
        test_content = b"fake 3d video content"
        (mock_app_state.output_dir / "test-file-id.mp4").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_200_OK
        assert response.content == test_content
        assert response.headers["content-type"] == "video/mp4"

    def test_download_file_avi(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test downloading an AVI file."""
        test_content = b"fake avi content"
        (mock_app_state.output_dir / "test-file-id.avi").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "video/x-msvideo"

    def test_download_file_mov(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test downloading a MOV file."""
        test_content = b"fake mov content"
        (mock_app_state.output_dir / "test-file-id.mov").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "video/quicktime"

    def test_download_file_mkv(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test downloading an MKV file."""
        test_content = b"fake mkv content"
        (mock_app_state.output_dir / "test-file-id.mkv").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "video/x-matroska"

    def test_download_file_webm(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test downloading a WebM file."""
        test_content = b"fake webm content"
        (mock_app_state.output_dir / "test-file-id.webm").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "video/webm"

    def test_download_file_not_found(self, client: TestClient) -> None:
        """Test downloading non-existent file."""
        response = client.get("/api/v1/download/nonexistent-file-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "file_not_found"

    def test_download_file_invalid_id(self, client: TestClient) -> None:
        """Test downloading with invalid file ID (path traversal)."""
        response = client.get("/api/v1/download/../etc/passwd")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "validation_error"

    def test_download_file_by_prefix(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test downloading file by ID prefix (for generated output names)."""
        test_content = b"fake 3d video content"
        # File with suffix pattern (e.g., job-id_3d.mp4)
        (mock_app_state.output_dir / "job-123_3d.mp4").write_bytes(test_content)

        response = client.get("/api/v1/download/job-123")

        assert response.status_code == status.HTTP_200_OK
        assert response.content == test_content


class TestGetDownloadInfo:
    """Tests for get download info endpoint."""

    def test_get_download_info_success(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test getting download info for a file."""
        test_content = b"fake video content"
        (mock_app_state.output_dir / "test-file-id.mp4").write_bytes(test_content)

        response = client.get("/api/v1/download/test-file-id/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["file_id"] == "test-file-id"
        assert "filename" in data
        assert data["file_size_bytes"] == len(test_content)
        assert data["content_type"] == "video/mp4"
        assert "download_url" in data
        assert "created_at" in data

    def test_get_download_info_not_found(self, client: TestClient) -> None:
        """Test getting info for non-existent file."""
        response = client.get("/api/v1/download/nonexistent-file-id/info")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_download_info_invalid_id(self, client: TestClient) -> None:
        """Test getting info with invalid file ID."""
        response = client.get("/api/v1/download/../../../etc/passwd/info")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestListDownloads:
    """Tests for list downloads endpoint."""

    def test_list_downloads_empty(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test listing downloads when directory is empty."""
        response = client.get("/api/v1/download/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_downloads_with_files(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test listing downloads when files exist."""
        # Create multiple output files
        for i in range(3):
            (mock_app_state.output_dir / f"output-{i}.mp4").write_bytes(b"content")

        response = client.get("/api/v1/download/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_list_downloads_excludes_non_video(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test listing downloads excludes non-video files."""
        # Create video file
        (mock_app_state.output_dir / "output.mp4").write_bytes(b"content")
        # Create non-video file
        (mock_app_state.output_dir / "readme.txt").write_text("not a video")

        response = client.get("/api/v1/download/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["filename"].endswith(".mp4")

    def test_list_downloads_sorted_by_time(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test downloads are sorted by creation time (newest first)."""
        import time

        # Create files with delay
        for i in range(3):
            (mock_app_state.output_dir / f"output-{i}.mp4").write_bytes(b"content")
            time.sleep(0.01)

        response = client.get("/api/v1/download/")
        data = response.json()

        # Check that files are sorted (newest first)
        if len(data) >= 2:
            # First file should be output-2 (most recent)
            assert "output-2" in data[0]["filename"]


class TestDeleteDownload:
    """Tests for delete download endpoint."""

    def test_delete_download_success(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test successful file deletion."""
        # Create a test file
        (mock_app_state.output_dir / "test-file-id.mp4").write_bytes(b"content")

        response = client.delete("/api/v1/download/test-file-id")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify file is gone
        assert not (mock_app_state.output_dir / "test-file-id.mp4").exists()

    def test_delete_download_not_found(self, client: TestClient) -> None:
        """Test deleting non-existent file."""
        response = client.delete("/api/v1/download/nonexistent-file-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_download_invalid_id(self, client: TestClient) -> None:
        """Test deleting with invalid file ID."""
        response = client.delete("/api/v1/download/../../etc/passwd")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDownloadSecurity:
    """Tests for download security measures."""

    def test_path_traversal_prevented(self, client: TestClient, mock_app_state: AppState) -> None:
        """Test path traversal is prevented."""
        # Create a file in output directory
        (mock_app_state.output_dir / "safe.mp4").write_bytes(b"content")

        # Try to access a file outside output directory
        response = client.get("/api/v1/download/../../../etc/passwd")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_access_upload_directory(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test cannot access files in upload directory."""
        # Create a file in upload directory
        (mock_app_state.upload_dir / "secret.mp4").write_bytes(b"secret content")

        # Try to download from upload dir (should fail)
        # The download endpoint only looks in output_dir
        response = client.get("/api/v1/download/secret")

        assert response.status_code == status.HTTP_404_NOT_FOUND
