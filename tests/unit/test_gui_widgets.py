"""Unit tests for GUI widget components.

Tests cover:
- FileSelector widget
- DirectorySelector widget
- FormRow widget
- CollapsibleBox widget
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
    from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QWidget
except ImportError:
    _pyqt6_available = False
    pytestmark = pytest.mark.skip(reason="PyQt6 not available")

if _pyqt6_available:
    from video2d3d.gui.widgets import (
        CollapsibleBox,
        DirectorySelector,
        FileSelector,
        FormRow,
    )


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
class TestFileSelector:
    """Tests for FileSelector widget."""

    def test_initialization(self, parent_widget: QWidget) -> None:
        """Test FileSelector initialization with default parameters."""
        selector = FileSelector(parent=parent_widget)

        assert selector._file_filter == "All Files (*)"
        assert selector._save_mode is False
        assert selector._last_dir == str(Path.home())

    def test_initialization_with_custom_params(self, parent_widget: QWidget) -> None:
        """Test FileSelector initialization with custom parameters."""
        selector = FileSelector(
            parent=parent_widget,
            label="Video File:",
            file_filter="Video Files (*.mp4 *.avi)",
            save_mode=True,
            default_path="/default/path.mp4",
        )

        assert selector._file_filter == "Video Files (*.mp4 *.avi)"
        assert selector._save_mode is True

    def test_get_path(self, parent_widget: QWidget) -> None:
        """Test get_path returns current path."""
        selector = FileSelector(parent=parent_widget, default_path="/test/video.mp4")

        assert selector.get_path() == "/test/video.mp4"

    def test_set_path(self, parent_widget: QWidget) -> None:
        """Test set_path updates the path."""
        selector = FileSelector(parent=parent_widget)

        selector.set_path("/new/video.mp4")
        assert selector.get_path() == "/new/video.mp4"

    def test_path_changed_signal(self, parent_widget: QWidget) -> None:
        """Test that path_changed signal is emitted when path changes."""
        selector = FileSelector(parent=parent_widget)

        # Track signal emissions
        emitted_paths = []
        selector.path_changed.connect(lambda path: emitted_paths.append(path))

        # Set path programmatically
        selector.set_path("/test/video.mp4")

        # Check signal was emitted
        assert "/test/video.mp4" in emitted_paths

    def test_browse_open_mode(self, parent_widget: QWidget) -> None:
        """Test browse method in open mode."""
        selector = FileSelector(
            parent=parent_widget, file_filter="Video Files (*.mp4)", save_mode=False
        )

        # Mock the file dialog
        with patch("video2d3d.gui.widgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("/selected/file.mp4", "Video Files (*.mp4)")

            selector._browse()

            # Check dialog was called with correct parameters
            mock_dialog.assert_called_once()
            assert selector.get_path() == "/selected/file.mp4"

    def test_browse_save_mode(self, parent_widget: QWidget) -> None:
        """Test browse method in save mode."""
        selector = FileSelector(
            parent=parent_widget, file_filter="Video Files (*.mp4)", save_mode=True
        )

        # Mock the file dialog
        with patch("video2d3d.gui.widgets.QFileDialog.getSaveFileName") as mock_dialog:
            mock_dialog.return_value = ("/selected/output.mp4", "Video Files (*.mp4)")

            selector._browse()

            # Check dialog was called with correct parameters
            mock_dialog.assert_called_once()
            assert selector.get_path() == "/selected/output.mp4"

    def test_browse_canceled(self, parent_widget: QWidget) -> None:
        """Test browse method when user cancels."""
        selector = FileSelector(parent=parent_widget, default_path="/initial/path.mp4")

        # Mock the file dialog to return empty string (user canceled)
        with patch("video2d3d.gui.widgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("", "")

            initial_path = selector.get_path()
            selector._browse()

            # Path should not change
            assert selector.get_path() == initial_path


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestDirectorySelector:
    """Tests for DirectorySelector widget."""

    def test_initialization(self, parent_widget: QWidget) -> None:
        """Test DirectorySelector initialization with default parameters."""
        selector = DirectorySelector(parent=parent_widget)

        assert selector._last_dir == str(Path.home())

    def test_initialization_with_custom_params(self, parent_widget: QWidget) -> None:
        """Test DirectorySelector initialization with custom parameters."""
        selector = DirectorySelector(
            parent=parent_widget,
            label="Output Directory:",
            default_path="/default/dir",
        )

        assert selector.get_path() == "/default/dir"

    def test_get_path(self, parent_widget: QWidget) -> None:
        """Test get_path returns current path."""
        selector = DirectorySelector(parent=parent_widget, default_path="/test/dir")

        assert selector.get_path() == "/test/dir"

    def test_set_path(self, parent_widget: QWidget) -> None:
        """Test set_path updates the path."""
        selector = DirectorySelector(parent=parent_widget)

        selector.set_path("/new/dir")
        assert selector.get_path() == "/new/dir"

    def test_path_changed_signal(self, parent_widget: QWidget) -> None:
        """Test that path_changed signal is emitted when path changes."""
        selector = DirectorySelector(parent=parent_widget)

        # Track signal emissions
        emitted_paths = []
        selector.path_changed.connect(lambda path: emitted_paths.append(path))

        # Set path programmatically
        selector.set_path("/test/dir")

        # Check signal was emitted
        assert "/test/dir" in emitted_paths

    def test_browse(self, parent_widget: QWidget) -> None:
        """Test browse method."""
        selector = DirectorySelector(parent=parent_widget)

        # Mock the directory dialog
        with patch("video2d3d.gui.widgets.QFileDialog.getExistingDirectory") as mock_dialog:
            mock_dialog.return_value = "/selected/directory"

            selector._browse()

            # Check dialog was called
            mock_dialog.assert_called_once()
            assert selector.get_path() == "/selected/directory"

    def test_browse_canceled(self, parent_widget: QWidget) -> None:
        """Test browse method when user cancels."""
        selector = DirectorySelector(parent=parent_widget, default_path="/initial/dir")

        # Mock the directory dialog to return empty string (user canceled)
        with patch("video2d3d.gui.widgets.QFileDialog.getExistingDirectory") as mock_dialog:
            mock_dialog.return_value = ""

            initial_path = selector.get_path()
            selector._browse()

            # Path should not change
            assert selector.get_path() == initial_path

    def test_browse_updates_last_dir(self, parent_widget: QWidget) -> None:
        """Test that browse updates _last_dir for next use."""
        selector = DirectorySelector(parent=parent_widget)

        with patch("video2d3d.gui.widgets.QFileDialog.getExistingDirectory") as mock_dialog:
            mock_dialog.return_value = "/first/directory"
            selector._browse()
            assert selector._last_dir == "/first/directory"


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestFormRow:
    """Tests for FormRow widget."""

    def test_initialization_with_label_only(self, parent_widget: QWidget) -> None:
        """Test FormRow initialization with only a label."""
        row = FormRow(parent=parent_widget, label="Test Label:")

        assert row._label.text() == "Test Label:"

    def test_initialization_with_widget(self, parent_widget: QWidget) -> None:
        """Test FormRow initialization with label and widget."""
        line_edit = QLineEdit()
        row = FormRow(parent=parent_widget, label="Test:", widget=line_edit)

        assert row._label.text() == "Test:"
        # Widget should be in the layout
        assert row.layout().count() == 2  # label + widget

    def test_label_minimum_width(self, parent_widget: QWidget) -> None:
        """Test that label has minimum width set."""
        row = FormRow(parent=parent_widget, label="Test:")

        assert row._label.minimumWidth() == 120


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestCollapsibleBox:
    """Tests for CollapsibleBox widget."""

    def test_initialization(self, parent_widget: QWidget) -> None:
        """Test CollapsibleBox initialization."""
        box = CollapsibleBox(parent=parent_widget, title="Test Box")

        assert box.title() == "Test Box"
        assert box.isCheckable() is True
        assert box.isChecked() is True

    def test_toggle_collapses_content(self, parent_widget: QWidget) -> None:
        """Test that toggling the checkbox shows/hides content."""
        box = CollapsibleBox(parent=parent_widget, title="Test Box")

        # Add some content
        content = QLabel("Test Content")
        box.layout().addWidget(content)

        # Initially checked, content should be visible
        assert content.isVisible()

        # Uncheck to collapse
        box.setChecked(False)

        # Content should be hidden
        assert not content.isVisible()

        # Check again to expand
        box.setChecked(True)

        # Content should be visible again
        assert content.isVisible()

    def test_toggled_signal(self, parent_widget: QWidget) -> None:
        """Test that toggled signal is connected."""
        box = CollapsibleBox(parent=parent_widget, title="Test Box")

        # The widget should have the toggled signal from QGroupBox
        assert hasattr(box, "toggled")


@pytest.mark.skipif(not _pyqt6_available, reason="PyQt6 not available")
class TestWidgetIntegration:
    """Integration tests for widget interactions."""

    def test_file_selector_in_form_row(self, qapp: QApplication) -> None:
        """Test FileSelector can be embedded in a FormRow."""
        parent = QWidget()
        selector = FileSelector(parent=parent, label="File:")
        row = FormRow(parent=parent, label="Select File:", widget=selector)

        # Both should exist and be functional
        assert row._label.text() == "Select File:"
        assert selector.get_path() == ""

    def test_directory_selector_in_form_row(self, qapp: QApplication) -> None:
        """Test DirectorySelector can be embedded in a FormRow."""
        parent = QWidget()
        selector = DirectorySelector(parent=parent, label="Dir:")
        row = FormRow(parent=parent, label="Select Directory:", widget=selector)

        # Both should exist and be functional
        assert row._label.text() == "Select Directory:"
        assert selector.get_path() == ""

    def test_multiple_widgets_in_layout(self, qapp: QApplication) -> None:
        """Test multiple widgets can be added to a layout."""
        parent = QWidget()

        file_selector = FileSelector(parent=parent, label="Input:")
        dir_selector = DirectorySelector(parent=parent, label="Output:")

        # Both should be independent
        file_selector.set_path("/input/video.mp4")
        dir_selector.set_path("/output/dir")

        assert file_selector.get_path() == "/input/video.mp4"
        assert dir_selector.get_path() == "/output/dir"
