"""Unit tests for web API schemas (Pydantic models).

Tests cover:
- Request model validation
- Response model serialization
- Enum values
- Field validators
- Default values
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError as PydanticValidationError

from video2d3d.web.schemas import (
    JobStatusResponse,
    JobPriorityRequest,
    StereoFormat,
    DepthModel,
    JobConfigRequest,
    SubmitJobRequest,
    SubmitBatchRequest,
    UploadResponse,
    JobResultResponse,
    JobResponse,
    JobListResponse,
    SubmitJobResponse,
    QueueStatsResponse,
    CancelJobResponse,
    RetryJobResponse,
    DownloadInfoResponse,
    ErrorResponse,
    HealthCheckResponse,
    APIInfoResponse,
    DepthFocusRequest,
    DepthCurveRequest,
)


class TestEnums:
    """Tests for enum types."""

    def test_job_status_values(self) -> None:
        """Test JobStatusResponse enum values."""
        assert JobStatusResponse.PENDING.value == "pending"
        assert JobStatusResponse.QUEUED.value == "queued"
        assert JobStatusResponse.RUNNING.value == "running"
        assert JobStatusResponse.COMPLETED.value == "completed"
        assert JobStatusResponse.FAILED.value == "failed"
        assert JobStatusResponse.CANCELLED.value == "cancelled"

    def test_job_priority_values(self) -> None:
        """Test JobPriorityRequest enum values."""
        assert JobPriorityRequest.LOW.value == "low"
        assert JobPriorityRequest.NORMAL.value == "normal"
        assert JobPriorityRequest.HIGH.value == "high"
        assert JobPriorityRequest.URGENT.value == "urgent"

    def test_stereo_format_values(self) -> None:
        """Test StereoFormat enum values."""
        assert StereoFormat.SIDE_BY_SIDE.value == "side_by_side"
        assert StereoFormat.ANAGLYPH.value == "anaglyph"
        assert StereoFormat.INTERLACED.value == "interlaced"
        assert StereoFormat.VR.value == "vr"

    def test_depth_model_values(self) -> None:
        """Test DepthModel enum values."""
        assert DepthModel.MIDAS_SMALL.value == "midas_small"
        assert DepthModel.MIDAS_HYBRID.value == "midas_hybrid"
        assert DepthModel.DPT_LARGE.value == "dpt_large"
        assert DepthModel.DPT_HYBRID.value == "dpt_hybrid"


class TestJobConfigRequest:
    """Tests for JobConfigRequest model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = JobConfigRequest()
        assert config.stereo_format == StereoFormat.SIDE_BY_SIDE
        assert config.depth_model == DepthModel.MIDAS_SMALL
        assert config.use_gpu is True
        assert config.quality_preset == "balanced"
        assert config.output_codec == "libx264"
        assert config.output_crf == 23
        assert config.extra_options == {}

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = JobConfigRequest(
            stereo_format=StereoFormat.ANAGLYPH,
            depth_model=DepthModel.DPT_LARGE,
            use_gpu=False,
            quality_preset="quality",
            output_codec="libx265",
            output_crf=18,
            extra_options={"custom_key": "custom_value"},
        )
        assert config.stereo_format == StereoFormat.ANAGLYPH
        assert config.depth_model == DepthModel.DPT_LARGE
        assert config.use_gpu is False
        assert config.quality_preset == "quality"
        assert config.output_codec == "libx265"
        assert config.output_crf == 18
        assert config.extra_options == {"custom_key": "custom_value"}

    def test_crf_validation_min(self) -> None:
        """Test CRF validation for minimum value."""
        config = JobConfigRequest(output_crf=0)
        assert config.output_crf == 0

    def test_crf_validation_max(self) -> None:
        """Test CRF validation for maximum value."""
        config = JobConfigRequest(output_crf=51)
        assert config.output_crf == 51

    def test_crf_validation_below_min(self) -> None:
        """Test CRF validation rejects below minimum."""
        with pytest.raises(PydanticValidationError):
            JobConfigRequest(output_crf=-1)

    def test_crf_validation_above_max(self) -> None:
        """Test CRF validation rejects above maximum."""
        with pytest.raises(PydanticValidationError):
            JobConfigRequest(output_crf=52)

    def test_model_config_example(self) -> None:
        """Test that model_config has example."""
        assert hasattr(JobConfigRequest, "model_config")
        assert "json_schema_extra" in JobConfigRequest.model_config


class TestSubmitJobRequest:
    """Tests for SubmitJobRequest model."""

    def test_required_fields(self) -> None:
        """Test that input_file_id is required."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SubmitJobRequest()
        assert "input_file_id" in str(exc_info.value)

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        request = SubmitJobRequest(input_file_id="test-file-id")
        assert request.input_file_id == "test-file-id"
        assert request.output_filename is None
        assert request.priority == JobPriorityRequest.NORMAL
        assert isinstance(request.config, JobConfigRequest)
        assert request.callback_url is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        request = SubmitJobRequest(
            input_file_id="test-file-id",
            output_filename="output.mp4",
            priority=JobPriorityRequest.HIGH,
            config=JobConfigRequest(stereo_format=StereoFormat.ANAGLYPH),
            callback_url="https://example.com/callback",
        )
        assert request.input_file_id == "test-file-id"
        assert request.output_filename == "output.mp4"
        assert request.priority == JobPriorityRequest.HIGH
        assert request.callback_url == "https://example.com/callback"

    def test_output_filename_sanitization_slash(self) -> None:
        """Test output_filename sanitizes slashes."""
        request = SubmitJobRequest(
            input_file_id="test-id",
            output_filename="../../../malicious.mp4",
        )
        assert "/" not in request.output_filename
        assert "\\" not in request.output_filename

    def test_output_filename_sanitization_backslash(self) -> None:
        """Test output_filename sanitizes backslashes."""
        request = SubmitJobRequest(
            input_file_id="test-id",
            output_filename="..\\..\\malicious.mp4",
        )
        assert "\\" not in request.output_filename

    def test_empty_file_id_rejected(self) -> None:
        """Test empty input_file_id is rejected."""
        with pytest.raises(PydanticValidationError):
            SubmitJobRequest(input_file_id="")


class TestSubmitBatchRequest:
    """Tests for SubmitBatchRequest model."""

    def test_required_fields(self) -> None:
        """Test that input_file_ids is required."""
        with pytest.raises(PydanticValidationError) as exc_info:
            SubmitBatchRequest()
        assert "input_file_ids" in str(exc_info.value)

    def test_empty_list_rejected(self) -> None:
        """Test empty input_file_ids list is rejected."""
        with pytest.raises(PydanticValidationError):
            SubmitBatchRequest(input_file_ids=[])

    def test_valid_list(self) -> None:
        """Test valid input_file_ids list."""
        request = SubmitBatchRequest(input_file_ids=["id1", "id2", "id3"])
        assert len(request.input_file_ids) == 3
        assert request.priority == JobPriorityRequest.NORMAL


class TestResponseModels:
    """Tests for response models."""

    def test_upload_response(self) -> None:
        """Test UploadResponse model."""
        now = datetime.now()
        response = UploadResponse(
            file_id="test-id",
            filename="video.mp4",
            file_size_bytes=1024,
            content_type="video/mp4",
            upload_time=now,
        )
        assert response.file_id == "test-id"
        assert response.filename == "video.mp4"
        assert response.file_size_bytes == 1024
        assert response.content_type == "video/mp4"
        assert response.upload_time == now
        assert response.message == "File uploaded successfully"

    def test_job_result_response(self) -> None:
        """Test JobResultResponse model."""
        result = JobResultResponse(
            success=True,
            output_file_id="output-id",
            output_filename="output_3d.mp4",
            frames_processed=100,
            processing_time_seconds=10.5,
        )
        assert result.success is True
        assert result.output_file_id == "output-id"
        assert result.output_filename == "output_3d.mp4"
        assert result.frames_processed == 100
        assert result.processing_time_seconds == 10.5

    def test_job_result_response_failure(self) -> None:
        """Test JobResultResponse for failure case."""
        result = JobResultResponse(
            success=False,
            error_message="Processing failed",
            error_type="ValueError",
        )
        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.error_type == "ValueError"

    def test_job_response(self) -> None:
        """Test JobResponse model."""
        now = datetime.now()
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.RUNNING,
            priority=JobPriorityRequest.HIGH,
            input_filename="input.mp4",
            progress=0.5,
            current_stage="Processing",
            created_at=now,
        )
        assert response.job_id == "job-id"
        assert response.status == JobStatusResponse.RUNNING
        assert response.priority == JobPriorityRequest.HIGH
        assert response.progress == 0.5
        assert response.current_stage == "Processing"

    def test_job_response_progress_validation(self) -> None:
        """Test JobResponse progress validation."""
        # Valid progress
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.RUNNING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
            progress=0.5,
        )
        assert response.progress == 0.5

    def test_job_response_progress_clamp_high(self) -> None:
        """Test JobResponse progress clamped to 1.0."""
        with pytest.raises(PydanticValidationError):
            JobResponse(
                job_id="job-id",
                status=JobStatusResponse.RUNNING,
                priority=JobPriorityRequest.NORMAL,
                input_filename="input.mp4",
                created_at=datetime.now(),
                progress=1.5,  # Above max
            )

    def test_job_list_response(self) -> None:
        """Test JobListResponse model."""
        response = JobListResponse(
            jobs=[],
            total_count=0,
            page=1,
            page_size=50,
        )
        assert response.jobs == []
        assert response.total_count == 0
        assert response.page == 1
        assert response.page_size == 50

    def test_submit_job_response(self) -> None:
        """Test SubmitJobResponse model."""
        response = SubmitJobResponse(
            job_id="job-id",
            status=JobStatusResponse.PENDING,
            status_url="/api/v1/jobs/job-id",
        )
        assert response.job_id == "job-id"
        assert response.status == JobStatusResponse.PENDING
        assert response.message == "Job submitted successfully"

    def test_cancel_job_response(self) -> None:
        """Test CancelJobResponse model."""
        response = CancelJobResponse(
            job_id="job-id",
            cancelled=True,
        )
        assert response.job_id == "job-id"
        assert response.cancelled is True
        assert response.message == "Job cancelled"

    def test_retry_job_response(self) -> None:
        """Test RetryJobResponse model."""
        response = RetryJobResponse(
            job_id="job-id",
            retried=True,
            retry_count=1,
        )
        assert response.job_id == "job-id"
        assert response.retried is True
        assert response.retry_count == 1

    def test_download_info_response(self) -> None:
        """Test DownloadInfoResponse model."""
        now = datetime.now()
        response = DownloadInfoResponse(
            file_id="file-id",
            filename="output.mp4",
            file_size_bytes=2048,
            content_type="video/mp4",
            download_url="/api/v1/download/file-id",
            created_at=now,
        )
        assert response.file_id == "file-id"
        assert response.file_size_bytes == 2048

    def test_error_response(self) -> None:
        """Test ErrorResponse model."""
        response = ErrorResponse(
            error="validation_error",
            message="Invalid input",
            detail={"field": "file_id"},
            request_id="req-123",
        )
        assert response.error == "validation_error"
        assert response.message == "Invalid input"
        assert response.detail == {"field": "file_id"}
        assert response.request_id == "req-123"

    def test_health_check_response(self) -> None:
        """Test HealthCheckResponse model."""
        response = HealthCheckResponse(
            version="1.0.0",
            uptime_seconds=3600.0,
            queue_running=True,
            gpu_available=True,
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime_seconds == 3600.0
        assert response.queue_running is True

    def test_api_info_response(self) -> None:
        """Test APIInfoResponse model."""
        response = APIInfoResponse(version="1.0.0")
        assert response.name == "2Dto3D Video Converter API"
        assert response.version == "1.0.0"
        assert "jobs" in response.endpoints
        assert "upload" in response.endpoints


class TestQueueStatsResponse:
    """Tests for QueueStatsResponse model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        stats = QueueStatsResponse()
        assert stats.total_jobs == 0
        assert stats.pending_jobs == 0
        assert stats.running_jobs == 0
        assert stats.completed_jobs == 0
        assert stats.failed_jobs == 0
        assert stats.cancelled_jobs == 0
        assert stats.skipped_jobs == 0
        assert stats.total_frames_processed == 0
        assert stats.total_processing_time_seconds == 0.0
        assert stats.average_processing_time_seconds == 0.0
        assert stats.success_rate_percent == 0.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        stats = QueueStatsResponse(
            total_jobs=100,
            pending_jobs=10,
            running_jobs=5,
            completed_jobs=80,
            failed_jobs=5,
            success_rate_percent=94.0,
        )
        assert stats.total_jobs == 100
        assert stats.completed_jobs == 80
        assert stats.success_rate_percent == 94.0


class TestModelSerialization:
    """Tests for model serialization."""

    def test_job_config_request_json(self) -> None:
        """Test JobConfigRequest JSON serialization."""
        config = JobConfigRequest(
            stereo_format=StereoFormat.ANAGLYPH,
            use_gpu=False,
        )
        json_data = config.model_dump()
        assert json_data["stereo_format"] == "anaglyph"
        assert json_data["use_gpu"] is False

    def test_submit_job_request_json(self) -> None:
        """Test SubmitJobRequest JSON serialization."""
        request = SubmitJobRequest(
            input_file_id="test-id",
            priority=JobPriorityRequest.HIGH,
        )
        json_data = request.model_dump()
        assert json_data["input_file_id"] == "test-id"
        assert json_data["priority"] == "high"

    def test_job_response_json(self) -> None:
        """Test JobResponse JSON serialization."""
        now = datetime.now()
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.RUNNING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=now,
        )
        json_data = response.model_dump()
        assert json_data["job_id"] == "job-id"
        assert json_data["status"] == "running"

        assert "request_id" not in json_data


class TestSchedulerFields:
    """Tests for scheduler fields in API schemas."""

    def test_submit_job_request_scheduled_at(self) -> None:
        """Test SubmitJobRequest with scheduled_at field."""
        scheduled = datetime.now() + timedelta(hours=1)
        request = SubmitJobRequest(
            input_file_id="test-file-id",
            scheduled_at=scheduled,
        )
        assert request.scheduled_at == scheduled

    def test_submit_job_request_scheduled_at_none(self) -> None:
        """Test SubmitJobRequest with no scheduled_at (immediate)."""
        request = SubmitJobRequest(input_file_id="test-file-id")
        assert request.scheduled_at is None

    def test_submit_job_request_depends_on(self) -> None:
        """Test SubmitJobRequest with depends_on field."""
        request = SubmitJobRequest(
            input_file_id="test-file-id",
            depends_on=["job-1", "job-2"],
        )
        assert request.depends_on == ["job-1", "job-2"]

    def test_submit_job_request_depends_on_none(self) -> None:
        """Test SubmitJobRequest with no depends_on."""
        request = SubmitJobRequest(input_file_id="test-file-id")
        assert request.depends_on is None

    def test_submit_job_request_scheduler_json(self) -> None:
        """Test SubmitJobRequest JSON serialization with scheduler fields."""
        scheduled = datetime.now() + timedelta(hours=1)
        request = SubmitJobRequest(
            input_file_id="test-file-id",
            scheduled_at=scheduled,
            depends_on=["job-1"],
        )
        json_data = request.model_dump()
        assert "scheduled_at" in json_data
        assert "depends_on" in json_data

    def test_job_response_scheduled_at(self) -> None:
        """Test JobResponse with scheduled_at field."""
        scheduled = datetime.now() + timedelta(hours=1)
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.PENDING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
            scheduled_at=scheduled,
        )
        assert response.scheduled_at == scheduled

    def test_job_response_depends_on(self) -> None:
        """Test JobResponse with depends_on field."""
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.PENDING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
            depends_on=["job-1", "job-2"],
        )
        assert response.depends_on == ["job-1", "job-2"]

    def test_job_response_dependent_jobs(self) -> None:
        """Test JobResponse with dependent_jobs field."""
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.COMPLETED,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
            dependent_jobs=["waiting-1", "waiting-2"],
        )
        assert response.dependent_jobs == ["waiting-1", "waiting-2"]

    def test_job_response_scheduler_defaults(self) -> None:
        """Test JobResponse default values for scheduler fields."""
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.PENDING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
        )
        assert response.scheduled_at is None
        assert response.depends_on == []
        assert response.dependent_jobs == []

    def test_job_response_scheduler_json(self) -> None:
        """Test JobResponse JSON serialization with scheduler fields."""
        response = JobResponse(
            job_id="job-id",
            status=JobStatusResponse.PENDING,
            priority=JobPriorityRequest.NORMAL,
            input_filename="input.mp4",
            created_at=datetime.now(),
            scheduled_at=datetime.now(),
            depends_on=["job-1"],
            dependent_jobs=["waiting-1"],
        )
        json_data = response.model_dump()
        assert "scheduled_at" in json_data
        assert "depends_on" in json_data
        assert "dependent_jobs" in json_data


class TestDepthFocusRequest:
    """Tests for DepthFocusRequest model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        focus = DepthFocusRequest()
        assert focus.enabled is False
        assert focus.focus_depth == 0.5
        assert focus.focus_range == 0.3

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        focus = DepthFocusRequest(
            enabled=True,
            focus_depth=0.7,
            focus_range=0.4,
        )
        assert focus.enabled is True
        assert focus.focus_depth == 0.7
        assert focus.focus_range == 0.4

    def test_focus_depth_validation_min(self) -> None:
        """Test focus_depth validation accepts minimum value (0.0)."""
        focus = DepthFocusRequest(focus_depth=0.0)
        assert focus.focus_depth == 0.0

    def test_focus_depth_validation_max(self) -> None:
        """Test focus_depth validation accepts maximum value (1.0)."""
        focus = DepthFocusRequest(focus_depth=1.0)
        assert focus.focus_depth == 1.0

    def test_focus_depth_validation_below_min(self) -> None:
        """Test focus_depth validation rejects below minimum."""
        with pytest.raises(PydanticValidationError):
            DepthFocusRequest(focus_depth=-0.1)

    def test_focus_depth_validation_above_max(self) -> None:
        """Test focus_depth validation rejects above maximum."""
        with pytest.raises(PydanticValidationError):
            DepthFocusRequest(focus_depth=1.1)

    def test_focus_range_validation_min(self) -> None:
        """Test focus_range validation accepts minimum value (0.0)."""
        focus = DepthFocusRequest(focus_range=0.0)
        assert focus.focus_range == 0.0

    def test_focus_range_validation_max(self) -> None:
        """Test focus_range validation accepts maximum value (1.0)."""
        focus = DepthFocusRequest(focus_range=1.0)
        assert focus.focus_range == 1.0

    def test_focus_range_validation_below_min(self) -> None:
        """Test focus_range validation rejects below minimum."""
        with pytest.raises(PydanticValidationError):
            DepthFocusRequest(focus_range=-0.1)

    def test_focus_range_validation_above_max(self) -> None:
        """Test focus_range validation rejects above maximum."""
        with pytest.raises(PydanticValidationError):
            DepthFocusRequest(focus_range=1.1)

    def test_model_config_example(self) -> None:
        """Test that model_config has example."""
        assert hasattr(DepthFocusRequest, "model_config")
        assert "json_schema_extra" in DepthFocusRequest.model_config

    def test_json_serialization(self) -> None:
        """Test JSON serialization of DepthFocusRequest."""
        focus = DepthFocusRequest(enabled=True, focus_depth=0.6, focus_range=0.2)
        json_data = focus.model_dump()
        assert json_data["enabled"] is True
        assert json_data["focus_depth"] == 0.6
        assert json_data["focus_range"] == 0.2


class TestJobConfigRequestDepthFocus:
    """Tests for depth_focus field in JobConfigRequest."""

    def test_depth_focus_default_none(self) -> None:
        """Test depth_focus defaults to None."""
        config = JobConfigRequest()
        assert config.depth_focus is None

    def test_depth_focus_with_value(self) -> None:
        """Test depth_focus can be set."""
        config = JobConfigRequest(
            depth_focus=DepthFocusRequest(
                enabled=True,
                focus_depth=0.7,
                focus_range=0.4,
            )
        )
        assert config.depth_focus is not None
        assert config.depth_focus.enabled is True
        assert config.depth_focus.focus_depth == 0.7
        assert config.depth_focus.focus_range == 0.4

    def test_depth_focus_serialization(self) -> None:
        """Test depth_focus serialization in JobConfigRequest."""
        config = JobConfigRequest(
            depth_focus=DepthFocusRequest(enabled=True, focus_depth=0.5, focus_range=0.3)
        )
        json_data = config.model_dump()
        assert "depth_focus" in json_data
        assert json_data["depth_focus"]["enabled"] is True


class TestDepthCurveRequest:
    """Tests for DepthCurveRequest model."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        curve = DepthCurveRequest()
        assert curve.enabled is False
        assert curve.preset is None
        assert len(curve.control_points) == 2
        assert curve.control_points[0].x == 0.0
        assert curve.control_points[-1].x == 1.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        curve = DepthCurveRequest(
            enabled=True,
            preset="s_curve",
        )
        assert curve.enabled is True
        assert curve.preset == "s_curve"

    def test_control_point_validation(self) -> None:
        """Test control point validation."""
        from video2d3d.web.schemas import CurveControlPointRequest
        point = CurveControlPointRequest(x=0.5, y=0.7)
        assert point.x == 0.5
        assert point.y == 0.7

    def test_control_point_x_validation_below_min(self) -> None:
        """Test control point x validation rejects below minimum."""
        from video2d3d.web.schemas import CurveControlPointRequest
        with pytest.raises(PydanticValidationError):
            CurveControlPointRequest(x=-0.1, y=0.5)

    def test_control_point_x_validation_above_max(self) -> None:
        """Test control point x validation rejects above maximum."""
        from video2d3d.web.schemas import CurveControlPointRequest
        with pytest.raises(PydanticValidationError):
            CurveControlPointRequest(x=1.1, y=0.5)

    def test_control_point_y_validation_below_min(self) -> None:
        """Test control point y validation rejects below minimum."""
        from video2d3d.web.schemas import CurveControlPointRequest
        with pytest.raises(PydanticValidationError):
            CurveControlPointRequest(x=0.5, y=-0.1)

    def test_control_point_y_validation_above_max(self) -> None:
        """Test control point y validation rejects above maximum."""
        from video2d3d.web.schemas import CurveControlPointRequest
        with pytest.raises(PydanticValidationError):
            CurveControlPointRequest(x=0.5, y=1.1)

    def test_json_serialization(self) -> None:
        """Test JSON serialization of DepthCurveRequest."""
        curve = DepthCurveRequest(enabled=True, preset="s_curve")
        json_data = curve.model_dump()
        assert json_data["enabled"] is True
        assert json_data["preset"] == "s_curve"
