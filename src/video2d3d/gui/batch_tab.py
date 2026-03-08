"""Batch video conversion tab."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from video2d3d.cli import DEPTH_MODELS, OUTPUT_FORMATS
from video2d3d.gui.widgets import DirectorySelector
from video2d3d.gui.workers import BatchConversionWorker

if TYPE_CHECKING:
    pass


class BatchTab(QWidget):
    """Tab for batch video conversion."""

    batch_started = pyqtSignal()
    batch_finished = pyqtSignal(int, int)  # successful, failed

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the batch tab.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._worker: BatchConversionWorker | None = None
        self._input_files: list[str] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Source section
        source_group = QGroupBox("Source")
        source_layout = QVBoxLayout(source_group)

        # Input directory
        self._input_dir_selector = DirectorySelector(
            label="Input Directory:",
        )
        self._input_dir_selector.path_changed.connect(self._on_input_dir_changed)
        source_layout.addWidget(self._input_dir_selector)

        # Pattern for file matching
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("File Pattern:")
        pattern_label.setMinimumWidth(120)
        self._pattern_edit = QLineEdit("*.mp4")
        self._pattern_edit.setPlaceholderText("e.g., *.mp4 or *.avi")
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self._pattern_edit, 1)

        self._recursive_checkbox = QCheckBox("Recursive")
        self._recursive_checkbox.setChecked(True)
        pattern_layout.addWidget(self._recursive_checkbox)

        source_layout.addLayout(pattern_layout)

        # Add files button
        add_files_layout = QHBoxLayout()
        self._add_files_btn = QPushButton("Add Files...")
        self._add_files_btn.clicked.connect(self._add_files)
        add_files_layout.addWidget(self._add_files_btn)

        self._scan_dir_btn = QPushButton("Scan Directory")
        self._scan_dir_btn.clicked.connect(self._scan_directory)
        add_files_layout.addWidget(self._scan_dir_btn)

        self._clear_files_btn = QPushButton("Clear List")
        self._clear_files_btn.clicked.connect(self._clear_files)
        add_files_layout.addWidget(self._clear_files_btn)

        add_files_layout.addStretch(1)
        source_layout.addLayout(add_files_layout)

        layout.addWidget(source_group)

        # Output section
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        self._output_dir_selector = DirectorySelector(
            label="Output Directory:",
        )
        output_layout.addWidget(self._output_dir_selector)

        layout.addWidget(output_group)

        # Options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        # Format row
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

        # Model row
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

        # Other options
        other_layout = QHBoxLayout()
        self._gpu_checkbox = QCheckBox("Use GPU")
        self._gpu_checkbox.setChecked(True)
        other_layout.addWidget(self._gpu_checkbox)

        self._skip_existing_checkbox = QCheckBox("Skip Existing")
        self._skip_existing_checkbox.setChecked(True)
        other_layout.addWidget(self._skip_existing_checkbox)

        concurrent_label = QLabel("Concurrent Jobs:")
        other_layout.addWidget(concurrent_label)
        self._concurrent_spin = QSpinBox()
        self._concurrent_spin.setRange(1, 8)
        self._concurrent_spin.setValue(1)
        other_layout.addWidget(self._concurrent_spin)

        other_layout.addStretch(1)
        options_layout.addLayout(other_layout)

        layout.addWidget(options_group)

        # File list section
        files_group = QGroupBox("Files to Convert")
        files_layout = QVBoxLayout(files_group)

        # File count label
        self._file_count_label = QLabel("0 files")
        files_layout.addWidget(self._file_count_label)

        # File list
        self._file_list = QListWidget()
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setAlternatingRowColors(True)
        files_layout.addWidget(self._file_list)

        # Remove selected button
        remove_layout = QHBoxLayout()
        self._remove_selected_btn = QPushButton("Remove Selected")
        self._remove_selected_btn.clicked.connect(self._remove_selected)
        remove_layout.addWidget(self._remove_selected_btn)
        remove_layout.addStretch(1)
        files_layout.addLayout(remove_layout)

        layout.addWidget(files_group)

        # Progress section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Overall progress
        overall_layout = QHBoxLayout()
        overall_label = QLabel("Overall:")
        self._overall_progress = QProgressBar()
        self._overall_progress.setRange(0, 100)
        self._overall_progress.setValue(0)
        overall_layout.addWidget(overall_label)
        overall_layout.addWidget(self._overall_progress, 1)

        self._stats_label = QLabel("0 / 0")
        overall_layout.addWidget(self._stats_label)
        progress_layout.addLayout(overall_layout)

        # Current file
        current_layout = QHBoxLayout()
        current_label = QLabel("Current:")
        self._current_file_label = QLabel("")
        current_layout.addWidget(current_label)
        current_layout.addWidget(self._current_file_label, 1)
        progress_layout.addLayout(current_layout)

        layout.addWidget(progress_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self._start_btn = QPushButton("Start Batch Conversion")
        self._start_btn.setMinimumWidth(180)
        self._start_btn.clicked.connect(self._start_batch)
        button_layout.addWidget(self._start_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumWidth(100)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel_batch)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def _on_input_dir_changed(self, path: str) -> None:
        """Handle input directory change.

        Args:
            path: New input directory path.
        """
        if path and not self._output_dir_selector.get_path():
            # Auto-set output directory
            output_dir = Path(path) / "3d_output"
            self._output_dir_selector.set_path(str(output_dir))

    def _add_files(self) -> None:
        """Add files to the list using file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            str(Path.home()),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)",
        )

        if files:
            for file_path in files:
                if file_path not in self._input_files:
                    self._input_files.append(file_path)
                    self._file_list.addItem(file_path)
            self._update_file_count()

    def _scan_directory(self) -> None:
        """Scan directory for video files."""
        input_dir = self._input_dir_selector.get_path()
        if not input_dir:
            QMessageBox.warning(
                self, "Missing Directory", "Please select an input directory first."
            )
            return

        pattern = self._pattern_edit.text() or "*.mp4"
        recursive = self._recursive_checkbox.isChecked()

        input_path = Path(input_dir)
        if recursive:
            files = list(input_path.rglob(pattern))
        else:
            files = list(input_path.glob(pattern))

        count = 0
        for file_path in files:
            if file_path.is_file() and str(file_path) not in self._input_files:
                self._input_files.append(str(file_path))
                self._file_list.addItem(str(file_path))
                count += 1

        self._update_file_count()
        QMessageBox.information(
            self,
            "Scan Complete",
            f"Found and added {count} video file(s).",
        )

    def _clear_files(self) -> None:
        """Clear the file list."""
        self._input_files.clear()
        self._file_list.clear()
        self._update_file_count()

    def _remove_selected(self) -> None:
        """Remove selected files from the list."""
        selected_items = self._file_list.selectedItems()
        for item in selected_items:
            row = self._file_list.row(item)
            self._file_list.takeItem(row)
            if item.text() in self._input_files:
                self._input_files.remove(item.text())
        self._update_file_count()

    def _update_file_count(self) -> None:
        """Update the file count label."""
        count = len(self._input_files)
        self._file_count_label.setText(f"{count} file{'s' if count != 1 else ''}")

    def _start_batch(self) -> None:
        """Start batch conversion."""
        if not self._input_files:
            QMessageBox.warning(self, "No Files", "Please add files to convert.")
            return

        output_dir = self._output_dir_selector.get_path()
        if not output_dir:
            QMessageBox.warning(self, "Missing Output", "Please specify an output directory.")
            return

        # Create output directory if needed
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Get options
        output_format = self._format_combo.currentData()
        model = self._model_combo.currentData()
        use_gpu = self._gpu_checkbox.isChecked()
        skip_existing = self._skip_existing_checkbox.isChecked()

        # Reset progress
        self._overall_progress.setValue(0)
        self._stats_label.setText(f"0 / {len(self._input_files)}")

        # Create worker
        self._worker = BatchConversionWorker(
            input_files=self._input_files.copy(),
            output_dir=output_dir,
            output_format=output_format,
            model=model,
            use_gpu=use_gpu,
            skip_existing=skip_existing,
        )

        # Connect signals
        self._worker.job_started.connect(self._on_job_started)
        self._worker.job_completed.connect(self._on_job_completed)
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker.all_complete.connect(self._on_all_complete)

        # Update UI
        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._set_inputs_enabled(False)

        self.batch_started.emit()
        self._worker.start()

    def _cancel_batch(self) -> None:
        """Cancel batch conversion."""
        if self._worker:
            self._worker.cancel()

    def _on_job_started(self, index: int, filename: str) -> None:
        """Handle job started.

        Args:
            index: Job index.
            filename: File name.
        """
        self._current_file_label.setText(filename)
        # Highlight current item
        if index < self._file_list.count():
            item = self._file_list.item(index)
            item.setBackground(Qt.GlobalColor.lightGray)

    def _on_job_completed(self, index: int, success: bool, message: str) -> None:
        """Handle job completed.

        Args:
            index: Job index.
            success: Whether job was successful.
            message: Completion message.
        """
        # Update item color
        if index < self._file_list.count():
            item = self._file_list.item(index)
            if success:
                item.setBackground(Qt.GlobalColor.green)
            else:
                item.setBackground(Qt.GlobalColor.red)

    def _on_progress_updated(self, completed: int, total: int) -> None:
        """Handle progress update.

        Args:
            completed: Number of completed jobs.
            total: Total number of jobs.
        """
        if total > 0:
            percent = int((completed / total) * 100)
            self._overall_progress.setValue(percent)
        self._stats_label.setText(f"{completed} / {total}")

    def _on_all_complete(self, successful: int, failed: int) -> None:
        """Handle batch completion.

        Args:
            successful: Number of successful conversions.
            failed: Number of failed conversions.
        """
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._set_inputs_enabled(True)

        self._current_file_label.setText("")

        QMessageBox.information(
            self,
            "Batch Complete",
            f"Batch conversion finished.\n\nSuccessful: {successful}\nFailed: {failed}",
        )

        self.batch_finished.emit(successful, failed)

    def _set_inputs_enabled(self, enabled: bool) -> None:
        """Enable or disable input controls.

        Args:
            enabled: Whether to enable controls.
        """
        self._input_dir_selector.setEnabled(enabled)
        self._pattern_edit.setEnabled(enabled)
        self._recursive_checkbox.setEnabled(enabled)
        self._add_files_btn.setEnabled(enabled)
        self._scan_dir_btn.setEnabled(enabled)
        self._clear_files_btn.setEnabled(enabled)
        self._output_dir_selector.setEnabled(enabled)
        self._format_combo.setEnabled(enabled)
        self._model_combo.setEnabled(enabled)
        self._gpu_checkbox.setEnabled(enabled)
        self._skip_existing_checkbox.setEnabled(enabled)
        self._concurrent_spin.setEnabled(enabled)

    def is_converting(self) -> bool:
        """Check if a batch conversion is currently in progress.

        Returns:
            True if batch conversion is running, False otherwise.
        """
        return self._worker is not None and self._worker.isRunning()

    def cancel_conversion(self) -> None:
        """Cancel the current batch conversion if one is in progress."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1000)
