"""Settings tab for configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from video2d3d.gui.widgets import DirectorySelector

if TYPE_CHECKING:
    pass


class SettingsTab(QWidget):
    """Tab for application settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings tab.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Processing Settings
        proc_group = QGroupBox("Processing")
        proc_layout = QVBoxLayout(proc_group)

        # Batch size
        batch_layout = QHBoxLayout()
        batch_label = QLabel("Batch Size:")
        batch_label.setMinimumWidth(150)
        self._batch_size_spin = QSpinBox()
        self._batch_size_spin.setRange(1, 64)
        self._batch_size_spin.setValue(4)
        batch_layout.addWidget(batch_label)
        batch_layout.addWidget(self._batch_size_spin, 1)
        proc_layout.addLayout(batch_layout)

        # Number of workers
        workers_layout = QHBoxLayout()
        workers_label = QLabel("Worker Processes:")
        workers_label.setMinimumWidth(150)
        self._workers_spin = QSpinBox()
        self._workers_spin.setRange(1, 16)
        self._workers_spin.setValue(4)
        workers_layout.addWidget(workers_label)
        workers_layout.addWidget(self._workers_spin, 1)
        proc_layout.addLayout(workers_layout)

        # GPU device
        gpu_device_layout = QHBoxLayout()
        gpu_device_label = QLabel("GPU Device:")
        gpu_device_label.setMinimumWidth(150)
        self._gpu_device_spin = QSpinBox()
        self._gpu_device_spin.setRange(0, 7)
        self._gpu_device_spin.setValue(0)
        gpu_device_layout.addWidget(gpu_device_label)
        gpu_device_layout.addWidget(self._gpu_device_spin, 1)
        proc_layout.addLayout(gpu_device_layout)

        # Memory limit
        memory_layout = QHBoxLayout()
        memory_label = QLabel("Memory Limit (%):")
        memory_label.setMinimumWidth(150)
        self._memory_spin = QSpinBox()
        self._memory_spin.setRange(10, 100)
        self._memory_spin.setValue(80)
        memory_layout.addWidget(memory_label)
        memory_layout.addWidget(self._memory_spin, 1)
        proc_layout.addLayout(memory_layout)

        # Checkboxes
        self._mixed_precision_cb = QCheckBox("Use Mixed Precision (FP16)")
        self._mixed_precision_cb.setChecked(True)
        proc_layout.addWidget(self._mixed_precision_cb)

        self._auto_batch_cb = QCheckBox("Auto-adjust Batch Size")
        self._auto_batch_cb.setChecked(True)
        proc_layout.addWidget(self._auto_batch_cb)

        layout.addWidget(proc_group)

        # Depth Estimation Settings
        depth_group = QGroupBox("Depth Estimation")
        depth_layout = QVBoxLayout(depth_group)

        # Output size
        size_layout = QHBoxLayout()
        size_label = QLabel("Output Size:")
        size_label.setMinimumWidth(150)
        self._width_spin = QSpinBox()
        self._width_spin.setRange(128, 1024)
        self._width_spin.setValue(384)
        self._width_spin.setSingleStep(64)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self._width_spin)
        size_layout.addWidget(QLabel("x"))
        self._height_spin = QSpinBox()
        self._height_spin.setRange(128, 1024)
        self._height_spin.setValue(384)
        self._height_spin.setSingleStep(64)
        size_layout.addWidget(self._height_spin)
        size_layout.addStretch(1)
        depth_layout.addLayout(size_layout)

        # Temporal consistency
        self._temporal_cb = QCheckBox("Enable Temporal Consistency")
        self._temporal_cb.setChecked(True)
        depth_layout.addWidget(self._temporal_cb)

        # Temporal smoothing
        smoothing_layout = QHBoxLayout()
        smoothing_label = QLabel("Temporal Smoothing:")
        smoothing_label.setMinimumWidth(150)
        self._smoothing_spin = QSpinBox()
        self._smoothing_spin.setRange(0, 100)
        self._smoothing_spin.setValue(50)
        smoothing_layout.addWidget(smoothing_label)
        smoothing_layout.addWidget(self._smoothing_spin, 1)
        depth_layout.addLayout(smoothing_layout)

        layout.addWidget(depth_group)

        # Video Output Settings
        video_group = QGroupBox("Video Output")
        video_layout = QVBoxLayout(video_group)

        # Codec
        codec_layout = QHBoxLayout()
        codec_label = QLabel("Codec:")
        codec_label.setMinimumWidth(150)
        self._codec_combo = QComboBox()
        self._codec_combo.addItems(["libx264", "libx265", "libvpx-vp9", "mpeg4"])
        codec_layout.addWidget(codec_label)
        codec_layout.addWidget(self._codec_combo, 1)
        video_layout.addLayout(codec_layout)

        # Preset
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Encoding Preset:")
        preset_label.setMinimumWidth(150)
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(
            [
                "ultrafast",
                "superfast",
                "veryfast",
                "faster",
                "fast",
                "medium",
                "slow",
                "slower",
                "veryslow",
            ]
        )
        self._preset_combo.setCurrentText("medium")
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self._preset_combo, 1)
        video_layout.addLayout(preset_layout)

        # CRF Quality
        crf_layout = QHBoxLayout()
        crf_label = QLabel("Quality (CRF):")
        crf_label.setMinimumWidth(150)
        self._crf_spin = QSpinBox()
        self._crf_spin.setRange(0, 51)
        self._crf_spin.setValue(23)
        crf_layout.addWidget(crf_label)
        crf_layout.addWidget(self._crf_spin, 1)
        video_layout.addLayout(crf_layout)

        layout.addWidget(video_group)

        # Logging Settings
        log_group = QGroupBox("Logging")
        log_layout = QVBoxLayout(log_group)

        # Log level
        level_layout = QHBoxLayout()
        level_label = QLabel("Log Level:")
        level_label.setMinimumWidth(150)
        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._log_level_combo.setCurrentText("INFO")
        level_layout.addWidget(level_label)
        level_layout.addWidget(self._log_level_combo, 1)
        log_layout.addLayout(level_layout)

        # Log directory
        self._log_dir_selector = DirectorySelector(
            label="Log Directory:",
            default_path="logs",
        )
        log_layout.addWidget(self._log_dir_selector)

        layout.addWidget(log_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self._reset_btn)

        self._save_btn = QPushButton("Save Settings")
        self._save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self._save_btn)

        layout.addLayout(button_layout)

        # Add stretch
        layout.addStretch(1)

    def _load_settings(self) -> None:
        """Load settings from configuration."""
        try:
            from video2d3d.utils.config import get_config

            config = get_config()

            # Processing
            self._batch_size_spin.setValue(config.processing.batch_size)
            self._workers_spin.setValue(config.processing.num_workers)
            self._gpu_device_spin.setValue(config.processing.gpu_device)
            self._memory_spin.setValue(config.processing.max_memory_percent)
            self._mixed_precision_cb.setChecked(config.processing.mixed_precision)
            self._auto_batch_cb.setChecked(config.processing.auto_batch_size)

            # Depth estimation
            self._width_spin.setValue(config.depth_estimation.output_width)
            self._height_spin.setValue(config.depth_estimation.output_height)
            self._temporal_cb.setChecked(config.depth_estimation.temporal_consistency)
            self._smoothing_spin.setValue(
                int(config.depth_estimation.temporal_smoothing_factor * 100)
            )

            # Video output
            self._codec_combo.setCurrentText(config.video_output.codec)
            self._preset_combo.setCurrentText(config.video_output.preset)
            self._crf_spin.setValue(config.video_output.crf)

            # Logging
            self._log_level_combo.setCurrentText(config.logging.level)
            self._log_dir_selector.set_path(str(Path(config.logging.file).parent))

        except Exception as e:
            print(f"Error loading settings: {e}")

    def _save_settings(self) -> None:
        """Save settings to configuration."""
        try:
            from video2d3d.utils.config import get_config

            config = get_config()

            # Processing
            config.processing.batch_size = self._batch_size_spin.value()
            config.processing.num_workers = self._workers_spin.value()
            config.processing.gpu_device = self._gpu_device_spin.value()
            config.processing.max_memory_percent = self._memory_spin.value()
            config.processing.mixed_precision = self._mixed_precision_cb.isChecked()
            config.processing.auto_batch_size = self._auto_batch_cb.isChecked()

            # Depth estimation
            config.depth_estimation.output_width = self._width_spin.value()
            config.depth_estimation.output_height = self._height_spin.value()
            config.depth_estimation.temporal_consistency = self._temporal_cb.isChecked()
            config.depth_estimation.temporal_smoothing_factor = self._smoothing_spin.value() / 100.0

            # Video output
            config.video_output.codec = self._codec_combo.currentText()
            config.video_output.preset = self._preset_combo.currentText()
            config.video_output.crf = self._crf_spin.value()

            # Logging
            config.logging.level = self._log_level_combo.currentText()
            config.logging.file = str(Path(self._log_dir_selector.get_path()) / "video2d3d.log")

            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully.\n\n"
                "Note: Some settings may require restarting the application to take effect.",
            )

            self.settings_changed.emit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings:\n{e}",
            )

    def _reset_to_defaults(self) -> None:
        """Reset settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Processing defaults
            self._batch_size_spin.setValue(4)
            self._workers_spin.setValue(4)
            self._gpu_device_spin.setValue(0)
            self._memory_spin.setValue(80)
            self._mixed_precision_cb.setChecked(True)
            self._auto_batch_cb.setChecked(True)

            # Depth estimation defaults
            self._width_spin.setValue(384)
            self._height_spin.setValue(384)
            self._temporal_cb.setChecked(True)
            self._smoothing_spin.setValue(50)

            # Video output defaults
            self._codec_combo.setCurrentText("libx264")
            self._preset_combo.setCurrentText("medium")
            self._crf_spin.setValue(23)

            # Logging defaults
            self._log_level_combo.setCurrentText("INFO")
            self._log_dir_selector.set_path("logs")

            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to their default values.",
            )
