"""Integration tests for health API endpoints.

Tests cover:
- Basic health check endpoint (/health)
- Comprehensive health check endpoint (/health/detailed)
- Response schema validation
- Component status reporting
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from video2d3d.web.app import create_app
from video2d3d.web.schemas import HealthStatus

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_queue() -> MagicMock:
    """Create a mock batch queue."""
    queue = MagicMock()
    queue.is_running = True
    queue.is_paused = False

    # Mock get_stats
    mock_stats = MagicMock()
    mock_stats.total_jobs = 10
    mock_stats.pending_jobs = 5
    mock_stats.running_jobs = 2
    mock_stats.completed_jobs = 2
    mock_stats.failed_jobs = 1
    mock_stats.success_rate = 66.67
    queue.get_stats.return_value = mock_stats

    return queue


@pytest.fixture
def mock_app_state(mock_queue: MagicMock) -> Generator[MagicMock, None, None]:
    """Create mock app state with queue."""
    with (
        patch.object(importlib.import_module("video2d3d.web.app"), "app_state") as mock_state,
        patch("video2d3d.web.state.app_state", new=mock_state),
    ):
        mock_state.queue = mock_queue
        mock_state.uptime_seconds = 3600.0
        yield mock_state


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    """Create test FastAPI app."""
    # Patch CUDA availability for consistent test results
    with patch("video2d3d.web.health.is_cuda_available", return_value=False):
        app = create_app()
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestHealthEndpoint:
    """Tests for basic /health endpoint."""

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """Test that health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_endpoint_response_schema(self, client: TestClient) -> None:
        """Test health endpoint response has required fields."""
        response = client.get("/health")
        data = response.json()

        # Required fields
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "queue_running" in data
        assert "gpu_available" in data

    def test_health_endpoint_status_values(self, client: TestClient) -> None:
        """Test health endpoint returns valid status string."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] in ["healthy", "unhealthy"]

    def test_health_endpoint_version_format(self, client: TestClient) -> None:
        """Test health endpoint returns valid version."""
        response = client.get("/health")
        data = response.json()

        # Version should be a string like "0.1.0"
        version = data["version"]
        assert isinstance(version, str)
        assert len(version.split(".")) >= 2

    def test_health_endpoint_uptime_positive(self, client: TestClient) -> None:
        """Test health endpoint returns positive uptime."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0


class TestHealthDetailedEndpoint:
    """Tests for comprehensive /health/detailed endpoint."""

    def test_health_detailed_returns_200(self, client: TestClient) -> None:
        """Test that detailed health endpoint returns 200 OK."""
        response = client.get("/health/detailed")
        assert response.status_code == status.HTTP_200_OK

    def test_health_detailed_response_schema(self, client: TestClient) -> None:
        """Test detailed health endpoint response has all required fields."""
        response = client.get("/health/detailed")
        data = response.json()

        # Top-level required fields
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert "gpu" in data
        assert "memory" in data
        assert "queue" in data
        assert "checks" in data

    def test_health_detailed_gpu_structure(self, client: TestClient) -> None:
        """Test GPU status structure in detailed health response."""
        response = client.get("/health/detailed")
        data = response.json()

        gpu = data["gpu"]
        assert "available" in gpu
        assert "device_count" in gpu
        assert "device_name" in gpu
        assert "memory_used_mb" in gpu
        assert "memory_free_mb" in gpu
        assert "memory_total_mb" in gpu
        assert "memory_utilization_percent" in gpu
        assert "compute_capability" in gpu

    def test_health_detailed_memory_structure(self, client: TestClient) -> None:
        """Test memory status structure in detailed health response."""
        response = client.get("/health/detailed")
        data = response.json()

        memory = data["memory"]
        assert "total_mb" in memory
        assert "available_mb" in memory
        assert "used_mb" in memory
        assert "utilization_percent" in memory

    def test_health_detailed_queue_structure(self, client: TestClient) -> None:
        """Test queue status structure in detailed health response."""
        response = client.get("/health/detailed")
        data = response.json()

        queue = data["queue"]
        assert "running" in queue
        assert "paused" in queue
        assert "total_jobs" in queue
        assert "pending_jobs" in queue
        assert "running_jobs" in queue
        assert "completed_jobs" in queue
        assert "failed_jobs" in queue
        assert "queue_depth" in queue
        assert "success_rate_percent" in queue

    def test_health_detailed_status_values(self, client: TestClient) -> None:
        """Test detailed health endpoint returns valid status enum."""
        response = client.get("/health/detailed")
        data = response.json()

        valid_statuses = [s.value for s in HealthStatus]
        assert data["status"] in valid_statuses

    def test_health_detailed_checks_structure(self, client: TestClient) -> None:
        """Test checks dictionary in detailed health response."""
        response = client.get("/health/detailed")
        data = response.json()

        checks = data["checks"]
        assert isinstance(checks, dict)
        assert "queue" in checks
        assert "memory" in checks
        assert "gpu" in checks

        # All check values should be booleans
        assert isinstance(checks["queue"], bool)
        assert isinstance(checks["memory"], bool)
        assert isinstance(checks["gpu"], bool)

    def test_health_detailed_timestamp_iso_format(self, client: TestClient) -> None:
        """Test timestamp is in ISO format."""
        response = client.get("/health/detailed")
        data = response.json()

        timestamp = data["timestamp"]
        assert isinstance(timestamp, str)
        # ISO format should contain 'T' and either 'Z' or timezone
        assert "T" in timestamp

    def test_health_detailed_queue_stats_consistency(self, client: TestClient) -> None:
        """Test queue statistics are internally consistent."""
        response = client.get("/health/detailed")
        data = response.json()

        queue = data["queue"]
        # Queue depth should equal pending + running
        expected_depth = queue["pending_jobs"] + queue["running_jobs"]
        assert queue["queue_depth"] == expected_depth


class TestHealthEndpointsWithGPU:
    """Tests for health endpoints with GPU available."""

    def test_health_detailed_with_gpu(self, client: TestClient, mock_app_state: MagicMock) -> None:
        """Test detailed health when GPU is available."""
        # Create mock GPU info
        mock_gpu_info = MagicMock()
        mock_gpu_info.name = "NVIDIA Test GPU"
        mock_gpu_info.used_memory_mb = 4000.0
        mock_gpu_info.free_memory_mb = 20000.0
        mock_gpu_info.total_memory_mb = 24000.0
        mock_gpu_info.memory_utilization = 16.67
        mock_gpu_info.compute_capability = (8, 6)

        with (
            patch("video2d3d.web.health.is_cuda_available", return_value=True),
            patch("video2d3d.web.health.get_device_count", return_value=1),
            patch("video2d3d.web.health.get_all_gpu_info", return_value=[mock_gpu_info]),
        ):
            response = client.get("/health/detailed")
            data = response.json()

            gpu = data["gpu"]
            assert gpu["available"] is True
            assert gpu["device_count"] == 1
            assert gpu["device_name"] == "NVIDIA Test GPU"
            assert gpu["compute_capability"] == "8.6"
            assert gpu["memory_utilization_percent"] > 0

    def test_health_endpoint_with_gpu_available(
        self, client: TestClient, mock_app_state: MagicMock
    ) -> None:
        """Test basic health endpoint reflects GPU availability."""
        mock_gpu_info = MagicMock()
        mock_gpu_info.name = "NVIDIA Test GPU"
        mock_gpu_info.used_memory_mb = 4000.0
        mock_gpu_info.free_memory_mb = 20000.0
        mock_gpu_info.total_memory_mb = 24000.0
        mock_gpu_info.memory_utilization = 16.67
        mock_gpu_info.compute_capability = (8, 6)

        with (
            patch("video2d3d.web.health.is_cuda_available", return_value=True),
            patch("video2d3d.web.health.get_device_count", return_value=1),
            patch("video2d3d.web.health.get_all_gpu_info", return_value=[mock_gpu_info]),
        ):
            response = client.get("/health")
            data = response.json()

            assert data["gpu_available"] is True


class TestHealthEndpointWithoutQueue:
    """Tests for health endpoints when queue is not available."""

    def test_health_detailed_without_queue(
        self, client: TestClient, mock_app_state: MagicMock
    ) -> None:
        """Test detailed health when queue is None."""
        mock_app_state.queue = None

        response = client.get("/health/detailed")
        data = response.json()

        queue = data["queue"]
        assert queue["running"] is False
        assert queue["paused"] is False
        assert queue["total_jobs"] == 0

        # Status should be unhealthy because queue is not running
        assert data["status"] == HealthStatus.UNHEALTHY.value
        assert data["checks"]["queue"] is False

    def test_health_endpoint_without_queue(
        self, client: TestClient, mock_app_state: MagicMock
    ) -> None:
        """Test basic health endpoint when queue is None."""
        mock_app_state.queue = None

        response = client.get("/health")
        data = response.json()

        assert data["queue_running"] is False
        assert data["status"] == "unhealthy"


class TestHealthEndpointOpenAPI:
    """Tests for OpenAPI documentation of health endpoints."""

    def test_health_endpoint_in_openapi(self, app: FastAPI) -> None:
        """Test that /health endpoint is in OpenAPI schema."""
        openapi = app.openapi()
        assert "/health" in openapi["paths"]

    def test_health_detailed_endpoint_in_openapi(self, app: FastAPI) -> None:
        """Test that /health/detailed endpoint is in OpenAPI schema."""
        openapi = app.openapi()
        assert "/health/detailed" in openapi["paths"]

    def test_health_endpoints_have_health_tag(self, app: FastAPI) -> None:
        """Test that health endpoints have 'Health' tag."""
        openapi = app.openapi()

        health_tags = openapi["paths"]["/health"]["get"]["tags"]
        assert "Health" in health_tags

        detailed_tags = openapi["paths"]["/health/detailed"]["get"]["tags"]
        assert "Health" in detailed_tags
