"""Pytest fixtures for Docker tests."""

from pathlib import Path
from typing import Generator

import pytest
import yaml


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def dockerfile_path(project_root: Path) -> Path:
    """Return the path to the GPU Dockerfile."""
    return project_root / "Dockerfile"


@pytest.fixture
def dockerfile_cpu_path(project_root: Path) -> Path:
    """Return the path to the CPU Dockerfile."""
    return project_root / "Dockerfile.cpu"


@pytest.fixture
def docker_compose_path(project_root: Path) -> Path:
    """Return the path to the GPU docker-compose.yml."""
    return project_root / "docker-compose.yml"


@pytest.fixture
def docker_compose_cpu_path(project_root: Path) -> Path:
    """Return the path to the CPU docker-compose.cpu.yml."""
    return project_root / "docker-compose.cpu.yml"


@pytest.fixture
def entrypoint_path(project_root: Path) -> Path:
    """Return the path to the entrypoint script."""
    return project_root / "docker" / "entrypoint.sh"


@pytest.fixture
def healthcheck_path(project_root: Path) -> Path:
    """Return the path to the healthcheck script."""
    return project_root / "docker" / "healthcheck.sh"


@pytest.fixture
def dockerignore_path(project_root: Path) -> Path:
    """Return the path to the .dockerignore file."""
    return project_root / ".dockerignore"


@pytest.fixture
def dockerfile_content(dockerfile_path: Path) -> str:
    """Return the content of the GPU Dockerfile."""
    return dockerfile_path.read_text()


@pytest.fixture
def dockerfile_cpu_content(dockerfile_cpu_path: Path) -> str:
    """Return the content of the CPU Dockerfile."""
    return dockerfile_cpu_path.read_text()


@pytest.fixture
def docker_compose_config(docker_compose_path: Path) -> dict:
    """Parse and return the docker-compose.yml configuration."""
    with open(docker_compose_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def docker_compose_cpu_config(docker_compose_cpu_path: Path) -> dict:
    """Parse and return the docker-compose.cpu.yml configuration."""
    with open(docker_compose_cpu_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def entrypoint_content(entrypoint_path: Path) -> str:
    """Return the content of the entrypoint script."""
    return entrypoint_path.read_text()


@pytest.fixture
def healthcheck_content(healthcheck_path: Path) -> str:
    """Return the content of the healthcheck script."""
    return healthcheck_path.read_text()
