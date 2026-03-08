"""Unit tests for web API exceptions.

Tests cover:
- Exception class hierarchy
- Exception attributes (message, status_code, error_type, detail)
- Exception handler functions
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.web.exceptions import (
    APIError,
    FileNotFoundError,
    FileSizeExceededError,
    FileUploadError,
    JobNotCancellableError,
    JobNotFoundError,
    JobNotRetryableError,
    ProcessingError,
    QueueNotRunningError,
    RateLimitExceededError,
    UnsupportedFormatError,
    ValidationError,
    register_exception_handlers,
)


class TestAPIError:
    """Tests for APIError base class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = APIError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.error_type == "api_error"
        assert error.detail == {}

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        error = APIError(
            message="Custom error",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="custom_error",
            detail={"key": "value"},
        )
        assert error.message == "Custom error"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "custom_error"
        assert error.detail == {"key": "value"}

    def test_inherits_from_exception(self) -> None:
        """Test APIError inherits from Exception."""
        error = APIError("Test error")
        assert isinstance(error, Exception)


class TestFileNotFoundError:
    """Tests for FileNotFoundError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = FileNotFoundError(file_id="test-id")
        assert error.message == "File not found"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.error_type == "file_not_found"
        assert error.file_id == "test-id"
        assert error.detail == {"file_id": "test-id"}

    def test_custom_message(self) -> None:
        """Test custom message."""
        error = FileNotFoundError(
            file_id="test-id",
            message="Video file not found",
        )
        assert error.message == "Video file not found"


class TestJobNotFoundError:
    """Tests for JobNotFoundError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = JobNotFoundError(job_id="job-id")
        assert error.message == "Job not found"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.error_type == "job_not_found"
        assert error.job_id == "job-id"
        assert error.detail == {"job_id": "job-id"}


class TestValidationError:
    """Tests for ValidationError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "validation_error"
        assert error.detail == {}

    def test_with_field_and_value(self) -> None:
        """Test with field and value details."""
        error = ValidationError(
            message="Invalid field value",
            field="priority",
            value="invalid",
        )
        assert error.detail == {"field": "priority", "value": "invalid"}


class TestFileUploadError:
    """Tests for FileUploadError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = FileUploadError("Upload failed")
        assert error.message == "Upload failed"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "file_upload_error"

    def test_with_details(self) -> None:
        """Test with filename and reason."""
        error = FileUploadError(
            message="Upload failed",
            filename="video.mp4",
            reason="Connection lost",
        )
        assert error.detail == {
            "filename": "video.mp4",
            "reason": "Connection lost",
        }


class TestFileSizeExceededError:
    """Tests for FileSizeExceededError class."""

    def test_calculates_detail(self) -> None:
        """Test detail is calculated correctly."""
        error = FileSizeExceededError(
            max_size_mb=500,
            actual_size_mb=750,
        )
        assert error.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert error.error_type == "file_too_large"
        assert "500MB" in error.message
        assert error.detail == {
            "max_size_mb": 500,
            "actual_size_mb": 750,
        }


class TestUnsupportedFormatError:
    """Tests for UnsupportedFormatError class."""

    def test_calculates_detail(self) -> None:
        """Test detail is calculated correctly."""
        error = UnsupportedFormatError(
            format=".txt",
            supported_formats=[".mp4", ".avi", ".mov"],
        )
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "unsupported_format"
        assert ".txt" in error.message
        assert error.detail == {
            "format": ".txt",
            "supported_formats": [".mp4", ".avi", ".mov"],
        }


class TestQueueNotRunningError:
    """Tests for QueueNotRunningError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = QueueNotRunningError()
        assert error.message == "Processing queue is not running"
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert error.error_type == "queue_not_running"


class TestJobNotRetryableError:
    """Tests for JobNotRetryableError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = JobNotRetryableError(
            job_id="job-id",
            status="completed",
        )
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "job_not_retryable"
        assert error.detail == {"job_id": "job-id", "status": "completed"}

    def test_custom_reason(self) -> None:
        """Test custom reason message."""
        error = JobNotRetryableError(
            job_id="job-id",
            status="completed",
            reason="Job already completed successfully",
        )
        assert error.message == "Job already completed successfully"


class TestJobNotCancellableError:
    """Tests for JobNotCancellableError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = JobNotCancellableError(
            job_id="job-id",
            status="completed",
        )
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_type == "job_not_cancellable"
        assert error.detail == {"job_id": "job-id", "status": "completed"}


class TestProcessingError:
    """Tests for ProcessingError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = ProcessingError("Processing failed")
        assert error.message == "Processing failed"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.error_type == "processing_error"

    def test_with_job_and_stage(self) -> None:
        """Test with job_id and stage details."""
        error = ProcessingError(
            message="Depth estimation failed",
            job_id="job-id",
            stage="depth_estimation",
        )
        assert error.detail == {
            "job_id": "job-id",
            "stage": "depth_estimation",
        }


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        error = RateLimitExceededError(limit="60 per 1 minute")
        assert error.message == "Rate limit exceeded"
        assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert error.error_type == "rate_limit_exceeded"
        assert error.detail == {"limit": "60 per 1 minute"}

    def test_with_retry_after(self) -> None:
        """Test with retry_after value."""
        error = RateLimitExceededError(
            limit="10 per 1 minute",
            retry_after=60,
        )
        assert error.detail == {
            "limit": "10 per 1 minute",
            "retry_after": 60,
        }

    def test_custom_message(self) -> None:
        """Test custom error message."""
        error = RateLimitExceededError(
            limit="100 per 1 hour",
            message="API rate limit exceeded, please try again later",
        )
        assert error.message == "API rate limit exceeded, please try again later"

    def test_429_status_code(self) -> None:
        """Test that 429 status code is always used."""
        error = RateLimitExceededError(limit="any limit")
        assert error.status_code == 429


class TestExceptionHandlers:
    """Tests for exception handler functions."""

    @pytest.fixture
    def app(self) -> Generator[FastAPI, None, None]:
        """Create a test FastAPI app with exception handlers."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-api-error")
        async def raise_api_error():
            raise APIError("Test API error", status_code=status.HTTP_400_BAD_REQUEST)

        @app.get("/test-file-not-found")
        async def raise_file_not_found():
            raise FileNotFoundError(file_id="test-file-id")

        @app.get("/test-http-error")
        async def raise_http_error():
            raise HTTPException(status_code=403, detail="Forbidden")

        @app.get("/test-generic-error")
        async def raise_generic_error():
            raise RuntimeError("Unexpected error")

        yield app

    @pytest.fixture
    def client(self, app: FastAPI) -> Generator[TestClient, None, None]:
        """Create a test client."""
        with TestClient(app) as client:
            yield client

    def test_api_error_handler(self, client: TestClient) -> None:
        """Test APIError handler returns correct response."""
        response = client.get("/test-api-error")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "api_error"
        assert data["message"] == "Test API error"

    def test_file_not_found_handler(self, client: TestClient) -> None:
        """Test FileNotFoundError handler returns correct response."""
        response = client.get("/test-file-not-found")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "file_not_found"
        assert "test-file-id" in str(data["detail"])

    def test_http_exception_handler(self, client: TestClient) -> None:
        """Test HTTPException handler returns correct response."""
        response = client.get("/test-http-error")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["error"] == "http_error"
        assert data["message"] == "Forbidden"

    def test_generic_exception_handler(self, client: TestClient) -> None:
        """Test generic exception handler returns 500."""
        response = client.get("/test-generic-error")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["error"] == "internal_error"
        assert data["message"] == "An unexpected error occurred"


class TestExceptionChaining:
    """Tests for exception chaining and inheritance."""

    def test_all_exceptions_inherit_from_api_error(self) -> None:
        """Test all custom exceptions inherit from APIError."""
        exceptions = [
            FileNotFoundError("id"),
            JobNotFoundError("id"),
            ValidationError("msg"),
            FileUploadError("msg"),
            FileSizeExceededError(100, 200),
            UnsupportedFormatError(".txt", [".mp4"]),
            QueueNotRunningError(),
            JobNotRetryableError("id", "status"),
            JobNotCancellableError("id", "status"),
            ProcessingError("msg"),
            RateLimitExceededError("60 per 1 minute"),
        ]
        for exc in exceptions:
            assert isinstance(exc, APIError)
            assert isinstance(exc, Exception)

    def test_file_not_found_vs_builtin(self) -> None:
        """Test that our FileNotFoundError is distinct from builtin."""
        from video2d3d.web.exceptions import FileNotFoundError as APIFileNotFoundError

        # Our error should not be the builtin
        assert APIFileNotFoundError is not FileNotFoundError  # type: ignore

        # Our error should be an APIError
        error = APIFileNotFoundError(file_id="test")
        assert isinstance(error, APIError)
