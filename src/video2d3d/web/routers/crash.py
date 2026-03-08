"""API router for crash report management.

This router provides endpoints for:
- Listing crash reports
- Getting individual crash report details
- Creating manual crash reports
- Deleting crash reports

All endpoints require crash reporting to be initialized.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from video2d3d.crash import CrashReport, CrashSeverity, get_crash_reporter
from video2d3d.crash.models import CrashType
from video2d3d.utils.logger import get_logger
from video2d3d.web.schemas import (
    CrashReportListResponse,
    CrashReportResponse,
    CrashReportSummaryResponse,
    CrashSeverityResponse,
    CrashTypeResponse,
    ErrorResponse,
    ManualCrashReportRequest,
)

logger = get_logger("web.crash")

router = APIRouter()


def _convert_crash_type(ct: CrashType) -> CrashTypeResponse:
    """Convert internal crash type to response type."""
    return CrashTypeResponse(ct.value)


def _convert_severity(s: CrashSeverity) -> CrashSeverityResponse:
    """Convert internal severity to response type."""
    return CrashSeverityResponse(s.value)


def _report_to_response(report: CrashReport) -> CrashReportResponse:
    """Convert internal CrashReport to API response model."""
    from video2d3d.web.schemas import (
        ActiveJobInfoResponse,
        GPUInfoResponse,
        MemoryInfoResponse,
        ProcessInfoResponse,
        SystemStateResponse,
    )

    system_state_response = None
    if report.system_state:
        ss = report.system_state
        system_state_response = SystemStateResponse(
            timestamp=ss.timestamp,
            uptime_seconds=ss.uptime_seconds,
            platform_system=ss.platform_system,
            platform_python_version=ss.platform_python_version,
            gpu=GPUInfoResponse(
                available=ss.gpu.available,
                device_name=ss.gpu.device_name,
                memory_used_mb=ss.gpu.memory_used_mb,
                memory_total_mb=ss.gpu.memory_total_mb,
                memory_utilization_percent=ss.gpu.memory_utilization_percent,
            ),
            memory=MemoryInfoResponse(
                total_mb=ss.memory.total_mb,
                available_mb=ss.memory.available_mb,
                used_mb=ss.memory.used_mb,
                utilization_percent=ss.memory.utilization_percent,
            ),
            process=ProcessInfoResponse(
                pid=ss.process.pid,
                cpu_percent=ss.process.cpu_percent,
                memory_rss_mb=ss.process.memory_rss_mb,
                num_threads=ss.process.num_threads,
                uptime_seconds=ss.process.uptime_seconds,
            ),
            active_jobs=[
                ActiveJobInfoResponse(
                    job_id=j.job_id,
                    status=j.status,
                    input_file=j.input_file,
                    output_file=j.output_file,
                    progress_percent=j.progress_percent,
                    current_stage=j.current_stage,
                    started_at=j.started_at,
                    frames_processed=j.frames_processed,
                    total_frames=j.total_frames,
                    error_message=j.error_message,
                )
                for j in ss.active_jobs
            ],
            queue_stats=ss.queue_stats,
            app_version=ss.app_version,
        )

    return CrashReportResponse(
        report_id=report.report_id,
        created_at=report.created_at,
        crash_type=_convert_crash_type(report.crash_type),
        severity=_convert_severity(report.severity),
        exception_type=report.exception_type,
        exception_message=report.exception_message,
        exception_traceback=report.exception_traceback,
        exception_module=report.exception_module,
        signal_number=report.signal_number,
        signal_name=report.signal_name,
        context=report.context,
        tags=report.tags,
        user_message=report.user_message,
        system_state=system_state_response,
        log_excerpts=report.log_excerpts,
        recovered=report.recovered,
        recovery_action=report.recovery_action,
    )


def _summary_to_response(report: CrashReport) -> CrashReportSummaryResponse:
    """Convert CrashReport to summary response."""
    return CrashReportSummaryResponse(
        report_id=report.report_id,
        created_at=report.created_at,
        crash_type=_convert_crash_type(report.crash_type),
        severity=_convert_severity(report.severity),
        exception_type=report.exception_type,
        exception_message=report.exception_message[:200] if report.exception_message else "",
        recovered=report.recovered,
    )


@router.get(
    "",
    response_model=CrashReportListResponse,
    summary="List crash reports",
    description="Get a paginated list of crash reports sorted by creation time (newest first).",
    responses={
        200: {"description": "List of crash reports"},
        503: {"model": ErrorResponse, "description": "Crash reporting not initialized"},
    },
)
async def list_crash_reports(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of reports per page"),
    severity: Optional[CrashSeverityResponse] = Query(None, description="Filter by severity"),
):
    """List all crash reports with pagination.

    Returns a paginated list of crash report summaries sorted by creation time
    in descending order (newest first).
    """
    crash_reporter = get_crash_reporter()
    if crash_reporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crash reporting not initialized",
        )

    severity_filter = None
    if severity:
        severity_filter = CrashSeverity(severity.value)

    report_list = crash_reporter.list_reports(
        page=page,
        page_size=page_size,
        severity=severity_filter,
    )

    return CrashReportListResponse(
        reports=[
            _summary_to_response(CrashReport.from_dict(r.to_dict())) for r in report_list.reports
        ],
        total_count=report_list.total_count,
        page=report_list.page,
        page_size=report_list.page_size,
    )


@router.get(
    "/{report_id}",
    response_model=CrashReportResponse,
    summary="Get crash report details",
    description="Get the full details of a specific crash report by its ID.",
    responses={
        200: {"description": "Crash report details"},
        404: {"model": ErrorResponse, "description": "Crash report not found"},
        503: {"model": ErrorResponse, "description": "Crash reporting not initialized"},
    },
)
async def get_crash_report(report_id: str):
    """Get detailed information about a specific crash report.

    Returns the full crash report including system state, traceback,
    and any additional context captured at crash time.
    """
    crash_reporter = get_crash_reporter()
    if crash_reporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crash reporting not initialized",
        )

    report = crash_reporter.get_report(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crash report not found: {report_id}",
        )

    return _report_to_response(report)


@router.post(
    "",
    response_model=CrashReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a manual crash report",
    description="Create a manual crash report for an issue or error encountered by a user.",
    responses={
        201: {"description": "Crash report created"},
        503: {"model": ErrorResponse, "description": "Crash reporting not initialized"},
    },
)
async def create_manual_crash_report(request: ManualCrashReportRequest):
    """Create a manual crash report.

    This endpoint allows users or client applications to submit crash reports
    for issues that weren't automatically captured. Useful for reporting:
    - Client-side errors
    - User-reported bugs
    - Performance issues
    """
    crash_reporter = get_crash_reporter()
    if crash_reporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crash reporting not initialized",
        )

    severity = CrashSeverity(request.severity.value)

    report = crash_reporter.report_manual(
        message=request.message,
        context=request.context,
        tags=request.tags,
        severity=severity,
    )

    logger.info(f"Manual crash report created: {report.report_id}")

    return _report_to_response(report)


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a crash report",
    description="Delete a specific crash report by its ID.",
    responses={
        204: {"description": "Crash report deleted"},
        404: {"model": ErrorResponse, "description": "Crash report not found"},
        503: {"model": ErrorResponse, "description": "Crash reporting not initialized"},
    },
)
async def delete_crash_report(report_id: str):
    """Delete a crash report.

    Permanently removes a crash report from the system.
    Use with caution as this action cannot be undone.
    """
    crash_reporter = get_crash_reporter()
    if crash_reporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crash reporting not initialized",
        )

    deleted = crash_reporter.delete_report(report_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crash report not found: {report_id}",
        )

    logger.info(f"Crash report deleted: {report_id}")
    return None


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Clear all crash reports",
    description="Delete all crash reports from the system.",
    responses={
        200: {"description": "Number of crash reports deleted"},
        503: {"model": ErrorResponse, "description": "Crash reporting not initialized"},
    },
)
async def clear_all_crash_reports():
    """Clear all crash reports.

    Permanently removes all crash reports from the system.
    Use with caution as this action cannot be undone.
    """
    crash_reporter = get_crash_reporter()
    if crash_reporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crash reporting not initialized",
        )

    count = crash_reporter.clear_reports()
    logger.info(f"Cleared {count} crash reports")

    return {"deleted_count": count}
