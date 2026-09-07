"""Unit tests for GUI CLI integration.

Tests cover:
- GUI command registration
- GUI command execution
- Error handling when PyQt6 is not installed
"""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Skip all tests in this module if typer is not available
_typer_available = True
try:
    from typer.testing import CliRunner
except ImportError:
    _typer_available = False
    pytestmark = pytest.mark.skip(reason="typer not available")

if TYPE_CHECKING:
    pass

if _typer_available:
    from video2d3d.cli import app


@pytest.fixture
def cli_runner() -> Generator[CliRunner, None, None]:
    """Create a CLI runner for testing."""
    runner = CliRunner()
    yield runner


@pytest.mark.skipif(not _typer_available, reason="typer not available")
class TestGUICLI:
    """Tests for GUI CLI command."""

    def test_gui_command_exists(self, cli_runner: CliRunner) -> None:
        """Test that gui command is registered in CLI."""
        result = cli_runner.invoke(app, ["--help"])

        # Check that gui command is listed
        assert result.exit_code == 0
        assert "gui" in result.output

    def test_gui_command_help(self, cli_runner: CliRunner) -> None:
        """Test gui command help output."""
        result = cli_runner.invoke(app, ["gui", "--help"])

        assert result.exit_code == 0
        assert "GUI" in result.output or "gui" in result.output.lower()

    @patch("video2d3d.gui.run_gui")
    def test_gui_command_calls_run_gui(
        self, mock_run_gui: MagicMock, cli_runner: CliRunner
    ) -> None:
        """Test that gui command calls run_gui function."""
        # Mock run_gui to return 0 (success)
        mock_run_gui.return_value = 0

        cli_runner.invoke(app, ["gui"])

        # run_gui should have been called
        mock_run_gui.assert_called_once()

    @patch("video2d3d.gui.run_gui")
    def test_gui_command_handles_exit_code(
        self, mock_run_gui: MagicMock, cli_runner: CliRunner
    ) -> None:
        """Test that gui command handles exit codes correctly."""
        # Mock run_gui to return non-zero exit code
        mock_run_gui.return_value = 1

        result = cli_runner.invoke(app, ["gui"])

        # Should exit with the same code
        assert result.exit_code == 1

    @patch("video2d3d.gui.run_gui", side_effect=ImportError("PyQt6 not found"))
    def test_gui_command_handles_import_error(
        self, mock_run_gui: MagicMock, cli_runner: CliRunner
    ) -> None:
        """Test that gui command handles ImportError when PyQt6 is not installed."""
        result = cli_runner.invoke(app, ["gui"])

        # Should exit with error code
        assert result.exit_code != 0
        # Should show helpful error message
        assert "PyQt6" in result.output or "Error" in result.output

    @patch("video2d3d.gui.run_gui", side_effect=Exception("Unexpected error"))
    def test_gui_command_handles_generic_error(
        self, mock_run_gui: MagicMock, cli_runner: CliRunner
    ) -> None:
        """Test that gui command handles generic exceptions."""
        result = cli_runner.invoke(app, ["gui"])

        # Should exit with error code
        assert result.exit_code != 0
        # Should show error message
        assert "Error" in result.output


@pytest.mark.skipif(not _typer_available, reason="typer not available")
class TestGUIFunctionAvailability:
    """Tests for GUI function availability."""

    def test_run_gui_function_exists(self) -> None:
        """Test that run_gui function exists in gui module."""
        try:
            from video2d3d.gui import run_gui

            assert callable(run_gui)
        except ImportError:
            pytest.skip("PyQt6 not installed")

    def test_main_window_class_exists(self) -> None:
        """Test that MainWindow class exists in gui module."""
        try:
            from video2d3d.gui import MainWindow

            assert MainWindow is not None
        except ImportError:
            pytest.skip("PyQt6 not installed")


@pytest.mark.skipif(not _typer_available, reason="typer not available")
class TestCLIGUIIntegration:
    """Integration tests for CLI and GUI interaction."""

    @patch("video2d3d.gui.run_gui")
    def test_full_gui_invocation_flow(self, mock_run_gui: MagicMock, cli_runner: CliRunner) -> None:
        """Test complete flow of GUI invocation from CLI."""
        mock_run_gui.return_value = 0

        # Invoke GUI command
        result = cli_runner.invoke(app, ["gui"])

        # Check that execution was successful
        assert mock_run_gui.called
        # Exit code should match run_gui return value
        assert result.exit_code == 0

    def test_cli_app_structure(self) -> None:
        """Test that CLI app has correct structure."""
        # App should have multiple commands
        assert hasattr(app, "command")

        # Test that we can get registered commands
        # The typer app should have multiple commands registered
        assert app.registered_commands is not None
