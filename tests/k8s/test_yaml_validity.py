"""Tests for Kubernetes manifest YAML validity.

This module tests that all Kubernetes manifest files:
- Exist in the expected locations
- Are valid YAML
- Have valid Kubernetes API versions
- Have required Kubernetes fields (kind, apiVersion, metadata)
"""

from pathlib import Path

import yaml


class TestK8sDirectoryStructure:
    """Test Kubernetes directory structure exists."""

    def test_k8s_directory_exists(self, k8s_dir: Path) -> None:
        """k8s/ directory should exist."""
        assert k8s_dir.exists(), "k8s/ directory not found"
        assert k8s_dir.is_dir(), "k8s/ should be a directory"

    def test_k8s_base_directory_exists(self, k8s_base_dir: Path) -> None:
        """k8s/base/ directory should exist."""
        assert k8s_base_dir.exists(), "k8s/base/ directory not found"
        assert k8s_base_dir.is_dir(), "k8s/base/ should be a directory"

    def test_k8s_overlays_directory_exists(self, k8s_overlays_dir: Path) -> None:
        """k8s/overlays/ directory should exist."""
        assert k8s_overlays_dir.exists(), "k8s/overlays/ directory not found"
        assert k8s_overlays_dir.is_dir(), "k8s/overlays/ should be a directory"

    def test_dev_overlay_directory_exists(self, k8s_overlays_dir: Path) -> None:
        """k8s/overlays/dev/ directory should exist."""
        dev_dir = k8s_overlays_dir / "dev"
        assert dev_dir.exists(), "k8s/overlays/dev/ directory not found"

    def test_prod_overlay_directory_exists(self, k8s_overlays_dir: Path) -> None:
        """k8s/overlays/prod/ directory should exist."""
        prod_dir = k8s_overlays_dir / "prod"
        assert prod_dir.exists(), "k8s/overlays/prod/ directory not found"


class TestManifestFilesExist:
    """Test that required manifest files exist."""

    def test_namespace_yaml_exists(self, namespace_path: Path) -> None:
        """namespace.yaml should exist."""
        assert namespace_path.exists(), "namespace.yaml not found"

    def test_configmap_yaml_exists(self, configmap_path: Path) -> None:
        """configmap.yaml should exist."""
        assert configmap_path.exists(), "configmap.yaml not found"

    def test_secrets_yaml_exists(self, secrets_path: Path) -> None:
        """secrets.yaml should exist."""
        assert secrets_path.exists(), "secrets.yaml not found"

    def test_pvc_yaml_exists(self, pvc_path: Path) -> None:
        """pvc.yaml should exist."""
        assert pvc_path.exists(), "pvc.yaml not found"

    def test_deployment_yaml_exists(self, deployment_path: Path) -> None:
        """deployment.yaml should exist."""
        assert deployment_path.exists(), "deployment.yaml not found"

    def test_service_yaml_exists(self, service_path: Path) -> None:
        """service.yaml should exist."""
        assert service_path.exists(), "service.yaml not found"

    def test_hpa_yaml_exists(self, hpa_path: Path) -> None:
        """hpa.yaml should exist."""
        assert hpa_path.exists(), "hpa.yaml not found"

    def test_ingress_yaml_exists(self, ingress_path: Path) -> None:
        """ingress.yaml should exist."""
        assert ingress_path.exists(), "ingress.yaml not found"

    def test_rbac_yaml_exists(self, rbac_path: Path) -> None:
        """rbac.yaml should exist."""
        assert rbac_path.exists(), "rbac.yaml not found"

    def test_pdb_yaml_exists(self, pdb_path: Path) -> None:
        """pdb.yaml should exist."""
        assert pdb_path.exists(), "pdb.yaml not found"

    def test_resource_quota_yaml_exists(self, resource_quota_path: Path) -> None:
        """resource-quota.yaml should exist."""
        assert resource_quota_path.exists(), "resource-quota.yaml not found"

    def test_kustomization_yaml_exists(self, kustomization_path: Path) -> None:
        """kustomization.yaml should exist."""
        assert kustomization_path.exists(), "kustomization.yaml not found"

    def test_readme_exists(self, k8s_dir: Path) -> None:
        """README.md should exist in k8s/."""
        readme_path = k8s_dir / "README.md"
        assert readme_path.exists(), "k8s/README.md not found"


class TestYamlValidity:
    """Test that all manifest files are valid YAML."""

    def test_namespace_is_valid_yaml(self, namespace_path: Path) -> None:
        """namespace.yaml should be valid YAML."""
        with open(namespace_path) as f:
            content = yaml.safe_load(f)
        assert content is not None

    def test_configmap_is_valid_yaml(self, configmap_path: Path) -> None:
        """configmap.yaml should be valid YAML (multi-document)."""
        with open(configmap_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_secrets_is_valid_yaml(self, secrets_path: Path) -> None:
        """secrets.yaml should be valid YAML (multi-document)."""
        with open(secrets_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_pvc_is_valid_yaml(self, pvc_path: Path) -> None:
        """pvc.yaml should be valid YAML (multi-document)."""
        with open(pvc_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_deployment_is_valid_yaml(self, deployment_path: Path) -> None:
        """deployment.yaml should be valid YAML (multi-document)."""
        with open(deployment_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_service_is_valid_yaml(self, service_path: Path) -> None:
        """service.yaml should be valid YAML (multi-document)."""
        with open(service_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_hpa_is_valid_yaml(self, hpa_path: Path) -> None:
        """hpa.yaml should be valid YAML (multi-document)."""
        with open(hpa_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_ingress_is_valid_yaml(self, ingress_path: Path) -> None:
        """ingress.yaml should be valid YAML (multi-document)."""
        with open(ingress_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_rbac_is_valid_yaml(self, rbac_path: Path) -> None:
        """rbac.yaml should be valid YAML (multi-document)."""
        with open(rbac_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_pdb_is_valid_yaml(self, pdb_path: Path) -> None:
        """pdb.yaml should be valid YAML."""
        with open(pdb_path) as f:
            content = yaml.safe_load(f)
        assert content is not None

    def test_resource_quota_is_valid_yaml(self, resource_quota_path: Path) -> None:
        """resource-quota.yaml should be valid YAML (multi-document)."""
        with open(resource_quota_path) as f:
            docs = list(yaml.safe_load_all(f))
        assert len(docs) > 0

    def test_kustomization_is_valid_yaml(self, kustomization_path: Path) -> None:
        """kustomization.yaml should be valid YAML."""
        with open(kustomization_path) as f:
            content = yaml.safe_load(f)
        assert content is not None

    def test_dev_kustomization_is_valid_yaml(self, dev_kustomization_path: Path) -> None:
        """dev overlay kustomization.yaml should be valid YAML."""
        with open(dev_kustomization_path) as f:
            content = yaml.safe_load(f)
        assert content is not None

    def test_prod_kustomization_is_valid_yaml(self, prod_kustomization_path: Path) -> None:
        """prod overlay kustomization.yaml should be valid YAML."""
        with open(prod_kustomization_path) as f:
            content = yaml.safe_load(f)
        assert content is not None


class TestKubernetesApiVersion:
    """Test that Kubernetes API versions are valid."""

    VALID_API_VERSIONS = {
        "v1",
        "apps/v1",
        "autoscaling/v2",
        "networking.k8s.io/v1",
        "rbac.authorization.k8s.io/v1",
        "policy/v1",
        "scheduling.k8s.io/v1",
    }

    def test_all_manifests_have_api_version(self, all_manifests_parsed: list) -> None:
        """All Kubernetes resources should have apiVersion."""
        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                assert "apiVersion" in doc, f"{path.name}: missing apiVersion"

    def test_all_manifests_have_kind(self, all_manifests_parsed: list) -> None:
        """All Kubernetes resources should have kind."""
        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                assert "kind" in doc, f"{path.name}: missing kind"

    def test_all_manifests_have_metadata(self, all_manifests_parsed: list) -> None:
        """All Kubernetes resources should have metadata."""
        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                # Skip kustomize configs (they don't follow Kubernetes resource format)
                if "kustomize.config.k8s.io" in doc.get("apiVersion", ""):
                    continue
                assert "metadata" in doc, f"{path.name}: missing metadata"

    def test_api_versions_are_valid(self, all_manifests_parsed: list) -> None:
        """All API versions should be valid Kubernetes API versions."""
        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                api_version = doc.get("apiVersion", "")
                # Allow kustomize config API version
                if "kustomize.config.k8s.io" in api_version:
                    continue
                assert (
                    api_version in self.VALID_API_VERSIONS
                ), f"{path.name}: invalid apiVersion '{api_version}'"


class TestKubernetesMetadata:
    """Test Kubernetes metadata fields."""

    def test_all_resources_have_name(self, all_manifests_parsed: list) -> None:
        """All Kubernetes resources should have metadata.name."""
        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                # Skip kustomize configs
                if "kustomize.config.k8s.io" in doc.get("apiVersion", ""):
                    continue
                metadata = doc.get("metadata", {})
                assert "name" in metadata, f"{path.name}: missing metadata.name"

    def test_all_resources_have_namespace_or_cluster_scoped(
        self, all_manifests_parsed: list
    ) -> None:
        """Namespaced resources should have metadata.namespace or be cluster-scoped."""
        CLUSTER_SCOPED_KINDS = {
            "Namespace",
            "ClusterRole",
            "ClusterRoleBinding",
            "PriorityClass",
        }

        for path, docs in all_manifests_parsed:
            for doc in docs:
                if doc is None:
                    continue
                # Skip kustomize configs
                if "kustomize.config.k8s.io" in doc.get("apiVersion", ""):
                    continue

                kind = doc.get("kind", "")
                metadata = doc.get("metadata", {})

                # Cluster-scoped resources don't need namespace
                if kind in CLUSTER_SCOPED_KINDS:
                    continue

                # Namespaced resources should have namespace
                assert (
                    "namespace" in metadata or kind == "Namespace"
                ), f"{path.name}: {kind} should have metadata.namespace"
