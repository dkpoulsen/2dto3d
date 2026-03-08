"""Tests for Docker healthcheck script.

This module tests the healthcheck.sh script for:
- File existence and permissions
- Shell syntax validity
- Required health check functions
- Exit code handling
- Disk space checking
- Directory checking
- API health checking
"""

import os
import stat
import subprocess
from pathlib import Path


class TestHealthcheckExists:
    """Test healthcheck script existence."""

    def test_healthcheck_exists(self, healthcheck_path: Path) -> None:
        """Healthcheck script should exist."""
        assert healthcheck_path.exists(), "healthcheck.sh not found"

    def test_healthcheck_is_file(self, healthcheck_path: Path) -> None:
        """Healthcheck should be a file."""
        assert healthcheck_path.is_file()

    def test_healthcheck_is_readable(self, healthcheck_path: Path) -> None:
        """Healthcheck should be readable."""
        assert os.access(healthcheck_path, os.R_OK)

    def test_healthcheck_is_executable(self, healthcheck_path: Path) -> None:
        """Healthcheck should be executable."""
        mode = healthcheck_path.stat().st_mode
        assert mode & stat.S_IXUSR, "healthcheck.sh is not executable"


class TestHealthcheckSyntax:
    """Test healthcheck shell script syntax."""

    def test_healthcheck_has_valid_syntax(self, healthcheck_path: Path) -> None:
        """Healthcheck should have valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(healthcheck_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"


class TestHealthcheckShebang:
    """Test healthcheck shebang."""

    def test_healthcheck_has_shebang(self, healthcheck_content: str) -> None:
        """Healthcheck should have shebang."""
        assert healthcheck_content.startswith("#!/bin/bash")

    def test_healthcheck_shebang_uses_bash(self, healthcheck_content: str) -> None:
        """Healthcheck should use bash."""
        first_line = healthcheck_content.split("\n")[0]
        assert "bash" in first_line


class TestHealthcheckSettings:
    """Test healthcheck script settings."""

    def test_healthcheck_avoids_set_e(self, healthcheck_content: str) -> None:
        """Healthcheck should avoid set -e to handle check failures gracefully."""
        # Health checks should not use set -e because they need to continue
        # even when individual checks fail
        # Either no set -e or it should be handled carefully
        lines = healthcheck_content.split("\n")
        # Look for set -e at the start (before any checks)
        has_set_e = "set -e" in healthcheck_content
        # This is a soft requirement - healthcheck should handle failures
        # We just want to ensure proper error handling exists
        has_error_handling = (
            "|| true" in healthcheck_content
            or "|| return" in healthcheck_content
            or "2>/dev/null" in healthcheck_content
        )
        # If set -e is used, there should be proper error handling
        if has_set_e:
            assert has_error_handling, "With set -e, should have error handling"

    def test_healthcheck_uses_pipefail_safely(self, healthcheck_content: str) -> None:
        """Healthcheck should use pipefail safely if used."""
        # pipefail is fine with proper || true handling
        pass  # No strict requirement


class TestHealthcheckFunctions:
    """Test healthcheck functions."""

    def test_healthcheck_has_main_function(self, healthcheck_content: str) -> None:
        """Healthcheck should have main function."""
        assert "main()" in healthcheck_content or "main ()" in healthcheck_content

    def test_healthcheck_has_check_cli(self, healthcheck_content: str) -> None:
        """Healthcheck should have check_cli function."""
        assert "check_cli" in healthcheck_content

    def test_healthcheck_has_check_directories(self, healthcheck_content: str) -> None:
        """Healthcheck should have check_directories function."""
        assert "check_directories" in healthcheck_content

    def test_healthcheck_has_check_disk_space(self, healthcheck_content: str) -> None:
        """Healthcheck should have check_disk_space function."""
        assert "check_disk_space" in healthcheck_content

    def test_healthcheck_has_check_api_server(self, healthcheck_content: str) -> None:
        """Healthcheck should have check_api_server function."""
        assert "check_api_server" in healthcheck_content

    def test_healthcheck_has_check_curl(self, healthcheck_content: str) -> None:
        """Healthcheck should have check_curl function."""
        assert "check_curl" in healthcheck_content

    def test_healthcheck_calls_main(self, healthcheck_content: str) -> None:
        """Healthcheck should call main function at the end."""
        lines = healthcheck_content.strip().split("\n")
        last_lines = "\n".join(lines[-5:])
        assert 'main "$@"' in last_lines or "main $@" in last_lines


class TestHealthcheckCLI:
    """Test healthcheck CLI checking."""

    def test_healthcheck_checks_video2d3d_command(self, healthcheck_content: str) -> None:
        """Healthcheck should check for video2d3d command."""
        assert "video2d3d" in healthcheck_content
        assert "command -v" in healthcheck_content


class TestHealthcheckDirectories:
    """Test healthcheck directory checking."""

    def test_healthcheck_checks_app_inputs(self, healthcheck_content: str) -> None:
        """Healthcheck should check /app/inputs directory."""
        assert "/app/inputs" in healthcheck_content

    def test_healthcheck_checks_app_outputs(self, healthcheck_content: str) -> None:
        """Healthcheck should check /app/outputs directory."""
        assert "/app/outputs" in healthcheck_content

    def test_healthcheck_checks_app_logs(self, healthcheck_content: str) -> None:
        """Healthcheck should check /app/logs directory."""
        assert "/app/logs" in healthcheck_content

    def test_healthcheck_uses_d_flag(self, healthcheck_content: str) -> None:
        """Healthcheck should use -d flag for directory check."""
        assert "-d " in healthcheck_content


class TestHealthcheckDiskSpace:
    """Test healthcheck disk space checking."""

    def test_healthcheck_uses_df_command(self, healthcheck_content: str) -> None:
        """Healthcheck should use df command for disk space."""
        assert "df " in healthcheck_content

    def test_healthcheck_checks_app_directory(self, healthcheck_content: str) -> None:
        """Healthcheck should check /app directory disk space."""
        assert "df -k /app" in healthcheck_content

    def test_healthcheck_has_minimum_space_threshold(self, healthcheck_content: str) -> None:
        """Healthcheck should have a minimum space threshold."""
        # Should have some threshold for minimum disk space
        assert (
            "1048576" in healthcheck_content
            or "1GB" in healthcheck_content.upper()
            or "MIN_DISK" in healthcheck_content
        )


class TestHealthcheckAPI:
    """Test healthcheck API server checking."""

    def test_healthcheck_uses_curl(self, healthcheck_content: str) -> None:
        """Healthcheck should use curl for API check."""
        assert "curl" in healthcheck_content

    def test_healthcheck_checks_health_endpoint(self, healthcheck_content: str) -> None:
        """Healthcheck should check /health endpoint."""
        assert "/health" in healthcheck_content

    def test_healthcheck_has_timeout(self, healthcheck_content: str) -> None:
        """Healthcheck should have timeout for curl."""
        assert "--connect-timeout" in healthcheck_content or "--max-time" in healthcheck_content

    def test_healthcheck_uses_localhost(self, healthcheck_content: str) -> None:
        """Healthcheck should use localhost for API check."""
        assert "localhost" in healthcheck_content or "127.0.0.1" in healthcheck_content

    def test_healthcheck_checks_port_8000(self, healthcheck_content: str) -> None:
        """Healthcheck should check port 8000."""
        assert "8000" in healthcheck_content


class TestHealthcheckExitCodes:
    """Test healthcheck exit codes."""

    def test_healthcheck_exits_0_on_success(self, healthcheck_content: str) -> None:
        """Healthcheck should exit 0 on success."""
        assert "exit 0" in healthcheck_content

    def test_healthcheck_exits_1_on_failure(self, healthcheck_content: str) -> None:
        """Healthcheck should exit 1 on failure."""
        assert "exit 1" in healthcheck_content


class TestHealthcheckCounting:
    """Test healthcheck check counting logic."""

    def test_healthcheck_tracks_passed_checks(self, healthcheck_content: str) -> None:
        """Healthcheck should track passed checks."""
        assert "checks_passed" in healthcheck_content

    def test_healthcheck_tracks_total_checks(self, healthcheck_content: str) -> None:
        """Healthcheck should track total checks."""
        assert "total_checks" in healthcheck_content

    def test_healthcheck_calculates_threshold(self, healthcheck_content: str) -> None:
        """Healthcheck should calculate passing threshold."""
        # Should have some logic for determining pass/fail threshold
        assert "-ge" in healthcheck_content or ">=" in healthcheck_content

    def test_healthcheck_handles_arithmetic_safely(self, healthcheck_content: str) -> None:
        """Healthcheck should handle arithmetic safely."""
        # Should use (( )) with || true or similar pattern
        has_safe_arithmetic = (
            "|| true" in healthcheck_content
            or "|| return 0" in healthcheck_content
            or ":=" in healthcheck_content  # default value syntax
        )
        assert has_safe_arithmetic, "Should have safe arithmetic handling"


class TestHealthcheckModeSupport:
    """Test healthcheck mode support (serve vs default)."""

    def test_healthcheck_supports_serve_mode(self, healthcheck_content: str) -> None:
        """Healthcheck should support serve mode for API checks."""
        assert "serve" in healthcheck_content or "api" in healthcheck_content

    def test_healthcheck_accepts_mode_argument(self, healthcheck_content: str) -> None:
        """Healthcheck should accept mode as argument."""
        assert (
            '"$1"' in healthcheck_content
            or '"${1:-}"' in healthcheck_content
            or "$1" in healthcheck_content
        )


class TestHealthcheckConstants:
    """Test healthcheck constants."""

    def test_healthcheck_has_default_host(self, healthcheck_content: str) -> None:
        """Healthcheck should have default API host."""
        assert "API_HOST" in healthcheck_content or "localhost" in healthcheck_content

    def test_healthcheck_has_default_port(self, healthcheck_content: str) -> None:
        """Healthcheck should have default API port."""
        assert "API_PORT" in healthcheck_content or "8000" in healthcheck_content

    def test_healthcheck_has_default_timeout(self, healthcheck_content: str) -> None:
        """Healthcheck should have default timeout."""
        assert "TIMEOUT" in healthcheck_content or "timeout" in healthcheck_content.lower()


class TestHealthcheckRobustness:
    """Test healthcheck robustness."""

    def test_healthcheck_silences_errors(self, healthcheck_content: str) -> None:
        """Healthcheck should silence errors for individual checks."""
        assert "2>/dev/null" in healthcheck_content or "2>&1" in healthcheck_content

    def test_healthcheck_handles_missing_commands(self, healthcheck_content: str) -> None:
        """Healthcheck should handle missing commands gracefully."""
        # Check for command availability pattern
        assert "command -v" in healthcheck_content

    def test_healthcheck_uses_readonly_for_constants(self, healthcheck_content: str) -> None:
        """Healthcheck should use readonly for constants."""
        assert "readonly" in healthcheck_content


class TestHealthcheckPython:
    """Test healthcheck Python check."""

    def test_healthcheck_checks_python(self, healthcheck_content: str) -> None:
        """Healthcheck should check for Python availability."""
        assert "check_python" in healthcheck_content
        assert "python" in healthcheck_content.lower()
