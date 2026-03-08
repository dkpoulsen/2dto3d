"""Conftest for Kubernetes manifest tests.

This module provides pytest fixtures for loading and validating
Kubernetes manifest files.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

# Path to k8s directory
K8S_DIR = Path(__file__).parent.parent.parent / "k8s"
K8S_BASE_DIR = K8S_DIR / "base"
K8S_OVERLAYS_DIR = K8S_DIR / "overlays"


def load_yaml_file(path: Path) -> Any:
    """Load a YAML file and return its contents.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML contents.
    """
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_yaml_docs(path: Path) -> list[Any]:
    """Load all YAML documents from a file (multi-document YAML).

    Args:
        path: Path to the YAML file.

    Returns:
        List of parsed YAML documents.
    """
    with open(path) as f:
        return list(yaml.safe_load_all(f))


def get_all_manifest_files() -> list[Path]:
    """Get all YAML manifest files in k8s/base.

    Returns:
        List of Path objects for all YAML files.
    """
    return list(K8S_BASE_DIR.glob("*.yaml"))


# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture
def k8s_dir() -> Path:
    """Path to k8s directory."""
    return K8S_DIR


@pytest.fixture
def k8s_base_dir() -> Path:
    """Path to k8s/base directory."""
    return K8S_BASE_DIR


@pytest.fixture
def k8s_overlays_dir() -> Path:
    """Path to k8s/overlays directory."""
    return K8S_OVERLAYS_DIR


@pytest.fixture
def namespace_path(k8s_base_dir: Path) -> Path:
    """Path to namespace.yaml."""
    return k8s_base_dir / "namespace.yaml"


@pytest.fixture
def configmap_path(k8s_base_dir: Path) -> Path:
    """Path to configmap.yaml."""
    return k8s_base_dir / "configmap.yaml"


@pytest.fixture
def secrets_path(k8s_base_dir: Path) -> Path:
    """Path to secrets.yaml."""
    return k8s_base_dir / "secrets.yaml"


@pytest.fixture
def pvc_path(k8s_base_dir: Path) -> Path:
    """Path to pvc.yaml."""
    return k8s_base_dir / "pvc.yaml"


@pytest.fixture
def deployment_path(k8s_base_dir: Path) -> Path:
    """Path to deployment.yaml."""
    return k8s_base_dir / "deployment.yaml"


@pytest.fixture
def service_path(k8s_base_dir: Path) -> Path:
    """Path to service.yaml."""
    return k8s_base_dir / "service.yaml"


@pytest.fixture
def hpa_path(k8s_base_dir: Path) -> Path:
    """Path to hpa.yaml."""
    return k8s_base_dir / "hpa.yaml"


@pytest.fixture
def ingress_path(k8s_base_dir: Path) -> Path:
    """Path to ingress.yaml."""
    return k8s_base_dir / "ingress.yaml"


@pytest.fixture
def rbac_path(k8s_base_dir: Path) -> Path:
    """Path to rbac.yaml."""
    return k8s_base_dir / "rbac.yaml"


@pytest.fixture
def pdb_path(k8s_base_dir: Path) -> Path:
    """Path to pdb.yaml."""
    return k8s_base_dir / "pdb.yaml"


@pytest.fixture
def resource_quota_path(k8s_base_dir: Path) -> Path:
    """Path to resource-quota.yaml."""
    return k8s_base_dir / "resource-quota.yaml"


@pytest.fixture
def kustomization_path(k8s_base_dir: Path) -> Path:
    """Path to kustomization.yaml."""
    return k8s_base_dir / "kustomization.yaml"


@pytest.fixture
def dev_kustomization_path(k8s_overlays_dir: Path) -> Path:
    """Path to dev overlay kustomization.yaml."""
    return k8s_overlays_dir / "dev" / "kustomization.yaml"


@pytest.fixture
def prod_kustomization_path(k8s_overlays_dir: Path) -> Path:
    """Path to prod overlay kustomization.yaml."""
    return k8s_overlays_dir / "prod" / "kustomization.yaml"


# =============================================================================
# Parsed Content Fixtures
# =============================================================================


@pytest.fixture
def namespace_config(namespace_path: Path) -> dict:
    """Parsed namespace.yaml content."""
    return load_yaml_file(namespace_path)


@pytest.fixture
def configmap_configs(configmap_path: Path) -> list[dict]:
    """Parsed configmap.yaml content (multiple ConfigMaps)."""
    return load_all_yaml_docs(configmap_path)


@pytest.fixture
def secrets_config(secrets_path: Path) -> dict:
    """Parsed secrets.yaml content."""
    return load_yaml_file(secrets_path)


@pytest.fixture
def pvc_configs(pvc_path: Path) -> list[dict]:
    """Parsed pvc.yaml content (multiple PVCs)."""
    return load_all_yaml_docs(pvc_path)


@pytest.fixture
def deployment_config(deployment_path: Path) -> dict:
    """Parsed deployment.yaml content (first active Deployment only)."""
    docs = load_all_yaml_docs(deployment_path)
    # Return first non-None Deployment document (the active GPU deployment)
    for doc in docs:
        if doc is not None and doc.get("kind") == "Deployment":
            return doc
    return docs[0] if docs else None


@pytest.fixture
def service_configs(service_path: Path) -> list[dict]:
    """Parsed service.yaml content (multiple Services)."""
    return load_all_yaml_docs(service_path)


@pytest.fixture
def hpa_configs(hpa_path: Path) -> list[dict]:
    """Parsed hpa.yaml content (multiple HPAs)."""
    return load_all_yaml_docs(hpa_path)


@pytest.fixture
def ingress_configs(ingress_path: Path) -> list[dict]:
    """Parsed ingress.yaml content (multiple resources)."""
    return load_all_yaml_docs(ingress_path)


@pytest.fixture
def rbac_configs(rbac_path: Path) -> list[dict]:
    """Parsed rbac.yaml content (multiple RBAC resources)."""
    return load_all_yaml_docs(rbac_path)


@pytest.fixture
def pdb_config(pdb_path: Path) -> dict:
    """Parsed pdb.yaml content."""
    return load_yaml_file(pdb_path)


@pytest.fixture
def resource_quota_configs(resource_quota_path: Path) -> list[dict]:
    """Parsed resource-quota.yaml content (multiple resources)."""
    return load_all_yaml_docs(resource_quota_path)


@pytest.fixture
def kustomization_config(kustomization_path: Path) -> dict:
    """Parsed kustomization.yaml content."""
    return load_yaml_file(kustomization_path)


@pytest.fixture
def dev_kustomization_config(dev_kustomization_path: Path) -> dict:
    """Parsed dev overlay kustomization.yaml content."""
    return load_yaml_file(dev_kustomization_path)


@pytest.fixture
def prod_kustomization_config(prod_kustomization_path: Path) -> dict:
    """Parsed prod overlay kustomization.yaml content."""
    return load_yaml_file(prod_kustomization_path)


@pytest.fixture
def all_manifest_files() -> list[Path]:
    """List of all manifest files in k8s/base."""
    return get_all_manifest_files()


@pytest.fixture
def all_manifests_parsed(all_manifest_files: list[Path]) -> list[tuple[Path, Any]]:
    """All manifest files parsed, as (path, content) tuples."""
    result = []
    for path in all_manifest_files:
        docs = load_all_yaml_docs(path)
        result.append((path, docs))
    return result
