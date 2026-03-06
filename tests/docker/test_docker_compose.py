"""Tests for Docker Compose configuration validation.

This module tests both GPU and CPU docker-compose files for:
- Valid YAML syntax
- Required services configuration
- Volume mounts
- Environment variables
- Health checks
- Resource limits
- Network configuration
"""

from pathlib import Path

import pytest
import yaml


class TestDockerComposeExists:
    """Test docker-compose file existence."""

    def test_docker_compose_exists(self, docker_compose_path: Path) -> None:
        """docker-compose.yml should exist."""
        assert docker_compose_path.exists(), "docker-compose.yml not found"

    def test_docker_compose_cpu_exists(self, docker_compose_cpu_path: Path) -> None:
        """docker-compose.cpu.yml should exist."""
        assert docker_compose_cpu_path.exists(), "docker-compose.cpu.yml not found"


class TestDockerComposeYamlValidity:
    """Test docker-compose YAML syntax validity."""

    def test_docker_compose_is_valid_yaml(self, docker_compose_path: Path) -> None:
        """docker-compose.yml should be valid YAML."""
        with open(docker_compose_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_docker_compose_cpu_is_valid_yaml(self, docker_compose_cpu_path: Path) -> None:
        """docker-compose.cpu.yml should be valid YAML."""
        with open(docker_compose_cpu_path) as f:
            config = yaml.safe_load(f)
        assert config is not None

    def test_docker_compose_has_version(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have a version."""
        assert "version" in docker_compose_config

    def test_docker_compose_cpu_has_version(self, docker_compose_cpu_config: dict) -> None:
        """docker-compose.cpu.yml should have a version."""
        assert "version" in docker_compose_cpu_config

    def test_docker_compose_has_services(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have services section."""
        assert "services" in docker_compose_config
        assert len(docker_compose_config["services"]) > 0


class TestDockerComposeServices:
    """Test docker-compose services configuration."""

    def test_docker_compose_has_main_service(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have video2d3d service."""
        assert "video2d3d" in docker_compose_config["services"]

    def test_docker_compose_has_api_service(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have api service."""
        assert "api" in docker_compose_config["services"]

    def test_docker_compose_has_batch_service(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have batch service."""
        assert "batch" in docker_compose_config["services"]

    def test_docker_compose_cpu_has_main_service(self, docker_compose_cpu_config: dict) -> None:
        """docker-compose.cpu.yml should have video2d3d service."""
        assert "video2d3d" in docker_compose_cpu_config["services"]

    def test_docker_compose_cpu_has_api_service(self, docker_compose_cpu_config: dict) -> None:
        """docker-compose.cpu.yml should have api service."""
        assert "api" in docker_compose_cpu_config["services"]

    def test_docker_compose_cpu_has_batch_service(self, docker_compose_cpu_config: dict) -> None:
        """docker-compose.cpu.yml should have batch service."""
        assert "batch" in docker_compose_cpu_config["services"]

    def test_api_service_has_profile(self, docker_compose_config: dict) -> None:
        """API service should have profile configured."""
        api_service = docker_compose_config["services"]["api"]
        assert "profiles" in api_service
        assert "api" in api_service["profiles"]

    def test_batch_service_has_profile(self, docker_compose_config: dict) -> None:
        """Batch service should have profile configured."""
        batch_service = docker_compose_config["services"]["batch"]
        assert "profiles" in batch_service
        assert "batch" in batch_service["profiles"]

    def test_batch_service_no_auto_restart(self, docker_compose_config: dict) -> None:
        """Batch service should not auto-restart."""
        batch_service = docker_compose_config["services"]["batch"]
        assert batch_service.get("restart") == "no"


class TestDockerComposeVolumes:
    """Test docker-compose volume configuration."""

    def test_main_service_has_inputs_volume(self, docker_compose_config: dict) -> None:
        """Main service should mount inputs directory."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        assert any("inputs" in str(v) for v in volumes)

    def test_main_service_has_outputs_volume(self, docker_compose_config: dict) -> None:
        """Main service should mount outputs directory."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        assert any("outputs" in str(v) for v in volumes)

    def test_main_service_has_logs_volume(self, docker_compose_config: dict) -> None:
        """Main service should mount logs directory."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        assert any("logs" in str(v) for v in volumes)

    def test_main_service_has_config_volume(self, docker_compose_config: dict) -> None:
        """Main service should mount config directory."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        assert any("config" in str(v) for v in volumes)

    def test_main_service_has_models_volume(self, docker_compose_config: dict) -> None:
        """Main service should mount models directory."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        assert any("models" in str(v) for v in volumes)

    def test_inputs_volume_is_read_only(self, docker_compose_config: dict) -> None:
        """Inputs volume should be read-only."""
        main_service = docker_compose_config["services"]["video2d3d"]
        volumes = main_service.get("volumes", [])
        inputs_volume = next((v for v in volumes if "inputs" in str(v)), None)
        assert inputs_volume is not None
        assert ":ro" in str(inputs_volume)

    def test_docker_compose_has_named_volumes(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have named volumes section."""
        assert "volumes" in docker_compose_config

    def test_docker_compose_has_models_named_volume(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have models named volume."""
        assert "volumes" in docker_compose_config
        assert "models_data" in docker_compose_config["volumes"]


class TestDockerComposeEnvironment:
    """Test docker-compose environment variables."""

    def test_main_service_has_env_vars(self, docker_compose_config: dict) -> None:
        """Main service should have environment variables."""
        main_service = docker_compose_config["services"]["video2d3d"]
        assert "environment" in main_service
        assert len(main_service["environment"]) > 0

    def test_main_service_has_video2d3d_env(self, docker_compose_config: dict) -> None:
        """Main service should have VIDEO2D3D_ENV variable."""
        main_service = docker_compose_config["services"]["video2d3d"]
        env_vars = main_service.get("environment", [])
        assert any("VIDEO2D3D_ENV" in str(e) for e in env_vars)

    def test_main_service_has_log_level(self, docker_compose_config: dict) -> None:
        """Main service should have LOG_LEVEL variable."""
        main_service = docker_compose_config["services"]["video2d3d"]
        env_vars = main_service.get("environment", [])
        assert any("LOG_LEVEL" in str(e) or "VIDEO2D3D_LOG_LEVEL" in str(e) for e in env_vars)

    def test_gpu_compose_has_cuda_device(self, docker_compose_config: dict) -> None:
        """GPU compose should have CUDA_VISIBLE_DEVICES."""
        main_service = docker_compose_config["services"]["video2d3d"]
        env_vars = main_service.get("environment", [])
        assert any("CUDA_VISIBLE_DEVICES" in str(e) for e in env_vars)

    def test_cpu_compose_has_no_gpu_flag(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should have VIDEO2D3D_NO_GPU flag."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        env_vars = main_service.get("environment", [])
        assert any("VIDEO2D3D_NO_GPU" in str(e) for e in env_vars)


class TestDockerComposeHealthCheck:
    """Test docker-compose health check configuration."""

    def test_main_service_has_healthcheck(self, docker_compose_config: dict) -> None:
        """Main service should have healthcheck configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        assert "healthcheck" in main_service

    def test_healthcheck_has_test(self, docker_compose_config: dict) -> None:
        """Healthcheck should have test command."""
        main_service = docker_compose_config["services"]["video2d3d"]
        healthcheck = main_service.get("healthcheck", {})
        assert "test" in healthcheck

    def test_healthcheck_uses_script(self, docker_compose_config: dict) -> None:
        """Healthcheck should use healthcheck.sh script."""
        main_service = docker_compose_config["services"]["video2d3d"]
        healthcheck = main_service.get("healthcheck", {})
        test_cmd = healthcheck.get("test", [])
        assert any("healthcheck.sh" in str(cmd) for cmd in test_cmd)

    def test_healthcheck_has_interval(self, docker_compose_config: dict) -> None:
        """Healthcheck should have interval configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        healthcheck = main_service.get("healthcheck", {})
        assert "interval" in healthcheck

    def test_healthcheck_has_timeout(self, docker_compose_config: dict) -> None:
        """Healthcheck should have timeout configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        healthcheck = main_service.get("healthcheck", {})
        assert "timeout" in healthcheck

    def test_healthcheck_has_retries(self, docker_compose_config: dict) -> None:
        """Healthcheck should have retries configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        healthcheck = main_service.get("healthcheck", {})
        assert "retries" in healthcheck


class TestDockerComposeGPUConfig:
    """Test docker-compose GPU configuration."""

    def test_gpu_compose_has_gpu_reservation(self, docker_compose_config: dict) -> None:
        """GPU compose should have GPU resource reservation."""
        main_service = docker_compose_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        reservations = deploy.get("resources", {}).get("reservations", {})
        devices = reservations.get("devices", [])
        assert len(devices) > 0

    def test_gpu_compose_uses_nvidia_driver(self, docker_compose_config: dict) -> None:
        """GPU compose should use nvidia driver."""
        main_service = docker_compose_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        reservations = deploy.get("resources", {}).get("reservations", {})
        devices = reservations.get("devices", [])
        assert any(d.get("driver") == "nvidia" for d in devices)

    def test_cpu_compose_no_gpu_reservation(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should not have GPU reservation."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        reservations = deploy.get("resources", {}).get("reservations", {})
        devices = reservations.get("devices", [])
        # Either no devices or no nvidia driver
        if devices:
            assert not any(d.get("driver") == "nvidia" for d in devices)


class TestDockerComposeResourceLimits:
    """Test docker-compose resource limits."""

    def test_cpu_compose_has_resource_limits(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should have resource limits configured."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        assert "resources" in deploy

    def test_cpu_compose_has_cpu_limit(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should have CPU limit."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        limits = deploy.get("resources", {}).get("limits", {})
        assert "cpus" in limits

    def test_cpu_compose_has_memory_limit(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should have memory limit."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        deploy = main_service.get("deploy", {})
        limits = deploy.get("resources", {}).get("limits", {})
        assert "memory" in limits


class TestDockerComposeNetworks:
    """Test docker-compose network configuration."""

    def test_docker_compose_has_networks(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have networks section."""
        assert "networks" in docker_compose_config

    def test_docker_compose_has_named_network(self, docker_compose_config: dict) -> None:
        """docker-compose.yml should have named network."""
        assert "default" in docker_compose_config["networks"]

    def test_docker_compose_cpu_has_networks(self, docker_compose_cpu_config: dict) -> None:
        """docker-compose.cpu.yml should have networks section."""
        assert "networks" in docker_compose_cpu_config


class TestDockerComposePorts:
    """Test docker-compose port configuration."""

    def test_main_service_exposes_port(self, docker_compose_config: dict) -> None:
        """Main service should expose port 8000."""
        main_service = docker_compose_config["services"]["video2d3d"]
        ports = main_service.get("ports", [])
        assert len(ports) > 0
        assert any("8000" in str(p) for p in ports)

    def test_api_service_exposes_port(self, docker_compose_config: dict) -> None:
        """API service should expose port 8000."""
        api_service = docker_compose_config["services"]["api"]
        ports = api_service.get("ports", [])
        assert len(ports) > 0
        assert any("8000" in str(p) for p in ports)


class TestDockerComposeBuildConfig:
    """Test docker-compose build configuration."""

    def test_main_service_specifies_dockerfile(self, docker_compose_config: dict) -> None:
        """Main service should specify Dockerfile."""
        main_service = docker_compose_config["services"]["video2d3d"]
        build = main_service.get("build", {})
        assert "dockerfile" in build

    def test_gpu_compose_uses_gpu_dockerfile(self, docker_compose_config: dict) -> None:
        """GPU compose should use GPU Dockerfile."""
        main_service = docker_compose_config["services"]["video2d3d"]
        build = main_service.get("build", {})
        assert build.get("dockerfile") == "Dockerfile"

    def test_cpu_compose_uses_cpu_dockerfile(self, docker_compose_cpu_config: dict) -> None:
        """CPU compose should use CPU Dockerfile."""
        main_service = docker_compose_cpu_config["services"]["video2d3d"]
        build = main_service.get("build", {})
        assert build.get("dockerfile") == "Dockerfile.cpu"

    def test_main_service_has_image_name(self, docker_compose_config: dict) -> None:
        """Main service should have image name."""
        main_service = docker_compose_config["services"]["video2d3d"]
        assert "image" in main_service
        assert "video2d3d" in main_service["image"]


class TestDockerComposeLogging:
    """Test docker-compose logging configuration."""

    def test_main_service_has_logging(self, docker_compose_config: dict) -> None:
        """Main service should have logging configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        assert "logging" in main_service

    def test_logging_uses_json_driver(self, docker_compose_config: dict) -> None:
        """Logging should use json-file driver."""
        main_service = docker_compose_config["services"]["video2d3d"]
        logging = main_service.get("logging", {})
        assert logging.get("driver") == "json-file"

    def test_logging_has_max_size(self, docker_compose_config: dict) -> None:
        """Logging should have max-size configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        logging = main_service.get("logging", {})
        options = logging.get("options", {})
        assert "max-size" in options

    def test_logging_has_max_file(self, docker_compose_config: dict) -> None:
        """Logging should have max-file configured."""
        main_service = docker_compose_config["services"]["video2d3d"]
        logging = main_service.get("logging", {})
        options = logging.get("options", {})
        assert "max-file" in options


class TestDockerComposeSecurity:
    """Test docker-compose security configuration."""

    def test_main_service_has_security_opt(self, docker_compose_config: dict) -> None:
        """Main service should have security options."""
        main_service = docker_compose_config["services"]["video2d3d"]
        assert "security_opt" in main_service

    def test_main_service_no_new_privileges(self, docker_compose_config: dict) -> None:
        """Main service should have no-new-privileges."""
        main_service = docker_compose_config["services"]["video2d3d"]
        security_opts = main_service.get("security_opt", [])
        assert any("no-new-privileges" in str(opt) for opt in security_opts)
