"""Integration tests for GUI tab components.

Tests cover:
- ConvertTab functionality
- BatchTab functionality
- SettingsTab functionality
- Tab interactions and signals
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Generator
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    pass

# Skip all tests in this module if PyQt6 is not available
_pyqt6_available = True
try:
    from PyQt6.QtWidgets import QApplication, QWidget
except ImportError:
    _pyqt6_available = False
    pytestmark = pytest.mark.skip(reason="PyQt6 not available")

if _pyqt6_available:
    from video2d3d.gui.batch_tab import BatchTab
    from video2d3d.gui.convert_tab import ConvertTab
    from video2d3d.gui.settings_tab import SettingsTab


@pytest.fixture(scope="module")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for the test module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def parent_widget(qapp: QApplication) -> Generator[QWidget, None, None]:
    """Create a parent widget for testing."""
    widget = QWidget()
    yield widget
    widget.deleteLater()


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestConvertTab:
    """Tests for ConvertTab widget."""

    def test_initialization(self, parent_widget: QWidget) -> None:
        """Test ConvertTab initialization."""
        tab = ConvertTab(parent=parent_widget)

        # Check that UI components exist
        assert hasattr(tab, "_input_selector")
        assert hasattr(tab, "_output_selector")
        assert hasattr(tab, "_format_combo")
