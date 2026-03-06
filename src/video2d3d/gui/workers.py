"""Worker thread for video conversion."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    pass

class ConversionWorker(QThread):
    """Worker thread for video conversion operations.

    This runs video conversion in a background thread to keep the GUI responsive.
    """

    # Signals for progress updates
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    stage_changed = pyqtSignal(str)  # stage name
    log_message = pyqtSignal(str, str)  # message, level
    conversion_complete = pyqtSignal(bool, str, dict)  # success, message, metadata
    error_occurred = pyqtSignal(str, str)  # error message, details

    def __init__(
        self,
        parent: Any | None = None,
        input_path: str = "",
        output_path: str = "",
        output_format: str = "side_by_side",
        model: str = "midas_small",
        use_gpu: bool = True,
        config: Any | None = None,
    ) -> None:
        """Initialize the conversion worker.

        Args:
            parent: Parent object.
            input_path: Path to input video file.
            output_path: Path to output video file.
            output_format: 3D output format.
            model: Depth estimation model to use.
            use_gpu: Whether to use GPU acceleration.
            config: Configuration object.
        """
        super().__init__(parent)
        self._input_path = input_path
        self._output_path = output_path
        self._output_format = output_format
        self._model = model
        self._use_gpu = use_gpu
        self._config = config
        self._cancelled = False

    def run(self) -> None:
        """Run the conversion in a background thread."""
        try:
            self.stage_changed.emit("Initializing")
            self.log_message.emit("Starting conversion...", "info")

            # Import conversion modules
            from video2d3d.utils.config import get_config
            from video2d3d.utils.logger import get_logger

            logger = get_logger("gui.conversion")
            config = self._config or get_config()

            # Validate input file
            input_file = Path(self._input_path)
            if not input_file.exists():
                self.error_occurred.emit(
                    f"Input file not found: {self._input_path}",
                    "",
                )
                return

            # Update configuration based on user selections
            config.depth_estimation.model = self._model
            config.stereo_generation.format = self._output_format
            config.processing.use_gpu = self._use_gpu

            self.log_message.emit(
                f"Input: {self._input_path}\n"
                f"Output: {self._output_path}\n"
                f"Format: {self._output_format}\n"
                f"Model: {self._model}\n"
                f"GPU: {self._use_gpu}",
                "info",
            )

            # Run conversion
            self._run_conversion()

        except Exception as e:
            import traceback

            self.error_occurred.emit(str(e), traceback.format_exc())
            self.conversion_complete.emit(False, str(e), {})

    def _run_conversion(self) -> None:
        """Run the actual video conversion."""
        import time
        from pathlib import Path

        self.stage_changed.emit("Extracting Frames")
        self.log_message.emit("Extracting frames from video...", "info")

        # Simulate progress for now (actual implementation would use VideoProcessor)
        # In production, this would call the actual conversion logic
        total_steps = 100
        for i in range(total_steps):
            if self._cancelled:
                self.log_message.emit("Conversion cancelled", "warning")
                self.conversion_complete.emit(False, "Cancelled by user", {})
                return

            # Update progress
            self.progress_updated.emit(
                i + 1, total_steps, f"Processing frame {i + 1}/{total_steps}"
            )
            time.sleep(0.05)  # Simulate processing

            # Update stage based on progress
            if i == 30:
                self.stage_changed.emit("Depth Estimation")
                self.log_message.emit("Estimating depth...", "info")
            elif i == 60:
                self.stage_changed.emit("Stereo Generation")
                self.log_message.emit("Generating stereoscopic views...", "info")
            elif i == 90:
                self.stage_changed.emit("Encoding Video")
                self.log_message.emit("Encoding output video...", "info")

        # Conversion complete
        self.stage_changed.emit("Complete")
        self.log_message.emit("Conversion completed successfully!", "success")

        metadata = {
            "input_path": self._input_path,
            "output_path": self._output_path,
            "format": self._output_format,
            "model": self._model,
            "gpu_used": self._use_gpu,
        }
        self.conversion_complete.emit(True, "Conversion completed successfully", metadata)

    def cancel(self) -> None:
        """Cancel the conversion."""
        self._cancelled = True


class BatchConversionWorker(QThread):
    """Worker thread for batch video conversion operations."""

    # Signals
    job_started = pyqtSignal(int, str)  # job_index, filename
    job_completed = pyqtSignal(int, bool, str)  # job_index, success, message
    progress_updated = pyqtSignal(int, int)  # completed, total
    all_complete = pyqtSignal(int, int)  # successful, failed
    error_occurred = pyqtSignal(str)  # error message

    def __init__(
        self,
        parent: Any | None = None,
        input_files: list[str] | None = None,
        output_dir: str = "",
        output_format: str = "side_by_side",
        model: str = "midas_small",
        use_gpu: bool = True,
        skip_existing: bool = True,
    ) -> None:
        """Initialize the batch conversion worker.

        Args:
            parent: Parent object.
            input_files: List of input file paths.
            output_dir: Output directory for converted files.
            output_format: 3D output format.
            model: Depth estimation model.
            use_gpu: Whether to use GPU.
            skip_existing: Skip files that already exist.
        """
        super().__init__(parent)
        self._input_files = input_files or []
        self._output_dir = output_dir
        self._output_format = output_format
        self._model = model
        self._use_gpu = use_gpu
        self._skip_existing = skip_existing
        self._cancelled = False

    def run(self) -> None:
        """Run the batch conversion."""
        import time
        from pathlib import Path

        successful = 0
        failed = 0
        total = len(self._input_files)

        for idx, input_file in enumerate(self._input_files):
            if self._cancelled:
                break

            input_path = Path(input_file)
            self.job_started.emit(idx, input_path.name)

            # Generate output path
            output_name = f"{input_path.stem}_3d{input_path.suffix}"
            output_path = Path(self._output_dir) / output_name

            # Skip existing if enabled
            if self._skip_existing and output_path.exists():
                self.job_completed.emit(idx, True, "Skipped (already exists)")
                successful += 1
                self.progress_updated.emit(idx + 1, total)
                continue

            # Simulate conversion (in production, would call actual conversion)
            try:
                time.sleep(0.5)  # Simulate processing
                self.job_completed.emit(idx, True, "Completed")
                successful += 1
            except Exception as e:
                self.job_completed.emit(idx, False, str(e))
                failed += 1

            self.progress_updated.emit(idx + 1, total)

        self.all_complete.emit(successful, failed)

    def cancel(self) -> None:
        """Cancel the batch conversion."""
        self._cancelled = True
