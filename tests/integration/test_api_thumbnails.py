"""Integration tests for thumbnail grid API endpoint.

Tests cover:
- Thumbnail grid retrieval
- Query parameter handling
- Error handling for invalid job IDs
- Edge cases (empty jobs, frame ranges)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.models import BatchJob, BatchQueueStats, JobPriority, JobStatus
from video2d3d.web.exceptions import register_exception_handlers
from video2d3d.web.routers import jobs
from video2d3d.web.state import AppState


@pytest.fixture
def mock_queue() -> MagicMock:
    """Create a mock batch queue."""
    queue = MagicMock()
    queue.is_running = True

    # Mock get_stats
    stats = BatchQueueStats(
        total_jobs=10,
        pending_jobs=5,
        running_jobs=2,
        completed_jobs=2,
        failed_jobs=1,
    )
    queue.get_stats.return_value = stats

    return queue


@pytest.fixture
def mock_app_state(tmp_path: Path, mock_queue: MagicMock) -> Generator[AppState, None, None]:
    """Create mock app state with temp directories and queue."""
    state = AppState()
    state.upload_dir = tmp_path / "uploads"
    state.output_dir = tmp_path / "outputs"
    state.max_upload_size_mb = 100
    state.queue = mock_queue
    state.upload_dir.mkdir(parents=True, exist_ok=True)
    state.output_dir.mkdir(parents=True, exist_ok=True)

    # Create a test input file
    (state.upload_dir / "test-file-id.mp4").write_bytes(b"fake video content")

    yield state


@pytest.fixture
def app(mock_app_state: AppState) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with jobs router."""
    app = FastAPI()
    register_exception_handlers(app)

    # Mock get_config
    with patch("video2d3d.web.routers.jobs.get_config") as mock_config:
        mock_config.return_value.web_api.prefix = "/api/v1"
        app.include_router(jobs.router, prefix="/api/v1/jobs")

    with patch("video2d3d.web.routers.jobs.app_state", mock_app_state):
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


def create_mock_job(
    job_id: str = "test-job-1",
    status: JobStatus = JobStatus.COMPLETED,
    total_frames: int = 100,
    fps: float = 30.0,
) -> MagicMock:
    """Create a mock BatchJob with video metadata."""
    mock_job = MagicMock(spec=BatchJob)
    mock_job.job_id = job_id
    mock_job.status = status
    mock_job.priority = JobPriority.NORMAL
    mock_job.input_path = Path("/input/video.mp4")
    mock_job.output_path = Path("/output/video_3d.mp4")
    mock_job.progress = 1.0
    mock_job.current_stage = "completed"
    mock_job.created_at = None
    mock_job.started_at = None
    mock_job.completed_at = None
    mock_job.elapsed_time = None
    mock_job.estimated_remaining_time = None
    mock_job.retry_count = 0
    mock_job.result = None
    mock_job.config = {}
    # Video metadata for thumbnails
    mock_job.total_frames = total_frames
    mock_job.fps = fps
    return mock_job


class TestGetThumbnailGrid:
    """Tests for the thumbnail grid endpoint."""

    def test_get_thumbnail_grid_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful retrieval of thumbnail grid."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "test-job-1"
        assert "thumbnails" in data
        assert data["total_frames"] == 100
        assert data["duration_seconds"] == pytest.approx(3.33, rel=0.1)

    def test_get_thumbnail_grid_with_count(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid with custom count parameter."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=12")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["thumbnails"]) == 12

    def test_get_thumbnail_grid_with_frame_range(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test thumbnail grid with start_frame and end_frame parameters."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get(
            "/api/v1/jobs/test-job-1/thumbnails?start_frame=10&end_frame=50&count=4"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        thumbnails = data["thumbnails"]

        # Verify frames are within the specified range
        for thumb in thumbnails:
            assert thumb["frame_index"] >= 10
            assert thumb["frame_index"] < 50

    def test_get_thumbnail_grid_even_distribution(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that thumbnails are evenly distributed across the video."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        thumbnails = data["thumbnails"]

        # Check that frames are evenly spaced
        frame_indices = [t["frame_index"] for t in thumbnails]
        expected_step = 100 / 5  # 20 frames apart
        for i in range(len(frame_indices) - 1):
            gap = frame_indices[i + 1] - frame_indices[i]
            # Allow for some rounding but should be close to expected_step
            assert abs(gap - expected_step) < 1.0

    def test_get_thumbnail_grid_returns_correct_urls(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that thumbnail URLs are correctly formatted."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        thumb = data["thumbnails"][0]

        assert "/api/v1/jobs/test-job-1/frames/" in thumb["original_url"]
        assert "/original" in thumb["original_url"]
        assert "/depth-map" in thumb["depth_map_url"]

    def test_get_thumbnail_grid_calculates_timestamps(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that timestamps are calculated correctly based on frame index and fps."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=3")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        thumbnails = data["thumbnails"]

        # Verify timestamps are rounded to 3 decimal places
        for thumb in thumbnails:
            timestamp = thumb["timestamp"]
            expected_timestamp = thumb["frame_index"] / 30.0
            assert abs(timestamp - expected_timestamp) < 0.001

    def test_get_thumbnail_grid_job_not_found(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test thumbnail grid for non-existent job."""
        mock_queue.get_job.return_value = None

        response = client.get("/api/v1/jobs/nonexistent-job/thumbnails")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "job_not_found"

    def test_get_thumbnail_grid_queue_not_running(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test thumbnail grid when queue is not running."""
        mock_app_state.queue = None
        mock_job = create_mock_job()

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_get_thumbnail_grid_count_validation_min(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that count parameter is validated (minimum 1)."""
        mock_job = create_mock_job()
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=0")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_thumbnail_grid_count_validation_max(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that count parameter is validated (maximum 100)."""
        mock_job = create_mock_job()
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=101")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_thumbnail_grid_start_frame_validation(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that start_frame parameter is validated (must be >= 0)."""
        mock_job = create_mock_job()
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?start_frame=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_thumbnail_grid_end_frame_validation(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test that end_frame parameter is validated (must be >= 0)."""
        mock_job = create_mock_job()
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?end_frame=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetThumbnailGridEdgeCases:
    """Tests for edge cases in the thumbnail grid endpoint."""

    def test_empty_job_zero_frames(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid for job with zero frames."""
        mock_job = create_mock_job(total_frames=0, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["thumbnails"] == []
        assert data["total_frames"] == 0

    def test_single_frame_job(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid for job with a single frame."""
        mock_job = create_mock_job(total_frames=1, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=24")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return 1 thumbnail since there's only 1 frame
        assert len(data["thumbnails"]) == 1
        assert data["thumbnails"][0]["frame_index"] == 0

    def test_frames_less_than_count(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test when total frames is less than requested count."""
        mock_job = create_mock_job(total_frames=10, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=24")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only return 10 thumbnails since there are only 10 frames
        assert len(data["thumbnails"]) == 10

    def test_invalid_frame_range(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test when start_frame >= end_frame."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        # start_frame > end_frame
        response = client.get("/api/v1/jobs/test-job-1/thumbnails?start_frame=50&end_frame=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return empty thumbnails due to invalid range
        assert data["thumbnails"] == []

    def test_same_start_and_end_frame(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test when start_frame equals end_frame."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?start_frame=50&end_frame=50")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return empty thumbnails due to zero range
        assert data["thumbnails"] == []

    def test_job_without_fps_attribute(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid for job without fps attribute."""
        mock_job = create_mock_job()
        delattr(mock_job, "fps")
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should use default fps (30.0)
        assert "duration_seconds" in data

    def test_job_without_total_frames_attribute(
        self, client: TestClient, mock_queue: MagicMock
    ) -> None:
        """Test thumbnail grid for job without total_frames attribute."""
        mock_job = create_mock_job()
        delattr(mock_job, "total_frames")
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should use default total_frames (0)
        assert data["total_frames"] == 0
        assert data["thumbnails"] == []

    def test_default_count_parameter(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test that default count parameter is 24."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["thumbnails"]) == 24

    def test_various_fps_values(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid with various FPS values."""
        fps_values = [23.976, 24.0, 25.0, 29.97, 30.0, 50.0, 59.94, 60.0]

        for fps in fps_values:
            mock_job = create_mock_job(total_frames=100, fps=fps)
            mock_queue.get_job.return_value = mock_job

            response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=1")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            expected_duration = 100 / fps
            assert abs(data["duration_seconds"] - expected_duration) < 0.01

    def test_large_frame_count(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test thumbnail grid with large number of frames."""
        mock_job = create_mock_job(total_frames=10000, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=100")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["thumbnails"]) == 100
        # Verify last frame is within bounds
        last_frame = data["thumbnails"][-1]["frame_index"]
        assert last_frame < 10000


class TestThumbnailGridResponseStructure:
    """Tests for thumbnail grid response structure."""

    def test_response_has_required_fields(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test that response contains all required fields."""
        mock_job = create_mock_job()
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "thumbnails" in data
        assert "total_frames" in data
        assert "duration_seconds" in data

    def test_thumbnail_has_required_fields(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test that each thumbnail contains all required fields."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails?count=1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        thumb = data["thumbnails"][0]

        assert "frame_index" in thumb
        assert "timestamp" in thumb
        assert "original_url" in thumb
        assert "depth_map_url" in thumb
        # Optional fields
        assert "confidence_score" in thumb
        assert "validation_status" in thumb

    def test_frame_index_is_integer(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test that frame_index is always an integer."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for thumb in data["thumbnails"]:
            assert isinstance(thumb["frame_index"], int)

    def test_timestamp_is_number(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test that timestamp is always a number."""
        mock_job = create_mock_job(total_frames=100, fps=30.0)
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-1/thumbnails")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for thumb in data["thumbnails"]:
            assert isinstance(thumb["timestamp"], (int, float))
