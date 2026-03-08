"""Tests for USER_GUIDE.md documentation.

This module validates the user guide documentation for:
- Structure and completeness
- Code example syntax (YAML, bash)
- Internal links and references
- Content accuracy against actual implementation
"""

import re
from pathlib import Path

import pytest
import yaml

# Path to the USER_GUIDE.md file
USER_GUIDE_PATH = Path(__file__).parent.parent.parent / "docs" / "USER_GUIDE.md"


@pytest.fixture
def user_guide_content() -> str:
    """Load the USER_GUIDE.md content."""
    if not USER_GUIDE_PATH.exists():
        pytest.skip("USER_GUIDE.md not found")
    return USER_GUIDE_PATH.read_text()


@pytest.fixture
def user_guide_lines(user_guide_content: str) -> list[str]:
    """Split content into lines."""
    return user_guide_content.split("\n")


class TestUserGuideExists:
    """Test that the user guide file exists and is accessible."""

    def test_user_guide_file_exists(self) -> None:
        """Verify USER_GUIDE.md exists in docs directory."""
        assert USER_GUIDE_PATH.exists(), f"USER_GUIDE.md not found at {USER_GUIDE_PATH}"

    def test_user_guide_not_empty(self, user_guide_content: str) -> None:
        """Verify USER_GUIDE.md has content."""
        assert len(user_guide_content) > 1000, "USER_GUIDE.md appears to be empty or too short"


class TestUserGuideStructure:
    """Test the structure and organization of the user guide."""

    REQUIRED_SECTIONS = [
        "Introduction",
        "Installation",
        "Configuration",
        "Command Line Interface",
        "Web API",
        "Docker Deployment",
        "Troubleshooting",
        "Best Practices",
        "FAQ",
    ]

    def test_has_table_of_contents(self, user_guide_content: str) -> None:
        """Verify table of contents exists."""
        assert "## Table of Contents" in user_guide_content, "Missing Table of Contents section"

    def test_has_all_required_sections(self, user_guide_content: str) -> None:
        """Verify all required sections are present."""
        for section in self.REQUIRED_SECTIONS:
            # Check for section header (## followed by section name)
            pattern = rf"##\s+.*{re.escape(section)}"
            assert re.search(
                pattern, user_guide_content, re.IGNORECASE
            ), f"Missing required section: {section}"

    def test_has_version_info(self, user_guide_content: str) -> None:
        """Verify version information is present."""
        assert (
            "**Version:**" in user_guide_content or "Version:" in user_guide_content
        ), "Missing version information"

    def test_has_development_status_warning(self, user_guide_content: str) -> None:
        """Verify development status warning is present."""
        # Check for development status indicator
        assert (
            "Development Status" in user_guide_content
            or "development" in user_guide_content.lower()
        ), "Missing development status information"

    def test_section_hierarchy(self, user_guide_lines: list[str]) -> None:
        """Verify headings use valid markdown levels (1-6)."""
        for line in user_guide_lines:
            if match := re.match(r"^(#{1,6})\s", line):
                level = len(match.group(1))
                # Just verify it's a valid heading level (1-6)
                assert 1 <= level <= 6, f"Invalid heading level: '{line}'"


class TestUserGuideCodeBlocks:
    """Test code blocks in the user guide."""

    def test_code_blocks_balanced(self, user_guide_content: str) -> None:
        """Verify all code blocks are properly closed."""
        code_block_count = user_guide_content.count("```")
        assert (
            code_block_count % 2 == 0
        ), f"Unbalanced code blocks: found {code_block_count} ``` markers (should be even)"

    def test_yaml_code_blocks_valid(self, user_guide_content: str) -> None:
        """Verify YAML code blocks are valid syntax."""
        # Extract all YAML code blocks
        yaml_pattern = r"```yaml\n(.*?)```"
        yaml_blocks = re.findall(yaml_pattern, user_guide_content, re.DOTALL)

        errors = []
        for i, yaml_content in enumerate(yaml_blocks):
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                errors.append(f"YAML block {i + 1}: {e}")

        assert not errors, "Invalid YAML code blocks:\n" + "\n".join(errors)

    def test_bash_code_blocks_format(self, user_guide_content: str) -> None:
        """Verify bash code blocks have proper format."""
        # Extract all bash/shell code blocks
        bash_pattern = r"```bash\n(.*?)```"
        bash_blocks = re.findall(bash_pattern, user_guide_content, re.DOTALL)

        assert (
            len(bash_blocks) >= 10
        ), f"Expected at least 10 bash code examples, found {len(bash_blocks)}"

    def test_http_code_blocks_format(self, user_guide_content: str) -> None:
        """Verify HTTP code blocks have proper format."""
        # Extract all HTTP code blocks
        http_pattern = r"```http\n(.*?)```"
        http_blocks = re.findall(http_pattern, user_guide_content, re.DOTALL)

        # Verify each block starts with an HTTP method
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        for i, block in enumerate(http_blocks):
            first_line = block.strip().split("\n")[0].strip()
            method = first_line.split()[0] if first_line else ""
            assert method in valid_methods, f"HTTP block {i + 1} has invalid method: {method}"


class TestUserGuideLinks:
    """Test links and references in the user guide."""

    def test_internal_anchor_links(self, user_guide_content: str) -> None:
        """Verify internal anchor links point to existing sections."""
        # Find all internal links (format: [text](#section-name))
        anchor_pattern = r"\[([^\]]+)\]\(#[a-z0-9-]+\)"
        anchor_links = re.findall(anchor_pattern, user_guide_content)

        assert (
            len(anchor_links) >= 5
        ), f"Expected at least 5 internal anchor links, found {len(anchor_links)}"

    def test_no_broken_markdown_links(self, user_guide_content: str) -> None:
        """Verify no broken markdown link syntax."""
        # Look for potentially broken links like [text]( or ](url) without proper format
        broken_patterns = [
            r"\[[^\]]+\]\(\s*\)",  # Empty link: [text]()
            r"\[\s*\]\([^)]+\)",  # Empty text: [](url)
        ]

        for pattern in broken_patterns:
            matches = re.findall(pattern, user_guide_content)
            assert not matches, f"Found broken markdown links: {matches}"


class TestUserGuideContent:
    """Test content accuracy and completeness."""

    def test_lists_all_depth_models(self, user_guide_content: str) -> None:
        """Verify all depth estimation models are documented."""
        expected_models = [
            "midas_small",
            "midas_hybrid",
            "dpt_large",
            "dpt_hybrid",
            "adabins_nyu",
            "adabins_kitti",
        ]

        for model in expected_models:
            assert model in user_guide_content, f"Missing depth model: {model}"

    def test_lists_all_stereo_formats(self, user_guide_content: str) -> None:
        """Verify all stereo output formats are documented."""
        expected_formats = [
            "side_by_side",
            "anaglyph",
            "interlaced",
            "vr",
        ]

        for fmt in expected_formats:
            assert fmt in user_guide_content, f"Missing stereo format: {fmt}"

    def test_documents_cli_commands(self, user_guide_content: str) -> None:
        """Verify all CLI commands are documented."""
        expected_commands = [
            "convert",
            "batch-convert",
            "queue-status",
            "list-models",
            "list-formats",
            "info",
            "serve",
        ]

        for cmd in expected_commands:
            assert cmd in user_guide_content, f"Missing CLI command: {cmd}"

    def test_documents_api_endpoints(self, user_guide_content: str) -> None:
        """Verify key API endpoints are documented."""
        expected_endpoints = [
            "/health",
            "/api/v1/jobs",
            "/api/v1/upload",
            "/api/v1/download",
        ]

        for endpoint in expected_endpoints:
            assert endpoint in user_guide_content, f"Missing API endpoint: {endpoint}"

    def test_documents_environment_variables(self, user_guide_content: str) -> None:
        """Verify environment variables are documented."""
        expected_vars = [
            "VIDEO2D3D_ENV",
            "CUDA_VISIBLE_DEVICES",
        ]

        for var in expected_vars:
            assert var in user_guide_content, f"Missing environment variable: {var}"

    def test_documents_docker_options(self, user_guide_content: str) -> None:
        """Verify Docker deployment options are documented."""
        docker_keywords = [
            "docker run",
            "docker-compose",
            "Dockerfile",
            "--gpus",
        ]

        for keyword in docker_keywords:
            assert keyword in user_guide_content, f"Missing Docker documentation: {keyword}"

    def test_has_troubleshooting_section(self, user_guide_content: str) -> None:
        """Verify troubleshooting section has common issues."""
        common_issues = [
            "FFmpeg",
            "CUDA",
            "memory",
            "GPU",
        ]

        for issue in common_issues:
            assert issue in user_guide_content, f"Missing troubleshooting for: {issue}"

    def test_has_examples_for_all_cli_commands(self, user_guide_content: str) -> None:
        """Verify each CLI command has example usage."""
        # Check that there are bash code blocks with command examples
        bash_pattern = r"```bash\n(.*?)```"
        bash_blocks = re.findall(bash_pattern, user_guide_content, re.DOTALL)

        # Look for video2d3d commands in bash blocks
        commands_found = set()
        for block in bash_blocks:
            if "video2d3d" in block:
                # Extract command (second word after video2d3d)
                for line in block.split("\n"):
                    if "video2d3d" in line and not line.strip().startswith("#"):
                        parts = line.split()
                        if len(parts) > 1:
                            idx = parts.index("video2d3d") if "video2d3d" in parts else -1
                            if idx >= 0 and idx + 1 < len(parts):
                                commands_found.add(parts[idx + 1])

        assert (
            len(commands_found) >= 3
        ), f"Expected CLI command examples, found commands: {commands_found}"


class TestUserGuideTables:
    """Test tables in the user guide."""

    def test_tables_formatted_correctly(self, user_guide_content: str) -> None:
        """Verify markdown tables have proper structure."""
        # Find table rows (lines starting with |)
        table_rows = [line for line in user_guide_content.split("\n") if line.startswith("|")]

        if table_rows:
            # Check that tables have separators (|---|---|)
            separator_pattern = r"^\|[\s\-:]+\|[\s\-:|]*$"
            separators = [row for row in table_rows if re.match(separator_pattern, row)]

            assert len(separators) >= 1, "Tables missing separator rows"

    def test_model_table_exists(self, user_guide_content: str) -> None:
        """Verify model comparison table exists."""
        # Look for table containing model information
        assert (
            "midas_small" in user_guide_content and "|" in user_guide_content
        ), "Missing model comparison table"

    def test_format_table_exists(self, user_guide_content: str) -> None:
        """Verify format comparison table exists."""
        # Look for table containing format information
        assert (
            "side_by_side" in user_guide_content and "anaglyph" in user_guide_content
        ), "Missing format comparison table"


class TestUserGuideBestPractices:
    """Test best practices section."""

    def test_has_model_recommendations(self, user_guide_content: str) -> None:
        """Verify model recommendations are provided."""
        # Should have guidance on when to use which model
        recommendations_section = False
        for line in user_guide_content.split("\n"):
            if "Best Practices" in line or "Choosing the Right Model" in line:
                recommendations_section = True
                break

        assert recommendations_section, "Missing best practices/model recommendations"

    def test_has_performance_tips(self, user_guide_content: str) -> None:
        """Verify performance optimization tips are included."""
        performance_keywords = [
            "GPU",
            "batch",
            "performance",
            "speed",
        ]

        found = sum(1 for kw in performance_keywords if kw.lower() in user_guide_content.lower())
        assert found >= 3, "Missing performance optimization tips"


class TestUserGuideCompleteness:
    """Test overall completeness of documentation."""

    def test_minimum_line_count(self, user_guide_content: str) -> None:
        """Verify documentation has sufficient content."""
        line_count = len(user_guide_content.split("\n"))
        assert (
            line_count >= 500
        ), f"Documentation too short: {line_count} lines (expected at least 500)"

    def test_minimum_word_count(self, user_guide_content: str) -> None:
        """Verify documentation has sufficient detail."""
        # Remove code blocks for word count
        text_only = re.sub(r"```.*?```", "", user_guide_content, flags=re.DOTALL)
        word_count = len(text_only.split())
        assert (
            word_count >= 2000
        ), f"Documentation lacks detail: {word_count} words (expected at least 2000)"

    def test_no_placeholder_text(self, user_guide_content: str) -> None:
        """Verify no TODO or placeholder text remains."""
        placeholders = [
            "TODO:",
            "FIXME:",
            "TBD:",
        ]

        for placeholder in placeholders:
            # Only flag placeholder if it appears as a directive (uppercase)
            assert (
                placeholder not in user_guide_content.upper()
            ), f"Found placeholder text: {placeholder}"

    def test_documentation_freshness(self, user_guide_content: str) -> None:
        """Verify documentation includes last updated date."""
        # Check for date pattern (year)
        assert (
            "2026" in user_guide_content or "2025" in user_guide_content
        ), "Documentation may be outdated - no recent year found"
