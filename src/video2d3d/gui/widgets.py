"""Common widgets and utilities for the GUI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

class FileSelector(QWidget):
    """A widget for selecting a file with a browse button."""

    path_changed = pyqtSignal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        label: str = "File:",
        file_filter: str = "All Files (*)",
        save_mode: bool = False,
        default_path: str = "",
    ) -> None:
        """Initialize the file selector widget.

        Args:
            parent: Parent widget.
            label: Label text for the file path.
            file_filter: File filter for the file dialog.
            save_mode: If True, use save file dialog; otherwise open file dialog.
            default_path: Default path to show in the line edit.
        """
        super().__init__(parent)
        self._file_filter = file_filter
        self._save_mode = save_mode
        self._last_dir = str(Path.home())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        layout.addWidget(self._label)

        self._path_edit = QLineEdit()
        self._path_edit.setText(default_path)
        self._path_edit.textChanged.connect(self._on_path_changed)
        layout.addWidget(self._path_edit, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse)
        layout.addWidget(self._browse_btn)

    def _browse(self) -> None:
        """Open file dialog to browse for a file."""
        current_path = self._path_edit.text()
        if current_path:
            start_dir = str(Path(current_path).parent)
        else:
            start_dir = self._last_dir

        if self._save_mode:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save File",
                start_dir,
                self._file_filter,
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Open File",
                start_dir,
                self._file_filter,
            )

        if path:
            self._path_edit.setText(path)
            self._last_dir = str(Path(path).parent)

    def _on_path_changed(self, path: str) -> None:
        """Emit path_changed signal when path changes."""
        self.path_changed.emit(path)

    def get_path(self) -> str:
        """Get the current file path."""
        return self._path_edit.text()

    def set_path(self, path: str) -> None:
        """Set the file path."""
        self._path_edit.setText(path)


class DirectorySelector(QWidget):
    """A widget for selecting a directory with a browse button."""

    path_changed = pyqtSignal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        label: str = "Directory:",
        default_path: str = "",
    ) -> None:
        """Initialize the directory selector widget.

        Args:
            parent: Parent widget.
            label: Label text for the directory path.
            default_path: Default path to show in the line edit.
        """
        super().__init__(parent)
        self._last_dir = str(Path.home())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        layout.addWidget(self._label)

        self._path_edit = QLineEdit()
        self._path_edit.setText(default_path)
        self._path_edit.textChanged.connect(self._on_path_changed)
        layout.addWidget(self._path_edit, 1)

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.clicked.connect(self._browse)
        layout.addWidget(self._browse_btn)

    def _browse(self) -> None:
        """Open directory dialog to browse for a directory."""
        current_path = self._path_edit.text()
        if current_path:
            start_dir = current_path
        else:
            start_dir = self._last_dir

        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            start_dir,
        )

        if path:
            self._path_edit.setText(path)
            self._last_dir = path

    def _on_path_changed(self, path: str) -> None:
        """Emit path_changed signal when path changes."""
        self.path_changed.emit(path)

    def get_path(self) -> str:
        """Get the current directory path."""
        return self._path_edit.text()

    def set_path(self, path: str) -> None:
        """Set the directory path."""
        self._path_edit.setText(path)


class FormRow(QWidget):
    """A row in a form with a label and widget."""

    def __init__(
        self,
        parent: QWidget | None = None,
        label: str = "",
        widget: QWidget | None = None,
    ) -> None:
        """Initialize the form row.

        Args:
            parent: Parent widget.
            label: Label text.
            widget: Widget to place next to the label.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setMinimumWidth(120)
        layout.addWidget(self._label)

        if widget:
            layout.addWidget(widget, 1)


class CollapsibleBox(QGroupBox):
    """A collapsible group box."""

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "",
    ) -> None:
        """Initialize the collapsible box.

        Args:
            parent: Parent widget.
            title: Title for the group box.
        """
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        """Toggle the visibility of the content."""
        # Show/hide all children except the checkbox
        for child in self.children():
            if child is not self.layout():
                if hasattr(child, "setVisible"):
                    child.setVisible(checked)

        # Also toggle content widget visibility in layout
        layout = self.layout()
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(checked)
