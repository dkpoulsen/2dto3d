"""Desktop GUI for 2Dto3D Video Converter using PyQt6."""

from __future__ import annotations


def run_gui() -> int:
    """Launch the desktop GUI (imports PyQt6 lazily)."""
    from video2d3d.gui.main_window import run_gui as _run_gui

    return _run_gui()


def __getattr__(name: str):
    """Lazily expose GUI classes so importing video2d3d.gui works without PyQt6."""
    if name in ("MainWindow", "run_gui"):
        from video2d3d.gui import main_window

        return getattr(main_window, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["MainWindow", "run_gui"]
