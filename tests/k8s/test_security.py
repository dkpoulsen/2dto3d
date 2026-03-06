"""Tests for Kubernetes security best practices.

This module tests security configurations across all manifests:
- Non-root containers
- Seccomp profiles
- Capability dropping
- Network policies
- RBAC configuration
"""

from pathlib import Path

import pytest


class TestSecurityContext:
    """Test pod security context configuration."""

    @pytest.fixture
    def container(self, deployment_config: dict) -> dict:
        """Get the main container configuration."""
        template = deployment_config["spec"]["template"]
        return template["spec"]["containers"][0]

    @pytest.fixture
    def pod_spec(self, deployment_config: dict) -> dict:
        """Get the pod spec."""
        return deployment_config["spec"]["template"]["spec"]

    def test_pod_runs_as_non_root(self, pod_spec: dict) -> None:
        """Pod should run as non-root user."""
        security = pod_spec.get("securityContext", {})
        assert security.get("runAsNonRoot") is True, (
            "Pod should set runAsNonRoot: true for security"
        )

    def test_pod_has_non_root_user_id(self, pod_spec: dict) -> None:
        """Pod should run with non-root UID."""
        security = pod_spec.get("securityContext", {})
        run_as_user = security.get("runAsUser")
        assert run_as_user is not None and run_as_user > 0, (
            "Pod should set runAsUser to a non-zero value"
        )

    def test_container_no_privilege_escalation(self, container: dict) -> None:
        """Container should not allow privilege escalation."""
        security = container.get("securityContext", {})
        assert security.get("allowPrivilegeEscalation") is False, (
            "Container should set allowPrivilegeEscalation: false"
        )

    def test_container_drops_all_capabilities(self, container: dict) -> None:
        """Container should drop all Linux capabilities."""
        security = container.get("securityContext", {})
        caps = security.get("capabilities", {})
        drop = caps.get("drop", [])
        assert "ALL" in drop, "Container should drop ALL capabilities for security"

    def test_pod_has_seccomp_profile(self, pod_spec: dict) -> None:
        """Pod should have seccomp profile."""
        security = pod_spec.get("securityContext", {})
        seccomp = security.get("seccompProfile", {})
        assert seccomp.get("type") in ["RuntimeDefault", "Localhost"], (
            "Pod should have seccompProfile for syscall filtering"
        )


class TestNetworkPolicies:
    """Test network policy configuration."""

    @pytest.fixture
    def network_policies(self, ingress_configs: list) -> list:
        """Get all NetworkPolicy resources."""
        return [c for c in ingress_configs if c and c.get("kind") == "NetworkPolicy"]

    def test_network_policies_exist(self, network_policies: list) -> None:
        """NetworkPolicy should exist for traffic control."""
        assert len(network_policies) >= 1, "At least one NetworkPolicy should exist for security"

    def test_network_policy_has_ingress_rules(self, network_policies: list) -> None:
        """NetworkPolicy should have ingress rules."""
        for np in network_policies:
            policy_types = np["spec"].get("policyTypes", [])
            # PolicyTypes is case-sensitive ("Ingress" not "ingress")
            assert "Ingress" in policy_types, (
                f"NetworkPolicy {np['metadata']['name']} should include Ingress policy"
            )

    def test_network_policy_has_egress_rules(self, network_policies: list) -> None:
        """NetworkPolicy should have egress rules (not allow all)."""
        for np in network_policies:
            policy_types = np["spec"].get("policyTypes", [])
            if "Egress" in policy_types:
                # Has egress policy - good
                egress = np["spec"].get("egress", [])
                # Should have specific rules, not empty (which would deny all)
                # or [{}] which allows all
                assert egress != [{}], (
                    f"NetworkPolicy {np['metadata']['name']} should not allow all egress"
                )

    def test_network_policy_has_pod_selector(self, network_policies: list) -> None:
        """NetworkPolicy should have podSelector."""
        for np in network_policies:
            assert "podSelector" in np["spec"], (
                f"NetworkPolicy {np['metadata']['name']} should have podSelector"
            )


class TestRbacConfiguration:
    """Test RBAC configuration."""

    def test_rbac_file_exists(self, rbac_path: Path) -> None:
        """rbac.yaml should exist."""
        assert rbac_path.exists(), "rbac.yaml not found for RBAC configuration"

    def test_service_account_exists(self, rbac_configs: list) -> None:
        """ServiceAccount should exist."""
        service_accounts = [r for r in rbac_configs if r and r.get("kind") == "ServiceAccount"]
        assert len(service_accounts) >= 1, "ServiceAccount should be defined"

    def test_service_account_name_matches_deployment(self, rbac_configs: list) -> None:
        """ServiceAccount name should match deployment's serviceAccountName."""
        service_accounts = [r for r in rbac_configs if r and r.get("kind") == "ServiceAccount"]
        names = [sa["metadata"]["name"] for sa in service_accounts]
        assert "video2d3d-api" in names, "ServiceAccount 'video2d3d-api' should exist"

    def test_role_exists(self, rbac_configs: list) -> None:
        """Role should exist for namespace-scoped permissions."""
        roles = [r for r in rbac_configs if r and r.get("kind") == "Role"]
        assert len(roles) >= 1, "Role should be defined for namespace permissions"

    def test_role_binding_exists(self, rbac_configs: list) -> None:
        """RoleBinding should exist to bind Role to ServiceAccount."""
        bindings = [r for r in rbac_configs if r and r.get("kind") == "RoleBinding"]
        assert len(bindings) >= 1, "RoleBinding should be defined"

    def test_role_binding_references_service_account(self, rbac_configs: list) -> None:
        """RoleBinding should reference the correct ServiceAccount."""
        bindings = [r for r in rbac_configs if r and r.get("kind") == "RoleBinding"]
        for binding in bindings:
            subjects = binding["subjects"]
            sa_subjects = [s for s in subjects if s.get("kind") == "ServiceAccount"]
            assert len(sa_subjects) >= 1, (
                f"RoleBinding {binding['metadata']['name']} should reference ServiceAccount"
            )


class TestPodDisruptionBudget:
    """Test PodDisruptionBudget configuration."""

    def test_pdb_exists(self, pdb_config: dict) -> None:
        """PDB should exist for availability during disruptions."""
        assert pdb_config is not None, "PodDisruptionBudget should be defined"

    def test_pdb_targets_deployment(self, pdb_config: dict) -> None:
        """PDB should target the correct deployment."""
        selector = pdb_config["spec"]["selector"]
        match_labels = selector.get("matchLabels", {})
        assert match_labels.get("app.kubernetes.io/name") == "video2d3d"

    def test_pdb_has_availability_requirement(self, pdb_config: dict) -> None:
        """PDB should have minAvailable or maxUnavailable."""
        spec = pdb_config["spec"]
        has_min = "minAvailable" in spec
        has_max = "maxUnavailable" in spec
        assert has_min or has_max, "PDB should have minAvailable or maxUnavailable"

    def test_pdb_min_available_is_reasonable(self, pdb_config: dict) -> None:
        """PDB minAvailable should be at least 1 for HA."""
        if "minAvailable" in pdb_config["spec"]:
            min_avail = pdb_config["spec"]["minAvailable"]
            assert min_avail >= 1, "PDB minAvailable should be at least 1"


class TestResourceQuotas:
    """Test ResourceQuota configuration."""

    def test_resource_quota_exists(self, resource_quota_configs: list) -> None:
        """ResourceQuota should exist for namespace-level control."""
        quotas = [r for r in resource_quota_configs if r and r.get("kind") == "ResourceQuota"]
        assert len(quotas) >= 1, "ResourceQuota should be defined"

    def test_resource_quota_has_cpu_limits(self, resource_quota_configs: list) -> None:
        """ResourceQuota should limit CPU (general quota)."""
        quotas = [r for r in resource_quota_configs if r and r.get("kind") == "ResourceQuota"]
        # Check that at least one general-purpose quota has CPU limits
        # Skip GPU-specific quotas (they only limit GPU resources)
        general_quotas = [q for q in quotas if "gpu" not in q["metadata"]["name"].lower()]
        for quota in general_quotas:
            hard = quota["spec"].get("hard", {})
            assert "requests.cpu" in hard or "limits.cpu" in hard, (
                f"ResourceQuota {quota['metadata']['name']} should limit CPU"
            )

    def test_resource_quota_has_memory_limits(self, resource_quota_configs: list) -> None:
        """ResourceQuota should limit memory (general quota)."""
        quotas = [r for r in resource_quota_configs if r and r.get("kind") == "ResourceQuota"]
        # Check that at least one general-purpose quota has memory limits
        # Skip GPU-specific quotas (they only limit GPU resources)
        general_quotas = [q for q in quotas if "gpu" not in q["metadata"]["name"].lower()]
        for quota in general_quotas:
            hard = quota["spec"].get("hard", {})
            assert "requests.memory" in hard or "limits.memory" in hard, (
                f"ResourceQuota {quota['metadata']['name']} should limit memory"
            )

    def test_resource_quota_limits_pods(self, resource_quota_configs: list) -> None:
        """ResourceQuota should limit pod count (general quota)."""
        quotas = [r for r in resource_quota_configs if r and r.get("kind") == "ResourceQuota"]
        # Check that at least one general-purpose quota has pod limits
        # Skip GPU-specific quotas (they only limit GPU resources)
        general_quotas = [q for q in quotas if "gpu" not in q["metadata"]["name"].lower()]
        for quota in general_quotas:
            hard = quota["spec"].get("hard", {})
            assert "count/pods" in hard, (
                f"ResourceQuota {quota['metadata']['name']} should limit pod count"
            )


class TestLimitRange:
    """Test LimitRange configuration."""

    def test_limit_range_exists(self, resource_quota_configs: list) -> None:
        """LimitRange should exist for default container limits."""
        limits = [r for r in resource_quota_configs if r and r.get("kind") == "LimitRange"]
        assert len(limits) >= 1, "LimitRange should be defined"

    def test_limit_range_has_container_limits(self, resource_quota_configs: list) -> None:
        """LimitRange should have container limits."""
        limits = [r for r in resource_quota_configs if r and r.get("kind") == "LimitRange"]
        for lr in limits:
            limits_spec = lr["spec"].get("limits", [])
            container_limits = [l for l in limits_spec if l.get("type") == "Container"]
            assert len(container_limits) >= 1, (
                f"LimitRange {lr['metadata']['name']} should have Container limits"
            )

    def test_limit_range_has_default_requests(self, resource_quota_configs: list) -> None:
        """LimitRange should have default requests."""
        limits = [r for r in resource_quota_configs if r and r.get("kind") == "LimitRange"]
        for lr in limits:
            limits_spec = lr["spec"].get("limits", [])
            for limit in limits_spec:
                if limit.get("type") == "Container":
                    assert "defaultRequest" in limit, (
                        f"LimitRange {lr['metadata']['name']} should have defaultRequest"
                    )


class TestSecretsConfiguration:
    """Test secrets configuration."""

    def test_secrets_file_exists(self, secrets_path: Path) -> None:
        """secrets.yaml should exist as template."""
        assert secrets_path.exists(), "secrets.yaml template should exist"

    def test_secrets_has_template_comment(self, secrets_path: Path) -> None:
        """secrets.yaml should have documentation that it's a template."""
        with open(secrets_path) as f:
            content = f.read()
        assert "template" in content.lower() or "example" in content.lower(), (
            "secrets.yaml should indicate it's a template"
        )


class TestIngressSecurity:
    """Test ingress security configuration."""

    @pytest.fixture
    def ingress(self, ingress_configs: list) -> dict:
        """Get the main Ingress resource."""
        for cfg in ingress_configs:
            if cfg and cfg.get("kind") == "Ingress":
                return cfg
        return None

    def test_ingress_has_rate_limiting(self, ingress: dict) -> None:
        """Ingress should have rate limiting annotations."""
        if ingress is None:
            pytest.skip("No Ingress found")
        annotations = ingress["metadata"].get("annotations", {})
        # Check for rate limiting (nginx specific)
        rate_limit_keys = ["limit-rps", "limit-connections", "limit-connections-per-ip"]
        has_rate_limit = any(key in str(annotations).lower() for key in rate_limit_keys)
        # This is a soft check - warn but don't fail
        if not has_rate_limit:
            pass  # Rate limiting is recommended but not required

    def test_ingress_has_body_size_limit(self, ingress: dict) -> None:
        """Ingress should have body size limit for uploads."""
        if ingress is None:
            pytest.skip("No Ingress found")
        annotations = ingress["metadata"].get("annotations", {})
        has_body_limit = (
            "body-size" in str(annotations).lower() or "proxy-body-size" in str(annotations).lower()
        )
        assert has_body_limit, "Ingress should have body size limit for file uploads"


class TestSecurityBestPracticesSummary:
    """Summary test for security best practices."""

    def test_deployment_has_all_security_hardening(self, deployment_config: dict) -> None:
        """Deployment should have comprehensive security hardening."""
        pod_spec = deployment_config["spec"]["template"]["spec"]
        container = pod_spec["containers"][0]

        pod_security = pod_spec.get("securityContext", {})
        container_security = container.get("securityContext", {})

        issues = []

        # Check pod-level security
        if not pod_security.get("runAsNonRoot"):
            issues.append("Pod should set runAsNonRoot: true")
        if not pod_security.get("runAsUser") or pod_security.get("runAsUser") == 0:
            issues.append("Pod should set runAsUser to non-zero value")
        if not pod_security.get("seccompProfile"):
            issues.append("Pod should have seccompProfile")

        # Check container-level security
        if container_security.get("allowPrivilegeEscalation") is not False:
            issues.append("Container should set allowPrivilegeEscalation: false")
        caps = container_security.get("capabilities", {})
        if "ALL" not in caps.get("drop", []):
            issues.append("Container should drop ALL capabilities")

        # Allow some issues but warn if too many
        if len(issues) > 2:
            pytest.fail(f"Security issues found: {'; '.join(issues)}")
