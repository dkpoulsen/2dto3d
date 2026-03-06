"""Unit tests for MainWindow component.

Tests cover:
- MainWindow initialization
- Menu and toolbar setup
- Tab management
- Signal connections
- Window close event handling
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    pass

# Skip all tests in this module if PyQt6 is not available
_pyqt6_available = True
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QCloseEvent
    from PyQt6.QtWidgets import QApplication, QMessageBox
except ImportError:
    _pyqt6_available = False
    pytestmark = pytest.mark.skip(reason="PyQt6 not available")

if _pyqt6_available:
    from video2d3d.gui.main_window import MainWindow, run_gui


@pytest.fixture(scope="module")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp: QApplication) -> Generator[MainWindow, None, None]:
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    yield window
    window.deleteLater()


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestMainWindow:
    """Tests for MainWindow class."""

    def test_initialization(self, main_window: MainWindow) -> None:
        """Test MainWindow initialization."""
        # Check window properties
        assert main_window.windowTitle().startswith("2Dto3D Video Converter")

    def test_ui_components_exist(self, main_window: MainWindow) -> None:
        """Test that UI components exist."""
        # Check tabs exist
        assert hasattr(main_window, "_tab_widget")
        assert hasattr(main_window, "_convert_tab")
        assert hasattr(main_window, "_batch_tab")
        assert hasattr(main_window, "_settings_tab")

        # Check tab widget has correct number of tabs
        assert main_window._tab_widget.count() == 3
