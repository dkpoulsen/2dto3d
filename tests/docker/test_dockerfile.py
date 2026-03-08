"""Tests for Dockerfile configuration and best practices.

This module tests both GPU and CPU Dockerfiles for:
- File existence and readability
- Required instructions (FROM, LABEL, HEALTHCHECK, etc.)
- Security best practices (non-root user, no sensitive data)
- Multi-stage build structure
- ARG and ENV configuration
- Proper layer ordering for caching
- Version pinning
"""

import re
from pathlib import Path


class TestDockerfileExists:
    """Test Dockerfile file existence and basic properties."""

    def test_dockerfile_exists(self, dockerfile_path: Path) -> None:
        """GPU Dockerfile should exist."""
        assert dockerfile_path.exists(), "Dockerfile not found"

    def test_dockerfile_cpu_exists(self, dockerfile_cpu_path: Path) -> None:
        """CPU Dockerfile should exist."""
        assert dockerfile_cpu_path.exists(), "Dockerfile.cpu not found"

    def test_dockerfile_is_readable(self, dockerfile_path: Path) -> None:
        """GPU Dockerfile should be readable."""
        assert dockerfile_path.is_file()
        content = dockerfile_path.read_text()
        assert len(content) > 0

    def test_dockerfile_cpu_is_readable(self, dockerfile_cpu_path: Path) -> None:
        """CPU Dockerfile should be readable."""
        assert dockerfile_cpu_path.is_file()
        content = dockerfile_cpu_path.read_text()
        assert len(content) > 0


class TestDockerfileStructure:
    """Test Dockerfile structural requirements."""

    def test_dockerfile_has_from_instruction(self, dockerfile_content: str) -> None:
        """Dockerfile should have FROM instructions."""
        assert "FROM " in dockerfile_content, "Missing FROM instruction"

    def test_dockerfile_has_arg_for_versions(self, dockerfile_content: str) -> None:
        """Dockerfile should use ARG for version pinning."""
        assert "ARG PYTHON_VERSION" in dockerfile_content
        assert "ARG TORCH_VERSION" in dockerfile_content

    def test_dockerfile_cpu_has_arg_for_versions(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should use ARG for version pinning."""
        assert "ARG PYTHON_VERSION" in dockerfile_cpu_content
        assert "ARG TORCH_VERSION" in dockerfile_cpu_content

    def test_dockerfile_uses_multistage_build(self, dockerfile_content: str) -> None:
        """Dockerfile should use multi-stage build."""
        from_count = dockerfile_content.count("FROM ")
        assert from_count >= 2, "Dockerfile should have at least 2 stages"

    def test_dockerfile_cpu_uses_multistage_build(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should use multi-stage build."""
        from_count = dockerfile_cpu_content.count("FROM ")
        assert from_count >= 2, "Dockerfile should have at least 2 stages"

    def test_dockerfile_has_builder_stage(self, dockerfile_content: str) -> None:
        """Dockerfile should have a builder stage."""
        assert "AS builder" in dockerfile_content

    def test_dockerfile_has_runtime_stage(self, dockerfile_content: str) -> None:
        """Dockerfile should have a runtime stage."""
        assert "AS runtime" in dockerfile_content


class TestDockerfileLabels:
    """Test OCI image labels in Dockerfile."""

    def test_dockerfile_has_maintainer_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have maintainer label."""
        assert "LABEL maintainer=" in dockerfile_content

    def test_dockerfile_has_title_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have image title label."""
        assert "org.opencontainers.image.title" in dockerfile_content

    def test_dockerfile_has_description_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have image description label."""
        assert "org.opencontainers.image.description" in dockerfile_content

    def test_dockerfile_has_version_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have image version label."""
        assert "org.opencontainers.image.version" in dockerfile_content

    def test_dockerfile_has_source_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have image source label."""
        assert "org.opencontainers.image.source" in dockerfile_content

    def test_dockerfile_has_licenses_label(self, dockerfile_content: str) -> None:
        """Dockerfile should have image licenses label."""
        assert "org.opencontainers.image.licenses" in dockerfile_content


class TestDockerfileSecurity:
    """Test Dockerfile security best practices."""

    def test_dockerfile_creates_non_root_user(self, dockerfile_content: str) -> None:
        """Dockerfile should create a non-root user."""
        assert "useradd" in dockerfile_content or "adduser" in dockerfile_content

    def test_dockerfile_switches_to_non_root(self, dockerfile_content: str) -> None:
        """Dockerfile should switch to non-root user."""
        assert "USER video2d3d" in dockerfile_content

    def test_dockerfile_no_secrets_hardcoded(self, dockerfile_content: str) -> None:
        """Dockerfile should not have hardcoded secrets."""
        # Check for common secret patterns
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]
        for pattern in secret_patterns:
            assert not re.search(
                pattern, dockerfile_content, re.IGNORECASE
            ), f"Potential hardcoded secret found: {pattern}"

    def test_dockerfile_no_sudo(self, dockerfile_content: str) -> None:
        """Dockerfile should not use sudo."""
        assert "sudo" not in dockerfile_content.lower()

    def test_dockerfile_no_ssh_private_keys(self, dockerfile_content: str) -> None:
        """Dockerfile should not contain SSH private keys."""
        assert "BEGIN RSA PRIVATE KEY" not in dockerfile_content
        assert "BEGIN OPENSSH PRIVATE KEY" not in dockerfile_content


class TestDockerfileHealthCheck:
    """Test Dockerfile HEALTHCHECK configuration."""

    def test_dockerfile_has_healthcheck(self, dockerfile_content: str) -> None:
        """Dockerfile should have HEALTHCHECK instruction."""
        assert "HEALTHCHECK" in dockerfile_content

    def test_dockerfile_healthcheck_interval(self, dockerfile_content: str) -> None:
        """Healthcheck should have interval configured."""
        assert "--interval=" in dockerfile_content

    def test_dockerfile_healthcheck_timeout(self, dockerfile_content: str) -> None:
        """Healthcheck should have timeout configured."""
        assert "--timeout=" in dockerfile_content

    def test_dockerfile_healthcheck_retries(self, dockerfile_content: str) -> None:
        """Healthcheck should have retries configured."""
        assert "--retries=" in dockerfile_content

    def test_dockerfile_healthcheck_start_period(self, dockerfile_content: str) -> None:
        """Healthcheck should have start_period configured."""
        assert "--start-period=" in dockerfile_content

    def test_dockerfile_healthcheck_uses_script(self, dockerfile_content: str) -> None:
        """Healthcheck should use the healthcheck script."""
        assert "/healthcheck.sh" in dockerfile_content


class TestDockerfileEntrypoint:
    """Test Dockerfile ENTRYPOINT configuration."""

    def test_dockerfile_has_entrypoint(self, dockerfile_content: str) -> None:
        """Dockerfile should have ENTRYPOINT instruction."""
        assert "ENTRYPOINT" in dockerfile_content

    def test_dockerfile_entrypoint_uses_script(self, dockerfile_content: str) -> None:
        """Entrypoint should use the entrypoint script."""
        assert "/entrypoint.sh" in dockerfile_content

    def test_dockerfile_copies_entrypoint(self, dockerfile_content: str) -> None:
        """Dockerfile should copy entrypoint script."""
        assert "COPY docker/entrypoint.sh" in dockerfile_content

    def test_dockerfile_makes_entrypoint_executable(self, dockerfile_content: str) -> None:
        """Dockerfile should make entrypoint executable."""
        assert "chmod +x /entrypoint.sh" in dockerfile_content


class TestDockerfileDependencies:
    """Test Dockerfile dependency installation."""

    def test_dockerfile_installs_ffmpeg(self, dockerfile_content: str) -> None:
        """Dockerfile should install FFmpeg."""
        assert "ffmpeg" in dockerfile_content

    def test_dockerfile_installs_pytorch(self, dockerfile_content: str) -> None:
        """Dockerfile should install PyTorch."""
        assert "torch" in dockerfile_content

    def test_dockerfile_uses_cuda_base_image(self, dockerfile_content: str) -> None:
        """GPU Dockerfile should use NVIDIA CUDA base image."""
        assert "nvidia/cuda" in dockerfile_content

    def test_dockerfile_cpu_uses_python_base(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should use Python slim base image."""
        assert "python:" in dockerfile_cpu_content
        assert "slim" in dockerfile_cpu_content

    def test_dockerfile_installs_requirements(self, dockerfile_content: str) -> None:
        """Dockerfile should install from requirements.txt."""
        assert "requirements.txt" in dockerfile_content

    def test_dockerfile_installs_package(self, dockerfile_content: str) -> None:
        """Dockerfile should install the package."""
        assert "pip install" in dockerfile_content

    def test_dockerfile_copies_source_code(self, dockerfile_content: str) -> None:
        """Dockerfile should copy source code."""
        assert "COPY" in dockerfile_content
        assert "src/" in dockerfile_content


class TestDockerfileEnvVars:
    """Test Dockerfile environment variables."""

    def test_dockerfile_sets_pythonunbuffered(self, dockerfile_content: str) -> None:
        """Dockerfile should set PYTHONUNBUFFERED."""
        assert "PYTHONUNBUFFERED" in dockerfile_content

    def test_dockerfile_sets_pythondontwritebytecode(self, dockerfile_content: str) -> None:
        """Dockerfile should set PYTHONDONTWRITEBYTECODE."""
        assert "PYTHONDONTWRITEBYTECODE" in dockerfile_content

    def test_dockerfile_sets_cuda_visible_devices(self, dockerfile_content: str) -> None:
        """GPU Dockerfile should set CUDA_VISIBLE_DEVICES."""
        assert "CUDA_VISIBLE_DEVICES" in dockerfile_content

    def test_dockerfile_cpu_sets_no_gpu_flag(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should set VIDEO2D3D_NO_GPU."""
        assert "VIDEO2D3D_NO_GPU" in dockerfile_cpu_content


class TestDockerfileDirectories:
    """Test Dockerfile directory structure."""

    def test_dockerfile_creates_app_directory(self, dockerfile_content: str) -> None:
        """Dockerfile should create /app directory."""
        assert "WORKDIR /app" in dockerfile_content

    def test_dockerfile_creates_inputs_dir(self, dockerfile_content: str) -> None:
        """Dockerfile should create inputs directory."""
        assert "/app/inputs" in dockerfile_content

    def test_dockerfile_creates_outputs_dir(self, dockerfile_content: str) -> None:
        """Dockerfile should create outputs directory."""
        assert "/app/outputs" in dockerfile_content

    def test_dockerfile_creates_logs_dir(self, dockerfile_content: str) -> None:
        """Dockerfile should create logs directory."""
        assert "/app/logs" in dockerfile_content

    def test_dockerfile_creates_models_dir(self, dockerfile_content: str) -> None:
        """Dockerfile should create models directory."""
        assert "/app/models" in dockerfile_content

    def test_dockerfile_sets_directory_permissions(self, dockerfile_content: str) -> None:
        """Dockerfile should set proper directory permissions."""
        assert "chown" in dockerfile_content


class TestDockerfilePorts:
    """Test Dockerfile port configuration."""

    def test_dockerfile_exposes_api_port(self, dockerfile_content: str) -> None:
        """Dockerfile should expose API port."""
        assert "EXPOSE 8000" in dockerfile_content

    def test_dockerfile_cpu_exposes_api_port(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should expose API port."""
        assert "EXPOSE 8000" in dockerfile_cpu_content


class TestDockerfileLayerOrdering:
    """Test Dockerfile layer ordering for optimal caching."""

    def test_dockerfile_copies_requirements_before_source(self, dockerfile_content: str) -> None:
        """Dockerfile should copy requirements.txt before source code."""
        # Find positions
        req_pos = dockerfile_content.find("COPY requirements.txt")
        src_pos = dockerfile_content.find("COPY src/")
        assert req_pos > 0, "requirements.txt should be copied"
        assert src_pos > 0, "src/ should be copied"
        assert req_pos < src_pos, "requirements.txt should be copied before src/"

    def test_dockerfile_installs_deps_before_copying_source(self, dockerfile_content: str) -> None:
        """Dockerfile should install dependencies before copying source."""
        # Find positions - look for pip install with -r requirements.txt
        pip_pos = dockerfile_content.find("pip install")
        req_pos = dockerfile_content.find("-r requirements.txt")
        src_pos = dockerfile_content.find("COPY src/")
        # Check that pip install and requirements.txt are found
        assert pip_pos > 0, "pip install should be called"
        assert req_pos > 0, "-r requirements.txt should be used"
        assert src_pos > 0, "src/ should be copied"
        # pip install should come before COPY src/
        assert pip_pos < src_pos, "pip install should come before COPY src/"


class TestDockerfileOpenCVDependencies:
    """Test Dockerfile OpenCV runtime dependencies."""

    def test_dockerfile_installs_opencv_deps(self, dockerfile_content: str) -> None:
        """Dockerfile should install OpenCV runtime dependencies."""
        assert "libgl1-mesa-glx" in dockerfile_content or "libgl1" in dockerfile_content
        assert "libglib2.0" in dockerfile_content or "libglib2" in dockerfile_content

    def test_dockerfile_cpu_installs_opencv_deps(self, dockerfile_cpu_content: str) -> None:
        """CPU Dockerfile should install OpenCV runtime dependencies."""
        assert "libgl1-mesa-glx" in dockerfile_cpu_content or "libgl1" in dockerfile_cpu_content
        assert "libglib2.0" in dockerfile_cpu_content or "libglib2" in dockerfile_cpu_content
