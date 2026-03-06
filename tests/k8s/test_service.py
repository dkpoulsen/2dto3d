"""Tests for Kubernetes Service configuration.

This module tests the service.yaml manifest for:
- Valid service structure
- Port configuration
- Service types
- Selector configuration
"""

from pathlib import Path

import pytest


class TestServiceExists:
    """Test service file existence."""

    def test_service_file_exists(self, service_path: Path) -> None:
        """service.yaml should exist."""
        assert service_path.exists(), "service.yaml not found"

    def test_service_is_valid_yaml(self, service_configs: list) -> None:
        """service.yaml should be valid YAML."""
        assert len(service_configs) > 0


class TestMainService:
    """Test the main ClusterIP service."""

    @pytest.fixture
    def main_service(self, service_configs: list) -> dict:
        """Get the main ClusterIP service."""
        for svc in service_configs:
            if svc and svc.get("metadata", {}).get("name") == "video2d3d-api":
                if svc.get("spec", {}).get("type") == "ClusterIP":
                    if svc.get("spec", {}).get("clusterIP") != "None":
                        return svc
        return None

    def test_main_service_exists(self, main_service: dict) -> None:
        """Main ClusterIP service should exist."""
        assert main_service is not None

    def test_main_service_api_version(self, main_service: dict) -> None:
        """Main service should use v1 API."""
        assert main_service.get("apiVersion") == "v1"

    def test_main_service_kind(self, main_service: dict) -> None:
        """Main service should be Service kind."""
        assert main_service.get("kind") == "Service"

    def test_main_service_has_namespace(self, main_service: dict) -> None:
        """Main service should have namespace."""
        assert main_service["metadata"].get("namespace") == "video2d3d"

    def test_main_service_type(self, main_service: dict) -> None:
        """Main service should be ClusterIP type."""
        assert main_service["spec"].get("type") == "ClusterIP"

    def test_main_service_has_selector(self, main_service: dict) -> None:
        """Main service should have selector."""
        assert "selector" in main_service["spec"]

    def test_main_service_selector_matches_deployment(self, main_service: dict) -> None:
        """Service selector should match deployment labels."""
        selector = main_service["spec"]["selector"]
        assert selector.get("app.kubernetes.io/name") == "video2d3d"
        assert selector.get("app.kubernetes.io/component") == "api"

    def test_main_service_has_ports(self, main_service: dict) -> None:
        """Main service should have ports."""
        assert "ports" in main_service["spec"]
        assert len(main_service["spec"]["ports"]) >= 1

    def test_main_service_http_port(self, main_service: dict) -> None:
        """Main service should have HTTP port."""
        ports = main_service["spec"]["ports"]
        http_port = next((p for p in ports if p.get("name") == "http"), None)
        assert http_port is not None
        assert http_port.get("port") == 80
        assert http_port.get("targetPort") == "http"


class TestHeadlessService:
    """Test the headless service for direct pod access."""

    @pytest.fixture
    def headless_service(self, service_configs: list) -> dict:
        """Get the headless service."""
        for svc in service_configs:
            if svc and svc.get("spec", {}).get("clusterIP") == "None":
                return svc
        return None

    def test_headless_service_exists(self, headless_service: dict) -> None:
        """Headless service should exist."""
        assert headless_service is not None

    def test_headless_service_has_none_cluster_ip(self, headless_service: dict) -> None:
        """Headless service should have clusterIP: None."""
        assert headless_service["spec"].get("clusterIP") == "None"

    def test_headless_service_has_selector(self, headless_service: dict) -> None:
        """Headless service should have selector."""
        assert "selector" in headless_service["spec"]


class TestServiceAnnotations:
    """Test service annotations."""

    @pytest.fixture
    def main_service(self, service_configs: list) -> dict:
        """Get the main ClusterIP service."""
        for svc in service_configs:
            if svc and svc.get("metadata", {}).get("name") == "video2d3d-api":
                if svc.get("spec", {}).get("type") == "ClusterIP":
                    if svc.get("spec", {}).get("clusterIP") != "None":
                        return svc
        return None

    def test_main_service_has_prometheus_annotations(self, main_service: dict) -> None:
        """Main service should have Prometheus scrape annotations."""
        annotations = main_service["metadata"].get("annotations", {})
        assert annotations.get("prometheus.io/scrape") == "true"
        assert "prometheus.io/port" in annotations


class TestServiceLabels:
    """Test service labels."""

    @pytest.fixture
    def main_service(self, service_configs: list) -> dict:
        """Get the main ClusterIP service."""
        for svc in service_configs:
            if svc and svc.get("metadata", {}).get("name") == "video2d3d-api":
                if svc.get("spec", {}).get("type") == "ClusterIP":
                    if svc.get("spec", {}).get("clusterIP") != "None":
                        return svc
        return None

    def test_main_service_has_app_label(self, main_service: dict) -> None:
        """Main service should have app.kubernetes.io/name label."""
        labels = main_service["metadata"].get("labels", {})
        assert labels.get("app.kubernetes.io/name") == "video2d3d"

    def test_main_service_has_component_label(self, main_service: dict) -> None:
        """Main service should have app.kubernetes.io/component label."""
        labels = main_service["metadata"].get("labels", {})
        assert "app.kubernetes.io/component" in labels
