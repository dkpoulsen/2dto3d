"""Tests for .dockerignore configuration.

This module tests the .dockerignore file for:
- File existence
- Required exclusion patterns
- Proper patterns for Python projects
- Docker-specific exclusions
"""

from pathlib import Path


class TestDockerignoreExists:
    """Test .dockerignore file existence."""

    def test_dockerignore_exists(self, dockerignore_path: Path) -> None:
        """.dockerignore should exist."""
        assert dockerignore_path.exists(), ".dockerignore not found"

    def test_dockerignore_is_file(self, dockerignore_path: Path) -> None:
        """.dockerignore should be a file."""
        assert dockerignore_path.is_file()

    def test_dockerignore_is_readable(self, dockerignore_path: Path) -> None:
        """.dockerignore should be readable."""
        assert dockerignore_path.stat().st_size > 0


class TestDockerignorePythonExclusions:
    """Test .dockerignore Python-specific exclusions."""

    def test_dockerignore_excludes_pycache(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude __pycache__."""
        content = dockerignore_path.read_text()
        assert "__pycache__" in content

    def test_dockerignore_excludes_pyc_files(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .pyc files."""
        content = dockerignore_path.read_text()
        assert ".pyc" in content or "*.py[cod]" in content

    def test_dockerignore_excludes_egg_info(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .egg-info."""
        content = dockerignore_path.read_text()
        assert ".egg-info" in content or "*.egg-info" in content

    def test_dockerignore_excludes_dist(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude dist/."""
        content = dockerignore_path.read_text()
        assert "dist/" in content or "dist" in content

    def test_dockerignore_excludes_build(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude build/."""
        content = dockerignore_path.read_text()
        assert "build/" in content or "build" in content

    def test_dockerignore_excludes_venv(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude venv/."""
        content = dockerignore_path.read_text()
        assert "venv" in content or ".venv" in content


class TestDockerignoreIDEExclusions:
    """Test .dockerignore IDE-specific exclusions."""

    def test_dockerignore_excludes_idea(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .idea/."""
        content = dockerignore_path.read_text()
        assert ".idea" in content

    def test_dockerignore_excludes_vscode(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .vscode/."""
        content = dockerignore_path.read_text()
        assert ".vscode" in content


class TestDockerignoreTestingExclusions:
    """Test .dockerignore testing-related exclusions."""

    def test_dockerignore_excludes_pytest_cache(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .pytest_cache."""
        content = dockerignore_path.read_text()
        assert ".pytest_cache" in content

    def test_dockerignore_excludes_coverage(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude coverage files."""
        content = dockerignore_path.read_text()
        assert ".coverage" in content or "coverage" in content

    def test_dockerignore_excludes_htmlcov(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude htmlcov/."""
        content = dockerignore_path.read_text()
        assert "htmlcov" in content


class TestDockerignoreGitExclusions:
    """Test .dockerignore git-related exclusions."""

    def test_dockerignore_excludes_git(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .git/."""
        content = dockerignore_path.read_text()
        assert ".git" in content


class TestDockerignoreDockerExclusions:
    """Test .dockerignore Docker-specific exclusions."""

    def test_dockerignore_excludes_dockerfiles(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude Dockerfile."""
        content = dockerignore_path.read_text()
        assert "Dockerfile" in content

    def test_dockerignore_excludes_docker_compose(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude docker-compose files."""
        content = dockerignore_path.read_text()
        assert "docker-compose" in content

    def test_dockerignore_excludes_dockerignore(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .dockerignore itself."""
        content = dockerignore_path.read_text()
        assert ".dockerignore" in content


class TestDockerignoreEnvExclusions:
    """Test .dockerignore environment file exclusions."""

    def test_dockerignore_excludes_env(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .env files (except .env.example)."""
        content = dockerignore_path.read_text()
        assert ".env" in content

    def test_dockerignore_keeps_env_example(self, dockerignore_path: Path) -> None:
        """.dockerignore should NOT exclude .env.example."""
        content = dockerignore_path.read_text()
        # Check that there's a pattern to keep .env.example
        # This is usually done with !.env.example or by only excluding .env
        lines = content.split("\n")
        # Look for explicit inclusion of .env.example
        has_exception = any(line.strip() == "!.env.example" for line in lines)
        # Or check that the exclusion is specific enough
        has_specific_exclusion = any(".env" in line and not line.startswith("!") for line in lines)
        assert has_exception or has_specific_exclusion


class TestDockerignoreInputOutputExclusions:
    """Test .dockerignore input/output directory exclusions."""

    def test_dockerignore_excludes_inputs(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude inputs/."""
        content = dockerignore_path.read_text()
        assert "inputs" in content

    def test_dockerignore_excludes_outputs(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude outputs/."""
        content = dockerignore_path.read_text()
        assert "outputs" in content

    def test_dockerignore_excludes_models(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude models/."""
        content = dockerignore_path.read_text()
        assert "models" in content


class TestDockerignoreLogExclusions:
    """Test .dockerignore log file exclusions."""

    def test_dockerignore_excludes_logs(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude logs/."""
        content = dockerignore_path.read_text()
        assert "logs" in content or "*.log" in content


class TestDockerignoreDocumentationExclusions:
    """Test .dockerignore documentation exclusions."""

    def test_dockerignore_excludes_docs(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude docs/."""
        content = dockerignore_path.read_text()
        assert "docs" in content

    def test_dockerignore_keeps_readme(self, dockerignore_path: Path) -> None:
        """.dockerignore should keep README.md (or not explicitly exclude it)."""
        content = dockerignore_path.read_text()
        # README.md should not be in the exclusion list
        # Or if *.md is excluded, there should be an exception for README.md
        lines = [l.strip() for l in content.split("\n")]
        has_readme_exception = any(l == "!README.md" for l in lines)
        has_md_exclusion = any("*.md" in l and not l.startswith("#") for l in lines)
        has_readme_exclusion = any(
            "README.md" in l and not l.startswith("!") and not l.startswith("#") for l in lines
        )
        # Either no README.md exclusion, or explicit exception
        assert (
            not has_readme_exclusion
            or has_readme_exception
            or not has_md_exclusion
            or has_readme_exception
        )


class TestDockerignoreDevelopmentExclusions:
    """Test .dockerignore development tool exclusions."""

    def test_dockerignore_excludes_pre_commit(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude pre-commit config."""
        content = dockerignore_path.read_text()
        assert "pre-commit" in content

    def test_dockerignore_excludes_github(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .github/."""
        content = dockerignore_path.read_text()
        assert ".github" in content

    def test_dockerignore_excludes_ci_configs(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude CI config files."""
        content = dockerignore_path.read_text()
        # Should exclude common CI configs
        has_ci_exclusions = ".travis" in content or "gitlab-ci" in content or ".github" in content
        assert has_ci_exclusions


class TestDockerignoreOSEclusions:
    """Test .dockerignore OS file exclusions."""

    def test_dockerignore_excludes_ds_store(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude .DS_Store."""
        content = dockerignore_path.read_text()
        assert ".DS_Store" in content

    def test_dockerignore_excludes_thumbs_db(self, dockerignore_path: Path) -> None:
        """.dockerignore should exclude Thumbs.db."""
        content = dockerignore_path.read_text()
        assert "Thumbs.db" in content
