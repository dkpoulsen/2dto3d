"""Tests for validating paths and references in CI workflow."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")
PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def workflow_yaml() -> dict:
    """Load and parse CI workflow YAML."""
    return yaml.safe_load(CI_WORKFLOW_PATH.read_text())


@pytest.fixture
def pyproject_config() -> dict:
    """Load pyproject.toml configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


@pytest.fixture
def pytest_markers(pyproject_config: dict) -> list[str]:
    """Get list of defined pytest markers."""
    pytest_config = pyproject_config.get("tool", {}).get("pytest", {}).get("ini_options", {})
    markers = pytest_config.get("markers", [])
    # Extract marker names (before the colon)
    return [m.split(":")[0].strip() for m in markers]


class TestRequiredFilesExist:
    """Test that all files referenced in CI workflow exist."""

    def test_requirements_dev_exists(self) -> None:
        """Verify requirements-dev.txt exists."""
        req_path = PROJECT_ROOT / "requirements-dev.txt"
        assert req_path.exists(), "requirements-dev.txt should exist for CI"

    def test_pyproject_toml_exists(self) -> None:
        """Verify pyproject.toml exists."""
        pyproject_path = PROJECT_ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist for CI"

    def test_src_directory_exists(self) -> None:
        """Verify src directory exists."""
        src_path = PROJECT_ROOT / "src"
        assert src_path.exists(), "src directory should exist"

    def test_tests_directory_exists(self) -> None:
        """Verify tests directory exists."""
        tests_path = PROJECT_ROOT / "tests"
        assert tests_path.exists(), "tests directory should exist"


class TestSourcePaths:
    """Test that source paths in CI workflow are correct."""

    def test_lint_source_path_exists(self) -> None:
        """Verify lint job source path exists."""
        # The lint job checks src/video2d3d and tests
        source_path = PROJECT_ROOT / "src" / "video2d3d"
        assert source_path.exists(), "src/video2d3d should exist for lint job"

    def test_tests_path_exists(self) -> None:
        """Verify tests path exists."""
        tests_path = PROJECT_ROOT / "tests"
        assert tests_path.exists(), "tests directory should exist"
        assert tests_path.is_dir(), "tests should be a directory"


class TestPytestMarkers:
    """Test that pytest markers used in CI are defined in pyproject.toml."""

    def test_slow_marker_defined(self, pytest_markers: list[str]) -> None:
        """Verify 'slow' marker is defined."""
        assert "slow" in pytest_markers, "'slow' marker should be defined in pyproject.toml"

    def test_gpu_marker_defined(self, pytest_markers: list[str]) -> None:
        """Verify 'gpu' marker is defined."""
        assert "gpu" in pytest_markers, "'gpu' marker should be defined in pyproject.toml"

    def test_integration_marker_defined(self, pytest_markers: list[str]) -> None:
        """Verify 'integration' marker is defined."""
        assert (
            "integration" in pytest_markers
        ), "'integration' marker should be defined in pyproject.toml"


class TestCoverageConfiguration:
    """Test coverage configuration in pyproject.toml."""

    def test_coverage_source_matches_lint_path(self, pyproject_config: dict) -> None:
        """Verify coverage source matches the source path used in CI."""
        coverage_config = pyproject_config.get("tool", {}).get("coverage", {}).get("run", {})
        sources = coverage_config.get("source", [])
        assert "src/video2d3d" in sources, "Coverage source should include src/video2d3d"


class TestPythonVersionSupport:
    """Test Python version support matches CI matrix."""

    def test_requires_python_matches_matrix(
        self, pyproject_config: dict, workflow_yaml: dict
    ) -> None:
        """Verify requires-python in pyproject.toml supports CI matrix versions."""
        project = pyproject_config.get("project", {})
        requires_python = project.get("requires-python", "")

        # Get Python versions from CI matrix
        # Note: YAML parses 'on' as True in Python, so we access it as True
        workflow_yaml.get(True, workflow_yaml.get("on", {}))
        workflow_yaml["jobs"]["test"]["strategy"]["matrix"]["python-version"]

        # Check that requires-python is compatible with matrix versions
        # Typically requires-python should be ">=3.9" for matrix ["3.9", "3.10", "3.11", "3.12"]
        assert (
            "3.9" in requires_python or ">=3.9" in requires_python
        ), "requires-python should support Python 3.9 (minimum in CI matrix)"


class TestLintingToolConfig:
    """Test that linting tools used in CI are properly configured."""

    def test_black_config_exists(self, pyproject_config: dict) -> None:
        """Verify black configuration exists."""
        assert "black" in pyproject_config.get(
            "tool", {}
        ), "Black config should be in pyproject.toml"

    def test_ruff_config_exists(self, pyproject_config: dict) -> None:
        """Verify ruff configuration exists."""
        assert "ruff" in pyproject_config.get("tool", {}), "Ruff config should be in pyproject.toml"

    def test_isort_config_exists_or_via_ruff(self, pyproject_config: dict) -> None:
        """Verify isort config exists (either standalone or via ruff)."""
        tools = pyproject_config.get("tool", {})
        has_isort = "isort" in tools
        has_ruff_isort = "ruff" in tools and "isort" in tools.get("ruff", {}).get("lint", {})
        assert has_isort or has_ruff_isort, "Isort config should exist (standalone or via ruff)"


class TestSystemDependencies:
    """Test that system dependencies in CI are documented."""

    def test_ffmpeg_is_documented_requirement(self) -> None:
        """Verify FFmpeg is documented as a requirement."""
        readme_path = PROJECT_ROOT / "README.md"
        if readme_path.exists():
            readme_content = readme_path.read_text().lower()
            assert "ffmpeg" in readme_content, "FFmpeg should be documented in README.md"


class TestWorkflowUsesCorrectCoveragePath:
    """Test that coverage path in workflow matches project structure."""

    def test_coverage_path_matches_source(self, workflow_yaml: dict) -> None:
        """Verify --cov path in workflow matches actual source structure."""
        test_steps = workflow_yaml["jobs"]["test"]["steps"]
        # Find the step that runs pytest with coverage (has --cov flag)
        pytest_step = next(
            (s for s in test_steps if "--cov" in str(s.get("run", ""))),
            None,
        )
        assert pytest_step is not None, "Should have pytest step with --cov"
        run_cmd = pytest_step["run"]
        # Coverage path should reference the actual package
        assert "src/video2d3d" in run_cmd, "Coverage should use src/video2d3d path"
        """Verify --cov path in workflow matches actual source structure."""
        test_steps = workflow_yaml["jobs"]["test"]["steps"]
        pytest_step = next(
            (s for s in test_steps if "pytest" in str(s.get("run", "")).lower()),
            None,
        )
        if pytest_step:
            run_cmd = pytest_step["run"]
            # Coverage path should reference the actual package
            assert "src/video2d3d" in run_cmd, "Coverage should use src/video2d3d path"
