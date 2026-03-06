"""Tests for Kubernetes Deployment configuration.

This module tests the deployment.yaml manifest for:
- Valid deployment structure
- Resource requests and limits
- GPU scheduling configuration
- Health checks
- Security context
- Volume mounts
- Environment configuration
"""

from pathlib import Path

import pytest


class TestDeploymentExists:
    """Test deployment file existence."""

    def test_deployment_file_exists(self, deployment_path: Path) -> None:
        """deployment.yaml should exist."""
        assert deployment_path.exists(), "deployment.yaml not found"

    def test_deployment_is_valid_yaml(self, deployment_config: dict) -> None:
        """deployment.yaml should be valid YAML."""
        assert deployment_config is not None


class TestDeploymentBasicStructure:
    """Test deployment basic structure."""

    def test_deployment_has_api_version(self, deployment_config: dict) -> None:
        """Deployment should have apiVersion."""
        assert deployment_config.get("apiVersion") == "apps/v1"

    def test_deployment_has_kind(self, deployment_config: dict) -> None:
        """Deployment should have kind Deployment."""
        assert deployment_config.get("kind") == "Deployment"

    def test_deployment_has_metadata(self, deployment_config: dict) -> None:
        """Deployment should have metadata."""
        assert "metadata" in deployment_config

    def test_deployment_has_name(self, deployment_config: dict) -> None:
        """Deployment should have metadata.name."""
        assert deployment_config["metadata"].get("name") == "video2d3d-api"

    def test_deployment_has_namespace(self, deployment_config: dict) -> None:
        """Deployment should have metadata.namespace."""
        assert deployment_config["metadata"].get("namespace") == "video2d3d"

    def test_deployment_has_spec(self, deployment_config: dict) -> None:
        """Deployment should have spec."""
        assert "spec" in deployment_config

    def test_deployment_has_replicas(self, deployment_config: dict) -> None:
        """Deployment should have spec.replicas."""
        assert "replicas" in deployment_config["spec"]
        assert deployment_config["spec"]["replicas"] >= 1

    def test_deployment_has_selector(self, deployment_config: dict) -> None:
        """Deployment should have spec.selector."""
        assert "selector" in deployment_config["spec"]
        assert "matchLabels" in deployment_config["spec"]["selector"]

    def test_deployment_has_template(self, deployment_config: dict) -> None:
        """Deployment should have spec.template."""
        assert "template" in deployment_config["spec"]

    def test_deployment_template_has_metadata(self, deployment_config: dict) -> None:
        """Deployment template should have metadata."""
        template = deployment_config["spec"]["template"]
        assert "metadata" in template
        assert "labels" in template["metadata"]


class TestDeploymentStrategy:
    """Test deployment strategy configuration."""

    def test_deployment_has_strategy(self, deployment_config: dict) -> None:
        """Deployment should have strategy."""
        assert "strategy" in deployment_config["spec"]

    def test_deployment_uses_rolling_update(self, deployment_config: dict) -> None:
        """Deployment should use RollingUpdate strategy."""
        strategy = deployment_config["spec"]["strategy"]
        assert strategy.get("type") == "RollingUpdate"

    def test_deployment_has_max_surge(self, deployment_config: dict) -> None:
        """Deployment should have maxSurge configured."""
        strategy = deployment_config["spec"]["strategy"]
        assert "rollingUpdate" in strategy
        assert "maxSurge" in strategy["rollingUpdate"]

    def test_deployment_has_max_unavailable(self, deployment_config: dict) -> None:
        """Deployment should have maxUnavailable configured."""
        strategy = deployment_config["spec"]["strategy"]
        assert "maxUnavailable" in strategy["rollingUpdate"]

    def test_deployment_zero_downtime(self, deployment_config: dict) -> None:
        """Deployment should have maxUnavailable=0 for zero-downtime."""
        strategy = deployment_config["spec"]["strategy"]
        max_unavailable = strategy["rollingUpdate"]["maxUnavailable"]
        assert max_unavailable == 0, "maxUnavailable should be 0 for zero-downtime deployments"


class TestDeploymentContainer:
    """Test deployment container configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        containers = template["spec"]["containers"]
        return containers[0]

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_deployment_has_containers(self, deployment_config: dict) -> None:
        """Deployment should have containers."""
        template = deployment_config["spec"]["template"]
        assert "containers" in template["spec"]
        assert len(template["spec"]["containers"]) >= 1

    def test_container_has_name(self, container: dict) -> None:
        """Container should have name."""
        assert "name" in container

    def test_container_has_image(self, container: dict) -> None:
        """Container should have image."""
        assert "image" in container

    def test_container_has_image_pull_policy(self, container: dict) -> None:
        """Container should have imagePullPolicy."""
        assert "imagePullPolicy" in container

    def test_container_has_ports(self, container: dict) -> None:
        """Container should have ports."""
        assert "ports" in container
        assert len(container["ports"]) >= 1

    def test_container_exposes_http_port(self, container: dict) -> None:
        """Container should expose port 8000 for HTTP."""
        ports = container["ports"]
        http_port = next((p for p in ports if p.get("name") == "http"), None)
        assert http_port is not None
        assert http_port.get("containerPort") == 8000


class TestDeploymentResources:
    """Test deployment resource configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    def test_container_has_resources(self, container: dict) -> None:
        """Container should have resources."""
        assert "resources" in container

    def test_container_has_cpu_request(self, container: dict) -> None:
        """Container should have CPU request."""
        resources = container["resources"]
        assert "requests" in resources
        assert "cpu" in resources["requests"]

    def test_container_has_memory_request(self, container: dict) -> None:
        """Container should have memory request."""
        resources = container["resources"]
        assert "memory" in resources["requests"]

    def test_container_has_cpu_limit(self, container: dict) -> None:
        """Container should have CPU limit."""
        resources = container["resources"]
        assert "limits" in resources
        assert "cpu" in resources["limits"]

    def test_container_has_memory_limit(self, container: dict) -> None:
        """Container should have memory limit."""
        resources = container["resources"]
        assert "memory" in resources["limits"]

    def test_gpu_resource_request(self, container: dict) -> None:
        """Container should request GPU resources."""
        resources = container["resources"]
        assert "requests" in resources
        assert "nvidia.com/gpu" in resources["requests"]
        assert resources["requests"]["nvidia.com/gpu"] == 1

    def test_gpu_resource_limit(self, container: dict) -> None:
        """Container should have GPU resource limit."""
        resources = container["resources"]
        assert "limits" in resources
        assert "nvidia.com/gpu" in resources["limits"]
        assert resources["limits"]["nvidia.com/gpu"] == 1


class TestDeploymentHealthChecks:
    """Test deployment health check configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    def test_container_has_liveness_probe(self, container: dict) -> None:
        """Container should have livenessProbe."""
        assert "livenessProbe" in container

    def test_container_has_readiness_probe(self, container: dict) -> None:
        """Container should have readinessProbe."""
        assert "readinessProbe" in container

    def test_container_has_startup_probe(self, container: dict) -> None:
        """Container should have startupProbe for slow startup."""
        assert "startupProbe" in container

    def test_liveness_probe_uses_http(self, container: dict) -> None:
        """Liveness probe should use HTTP."""
        probe = container["livenessProbe"]
        assert "httpGet" in probe
        assert probe["httpGet"].get("path") == "/health"

    def test_readiness_probe_uses_http(self, container: dict) -> None:
        """Readiness probe should use HTTP."""
        probe = container["readinessProbe"]
        assert "httpGet" in probe
        assert probe["httpGet"].get("path") == "/health"

    def test_liveness_probe_has_initial_delay(self, container: dict) -> None:
        """Liveness probe should have initialDelaySeconds."""
        probe = container["livenessProbe"]
        assert "initialDelaySeconds" in probe
        # Allow enough time for model loading
        assert probe["initialDelaySeconds"] >= 60

    def test_readiness_probe_has_initial_delay(self, container: dict) -> None:
        """Readiness probe should have initialDelaySeconds."""
        probe = container["readinessProbe"]
        assert "initialDelaySeconds" in probe
        assert probe["initialDelaySeconds"] >= 30

    def test_liveness_probe_has_timeout(self, container: dict) -> None:
        """Liveness probe should have timeoutSeconds."""
        probe = container["livenessProbe"]
        assert "timeoutSeconds" in probe

    def test_readiness_probe_has_timeout(self, container: dict) -> None:
        """Readiness probe should have timeoutSeconds."""
        probe = container["readinessProbe"]
        assert "timeoutSeconds" in probe


class TestDeploymentSecurityContext:
    """Test deployment security context configuration."""

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_pod_has_security_context(self, pod_spec: dict) -> None:
        """Pod should have securityContext."""
        assert "securityContext" in pod_spec

    def test_pod_runs_as_non_root(self, pod_spec: dict) -> None:
        """Pod should run as non-root user."""
        security = pod_spec["securityContext"]
        assert security.get("runAsNonRoot") is True

    def test_pod_has_run_as_user(self, pod_spec: dict) -> None:
        """Pod should specify runAsUser."""
        security = pod_spec["securityContext"]
        assert "runAsUser" in security
        assert security["runAsUser"] > 0  # Non-root user

    def test_pod_has_run_as_group(self, pod_spec: dict) -> None:
        """Pod should specify runAsGroup."""
        security = pod_spec["securityContext"]
        assert "runAsGroup" in security

    def test_pod_has_fs_group(self, pod_spec: dict) -> None:
        """Pod should specify fsGroup."""
        security = pod_spec["securityContext"]
        assert "fsGroup" in security

    def test_pod_has_seccomp_profile(self, pod_spec: dict) -> None:
        """Pod should have seccompProfile for security."""
        security = pod_spec["securityContext"]
        assert "seccompProfile" in security
        assert security["seccompProfile"].get("type") in ["RuntimeDefault", "Localhost"]


class TestDeploymentContainerSecurity:
    """Test deployment container security configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    def test_container_has_security_context(self, container: dict) -> None:
        """Container should have securityContext."""
        assert "securityContext" in container

    def test_container_no_privilege_escalation(self, container: dict) -> None:
        """Container should not allow privilege escalation."""
        security = container["securityContext"]
        assert security.get("allowPrivilegeEscalation") is False

    def test_container_drops_capabilities(self, container: dict) -> None:
        """Container should drop all capabilities."""
        security = container["securityContext"]
        assert "capabilities" in security
        assert "drop" in security["capabilities"]
        assert "ALL" in security["capabilities"]["drop"]


class TestDeploymentVolumes:
    """Test deployment volume configuration."""

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    def test_pod_has_volumes(self, pod_spec: dict) -> None:
        """Pod should have volumes defined."""
        assert "volumes" in pod_spec
        assert len(pod_spec["volumes"]) >= 1

    def test_container_has_volume_mounts(self, container: dict) -> None:
        """Container should have volumeMounts."""
        assert "volumeMounts" in container
        assert len(container["volumeMounts"]) >= 1

    def test_has_models_volume(self, pod_spec: dict) -> None:
        """Pod should have models volume."""
        volumes = pod_spec["volumes"]
        models_volume = next((v for v in volumes if v.get("name") == "models-storage"), None)
        assert models_volume is not None

    def test_has_inputs_volume(self, pod_spec: dict) -> None:
        """Pod should have inputs volume."""
        volumes = pod_spec["volumes"]
        inputs_volume = next((v for v in volumes if v.get("name") == "inputs-storage"), None)
        assert inputs_volume is not None

    def test_has_outputs_volume(self, pod_spec: dict) -> None:
        """Pod should have outputs volume."""
        volumes = pod_spec["volumes"]
        outputs_volume = next((v for v in volumes if v.get("name") == "outputs-storage"), None)
        assert outputs_volume is not None

    def test_has_tmp_volume(self, pod_spec: dict) -> None:
        """Pod should have tmp volume for temporary files."""
        volumes = pod_spec["volumes"]
        tmp_volume = next((v for v in volumes if v.get("name") == "tmp-storage"), None)
        assert tmp_volume is not None


class TestDeploymentGPUScheduling:
    """Test deployment GPU scheduling configuration."""

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_has_node_affinity(self, pod_spec: dict) -> None:
        """Pod should have nodeAffinity for GPU nodes."""
        assert "affinity" in pod_spec
        assert "nodeAffinity" in pod_spec["affinity"]

    def test_node_affinity_requires_gpu(self, pod_spec: dict) -> None:
        """Node affinity should require GPU nodes."""
        node_affinity = pod_spec["affinity"]["nodeAffinity"]
        assert "requiredDuringSchedulingIgnoredDuringExecution" in node_affinity

    def test_has_tolerations(self, pod_spec: dict) -> None:
        """Pod should have tolerations for GPU nodes."""
        assert "tolerations" in pod_spec

    def test_tolerates_gpu_taint(self, pod_spec: dict) -> None:
        """Pod should tolerate nvidia.com/gpu taint."""
        tolerations = pod_spec["tolerations"]
        gpu_toleration = next(
            (t for t in tolerations if "nvidia.com/gpu" in str(t.get("key", ""))), None
        )
        assert gpu_toleration is not None


class TestDeploymentHighAvailability:
    """Test deployment high availability configuration."""

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_has_pod_anti_affinity(self, pod_spec: dict) -> None:
        """Pod should have podAntiAffinity for HA."""
        assert "affinity" in pod_spec
        assert "podAntiAffinity" in pod_spec["affinity"]

    def test_has_topology_spread_constraints(self, pod_spec: dict) -> None:
        """Pod should have topologySpreadConstraints for even distribution."""
        assert "topologySpreadConstraints" in pod_spec

    def test_topology_spread_uses_hostname(self, pod_spec: dict) -> None:
        """Topology spread should use hostname for pod distribution."""
        constraints = pod_spec["topologySpreadConstraints"]
        hostname_constraint = next(
            (c for c in constraints if c.get("topologyKey") == "kubernetes.io/hostname"), None
        )
        assert hostname_constraint is not None

    def test_has_termination_grace_period(self, pod_spec: dict) -> None:
        """Pod should have terminationGracePeriodSeconds for graceful shutdown."""
        assert "terminationGracePeriodSeconds" in pod_spec
        assert pod_spec["terminationGracePeriodSeconds"] >= 30


class TestDeploymentEnvironment:
    """Test deployment environment configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    def test_container_has_env_from(self, container: dict) -> None:
        """Container should have envFrom for configmap/secrets."""
        assert "envFrom" in container

    def test_container_mounts_configmap(self, container: dict) -> None:
        """Container should mount video2d3d-config ConfigMap."""
        env_from = container["envFrom"]
        configmap_ref = next((e for e in env_from if "configMapRef" in e), None)
        assert configmap_ref is not None
        assert configmap_ref["configMapRef"].get("name") == "video2d3d-config"


class TestDeploymentServiceAccount:
    """Test deployment service account configuration."""

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_has_service_account_name(self, pod_spec: dict) -> None:
        """Pod should have serviceAccountName."""
        assert "serviceAccountName" in pod_spec

    def test_does_not_automount_service_account_token(self, pod_spec: dict) -> None:
        """Pod should not auto-mount service account token."""
        assert pod_spec.get("automountServiceAccountToken") is False
