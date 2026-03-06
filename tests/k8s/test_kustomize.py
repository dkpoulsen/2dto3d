"""Tests for Kustomize configuration.

This module tests kustomization files for:
- Valid kustomization structure
- Resource references
- Overlay configuration
"""

from pathlib import Path

import pytest


class TestBaseKustomization:
    """Test base kustomization.yaml."""

    def test_kustomization_exists(self, kustomization_path: Path) -> None:
        """kustomization.yaml should exist in base."""
        assert kustomization_path.exists(), "k8s/base/kustomization.yaml not found"

    def test_kustomization_is_valid_yaml(self, kustomization_config: dict) -> None:
        """kustomization.yaml should be valid YAML."""
        assert kustomization_config is not None

    def test_kustomization_has_api_version(self, kustomization_config: dict) -> None:
        """kustomization.yaml should have apiVersion."""
        assert "apiVersion" in kustomization_config
        assert "kustomize.config.k8s.io" in kustomization_config["apiVersion"]

    def test_kustomization_has_kind(self, kustomization_config: dict) -> None:
        """kustomization.yaml should have kind Kustomization."""
        assert kustomization_config.get("kind") == "Kustomization"

    def test_kustomization_has_namespace(self, kustomization_config: dict) -> None:
        """kustomization.yaml should define namespace."""
        assert "namespace" in kustomization_config
        assert kustomization_config["namespace"] == "video2d3d"

    def test_kustomization_has_resources(self, kustomization_config: dict) -> None:
        """kustomization.yaml should list resources."""
        assert "resources" in kustomization_config
        assert len(kustomization_config["resources"]) >= 1

    def test_kustomization_references_namespace(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference namespace.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "namespace.yaml" in resources

    def test_kustomization_references_deployment(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference deployment.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "deployment.yaml" in resources

    def test_kustomization_references_service(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference service.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "service.yaml" in resources

    def test_kustomization_references_configmap(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference configmap.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "configmap.yaml" in resources

    def test_kustomization_references_hpa(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference hpa.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "hpa.yaml" in resources

    def test_kustomization_references_pvc(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference pvc.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "pvc.yaml" in resources

    def test_kustomization_references_rbac(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference rbac.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "rbac.yaml" in resources

    def test_kustomization_references_ingress(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference ingress.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "ingress.yaml" in resources

    def test_kustomization_references_pdb(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference pdb.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "pdb.yaml" in resources

    def test_kustomization_references_resource_quota(self, kustomization_config: dict) -> None:
        """kustomization.yaml should reference resource-quota.yaml."""
        resources = kustomization_config.get("resources", [])
        assert "resource-quota.yaml" in resources

    def test_kustomization_has_common_labels(self, kustomization_config: dict) -> None:
        """kustomization.yaml should have commonLabels."""
        assert "commonLabels" in kustomization_config
        labels = kustomization_config["commonLabels"]
        assert labels.get("app.kubernetes.io/name") == "video2d3d"

    def test_kustomization_has_images(self, kustomization_config: dict) -> None:
        """kustomization.yaml should have images configuration."""
        assert "images" in kustomization_config


class TestDevOverlay:
    """Test development overlay kustomization."""

    def test_dev_kustomization_exists(self, dev_kustomization_path: Path) -> None:
        """dev overlay kustomization.yaml should exist."""
        assert dev_kustomization_path.exists(), "k8s/overlays/dev/kustomization.yaml not found"

    def test_dev_kustomization_is_valid_yaml(self, dev_kustomization_config: dict) -> None:
        """dev overlay kustomization.yaml should be valid YAML."""
        assert dev_kustomization_config is not None

    def test_dev_references_base(self, dev_kustomization_config: dict) -> None:
        """dev overlay should reference base."""
        resources = dev_kustomization_config.get("resources", [])
        assert any("../../base" in str(r) for r in resources)

    def test_dev_has_namespace(self, dev_kustomization_config: dict) -> None:
        """dev overlay should have namespace."""
        assert "namespace" in dev_kustomization_config
        assert dev_kustomization_config["namespace"] == "video2d3d-dev"

    def test_dev_has_environment_label(self, dev_kustomization_config: dict) -> None:
        """dev overlay should have environment label."""
        labels = dev_kustomization_config.get("commonLabels", {})
        assert labels.get("environment") == "development"


class TestProdOverlay:
    """Test production overlay kustomization."""

    def test_prod_kustomization_exists(self, prod_kustomization_path: Path) -> None:
        """prod overlay kustomization.yaml should exist."""
        assert prod_kustomization_path.exists(), "k8s/overlays/prod/kustomization.yaml not found"

    def test_prod_kustomization_is_valid_yaml(self, prod_kustomization_config: dict) -> None:
        """prod overlay kustomization.yaml should be valid YAML."""
        assert prod_kustomization_config is not None

    def test_prod_references_base(self, prod_kustomization_config: dict) -> None:
        """prod overlay should reference base."""
        resources = prod_kustomization_config.get("resources", [])
        assert any("../../base" in str(r) for r in resources)

    def test_prod_has_namespace(self, prod_kustomization_config: dict) -> None:
        """prod overlay should have namespace."""
        assert "namespace" in prod_kustomization_config
        assert prod_kustomization_config["namespace"] == "video2d3d-prod"

    def test_prod_has_environment_label(self, prod_kustomization_config: dict) -> None:
        """prod overlay should have environment label."""
        labels = prod_kustomization_config.get("commonLabels", {})
        assert labels.get("environment") == "production"


class TestResourceReferences:
    """Test that all referenced resources exist."""

    def test_all_base_resources_exist(self, kustomization_config: dict, k8s_base_dir: Path) -> None:
        """All resources referenced in kustomization.yaml should exist."""
        resources = kustomization_config.get("resources", [])
        for resource in resources:
            resource_path = k8s_base_dir / resource
            assert resource_path.exists(), f"Referenced resource not found: {resource}"


class TestNamespaceConsistency:
    """Test namespace consistency across manifests."""

    def test_all_namespaced_resources_use_same_namespace(self, all_manifests_parsed: list) -> None:
        """All namespaced resources should use the video2d3d namespace."""
        CLUSTER_SCOPED = {"Namespace", "ClusterRole", "ClusterRoleBinding", "PriorityClass"}

        for path, docs in all_manifests_parsed:
            # Skip kustomization configs
            if "kustomize" in str(path):
                continue

            for doc in docs:
                if doc is None:
                    continue

                kind = doc.get("kind", "")
                if kind in CLUSTER_SCOPED:
                    continue

                metadata = doc.get("metadata", {})
                namespace = metadata.get("namespace", "")

                # If namespace is set, it should be video2d3d
                if namespace:
                    assert namespace == "video2d3d", (
                        f"{path.name}: {kind} has namespace '{namespace}', expected 'video2d3d'"
                    )


class TestLabelConsistency:
    """Test label consistency across manifests."""

    def test_all_resources_have_app_label(self, all_manifests_parsed: list) -> None:
        """All resources should have app.kubernetes.io/name label."""
        for path, docs in all_manifests_parsed:
            # Skip kustomization configs
            if "kustomize" in str(path):
                continue

            for doc in docs:
                if doc is None:
                    continue

                # Skip PriorityClass and similar cluster resources
                if doc.get("kind") in ["PriorityClass"]:
                    continue

                metadata = doc.get("metadata", {})
                labels = metadata.get("labels", {})

                # Most resources should have app.kubernetes.io/name
                if labels:
                    assert "app.kubernetes.io/name" in labels, (
                        f"{path.name}: {doc.get('kind')} missing app.kubernetes.io/name label"
                    )
