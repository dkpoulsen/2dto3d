"""Integration tests for jobs API endpoints.

Tests cover:
- Job submission
- Job status retrieval
- Job listing
- Job cancellation
- Job retry
- Queue statistics
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.models import BatchJob, BatchQueueStats, JobPriority, JobStatus
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


class TestSubmitJob:
    """Tests for job submission endpoint."""

    def test_submit_job_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful job submission."""
        # Create mock job
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.PENDING
        mock_queue.add_job.return_value = mock_job

        response = client.post(
            "/api/v1/jobs/",
            json={
                "input_file_id": "test-file-id",
                "priority": "normal",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "pending"
        assert data["message"] == "Job submitted successfully"
        assert "status_url" in data

    def test_submit_job_with_config(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test job submission with configuration."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.PENDING
        mock_queue.add_job.return_value = mock_job

        response = client.post(
            "/api/v1/jobs/",
            json={
                "input_file_id": "test-file-id",
                "output_filename": "output_3d.mp4",
                "priority": "high",
                "config": {
                    "stereo_format": "anaglyph",
                    "depth_model": "dpt_large",
                    "use_gpu": True,
                    "quality_preset": "quality",
                },
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_submit_job_file_not_found(self, client: TestClient) -> None:
        """Test job submission with non-existent file."""
        response = client.post(
            "/api/v1/jobs/",
            json={
                "input_file_id": "nonexistent-file-id",
                "priority": "normal",
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submit_job_queue_not_running(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test job submission when queue is not running."""
        mock_app_state.queue.is_running = False

        response = client.post(
            "/api/v1/jobs/",
            json={
                "input_file_id": "test-file-id",
                "priority": "normal",
            },
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_submit_job_invalid_file_id(self, client: TestClient) -> None:
        """Test job submission with invalid file ID (path traversal)."""
        response = client.post(
            "/api/v1/jobs/",
            json={
                "input_file_id": "../../../etc/passwd",
                "priority": "normal",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestSubmitBatchJobs:
    """Tests for batch job submission endpoint."""

    def test_submit_batch_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful batch job submission."""
        # Create mock jobs
        mock_jobs = []
        for i in range(3):
            job = MagicMock(spec=BatchJob)
            job.job_id = f"job-{i}"
            job.status = JobStatus.PENDING
            mock_jobs.append(job)

        # Create additional input files
        mock_queue.add_job.side_effect = mock_jobs

        response = client.post(
            "/api/v1/jobs/batch",
            json={
                "input_file_ids": ["test-file-id", "test-file-id", "test-file-id"],
                "priority": "normal",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 3


class TestGetJob:
    """Tests for get job endpoint."""

    def test_get_job_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test getting job details."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.RUNNING
        mock_job.priority = JobPriority.NORMAL
        mock_job.input_path = Path("/input/video.mp4")
        mock_job.output_path = Path("/output/video_3d.mp4")
        mock_job.progress = 0.5
        mock_job.current_stage = "Processing"
        mock_job.created_at = None
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.elapsed_time = None
        mock_job.estimated_remaining_time = None
        mock_job.retry_count = 0
        mock_job.result = None
        mock_job.config = {}
        mock_queue.get_job.return_value = mock_job

        response = client.get("/api/v1/jobs/test-job-id")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "running"
        assert data["progress"] == 0.5

    def test_get_job_not_found(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test getting non-existent job."""
        mock_queue.get_job.return_value = None

        response = client.get("/api/v1/jobs/nonexistent-job-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "job_not_found"


class TestListJobs:
    """Tests for list jobs endpoint."""

    def test_list_jobs_empty(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test listing jobs when queue is empty."""
        mock_queue.get_all_jobs.return_value = []

        response = client.get("/api/v1/jobs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["jobs"] == []
        assert data["total_count"] == 0

    def test_list_jobs_with_jobs(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test listing jobs when jobs exist."""
        mock_jobs = []
        for i in range(3):
            job = MagicMock(spec=BatchJob)
            job.job_id = f"job-{i}"
            job.status = JobStatus.PENDING
            job.priority = JobPriority.NORMAL
            job.input_path = Path(f"/input/video{i}.mp4")
            job.output_path = None
            job.progress = 0.0
            job.current_stage = ""
            job.created_at = None
            job.started_at = None
            job.completed_at = None
            job.elapsed_time = None
            job.estimated_remaining_time = None
            job.retry_count = 0
            job.result = None
            job.config = {}
            mock_jobs.append(job)

        mock_queue.get_all_jobs.return_value = mock_jobs

        response = client.get("/api/v1/jobs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["jobs"]) == 3
        assert data["total_count"] == 3

    def test_list_jobs_pagination(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test job listing pagination."""
        mock_queue.get_all_jobs.return_value = []

        response = client.get("/api/v1/jobs/?page=2&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_list_jobs_filter_by_status(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test filtering jobs by status."""
        mock_queue.get_all_jobs.return_value = []

        response = client.get("/api/v1/jobs/?status=running")

        assert response.status_code == status.HTTP_200_OK
        # Verify get_all_jobs was called with status filter
        mock_queue.get_all_jobs.assert_called()


class TestCancelJob:
    """Tests for cancel job endpoint."""

    def test_cancel_job_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful job cancellation."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.RUNNING
        mock_job.status.is_terminal = False
        mock_queue.get_job.return_value = mock_job
        mock_queue.cancel_job.return_value = True

        response = client.post("/api/v1/jobs/test-job-id/cancel")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["cancelled"] is True

    def test_cancel_job_not_found(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test cancelling non-existent job."""
        mock_queue.get_job.return_value = None

        response = client.post("/api/v1/jobs/nonexistent-job-id/cancel")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_completed_job(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test cancelling a completed job fails."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.COMPLETED
        mock_job.status.is_terminal = True
        mock_queue.get_job.return_value = mock_job

        response = client.post("/api/v1/jobs/test-job-id/cancel")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "job_not_cancellable"


class TestRetryJob:
    """Tests for retry job endpoint."""

    def test_retry_job_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful job retry."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.FAILED
        mock_job.is_retryable = True
        mock_job.retry_count = 1
        mock_queue.get_job.return_value = mock_job
        mock_queue.retry_job.return_value = True

        response = client.post("/api/v1/jobs/test-job-id/retry")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["retried"] is True

    def test_retry_job_not_found(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test retrying non-existent job."""
        mock_queue.get_job.return_value = None

        response = client.post("/api/v1/jobs/nonexistent-job-id/retry")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retry_non_retryable_job(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test retrying a non-retryable job fails."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.COMPLETED
        mock_job.is_retryable = False
        mock_queue.get_job.return_value = mock_job

        response = client.post("/api/v1/jobs/test-job-id/retry")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "job_not_retryable"


class TestRemoveJob:
    """Tests for remove job endpoint."""

    def test_remove_job_success(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test successful job removal."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.COMPLETED
        mock_queue.get_job.return_value = mock_job
        mock_queue.remove_job.return_value = True

        response = client.delete("/api/v1/jobs/test-job-id")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_remove_running_job_fails(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test removing a running job fails."""
        mock_job = MagicMock(spec=BatchJob)
        mock_job.job_id = "test-job-id"
        mock_job.status = JobStatus.RUNNING
        mock_queue.get_job.return_value = mock_job

        response = client.delete("/api/v1/jobs/test-job-id")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestQueueStats:
    """Tests for queue statistics endpoint."""

    def test_get_queue_stats(self, client: TestClient, mock_queue: MagicMock) -> None:
        """Test getting queue statistics."""
        response = client.get("/api/v1/jobs/stats/queue")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_jobs" in data
        assert "pending_jobs" in data
        assert "running_jobs" in data
        assert "completed_jobs" in data
        assert "failed_jobs" in data

    def test_get_queue_stats_empty_queue(
        self, client: TestClient, mock_app_state: AppState
    ) -> None:
        """Test getting stats when queue is None."""
        mock_app_state.queue = None

        response = client.get("/api/v1/jobs/stats/queue")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return default/empty stats
        assert "total_jobs" in data
