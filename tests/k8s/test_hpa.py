"""Tests for Kubernetes HorizontalPodAutoscaler configuration.

This module tests the hpa.yaml manifest for:
- Valid HPA structure
- Scaling metrics
- Scaling behavior
- Target reference
"""

from pathlib import Path

import pytest


class TestHpaExists:
    """Test HPA file existence."""

    def test_hpa_file_exists(self, hpa_path: Path) -> None:
        """hpa.yaml should exist."""
        assert hpa_path.exists(), "hpa.yaml not found"

    def test_hpa_is_valid_yaml(self, hpa_configs: list) -> None:
        """hpa.yaml should be valid YAML."""
        assert len(hpa_configs) > 0


class TestMainHpa:
    """Test the main HPA configuration."""

    @pytest.fixture
    def main_hpa(self, hpa_configs: list) -> dict:
        """Get the main HPA (the active one, not commented out)."""
        for hpa in hpa_configs:
            if hpa and hpa.get("kind") == "HorizontalPodAutoscaler":
                if hpa.get("metadata", {}).get("name") == "video2d3d-api-hpa":
                    return hpa
        return None

    def test_main_hpa_exists(self, main_hpa: dict) -> None:
        """Main HPA should exist."""
        assert main_hpa is not None

    def test_hpa_api_version(self, main_hpa: dict) -> None:
        """HPA should use autoscaling/v2 API."""
        assert main_hpa.get("apiVersion") == "autoscaling/v2"

    def test_hpa_has_namespace(self, main_hpa: dict) -> None:
        """HPA should have namespace."""
        assert main_hpa["metadata"].get("namespace") == "video2d3d"

    def test_hpa_targets_deployment(self, main_hpa: dict) -> None:
        """HPA should target the video2d3d-api deployment."""
        scale_target = main_hpa["spec"]["scaleTargetRef"]
        assert scale_target.get("kind") == "Deployment"
        assert scale_target.get("name") == "video2d3d-api"


class TestHpaReplicas:
    """Test HPA replica configuration."""

    @pytest.fixture
    def main_hpa(self, hpa_configs: list) -> dict:
        """Get the main HPA."""
        for hpa in hpa_configs:
            if hpa and hpa.get("kind") == "HorizontalPodAutoscaler":
                if hpa.get("metadata", {}).get("name") == "video2d3d-api-hpa":
                    return hpa
        return None

    def test_hpa_has_min_replicas(self, main_hpa: dict) -> None:
        """HPA should have minReplicas."""
        assert "minReplicas" in main_hpa["spec"]
        assert main_hpa["spec"]["minReplicas"] >= 1

    def test_hpa_has_max_replicas(self, main_hpa: dict) -> None:
        """HPA should have maxReplicas."""
        assert "maxReplicas" in main_hpa["spec"]
        assert main_hpa["spec"]["maxReplicas"] >= main_hpa["spec"]["minReplicas"]

    def test_hpa_max_greater_than_min(self, main_hpa: dict) -> None:
        """HPA maxReplicas should be greater than minReplicas."""
        min_replicas = main_hpa["spec"]["minReplicas"]
        max_replicas = main_hpa["spec"]["maxReplicas"]
        assert max_replicas > min_replicas


class TestHpaMetrics:
    """Test HPA metrics configuration."""

    @pytest.fixture
    def main_hpa(self, hpa_configs: list) -> dict:
        """Get the main HPA."""
        for hpa in hpa_configs:
            if hpa and hpa.get("kind") == "HorizontalPodAutoscaler":
                if hpa.get("metadata", {}).get("name") == "video2d3d-api-hpa":
                    return hpa
        return None

    def test_hpa_has_metrics(self, main_hpa: dict) -> None:
        """HPA should have metrics."""
        assert "metrics" in main_hpa["spec"]
        assert len(main_hpa["spec"]["metrics"]) >= 1

    def test_hpa_has_cpu_metric(self, main_hpa: dict) -> None:
        """HPA should have CPU metric."""
        metrics = main_hpa["spec"]["metrics"]
        cpu_metric = next((m for m in metrics if m.get("type") == "Resource"), None)
        assert cpu_metric is not None
        assert cpu_metric["resource"].get("name") == "cpu"

    def test_hpa_cpu_metric_uses_utilization(self, main_hpa: dict) -> None:
        """HPA CPU metric should use Utilization target."""
        metrics = main_hpa["spec"]["metrics"]
        cpu_metric = next((m for m in metrics if m.get("type") == "Resource"), None)
        target = cpu_metric["resource"].get("target", {})
        assert target.get("type") == "Utilization"
        assert "averageUtilization" in target

    def test_hpa_has_memory_metric(self, main_hpa: dict) -> None:
        """HPA should have memory metric."""
        metrics = main_hpa["spec"]["metrics"]
        memory_metrics = [
            m
            for m in metrics
            if m.get("type") == "Resource" and m["resource"].get("name") == "memory"
        ]
        assert len(memory_metrics) >= 1


class TestHpaBehavior:
    """Test HPA scaling behavior."""

    @pytest.fixture
    def main_hpa(self, hpa_configs: list) -> dict:
        """Get the main HPA."""
        for hpa in hpa_configs:
            if hpa and hpa.get("kind") == "HorizontalPodAutoscaler":
                if hpa.get("metadata", {}).get("name") == "video2d3d-api-hpa":
                    return hpa
        return None

    def test_hpa_has_behavior(self, main_hpa: dict) -> None:
        """HPA should have behavior configuration."""
        assert "behavior" in main_hpa["spec"]

    def test_hpa_has_scale_down_behavior(self, main_hpa: dict) -> None:
        """HPA should have scaleDown behavior."""
        behavior = main_hpa["spec"]["behavior"]
        assert "scaleDown" in behavior

    def test_hpa_has_scale_up_behavior(self, main_hpa: dict) -> None:
        """HPA should have scaleUp behavior."""
        behavior = main_hpa["spec"]["behavior"]
        assert "scaleUp" in behavior

    def test_hpa_has_stabilization_window(self, main_hpa: dict) -> None:
        """HPA should have stabilization window for scale down."""
        scale_down = main_hpa["spec"]["behavior"]["scaleDown"]
        assert "stabilizationWindowSeconds" in scale_down

    def test_hpa_scale_down_has_policies(self, main_hpa: dict) -> None:
        """HPA should have scale down policies."""
        scale_down = main_hpa["spec"]["behavior"]["scaleDown"]
        assert "policies" in scale_down
        assert len(scale_down["policies"]) >= 1


class TestPriorityClasses:
    """Test PriorityClass configuration."""

    @pytest.fixture
    def priority_classes(self, hpa_configs: list) -> list:
        """Get all PriorityClass resources."""
        return [h for h in hpa_configs if h and h.get("kind") == "PriorityClass"]

    def test_priority_classes_exist(self, priority_classes: list) -> None:
        """PriorityClasses should exist for GPU scheduling."""
        assert len(priority_classes) >= 1

    def test_has_high_priority_class(self, priority_classes: list) -> None:
        """Should have high priority class for GPU workloads."""
        high_priority = next(
            (
                p
                for p in priority_classes
                if "high" in p.get("metadata", {}).get("name", "").lower()
            ),
            None,
        )
        assert high_priority is not None

    def test_priority_class_has_value(self, priority_classes: list) -> None:
        """PriorityClass should have value."""
        for pc in priority_classes:
            assert "value" in pc
            assert isinstance(pc["value"], int)

    def test_priority_class_has_description(self, priority_classes: list) -> None:
        """PriorityClass should have description."""
        for pc in priority_classes:
            assert "description" in pc
            assert pc.get("globalDefault") is not None


class TestNoDuplicateHpaTargets:
    """Test that there are no duplicate HPA targets (CRITICAL)."""

    def test_only_one_active_hpa_per_deployment(self, hpa_configs: list) -> None:
        """Only one HPA should target each deployment (HPA conflict prevention)."""
        active_hpas = [h for h in hpa_configs if h and h.get("kind") == "HorizontalPodAutoscaler"]

        # Count HPAs targeting the same deployment
        targets = {}
        for hpa in active_hpas:
            target_name = hpa["spec"]["scaleTargetRef"].get("name")
            if target_name:
                if target_name not in targets:
                    targets[target_name] = []
                targets[target_name].append(hpa["metadata"]["name"])

        # Each deployment should only be targeted by ONE HPA
        for deployment_name, hpa_names in targets.items():
            assert len(hpa_names) <= 1, (
                f"Multiple HPAs target deployment '{deployment_name}': {hpa_names}. "
                "Only ONE HPA can target a deployment at a time!"
            )
