"""Tests for GitHub Actions CI workflow YAML validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CI_WORKFLOW_PATH = Path(".github/workflows/ci.yml")


def get_triggers(workflow_yaml: dict) -> dict:
    """Get workflow triggers, handling YAML 'on' -> True conversion.

    YAML 1.1 parses 'on' as Python True boolean.
    """
    return workflow_yaml.get(True, workflow_yaml.get("on", {}))


@pytest.fixture
def workflow_content() -> str:
    """Load CI workflow file content."""
    return CI_WORKFLOW_PATH.read_text()


@pytest.fixture
def workflow_yaml(workflow_content: str) -> dict:
    """Parse CI workflow YAML."""
    return yaml.safe_load(workflow_content)


class TestCIWorkflowSyntax:
    """Test CI workflow YAML syntax and structure."""

    def test_workflow_file_exists(self) -> None:
        """Verify CI workflow file exists."""
        assert CI_WORKFLOW_PATH.exists(), f"CI workflow file not found at {CI_WORKFLOW_PATH}"

    def test_workflow_is_valid_yaml(self, workflow_yaml: dict) -> None:
        """Verify CI workflow is valid YAML."""
        assert isinstance(workflow_yaml, dict), "Workflow should be a dictionary"

    def test_workflow_has_name(self, workflow_yaml: dict) -> None:
        """Verify workflow has a name."""
        assert "name" in workflow_yaml, "Workflow should have a 'name' field"
        assert workflow_yaml["name"] == "CI"

    def test_workflow_has_on_triggers(self, workflow_yaml: dict) -> None:
        """Verify workflow has trigger configuration."""
        triggers = get_triggers(workflow_yaml)
        assert triggers, "Workflow should have triggers"
        assert isinstance(triggers, dict), "Triggers should be a dictionary"

    def test_workflow_has_push_trigger(self, workflow_yaml: dict) -> None:
        """Verify workflow triggers on push."""
        triggers = get_triggers(workflow_yaml)
        assert "push" in triggers, "Workflow should trigger on push"
        push_config = triggers["push"]
        assert "branches" in push_config, "Push trigger should specify branches"
        assert "main" in push_config["branches"], "Should trigger on main branch"
        assert "develop" in push_config["branches"], "Should trigger on develop branch"

    def test_workflow_has_pull_request_trigger(self, workflow_yaml: dict) -> None:
        """Verify workflow triggers on pull requests."""
        triggers = get_triggers(workflow_yaml)
        assert "pull_request" in triggers, "Workflow should trigger on pull_request"
        pr_config = triggers["pull_request"]
        assert "branches" in pr_config, "PR trigger should specify branches"

    def test_workflow_has_workflow_dispatch(self, workflow_yaml: dict) -> None:
        """Verify workflow supports manual trigger."""
        triggers = get_triggers(workflow_yaml)
        assert "workflow_dispatch" in triggers, "Workflow should support manual dispatch"


class TestCIWorkflowPermissions:
    """Test CI workflow security configuration."""

    def test_workflow_has_permissions(self, workflow_yaml: dict) -> None:
        """Verify workflow has permissions defined."""
        assert "permissions" in workflow_yaml, "Workflow should have permissions block"

    def test_permissions_are_minimal(self, workflow_yaml: dict) -> None:
        """Verify permissions follow principle of least privilege."""
        permissions = workflow_yaml["permissions"]
        assert permissions.get("contents") == "read", "Should have read-only contents permission"


class TestCIWorkflowConcurrency:
    """Test CI workflow concurrency control."""

    def test_workflow_has_concurrency(self, workflow_yaml: dict) -> None:
        """Verify workflow has concurrency control to prevent redundant runs."""
        assert "concurrency" in workflow_yaml, "Workflow should have concurrency control"

    def test_concurrency_cancels_in_progress(self, workflow_yaml: dict) -> None:
        """Verify concurrency cancels in-progress runs."""
        concurrency = workflow_yaml["concurrency"]
        assert concurrency.get("cancel-in-progress") is True, "Should cancel in-progress runs"


class TestCIWorkflowEnvVars:
    """Test CI workflow environment variables."""

    def test_workflow_has_env_block(self, workflow_yaml: dict) -> None:
        """Verify workflow has environment variables."""
        assert "env" in workflow_yaml, "Workflow should have env block"

    def test_pythondontwritebytecode_set(self, workflow_yaml: dict) -> None:
        """Verify PYTHONDONTWRITEBYTECODE is set."""
        env = workflow_yaml["env"]
        assert env.get("PYTHONDONTWRITEBYTECODE") == "1", "Should disable .pyc files"


class TestCIWorkflowJobs:
    """Test CI workflow job definitions."""

    def test_workflow_has_jobs(self, workflow_yaml: dict) -> None:
        """Verify workflow has jobs defined."""
        assert "jobs" in workflow_yaml, "Workflow should have jobs"
        jobs = workflow_yaml["jobs"]
        assert isinstance(jobs, dict), "Jobs should be a dictionary"
        assert len(jobs) > 0, "Workflow should have at least one job"

    def test_has_lint_job(self, workflow_yaml: dict) -> None:
        """Verify lint job exists."""
        jobs = workflow_yaml["jobs"]
        assert "lint" in jobs, "Workflow should have 'lint' job"

    def test_has_test_job(self, workflow_yaml: dict) -> None:
        """Verify test job exists."""
        jobs = workflow_yaml["jobs"]
        assert "test" in jobs, "Workflow should have 'test' job"

    def test_has_test_integration_job(self, workflow_yaml: dict) -> None:
        """Verify integration test job exists."""
        jobs = workflow_yaml["jobs"]
        assert "test-integration" in jobs, "Workflow should have 'test-integration' job"

    def test_has_ci_status_job(self, workflow_yaml: dict) -> None:
        """Verify CI status summary job exists."""
        jobs = workflow_yaml["jobs"]
        assert "ci-status" in jobs, "Workflow should have 'ci-status' summary job"


class TestLintJob:
    """Test lint job configuration."""

    @pytest.fixture
    def lint_job(self, workflow_yaml: dict) -> dict:
        """Get lint job configuration."""
        return workflow_yaml["jobs"]["lint"]

    def test_lint_runs_on_ubuntu(self, lint_job: dict) -> None:
        """Verify lint job runs on ubuntu-latest."""
        assert lint_job["runs-on"] == "ubuntu-latest"

    def test_lint_has_timeout(self, lint_job: dict) -> None:
        """Verify lint job has timeout configured."""
        assert "timeout-minutes" in lint_job, "Lint job should have timeout"
        assert lint_job["timeout-minutes"] > 0, "Timeout should be positive"

    def test_lint_uses_python_311(self, lint_job: dict) -> None:
        """Verify lint job uses Python 3.11."""
        steps = lint_job["steps"]
        setup_python = next(
            (s for s in steps if s.get("uses", "").startswith("actions/setup-python")),
            None,
        )
        assert setup_python is not None, "Lint job should have setup-python step"
        assert setup_python["with"]["python-version"] == "3.11"

    def test_lint_runs_black(self, lint_job: dict) -> None:
        """Verify lint job runs black."""
        steps = lint_job["steps"]
        black_step = next((s for s in steps if "black" in s.get("name", "").lower()), None)
        assert black_step is not None, "Lint job should run black"

    def test_lint_runs_ruff(self, lint_job: dict) -> None:
        """Verify lint job runs ruff."""
        steps = lint_job["steps"]
        ruff_step = next((s for s in steps if "ruff" in s.get("name", "").lower()), None)
        assert ruff_step is not None, "Lint job should run ruff"

    def test_lint_runs_isort(self, lint_job: dict) -> None:
        """Verify lint job runs isort."""
        steps = lint_job["steps"]
        isort_step = next((s for s in steps if "isort" in s.get("name", "").lower()), None)
        assert isort_step is not None, "Lint job should run isort"


class TestTestJob:
    """Test the test job configuration."""

    @pytest.fixture
    def test_job(self, workflow_yaml: dict) -> dict:
        """Get test job configuration."""
        return workflow_yaml["jobs"]["test"]

    def test_test_runs_on_ubuntu(self, test_job: dict) -> None:
        """Verify test job runs on ubuntu-latest."""
        assert test_job["runs-on"] == "ubuntu-latest"

    def test_test_depends_on_lint(self, test_job: dict) -> None:
        """Verify test job depends on lint job."""
        assert "needs" in test_job, "Test job should have dependencies"
        assert "lint" in test_job["needs"], "Test job should depend on lint"

    def test_test_has_timeout(self, test_job: dict) -> None:
        """Verify test job has timeout configured."""
        assert "timeout-minutes" in test_job, "Test job should have timeout"

    def test_test_has_matrix_strategy(self, test_job: dict) -> None:
        """Verify test job uses matrix strategy for Python versions."""
        assert "strategy" in test_job, "Test job should have strategy"
        strategy = test_job["strategy"]
        assert "matrix" in strategy, "Strategy should be matrix"
        assert "python-version" in strategy["matrix"], "Matrix should have python-version"

    def test_matrix_includes_python_versions(self, test_job: dict) -> None:
        """Verify matrix includes Python 3.9, 3.10, 3.11, 3.12."""
        python_versions = test_job["strategy"]["matrix"]["python-version"]
        expected_versions = ["3.9", "3.10", "3.11", "3.12"]
        for version in expected_versions:
            assert version in python_versions, f"Matrix should include Python {version}"

    def test_matrix_does_not_fail_fast(self, test_job: dict) -> None:
        """Verify matrix doesn't fail fast (runs all versions even if one fails)."""
        strategy = test_job["strategy"]
        assert strategy.get("fail-fast") is False, "Should not fail-fast to test all versions"

    def test_test_uses_pytest(self, test_job: dict) -> None:
        """Verify test job uses pytest."""
        steps = test_job["steps"]
        pytest_step = next(
            (s for s in steps if "pytest" in str(s.get("run", "")).lower()),
            None,
        )
        assert pytest_step is not None, "Test job should run pytest"

    def test_test_uses_coverage(self, test_job: dict) -> None:
        """Verify test job uses coverage."""
        steps = test_job["steps"]
        coverage_step = next(
            (s for s in steps if "coverage" in str(s.get("run", "")).lower()),
            None,
        )
        assert coverage_step is not None, "Test job should run with coverage"

    def test_test_excludes_slow_and_gpu_tests(self, test_job: dict) -> None:
        """Verify test job excludes slow and GPU tests by default."""
        steps = test_job["steps"]
        pytest_step = next(
            (
                s
                for s in steps
                if "pytest" in str(s.get("run", "")) and "--durations" in str(s.get("run", ""))
            ),
            None,
        )
        assert pytest_step is not None
        run_cmd = pytest_step["run"]
        # The pytest command is a multiline string, check for markers
        # Both 'not slow' and 'not gpu' should appear in the command
        assert "slow" in run_cmd, "Should reference slow marker"
        assert "gpu" in run_cmd, "Should reference gpu marker"
        # Verify exclusion pattern exists (with quotes or without)
        has_slow_exclusion = (
            "'not slow" in run_cmd or '"not slow' in run_cmd or "not slow" in run_cmd
        )
        has_gpu_exclusion = "'not gpu" in run_cmd or '"not gpu' in run_cmd or "not gpu" in run_cmd
        assert has_slow_exclusion, "Should exclude slow tests"
        assert has_gpu_exclusion, "Should exclude GPU tests"

    def test_test_uploads_artifacts(self, test_job: dict) -> None:
        """Verify test job uploads test artifacts."""
        steps = test_job["steps"]
        upload_step = next(
            (s for s in steps if s.get("uses", "").startswith("actions/upload-artifact")),
            None,
        )
        assert upload_step is not None, "Test job should upload artifacts"


class TestCIStatusJob:
    """Test the CI status summary job."""

    @pytest.fixture
    def ci_status_job(self, workflow_yaml: dict) -> dict:
        """Get CI status job configuration."""
        return workflow_yaml["jobs"]["ci-status"]

    def test_ci_status_needs_all_jobs(self, ci_status_job: dict) -> None:
        """Verify CI status job depends on all main jobs."""
        needs = ci_status_job.get("needs", [])
        assert "lint" in needs, "CI status should depend on lint"
        assert "test" in needs, "CI status should depend on test"
        assert "test-integration" in needs, "CI status should depend on test-integration"

    def test_ci_status_runs_always(self, ci_status_job: dict) -> None:
        """Verify CI status runs even if dependent jobs fail."""
        assert ci_status_job.get("if") == "always()", "CI status should run always"

    def test_ci_status_has_timeout(self, ci_status_job: dict) -> None:
        """Verify CI status has a short timeout."""
        assert "timeout-minutes" in ci_status_job, "CI status should have timeout"


class TestCacheConfiguration:
    """Test cache configuration across jobs."""

    def test_lint_job_has_cache(self, workflow_yaml: dict) -> None:
        """Verify lint job uses caching."""
        lint_steps = workflow_yaml["jobs"]["lint"]["steps"]
        cache_step = next(
            (s for s in lint_steps if s.get("uses", "").startswith("actions/cache")),
            None,
        )
        assert cache_step is not None, "Lint job should use cache"

    def test_test_job_has_cache(self, workflow_yaml: dict) -> None:
        """Verify test job uses caching."""
        test_steps = workflow_yaml["jobs"]["test"]["steps"]
        cache_step = next(
            (s for s in test_steps if s.get("uses", "").startswith("actions/cache")),
            None,
        )
        assert cache_step is not None, "Test job should use cache"

    def test_cache_key_includes_requirements(self, workflow_yaml: dict) -> None:
        """Verify cache key includes requirements files hash."""
        test_steps = workflow_yaml["jobs"]["test"]["steps"]
        cache_step = next(
            (s for s in test_steps if s.get("uses", "").startswith("actions/cache")),
            None,
        )
        assert cache_step is not None
        key = cache_step["with"]["key"]
        assert "requirements" in key.lower(), "Cache key should include requirements"

    def test_cache_key_includes_pyproject(self, workflow_yaml: dict) -> None:
        """Verify cache key includes pyproject.toml hash."""
        test_steps = workflow_yaml["jobs"]["test"]["steps"]
        cache_step = next(
            (s for s in test_steps if s.get("uses", "").startswith("actions/cache")),
            None,
        )
        assert cache_step is not None
        key = cache_step["with"]["key"]
        assert "pyproject" in key.lower(), "Cache key should include pyproject.toml"


class TestActionVersions:
    """Test that GitHub Actions use modern versions."""

    def test_checkout_is_v4(self, workflow_yaml: dict) -> None:
        """Verify checkout action is v4."""
        for _job_name, job in workflow_yaml["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/checkout"):
                    assert "v4" in step["uses"], f"Checkout should be v4, got {step['uses']}"

    def test_setup_python_is_v5(self, workflow_yaml: dict) -> None:
        """Verify setup-python action is v5."""
        for _job_name, job in workflow_yaml["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/setup-python"):
                    assert "v5" in step["uses"], f"Setup-python should be v5, got {step['uses']}"

    def test_cache_is_v4(self, workflow_yaml: dict) -> None:
        """Verify cache action is v4."""
        for _job_name, job in workflow_yaml["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/cache"):
                    assert "v4" in step["uses"], f"Cache should be v4, got {step['uses']}"

    def test_upload_artifact_is_v4(self, workflow_yaml: dict) -> None:
        """Verify upload-artifact action is v4."""
        for _job_name, job in workflow_yaml["jobs"].items():
            for step in job.get("steps", []):
                if step.get("uses", "").startswith("actions/upload-artifact"):
                    assert "v4" in step["uses"], f"Upload-artifact should be v4, got {step['uses']}"
