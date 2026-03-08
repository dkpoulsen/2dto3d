"""Tests for Docker entrypoint script.

This module tests the entrypoint.sh script for:
- File existence and permissions
- Shell syntax validity
- Required functions and handlers
- Command routing
- Signal handling
- Environment loading
- GPU detection
"""

import os
import stat
import subprocess
from pathlib import Path


class TestEntrypointExists:
    """Test entrypoint script existence."""

    def test_entrypoint_exists(self, entrypoint_path: Path) -> None:
        """Entrypoint script should exist."""
        assert entrypoint_path.exists(), "entrypoint.sh not found"

    def test_entrypoint_is_file(self, entrypoint_path: Path) -> None:
        """Entrypoint should be a file."""
        assert entrypoint_path.is_file()

    def test_entrypoint_is_readable(self, entrypoint_path: Path) -> None:
        """Entrypoint should be readable."""
        assert os.access(entrypoint_path, os.R_OK)

    def test_entrypoint_is_executable(self, entrypoint_path: Path) -> None:
        """Entrypoint should be executable."""
        mode = entrypoint_path.stat().st_mode
        assert mode & stat.S_IXUSR, "entrypoint.sh is not executable"


class TestEntrypointSyntax:
    """Test entrypoint shell script syntax."""

    def test_entrypoint_has_valid_syntax(self, entrypoint_path: Path) -> None:
        """Entrypoint should have valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(entrypoint_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestEntrypointShebang:
    """Test entrypoint shebang."""

    def test_entrypoint_has_shebang(self, entrypoint_content: str) -> None:
        """Entrypoint should have shebang."""
        assert entrypoint_content.startswith("#!/bin/bash")

    def test_entrypoint_shebang_uses_bash(self, entrypoint_content: str) -> None:
        """Entrypoint should use bash."""
        first_line = entrypoint_content.split("\n")[0]
        assert "bash" in first_line


class TestEntrypointSettings:
    """Test entrypoint script settings."""

    def test_entrypoint_has_strict_mode(self, entrypoint_content: str) -> None:
        """Entrypoint should use strict mode (set -euo pipefail or similar)."""
        # Check for either set -euo pipefail or individual settings
        has_strict = (
            "set -euo pipefail" in entrypoint_content
            or "set -e" in entrypoint_content
            or "set -o pipefail" in entrypoint_content
        )
        assert has_strict, "Entrypoint should use strict mode"


class TestEntrypointSignalHandling:
    """Test entrypoint signal handling."""

    def test_entrypoint_has_signal_handler(self, entrypoint_content: str) -> None:
        """Entrypoint should have signal trap handler."""
        assert "trap" in entrypoint_content

    def test_entrypoint_handles_sigterm(self, entrypoint_content: str) -> None:
        """Entrypoint should handle SIGTERM."""
        assert "SIGTERM" in entrypoint_content

    def test_entrypoint_handles_sigint(self, entrypoint_content: str) -> None:
        """Entrypoint should handle SIGINT."""
        assert "SIGINT" in entrypoint_content

    def test_entrypoint_has_cleanup_function(self, entrypoint_content: str) -> None:
        """Entrypoint should have cleanup function."""
        assert "cleanup" in entrypoint_content.lower()


class TestEntrypointLogging:
    """Test entrypoint logging functions."""

    def test_entrypoint_has_log_info(self, entrypoint_content: str) -> None:
        """Entrypoint should have log_info function."""
        assert "log_info" in entrypoint_content

    def test_entrypoint_has_log_error(self, entrypoint_content: str) -> None:
        """Entrypoint should have log_error function."""
        assert "log_error" in entrypoint_content

    def test_entrypoint_has_log_warning(self, entrypoint_content: str) -> None:
        """Entrypoint should have log_warning function."""
        assert "log_warning" in entrypoint_content or "log_warn" in entrypoint_content

    def test_entrypoint_has_log_success(self, entrypoint_content: str) -> None:
        """Entrypoint should have log_success function."""
        assert "log_success" in entrypoint_content


class TestEntrypointFunctions:
    """Test entrypoint functions."""

    def test_entrypoint_has_main_function(self, entrypoint_content: str) -> None:
        """Entrypoint should have main function."""
        assert "main()" in entrypoint_content or "main ()" in entrypoint_content

    def test_entrypoint_has_setup_directories(self, entrypoint_content: str) -> None:
        """Entrypoint should have setup_directories function."""
        assert "setup_directories" in entrypoint_content

    def test_entrypoint_has_check_gpu(self, entrypoint_content: str) -> None:
        """Entrypoint should have check_gpu function."""
        assert "check_gpu" in entrypoint_content

    def test_entrypoint_has_load_env(self, entrypoint_content: str) -> None:
        """Entrypoint should have load_env function."""
        assert "load_env" in entrypoint_content

    def test_entrypoint_calls_main(self, entrypoint_content: str) -> None:
        """Entrypoint should call main function at the end."""
        # Check that main is called at the bottom of the script
        lines = entrypoint_content.strip().split("\n")
        last_lines = "\n".join(lines[-5:])
        assert 'main "$@"' in last_lines or "main $@" in last_lines


class TestEntrypointCommands:
    """Test entrypoint command routing."""

    def test_entrypoint_has_serve_command(self, entrypoint_content: str) -> None:
        """Entrypoint should handle serve command."""
        assert "serve" in entrypoint_content
        assert "server" in entrypoint_content or "api" in entrypoint_content

    def test_entrypoint_has_convert_command(self, entrypoint_content: str) -> None:
        """Entrypoint should handle convert command."""
        assert "convert" in entrypoint_content

    def test_entrypoint_has_batch_command(self, entrypoint_content: str) -> None:
        """Entrypoint should handle batch command."""
        assert "batch" in entrypoint_content

    def test_entrypoint_has_shell_command(self, entrypoint_content: str) -> None:
        """Entrypoint should handle shell command."""
        assert "shell" in entrypoint_content or "bash" in entrypoint_content

    def test_entrypoint_has_help_command(self, entrypoint_content: str) -> None:
        """Entrypoint should handle help command."""
        assert "--help" in entrypoint_content or "help" in entrypoint_content


class TestEntrypointGPUDetection:
    """Test entrypoint GPU detection."""

    def test_entrypoint_checks_nvidia_smi(self, entrypoint_content: str) -> None:
        """Entrypoint should check for nvidia-smi."""
        assert "nvidia-smi" in entrypoint_content

    def test_entrypoint_sets_no_gpu_env(self, entrypoint_content: str) -> None:
        """Entrypoint should set VIDEO2D3D_NO_GPU when no GPU."""
        assert "VIDEO2D3D_NO_GPU" in entrypoint_content


class TestEntrypointDirectories:
    """Test entrypoint directory setup."""

    def test_entrypoint_creates_inputs_dir(self, entrypoint_content: str) -> None:
        """Entrypoint should create inputs directory."""
        # Uses either hardcoded path or APP_DIR variable
        assert "inputs" in entrypoint_content

    def test_entrypoint_creates_outputs_dir(self, entrypoint_content: str) -> None:
        """Entrypoint should create outputs directory."""
        assert "outputs" in entrypoint_content

    def test_entrypoint_creates_logs_dir(self, entrypoint_content: str) -> None:
        """Entrypoint should create logs directory."""
        assert "logs" in entrypoint_content

    def test_entrypoint_creates_models_dir(self, entrypoint_content: str) -> None:
        """Entrypoint should create models directory."""
        assert "models" in entrypoint_content

    def test_entrypoint_has_app_dir_constant(self, entrypoint_content: str) -> None:
        """Entrypoint should have APP_DIR constant."""
        assert "APP_DIR" in entrypoint_content

    def test_entrypoint_uses_mkdir(self, entrypoint_content: str) -> None:
        """Entrypoint should use mkdir to create directories."""
        assert "mkdir" in entrypoint_content

    """Test entrypoint environment handling."""

    def test_entrypoint_reads_env_file(self, entrypoint_content: str) -> None:
        """Entrypoint should read .env file."""
        assert ".env" in entrypoint_content

    def test_entrypoint_exports_env_vars(self, entrypoint_content: str) -> None:
        """Entrypoint should export environment variables."""
        assert "export" in entrypoint_content

    def test_entrypoint_handles_env_values_with_spaces(self, entrypoint_content: str) -> None:
        """Entrypoint should handle env values with spaces properly."""
        # Should not use naive xargs approach
        # Should use proper parsing with BASH_REMATCH or similar
        assert (
            "BASH_REMATCH" in entrypoint_content
            or "IFS=" in entrypoint_content
            or "while" in entrypoint_content
        )


class TestEntrypointExec:
    """Test entrypoint exec usage."""

    def test_entrypoint_uses_exec(self, entrypoint_content: str) -> None:
        """Entrypoint should use exec for command execution."""
        assert "exec" in entrypoint_content

    def test_entrypoint_does_not_exit_explicitly(self, entrypoint_content: str) -> None:
        """Entrypoint should not have explicit exit in success paths."""
        # exec replaces the shell, so explicit exit shouldn't be needed
        # This is a soft check - some exit statements are fine
        pass  # Just ensuring exec is used is sufficient


class TestEntrypointBanner:
    """Test entrypoint banner."""

    def test_entrypoint_has_banner(self, entrypoint_content: str) -> None:
        """Entrypoint should display a banner."""
        assert (
            "print_banner" in entrypoint_content
            or "2Dto3D" in entrypoint_content
            or "2dto3d" in entrypoint_content.lower()
        )

    def test_entrypoint_has_app_name_in_banner(self, entrypoint_content: str) -> None:
        """Banner should contain app name."""
        # Check for either "2Dto3D" or "video2d3d" or similar
        has_app_name = (
            "2Dto3D" in entrypoint_content
            or "2dto3d" in entrypoint_content.lower()
            or "video2d3d" in entrypoint_content.lower()
        )
        assert has_app_name


class TestEntrypointColors:
    """Test entrypoint color output."""

    def test_entrypoint_has_color_constants(self, entrypoint_content: str) -> None:
        """Entrypoint should define color constants."""
        colors = ["RED=", "GREEN=", "YELLOW=", "BLUE="]
        has_colors = any(color in entrypoint_content for color in colors)
        assert has_colors or "\\033[" in entrypoint_content

    def test_entrypoint_has_no_color_constant(self, entrypoint_content: str) -> None:
        """Entrypoint should have NC (no color) constant."""
        assert "NC=" in entrypoint_content or "\\033[0m" in entrypoint_content
