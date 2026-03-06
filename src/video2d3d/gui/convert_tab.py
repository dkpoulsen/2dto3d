"""Single video conversion tab."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from video2d3d.cli import DEPTH_MODELS, OUTPUT_FORMATS
from video2d3d.gui.widgets import FileSelector
from video2d3d.gui.workers import ConversionWorker
from video2d3d.gui.workers import ConversionWorker

if TYPE_CHECKING:
    pass

class ConvertTab(QWidget):
    """Tab for single video conversion."""

    conversion_started = pyqtSignal()
    conversion_finished = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the convert tab.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._worker: ConversionWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Input/Output section
        io_group = QGroupBox("Input / Output")
        io_layout = QVBoxLayout(io_group)

        # Input file selector
        self._input_selector = FileSelector(
            label="Input Video:",
            file_filter="Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)",
            save_mode=False,
        )
        self._input_selector.path_changed.connect(self._on_input_changed)
        io_layout.addWidget(self._input_selector)

        # Output file selector
        self._output_selector = FileSelector(
            label="Output Video:",
            file_filter="Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)",
            save_mode=True,
        )
        io_layout.addWidget(self._output_selector)

        layout.addWidget(io_group)

        # Options section
        options_group = QGroupBox("Conversion Options")
        options_layout = QVBoxLayout(options_group)

        # Output format
        format_layout = QHBoxLayout()
        format_label = QLabel("Output Format:")
        format_label.setMinimumWidth(120)
        self._format_combo = QComboBox()
        for format_id, format_desc in OUTPUT_FORMATS.items():
            self._format_combo.addItem(f"{format_id} - {format_desc}", format_id)
        self._format_combo.setCurrentText("side_by_side")
        format_layout.addWidget(format_label)
        format_layout.addWidget(self._format_combo, 1)
        options_layout.addLayout(format_layout)

        # Depth model
        model_layout = QHBoxLayout()
        model_label = QLabel("Depth Model:")
        model_label.setMinimumWidth(120)
        self._model_combo = QComboBox()
        for model_id, model_info in DEPTH_MODELS.items():
            self._model_combo.addItem(
                f"{model_id} - {model_info['description']}",
                model_id,
            )
        model_layout.addWidget(model_label)
        model_layout.addWidget(self._model_combo, 1)
        options_layout.addLayout(model_layout)

        # GPU checkbox
        gpu_layout = QHBoxLayout()
        self._gpu_checkbox = QCheckBox("Use GPU Acceleration")
        self._gpu_checkbox.setChecked(True)
        gpu_layout.addWidget(self._gpu_checkbox)
        gpu_layout.addStretch(1)
        options_layout.addLayout(gpu_layout)

        layout.addWidget(options_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Stage label
        stage_layout = QHBoxLayout()
        stage_label = QLabel("Stage:")
        self._stage_text = QLabel("Ready")
        stage_layout.addWidget(stage_label)
        stage_layout.addWidget(self._stage_text, 1)
        progress_layout.addLayout(stage_layout)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        progress_layout.addWidget(self._progress_bar)

        # Progress label
        self._progress_label = QLabel("")
        progress_layout.addWidget(self._progress_label)

        layout.addWidget(progress_group)

        # Log section
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self._log_text = QPlainTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(150)
        self._log_text.setPlaceholderText("Conversion log will appear here...")
        log_layout.addWidget(self._log_text)

        layout.addWidget(log_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self._convert_btn = QPushButton("Start Conversion")
        self._convert_btn.setMinimumWidth(150)
        self._convert_btn.clicked.connect(self._start_conversion)
        button_layout.addWidget(self._convert_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_conversion)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

        # Add stretch to push everything up
        layout.addStretch(1)

    def _on_input_changed(self, path: str) -> None:
        """Handle input file path change.

        Args:
            path: New input file path.
        """
        if path and not self._output_selector.get_path():
            # Auto-generate output path
            input_path = Path(path)
            output_name = f"{input_path.stem}_3d{input_path.suffix}"
            self._output_selector.set_path(str(input_path.parent / output_name))

    def _start_conversion(self) -> None:
        """Start the video conversion."""
        # Validate inputs
        input_path = self._input_selector.get_path()
        output_path = self._output_selector.get_path()

        if not input_path:
            QMessageBox.warning(self, "Missing Input", "Please select an input video file.")
            return

        if not output_path:
            QMessageBox.warning(self, "Missing Output", "Please specify an output video file.")
            return

        if not Path(input_path).exists():
            QMessageBox.warning(self, "File Not Found", f"Input file does not exist:\n{input_path}")
            return

        # Get options
        output_format = self._format_combo.currentData()
        model = self._model_combo.currentData()
        use_gpu = self._gpu_checkbox.isChecked()

        # Clear log
        self._log_text.clear()
        self._progress_bar.setValue(0)
        self._progress_label.setText("")
        self._stage_text.setText("Starting...")

        # Create and start worker
        self._worker = ConversionWorker(
            input_path=input_path,
            output_path=output_path,
            output_format=output_format,
            model=model,
            use_gpu=use_gpu,
        )

        # Connect signals
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker.stage_changed.connect(self._on_stage_changed)
        self._worker.log_message.connect(self._on_log_message)
        self._worker.conversion_complete.connect(self._on_conversion_complete)
        self._worker.error_occurred.connect(self._on_error)

        # Update UI state
        self._convert_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._set_inputs_enabled(False)

        self.conversion_started.emit()
        self._worker.start()

    def _cancel_conversion(self) -> None:
        """Cancel the current conversion."""
        if self._worker:
            self._worker.cancel()
            self._log_text.appendPlainText("Cancelling conversion...")

    def _on_progress_updated(self, current: int, total: int, message: str) -> None:
        """Handle progress update.

        Args:
            current: Current progress value.
            total: Total progress value.
            message: Progress message.
        """
        if total > 0:
            percent = int((current / total) * 100)
            self._progress_bar.setValue(percent)
        self._progress_label.setText(message)

    def _on_stage_changed(self, stage: str) -> None:
        """Handle stage change.

        Args:
            stage: New stage name.
        """
        self._stage_text.setText(stage)

    def _on_log_message(self, message: str, level: str) -> None:
        """Handle log message.

        Args:
            message: Log message.
            level: Log level.
        """
        timestamp = self._get_timestamp()
        formatted = f"[{timestamp}] [{level.upper()}] {message}"
        self._log_text.appendPlainText(formatted)

    def _on_conversion_complete(self, success: bool, message: str, metadata: dict) -> None:
        """Handle conversion completion.

        Args:
            success: Whether conversion was successful.
            message: Completion message.
            metadata: Additional metadata.
        """
        self._convert_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._set_inputs_enabled(True)

        if success:
            self._stage_text.setText("Complete")
            self._progress_bar.setValue(100)
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"Video converted successfully!\n\nOutput: {metadata.get('output_path', 'N/A')}",
            )
        else:
            self._stage_text.setText("Failed")

        self.conversion_finished.emit(success)

    def _on_error(self, message: str, details: str) -> None:
        """Handle conversion error.

        Args:
            message: Error message.
            details: Error details/traceback.
        """
        self._log_text.appendPlainText(f"ERROR: {message}")
        if details:
            self._log_text.appendPlainText(f"Details:\n{details}")

        QMessageBox.critical(
            self,
            "Conversion Error",
            f"An error occurred during conversion:\n\n{message}",
        )

    def _set_inputs_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.

        Args:
            enabled: Whether to enable controls.
        """
        self._input_selector.setEnabled(enabled)
        self._output_selector.setEnabled(enabled)
        self._format_combo.setEnabled(enabled)
        self._model_combo.setEnabled(enabled)
        self._gpu_checkbox.setEnabled(enabled)

    def _get_timestamp(self) -> str:
        """Get current timestamp string.

        Returns:
            Formatted timestamp string.
        """
        from datetime import datetime

        return datetime.now().strftime("%H:%M:%S")

    def is_converting(self) -> bool:
        """Check if a conversion is currently in progress.

        Returns:
            True if conversion is running, False otherwise.
        """
        return self._worker is not None and self._worker.isRunning()

    def cancel_conversion(self) -> None:
        """Cancel the current conversion if one is in progress."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)

    def set_input_file(self, path: str) -> None:
        """Set the input file path.

        Args:
            path: Path to the input video file.
        """
        self._input_selector.set_path(path)
