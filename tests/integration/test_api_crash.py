"""Integration tests for crash report API endpoints.

Tests cover:
- List crash reports endpoint (/api/v1/crash-reports)
- Get crash report details endpoint (/api/v1/crash-reports/{id})
- Create manual crash report endpoint (POST /api/v1/crash-reports)
- Delete crash report endpoint (DELETE /api/v1/crash-reports/{id})
- Clear all crash reports endpoint (DELETE /api/v1/crash-reports)
- Response schema validation
- Error handling
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from video2d3d.crash import (
    CrashReporter,
    CrashReporterConfig,
    get_crash_reporter,
    init_crash_reporting,
    shutdown_crash_reporting,
)
from video2d3d.crash.models import CrashSeverity, CrashType
from video2d3d.web.app import create_app

if TYPE_CHECKING:
    pass


@pytest.fixture
def crash_dir() -> Generator[Path, None, None]:
    """Create temporary crash directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def crash_reporter(crash_dir: Path) -> Generator[CrashReporter, None, None]:
    """Create test crash reporter."""
    config = CrashReporterConfig(
        crash_dir=crash_dir,
        app_version="test-1.0.0",
        enabled=True,
        capture_system_state=True,
    )
    reporter = init_crash_reporting(config)
    yield reporter
    shutdown_crash_reporting()


@pytest.fixture
def app(crash_reporter: CrashReporter) -> Generator[FastAPI, None, None]:
    """Create test FastAPI app with crash reporter initialized."""
    with patch("video2d3d.web.health.is_cuda_available", return_value=False):
        app = create_app()
        yield app


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as client:
        yield client


class TestListCrashReports:
    """Tests for GET /api/v1/crash-reports endpoint."""

    def test_list_empty_reports(self, client: TestClient) -> None:
        """Test listing reports when none exist."""
        response = client.get("/api/v1/crash-reports")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_count"] == 0
        assert data["reports"] == []
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_reports_with_data(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test listing reports when reports exist."""
        # Create some reports
        for i in range(3):
            crash_reporter.report_manual(f"Test report {i}")

        response = client.get("/api/v1/crash-reports")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_count"] == 3
        assert len(data["reports"]) == 3

    def test_list_reports_pagination(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test listing reports with pagination."""
        # Create 5 reports
        for i in range(5):
            crash_reporter.report_manual(f"Test report {i}")

        # Get first page
        response = client.get("/api/v1/crash-reports?page=1&page_size=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["reports"]) == 2
        assert data["total_count"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_list_reports_filter_severity(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test listing reports filtered by severity."""
        # Create reports with different severities
        crash_reporter.report_manual("Low severity", severity=CrashSeverity.LOW)
        crash_reporter.report_manual("High severity", severity=CrashSeverity.HIGH)

        response = client.get("/api/v1/crash-reports?severity=high")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_count"] == 1
        assert data["reports"][0]["severity"] == "high"

    def test_list_reports_response_schema(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test list reports response has required fields."""
        crash_reporter.report_manual("Test")

        response = client.get("/api/v1/crash-reports")
        data = response.json()

        assert "reports" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data

        # Check report summary structure
        report = data["reports"][0]
        assert "report_id" in report
        assert "created_at" in report
        assert "crash_type" in report
        assert "severity" in report
        assert "exception_type" in report
        assert "exception_message" in report


class TestGetCrashReport:
    """Tests for GET /api/v1/crash-reports/{report_id} endpoint."""

    def test_get_report_not_found(self, client: TestClient) -> None:
        """Test getting non-existent report returns 404."""
        response = client.get("/api/v1/crash-reports/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_report_success(self, client: TestClient, crash_reporter: CrashReporter) -> None:
        """Test getting an existing report."""
        report = crash_reporter.report_manual("Test report")

        response = client.get(f"/api/v1/crash-reports/{report.report_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["report_id"] == report.report_id
        assert data["crash_type"] == "manual_report"

    def test_get_report_response_schema(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test get report response has all required fields."""
        report = crash_reporter.report_manual("Test report")

        response = client.get(f"/api/v1/crash-reports/{report.report_id}")
        data = response.json()

        # Top-level fields
        assert "report_id" in data
        assert "created_at" in data
        assert "crash_type" in data
        assert "severity" in data
        assert "exception_type" in data
        assert "exception_message" in data
        assert "exception_traceback" in data
        assert "context" in data
        assert "tags" in data
        assert "recovered" in data

        # System state structure
        if data.get("system_state"):
            state = data["system_state"]
            assert "timestamp" in state
            assert "uptime_seconds" in state
            assert "platform_system" in state
            assert "gpu" in state
            assert "memory" in state
            assert "process" in state

    def test_get_report_with_exception(
        self, client: TestClient, crash_reporter: CrashReporter
    ) -> None:
        """Test getting report with exception info."""
        try:
            raise ValueError("Test error for report")
        except ValueError as e:
            report = crash_reporter.report_manual(
                "Report with exception",
                exception=e,
                severity=CrashSeverity.HIGH,
            )

        response = client.get(f"/api/v1/crash-reports/{report.report_id}")
        data = response.json()

        assert data["exception_type"] == "ValueError"
        assert "Test error for report" in data["exception_message"]
        assert "Traceback" in data["exception_traceback"]


class TestCreateManualCrashReport:
    """Tests for POST /api/v1/crash-reports endpoint."""

    def test_create_manual_report_success(self, client: TestClient) -> None:
        """Test creating a manual crash report."""
        response = client.post(
            "/api/v1/crash-reports",
            json={
                "message": "User reported issue",
                "severity": "medium",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["crash_type"] == "manual_report"
        assert data["severity"] == "medium"
        assert data["user_message"] == "User reported issue"

    def test_create_manual_report_with_context(self, client: TestClient) -> None:
        """Test creating manual report with context."""
        response = client.post(
            "/api/v1/crash-reports",
            json={
                "message": "Processing failed",
                "context": {
                    "input_file": "video.mp4",
                    "frame_number": 150,
                },
                "tags": ["processing", "video"],
                "severity": "high",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["context"]["input_file"] == "video.mp4"
        assert "processing" in data["tags"]

    def test_create_manual_report_validation(self, client: TestClient) -> None:
        """Test validation when creating manual report."""
        # Missing required message
        response = client.post(
            "/api/v1/crash-reports",
            json={
                "severity": "high",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_manual_report_invalid_severity(self, client: TestClient) -> None:
        """Test creating manual report with invalid severity."""
        response = client.post(
            "/api/v1/crash-reports",
            json={
                "message": "Test",
                "severity": "invalid_severity",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDeleteCrashReport:
    """Tests for DELETE /api/v1/crash-reports/{report_id} endpoint."""

    def test_delete_report_success(self, client: TestClient, crash_reporter: CrashReporter) -> None:
        """Test deleting an existing report."""
        report = crash_reporter.report_manual("Test to delete")

        response = client.delete(f"/api/v1/crash-reports/{report.report_id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's deleted
        get_response = client.get(f"/api/v1/crash-reports/{report.report_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_report_not_found(self, client: TestClient) -> None:
        """Test deleting non-existent report returns 404."""
        response = client.delete("/api/v1/crash-reports/non-existent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestClearAllCrashReports:
    """Tests for DELETE /api/v1/crash-reports (clear all) endpoint."""

    def test_clear_all_reports(self, client: TestClient, crash_reporter: CrashReporter) -> None:
        """Test clearing all crash reports."""
        # Create some reports
        for i in range(3):
            crash_reporter.report_manual(f"Report {i}")

        # Verify they exist
        list_response = client.get("/api/v1/crash-reports")
        assert list_response.json()["total_count"] == 3

        # Clear all
        response = client.delete("/api/v1/crash-reports")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 3

        # Verify empty
        list_response = client.get("/api/v1/crash-reports")
        assert list_response.json()["total_count"] == 0

    def test_clear_all_when_empty(self, client: TestClient) -> None:
        """Test clearing when no reports exist."""
        response = client.delete("/api/v1/crash-reports")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0


class TestCrashReportWithoutReporter:
    """Tests for crash API when reporter is not initialized."""

    def test_list_without_reporter(self) -> None:
        """Test listing reports without initialized reporter."""
        # Ensure no reporter
        shutdown_crash_reporting()

        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            app = create_app()

        with TestClient(app) as client:
            response = client.get("/api/v1/crash-reports")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert "not initialized" in data["detail"].lower()

    def test_get_without_reporter(self) -> None:
        """Test getting report without initialized reporter."""
        shutdown_crash_reporting()

        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            app = create_app()

        with TestClient(app) as client:
            response = client.get("/api/v1/crash-reports/some-id")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_create_without_reporter(self) -> None:
        """Test creating report without initialized reporter."""
        shutdown_crash_reporting()

        with patch("video2d3d.web.health.is_cuda_available", return_value=False):
            app = create_app()

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/crash-reports",
                json={"message": "Test"},
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestCrashAPIOpenAPI:
    """Tests for OpenAPI documentation of crash report endpoints."""

    def test_crash_endpoints_in_openapi(self, app: FastAPI) -> None:
        """Test that crash endpoints are in OpenAPI schema."""
        openapi = app.openapi()
        assert "/api/v1/crash-reports" in openapi["paths"]

    def test_crash_endpoints_have_tag(self, app: FastAPI) -> None:
        """Test that crash endpoints have correct tag."""
        openapi = app.openapi()

        # GET list
        get_tags = openapi["paths"]["/api/v1/crash-reports"]["get"]["tags"]
        assert "Crash Reports" in get_tags

        # POST create
        post_tags = openapi["paths"]["/api/v1/crash-reports"]["post"]["tags"]
        assert "Crash Reports" in post_tags

        # GET by ID
        get_id_tags = openapi["paths"]["/api/v1/crash-reports/{report_id}"]["get"]["tags"]
        assert "Crash Reports" in get_id_tags

    def test_crash_endpoints_have_descriptions(self, app: FastAPI) -> None:
        """Test that crash endpoints have descriptions."""
        openapi = app.openapi()

        get_list = openapi["paths"]["/api/v1/crash-reports"]["get"]
        assert "summary" in get_list
        assert "description" in get_list or "summary" in get_list
