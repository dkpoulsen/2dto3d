"""Main window for the 2Dto3D GUI application."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from video2d3d import __version__
from video2d3d.gui.batch_tab import BatchTab
from video2d3d.gui.convert_tab import ConvertTab
from video2d3d.gui.settings_tab import SettingsTab

if TYPE_CHECKING:
    pass

class MainWindow(QMainWindow):
    """Main application window for 2Dto3D Video Converter."""

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_window(self) -> None:
        """Set up window properties."""
        self.setWindowTitle(f"2Dto3D Video Converter v{__version__}")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Tab widget
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self._tab_widget)

        # Create tabs
        self._convert_tab = ConvertTab()
        self._tab_widget.addTab(self._convert_tab, "Single Conversion")

        self._batch_tab = BatchTab()
        self._tab_widget.addTab(self._batch_tab, "Batch Conversion")

        self._settings_tab = SettingsTab()
        self._tab_widget.addTab(self._settings_tab, "Settings")

        # Info bar at bottom
        info_layout = QVBoxLayout()
        self._info_label = QLabel(
            "Convert 2D videos to 3D using deep learning depth estimation. "
            "Select a video file, choose your options, and click Start Conversion."
        )
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
        info_layout.addWidget(self._info_label)
        layout.addLayout(info_layout)

    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Video...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open_video)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._show_settings_tab)
        edit_menu.addAction(settings_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        logs_action = QAction("Open &Logs Folder", self)
        logs_action.triggered.connect(self._open_logs_folder)
        view_menu.addAction(logs_action)

        outputs_action = QAction("Open &Outputs Folder", self)
        outputs_action.triggered.connect(self._open_outputs_folder)
        view_menu.addAction(outputs_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        about_qt_action = QAction("About &Qt", self)
        about_qt_action.triggered.connect(QApplication.aboutQt)
        help_menu.addAction(about_qt_action)

    def _setup_toolbar(self) -> None:
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Open file
        open_action = QAction("Open Video", self)
        open_action.setToolTip("Open a video file for conversion")
        open_action.triggered.connect(self._on_open_video)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        # Settings
        settings_action = QAction("Settings", self)
        settings_action.setToolTip("Open settings")
        settings_action.triggered.connect(self._show_settings_tab)
        toolbar.addAction(settings_action)

    def _setup_statusbar(self) -> None:
        """Set up the status bar."""
        statusbar = self.statusBar()

        # Status label
        self._status_label = QLabel("Ready")
        statusbar.addWidget(self._status_label, 1)

        # Progress bar (for operations)
        self._status_progress = QProgressBar()
        self._status_progress.setMaximumWidth(200)
        self._status_progress.setVisible(False)
        statusbar.addPermanentWidget(self._status_progress)

        # GPU indicator
        self._gpu_label = QLabel("GPU: Ready")
        statusbar.addPermanentWidget(self._gpu_label)

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Conversion signals
        self._convert_tab.conversion_started.connect(self._on_conversion_started)
        self._convert_tab.conversion_finished.connect(self._on_conversion_finished)

        # Batch signals
        self._batch_tab.batch_started.connect(self._on_batch_started)
        self._batch_tab.batch_finished.connect(self._on_batch_finished)

        # Settings signals
        self._settings_tab.settings_changed.connect(self._on_settings_changed)

    def _on_open_video(self) -> None:
        """Handle opening a video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            str(),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)",
        )

        if file_path:
            self._convert_tab._input_selector.set_path(file_path)
            self._tab_widget.setCurrentIndex(0)  # Switch to convert tab

    def _show_settings_tab(self) -> None:
        """Switch to settings tab."""
        self._tab_widget.setCurrentIndex(2)

    def _open_logs_folder(self) -> None:
        """Open the logs folder in file manager."""
        from pathlib import Path

        logs_path = Path("logs")
        logs_path.mkdir(exist_ok=True)
        self._open_folder(str(logs_path))

    def _open_outputs_folder(self) -> None:
        """Open the outputs folder in file manager."""
        from pathlib import Path

        outputs_path = Path("outputs")
        outputs_path.mkdir(exist_ok=True)
        self._open_folder(str(outputs_path))

    def _open_folder(self, path: str) -> None:
        """Open a folder in the system file manager.

        Args:
            path: Path to the folder.
        """
        import subprocess
        import sys

        if sys.platform == "win32":
            subprocess.run(["explorer", path], check=False)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)

    def _show_about(self) -> None:
        """Show about dialog."""
        from video2d3d import __version__

        QMessageBox.about(
            self,
            "About 2Dto3D Video Converter",
            f"<h3>2Dto3D Video Converter</h3>"
            f"<p>Version {__version__}</p>"
            f"<p>Convert 2D videos to 3D using deep learning depth estimation.</p>"
            f"<p>Features:</p>"
            f"<ul>"
            f"<li>Multiple depth estimation models (MiDaS, DPT)</li>"
            f"<li>Various 3D output formats (side-by-side, anaglyph, VR)</li>"
            f"<li>GPU acceleration support</li>"
            f"<li>Batch processing</li>"
            f"</ul>"
            f"<p>&copy; 2024 Automaker</p>"
            f"<p><a href='https://github.com/automaker/2dto3d'>GitHub Repository</a></p>",
        )

    def _on_conversion_started(self) -> None:
        """Handle conversion started."""
        self._status_label.setText("Converting...")
        self._status_progress.setVisible(True)
        self._status_progress.setRange(0, 0)  # Indeterminate progress
        self._gpu_label.setText("GPU: Processing")

    def _on_conversion_finished(self, success: bool) -> None:
        """Handle conversion finished.

        Args:
            success: Whether conversion was successful.
        """
        self._status_progress.setVisible(False)
        if success:
            self._status_label.setText("Conversion completed")
            self._gpu_label.setText("GPU: Ready")
        else:
            self._status_label.setText("Conversion failed")

    def _on_batch_started(self) -> None:
        """Handle batch conversion started."""
        self._status_label.setText("Batch processing...")
        self._status_progress.setVisible(True)

    def _on_batch_finished(self, successful: int, failed: int) -> None:
        """Handle batch conversion finished.

        Args:
            successful: Number of successful conversions.
            failed: Number of failed conversions.
        """
        self._status_progress.setVisible(False)
        total = successful + failed
        self._status_label.setText(f"Batch complete: {successful}/{total} successful")
        self._gpu_label.setText("GPU: Ready")

    def _on_settings_changed(self) -> None:
        """Handle settings changed."""
        self._status_label.setText("Settings saved")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close event.

        Args:
            event: Close event.
        """
        # Check if any conversion is in progress
        if self._convert_tab.is_converting():
            reply = QMessageBox.question(
                self,
                "Conversion in Progress",
                "A conversion is currently in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            # Cancel the conversion
            self._convert_tab.cancel_conversion()

        if self._batch_tab.is_converting():
            reply = QMessageBox.question(
                self,
                "Batch Conversion in Progress",
                "A batch conversion is currently in progress. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            # Cancel the batch
            self._batch_tab.cancel_conversion()
        event.accept()


def run_gui() -> int:
    """Run the GUI application.

    Returns:
        Application exit code.
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )

    app = QApplication(sys.argv)
    app.setApplicationName("2Dto3D Video Converter")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Automaker")

    # Set application style
    app.setStyle("Fusion")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application
    return app.exec()


if __name__ == "__main__":
    sys.exit(run_gui())
