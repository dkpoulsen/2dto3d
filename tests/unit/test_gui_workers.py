"""Unit tests for GUI worker threads.

Tests cover:
- ConversionWorker initialization and execution
- BatchConversionWorker initialization and execution
- Signal emissions
- Cancellation handling
- Error handling
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Skip all tests in this module if PyQt6 is not available
# Must be before any PyQt6 imports
_pyqt6_available = True
try:
    from PyQt6.QtCore import QThread
except ImportError:
    _pyqt6_available = False
    pytestmark = pytest.mark.skip(reason="PyQt6 not available")

if TYPE_CHECKING:
    from collections.abc import Generator

if _pyqt6_available:
    from video2d3d.gui.workers import BatchConversionWorker, ConversionWorker


@pytest.fixture
def qapp() -> Generator[MagicMock, None, None]:
    """Create a mock QApplication instance."""
    with patch("PyQt6.QtWidgets.QApplication.instance") as mock_instance:
        mock_app = MagicMock()
        mock_instance.return_value = mock_app
        yield mock_app


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Create a sample video file for testing."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b"fake video content")
    return video_path


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestConversionWorker:
    """Tests for ConversionWorker class."""

    def test_initialization(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test ConversionWorker initialization with default parameters."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        assert worker._input_path == str(sample_video)
        assert worker._output_path == str(sample_video.parent / "output.mp4")
        assert worker._output_format == "side_by_side"
        assert worker._model == "midas_small"
        assert worker._use_gpu is True
        assert worker._cancelled is False

    def test_initialization_with_custom_params(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test ConversionWorker initialization with custom parameters."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
            output_format="anaglyph",
            model="dpt_large",
            use_gpu=False,
        )

        assert worker._output_format == "anaglyph"
        assert worker._model == "dpt_large"
        assert worker._use_gpu is False

    def test_signals_defined(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that all required signals are defined."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        # Check signals exist
        assert hasattr(worker, "progress_updated")
        assert hasattr(worker, "stage_changed")
        assert hasattr(worker, "log_message")
        assert hasattr(worker, "conversion_complete")
        assert hasattr(worker, "error_occurred")

    def test_cancel_method(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that cancel method sets _cancelled flag."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        assert worker._cancelled is False
        worker.cancel()
        assert worker._cancelled is True

    def test_run_missing_input_file(self, qapp: MagicMock, tmp_path: Path) -> None:
        """Test run method handles missing input file."""
        worker = ConversionWorker(
            input_path=str(tmp_path / "nonexistent.mp4"),
            output_path=str(tmp_path / "output.mp4"),
        )

        # Track signal emissions
        error_messages = []
        worker.error_occurred.connect(lambda msg, details: error_messages.append(msg))

        # Run the worker (synchronously for testing)
        worker.run()

        # Check error was emitted
        assert len(error_messages) > 0
        assert "Input file not found" in error_messages[0]

    def test_run_with_valid_input(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test run method with valid input file."""
        output_path = sample_video.parent / "output_3d.mp4"
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(output_path),
        )

        # Track signal emissions
        complete_results = []
        worker.conversion_complete.connect(
            lambda success, msg, metadata: complete_results.append(
                {"success": success, "message": msg, "metadata": metadata}
            )
        )

        # Run the worker (this is a simulation in the worker)
        worker.run()

        # Check completion signal was emitted
        assert len(complete_results) > 0
        result = complete_results[0]
        assert result["success"] is True
        assert "metadata" in result
        assert result["metadata"]["input_path"] == str(sample_video)
        assert result["metadata"]["output_format"] == "side_by_side"

    def test_run_emits_progress_signals(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that run emits progress signals."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        # Track progress updates
        progress_updates = []
        worker.progress_updated.connect(
            lambda current, total, msg: progress_updates.append(
                {"current": current, "total": total, "message": msg}
            )
        )

        # Run the worker
        worker.run()

        # Check progress signals were emitted
        assert len(progress_updates) > 0
        # First progress should be frame 1
        assert progress_updates[0]["current"] == 1
        assert progress_updates[0]["total"] == 100

    def test_run_emits_stage_changes(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that run emits stage change signals."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        # Track stage changes
        stages = []
        worker.stage_changed.connect(lambda stage: stages.append(stage))

        # Run the worker
        worker.run()

        # Check stages were emitted
        assert len(stages) > 0
        assert "Initializing" in stages
        assert "Complete" in stages

    def test_run_handles_cancellation(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that run respects cancellation."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )

        # Track completion
        complete_results = []
        worker.conversion_complete.connect(
            lambda success, msg, metadata: complete_results.append(
                {"success": success, "message": msg}
            )
        )

        # Cancel before running
        worker.cancel()
        worker.run()

        # Check cancellation was handled
        assert len(complete_results) > 0
        assert complete_results[0]["success"] is False
        assert "Cancelled" in complete_results[0]["message"]


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestBatchConversionWorker:
    """Tests for BatchConversionWorker class."""

    def test_initialization(self, qapp: MagicMock) -> None:
        """Test BatchConversionWorker initialization with default parameters."""
        worker = BatchConversionWorker(
            input_files=["/path/to/video1.mp4", "/path/to/video2.mp4"],
            output_dir="/path/to/output",
        )

        assert len(worker._input_files) == 2
        assert worker._output_dir == "/path/to/output"
        assert worker._output_format == "side_by_side"
        assert worker._model == "midas_small"
        assert worker._use_gpu is True
        assert worker._skip_existing is True
        assert worker._cancelled is False

    def test_initialization_with_custom_params(self, qapp: MagicMock) -> None:
        """Test BatchConversionWorker initialization with custom parameters."""
        worker = BatchConversionWorker(
            input_files=["/path/to/video.mp4"],
            output_dir="/output",
            output_format="anaglyph",
            model="dpt_large",
            use_gpu=False,
            skip_existing=False,
        )

        assert worker._output_format == "anaglyph"
        assert worker._model == "dpt_large"
        assert worker._use_gpu is False
        assert worker._skip_existing is False

    def test_signals_defined(self, qapp: MagicMock) -> None:
        """Test that all required signals are defined."""
        worker = BatchConversionWorker(
            input_files=[],
            output_dir="/output",
        )

        # Check signals exist
        assert hasattr(worker, "job_started")
        assert hasattr(worker, "job_completed")
        assert hasattr(worker, "progress_updated")
        assert hasattr(worker, "all_complete")
        assert hasattr(worker, "error_occurred")

    def test_cancel_method(self, qapp: MagicMock) -> None:
        """Test that cancel method sets _cancelled flag."""
        worker = BatchConversionWorker(
            input_files=[],
            output_dir="/output",
        )

        assert worker._cancelled is False
        worker.cancel()
        assert worker._cancelled is True

    def test_run_with_no_files(self, qapp: MagicMock) -> None:
        """Test run method handles empty file list."""
        worker = BatchConversionWorker(
            input_files=[],
            output_dir="/output",
        )

        # Track completion
        complete_results = []
        worker.all_complete.connect(
            lambda successful, failed: complete_results.append(
                {"successful": successful, "failed": failed}
            )
        )

        # Run the worker
        worker.run()

        # Check completion
        assert len(complete_results) > 0
        assert complete_results[0]["successful"] == 0
        assert complete_results[0]["failed"] == 0

    def test_run_processes_multiple_files(
        self, qapp: MagicMock, sample_video: Path, tmp_path: Path
    ) -> None:
        """Test that run processes multiple files."""
        # Create multiple test files
        video2 = tmp_path / "test_video2.mp4"
        video2.write_bytes(b"fake video content 2")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        worker = BatchConversionWorker(
            input_files=[str(sample_video), str(video2)],
            output_dir=str(output_dir),
        )

        # Track job completions
        job_completions = []
        worker.job_completed.connect(
            lambda idx, success, msg: job_completions.append(
                {"index": idx, "success": success, "message": msg}
            )
        )

        # Track overall completion
        complete_results = []
        worker.all_complete.connect(
            lambda successful, failed: complete_results.append(
                {"successful": successful, "failed": failed}
            )
        )

        # Run the worker
        worker.run()

        # Check all jobs were processed
        assert len(job_completions) == 2
        assert len(complete_results) > 0
        assert complete_results[0]["successful"] == 2

    def test_run_emits_progress_updates(self, qapp: MagicMock, tmp_path: Path) -> None:
        """Test that run emits progress updates."""
        video1 = tmp_path / "video1.mp4"
        video1.write_bytes(b"fake video")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        worker = BatchConversionWorker(
            input_files=[str(video1)],
            output_dir=str(output_dir),
        )

        # Track progress updates
        progress_updates = []
        worker.progress_updated.connect(
            lambda completed, total: progress_updates.append(
                {"completed": completed, "total": total}
            )
        )

        # Run the worker
        worker.run()

        # Check progress was reported
        assert len(progress_updates) > 0
        # Final progress should be 1/1
        final = progress_updates[-1]
        assert final["completed"] == 1
        assert final["total"] == 1

    def test_run_handles_cancellation(
        self, qapp: MagicMock, sample_video: Path, tmp_path: Path
    ) -> None:
        """Test that run respects cancellation during batch processing."""
        video2 = tmp_path / "video2.mp4"
        video2.write_bytes(b"fake video 2")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        worker = BatchConversionWorker(
            input_files=[str(sample_video), str(video2)],
            output_dir=str(output_dir),
        )

        # Track completion
        complete_results = []
        worker.all_complete.connect(
            lambda successful, failed: complete_results.append(
                {"successful": successful, "failed": failed}
            )
        )

        # Cancel before running
        worker.cancel()
        worker.run()

        # Check no jobs completed
        assert len(complete_results) > 0
        # Should have stopped immediately due to cancellation
        assert complete_results[0]["successful"] == 0

    def test_run_skips_existing_files(self, qapp: MagicMock, tmp_path: Path) -> None:
        """Test that run skips files that already exist when skip_existing is True."""
        video1 = tmp_path / "video.mp4"
        video1.write_bytes(b"fake video")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create existing output file
        existing_output = output_dir / "video_3d.mp4"
        existing_output.write_bytes(b"existing output")

        worker = BatchConversionWorker(
            input_files=[str(video1)],
            output_dir=str(output_dir),
            skip_existing=True,
        )

        # Track job completions
        job_completions = []
        worker.job_completed.connect(
            lambda idx, success, msg: job_completions.append(
                {"index": idx, "success": success, "message": msg}
            )
        )

        # Run the worker
        worker.run()

        # Check file was skipped
        assert len(job_completions) > 0
        assert "Skipped" in job_completions[0]["message"]


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestWorkerThreadInheritance:
    """Tests for QThread inheritance."""

    def test_conversion_worker_is_qthread(self, qapp: MagicMock, sample_video: Path) -> None:
        """Test that ConversionWorker inherits from QThread."""
        worker = ConversionWorker(
            input_path=str(sample_video),
            output_path=str(sample_video.parent / "output.mp4"),
        )
        assert isinstance(worker, QThread)

    def test_batch_worker_is_qthread(self, qapp: MagicMock) -> None:
        """Test that BatchConversionWorker inherits from QThread."""
        worker = BatchConversionWorker(
            input_files=[],
            output_dir="/output",
        )
        assert isinstance(worker, QThread)
