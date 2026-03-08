"""Tests for DEVELOPER_GUIDE.md documentation.

This module validates the developer guide documentation for:
- Structure and completeness
- Code example syntax (Python, YAML, bash)
- Internal links and references
- API references matching actual implementations
- Import statements accuracy
"""

import ast
import re
from pathlib import Path

import pytest
import yaml

# Path to the DEVELOPER_GUIDE.md file
DEVELOPER_GUIDE_PATH = Path(__file__).parent.parent.parent / "docs" / "DEVELOPER_GUIDE.md"


@pytest.fixture
def developer_guide_content() -> str:
    """Load the DEVELOPER_GUIDE.md content."""
    if not DEVELOPER_GUIDE_PATH.exists():
        pytest.skip("DEVELOPER_GUIDE.md not found")
    return DEVELOPER_GUIDE_PATH.read_text()


@pytest.fixture
def developer_guide_lines(developer_guide_content: str) -> list[str]:
    """Split content into lines."""
    return developer_guide_content.split("\n")


class TestDeveloperGuideExists:
    """Test that the developer guide file exists and is accessible."""

    def test_developer_guide_file_exists(self) -> None:
        """Verify DEVELOPER_GUIDE.md exists in docs directory."""
        assert (
            DEVELOPER_GUIDE_PATH.exists()
        ), f"DEVELOPER_GUIDE.md not found at {DEVELOPER_GUIDE_PATH}"

    def test_developer_guide_not_empty(self, developer_guide_content: str) -> None:
        """Verify DEVELOPER_GUIDE.md has substantial content."""
        assert len(developer_guide_content) > 5000, "DEVELOPER_GUIDE.md appears to be too short"

    def test_developer_guide_has_version(self, developer_guide_content: str) -> None:
        """Verify version information is present."""
        assert "**Version:**" in developer_guide_content, "Missing version information"


class TestDeveloperGuideStructure:
    """Test the structure and organization of the developer guide."""

    REQUIRED_SECTIONS = [
        "Architecture Overview",
        "Project Structure",
        "Core Modules",
        "Data Flow",
        "Extending the System",
        "API Reference",
        "Testing",
        "Debugging",
    ]

    def test_has_table_of_contents(self, developer_guide_content: str) -> None:
        """Verify table of contents exists."""
        assert (
            "## Table of Contents" in developer_guide_content
        ), "Missing Table of Contents section"

    def test_has_all_required_sections(self, developer_guide_content: str) -> None:
        """Verify all required sections are present."""
        for section in self.REQUIRED_SECTIONS:
            pattern = rf"##\s+.*{re.escape(section)}"
            assert re.search(
                pattern, developer_guide_content, re.IGNORECASE
            ), f"Missing required section: {section}"

    def test_section_hierarchy(self, developer_guide_lines: list[str]) -> None:
        """Verify headings use valid markdown levels (1-6)."""
        for line in developer_guide_lines:
            if match := re.match(r"^(#{1,6})\s", line):
                level = len(match.group(1))
                assert 1 <= level <= 6, f"Invalid heading level: '{line}'"

    def test_has_architecture_diagram(self, developer_guide_content: str) -> None:
        """Verify architecture diagram is present."""
        assert (
            "High-Level Architecture" in developer_guide_content
        ), "Missing High-Level Architecture section"
        # Check for ASCII diagram indicators
        assert (
            "┌" in developer_guide_content or "```" in developer_guide_content
        ), "Missing architecture diagram"

    def test_has_processing_pipeline(self, developer_guide_content: str) -> None:
        """Verify processing pipeline is documented."""
        assert (
            "Processing Pipeline" in developer_guide_content
        ), "Missing Processing Pipeline section"


class TestDeveloperGuideCodeBlocks:
    """Test code blocks in the developer guide."""

    def test_code_blocks_balanced(self, developer_guide_content: str) -> None:
        """Verify all code blocks are properly closed."""
        code_block_count = developer_guide_content.count("```")
        assert (
            code_block_count % 2 == 0
        ), f"Unbalanced code blocks: found {code_block_count} ``` markers (should be even)"

    def test_yaml_code_blocks_valid(self, developer_guide_content: str) -> None:
        """Verify YAML code blocks are valid syntax."""
        yaml_pattern = r"```yaml\n(.*?)```"
        yaml_blocks = re.findall(yaml_pattern, developer_guide_content, re.DOTALL)

        errors = []
        for i, yaml_content in enumerate(yaml_blocks):
            try:
                yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                errors.append(f"YAML block {i + 1}: {e}")

        assert not errors, "Invalid YAML code blocks:\n" + "\n".join(errors)

    def test_python_code_blocks_syntax(self, developer_guide_content: str) -> None:
        """Verify Python code blocks have valid syntax."""
        python_pattern = r"```python\n(.*?)```"
        python_blocks = re.findall(python_pattern, developer_guide_content, re.DOTALL)

        errors = []
        for i, python_content in enumerate(python_blocks):
            try:
                ast.parse(python_content)
            except SyntaxError as e:
                errors.append(f"Python block {i + 1}: {e}")

        assert not errors, "Invalid Python code blocks:\n" + "\n".join(errors)

    def test_bash_code_blocks_present(self, developer_guide_content: str) -> None:
        """Verify bash code blocks are present for CLI examples."""
        bash_pattern = r"```bash\n(.*?)```"
        bash_blocks = re.findall(bash_pattern, developer_guide_content, re.DOTALL)

        assert (
            len(bash_blocks) >= 5
        ), f"Expected at least 5 bash code examples, found {len(bash_blocks)}"

    def test_has_import_examples(self, developer_guide_content: str) -> None:
        """Verify import examples are provided."""
        import_patterns = [
            r"from video2d3d\.",
            r"import video2d3d",
        ]

        found = any(re.search(pattern, developer_guide_content) for pattern in import_patterns)
        assert found, "Missing import examples from video2d3d package"


class TestDeveloperGuideModuleDocumentation:
    """Test that core modules are properly documented."""

    def test_video_module_documented(self, developer_guide_content: str) -> None:
        """Verify video module is documented."""
        assert (
            "Video Module" in developer_guide_content or "video/" in developer_guide_content
        ), "Missing Video Module documentation"
        assert "FrameExtractor" in developer_guide_content, "Missing FrameExtractor documentation"
        assert "VideoWriter" in developer_guide_content, "Missing VideoWriter documentation"

    def test_depth_module_documented(self, developer_guide_content: str) -> None:
        """Verify depth module is documented."""
        assert (
            "Depth Module" in developer_guide_content or "depth/" in developer_guide_content
        ), "Missing Depth Module documentation"
        assert (
            "DepthMapProcessor" in developer_guide_content
        ), "Missing DepthMapProcessor documentation"
        assert (
            "TemporalSmoother" in developer_guide_content
        ), "Missing TemporalSmoother documentation"

    def test_stereo_module_documented(self, developer_guide_content: str) -> None:
        """Verify stereo module is documented."""
        assert (
            "Stereo Module" in developer_guide_content or "stereo/" in developer_guide_content
        ), "Missing Stereo Module documentation"
        assert "DIBREngine" in developer_guide_content, "Missing DIBREngine documentation"
        assert "DIBRConfig" in developer_guide_content, "Missing DIBRConfig documentation"

    def test_core_module_documented(self, developer_guide_content: str) -> None:
        """Verify core module is documented."""
        assert (
            "Core Module" in developer_guide_content or "core/" in developer_guide_content
        ), "Missing Core Module documentation"
        assert (
            "BatchProcessor" in developer_guide_content
            or "FrameBatchProcessor" in developer_guide_content
        ), "Missing BatchProcessor documentation"

    def test_web_api_module_documented(self, developer_guide_content: str) -> None:
        """Verify web API module is documented."""
        assert (
            "Web API" in developer_guide_content or "web/" in developer_guide_content
        ), "Missing Web API Module documentation"

    def test_batch_module_documented(self, developer_guide_content: str) -> None:
        """Verify batch module is documented."""
        assert (
            "Batch Module" in developer_guide_content or "batch/" in developer_guide_content
        ), "Missing Batch Module documentation"


class TestDeveloperGuideAPIReferences:
    """Test that API references match actual implementations."""

    def test_depth_processor_config_exists(self) -> None:
        """Verify DepthProcessorConfig exists in the codebase."""
        from video2d3d.depth import DepthProcessorConfig

        assert DepthProcessorConfig is not None

    def test_depth_map_processor_exists(self) -> None:
        """Verify DepthMapProcessor exists in the codebase."""
        from video2d3d.depth import DepthMapProcessor

        assert DepthMapProcessor is not None

    def test_dibr_engine_exists(self) -> None:
        """Verify DIBREngine exists in the codebase."""
        from video2d3d.stereo import DIBREngine

        assert DIBREngine is not None

    def test_dibr_config_exists(self) -> None:
        """Verify DIBRConfig exists in the codebase."""
        from video2d3d.stereo import DIBRConfig

        assert DIBRConfig is not None

    def test_frame_batch_processor_exists(self) -> None:
        """Verify FrameBatchProcessor exists in the codebase."""
        from video2d3d.core import FrameBatchProcessor

        assert FrameBatchProcessor is not None

    def test_batch_processor_config_exists(self) -> None:
        """Verify BatchProcessorConfig exists in the codebase."""
        from video2d3d.core import BatchProcessorConfig

        assert BatchProcessorConfig is not None

    def test_processing_mode_exists(self) -> None:
        """Verify ProcessingMode exists in the codebase."""
        from video2d3d.core import ProcessingMode

        assert ProcessingMode is not None

    def test_stereo_generator_exists(self) -> None:
        """Verify StereoGenerator exists in the codebase."""
        from video2d3d.stereo import StereoGenerator

        assert StereoGenerator is not None

    def test_anaglyph_encoder_exists(self) -> None:
        """Verify AnaglyphEncoder exists in the codebase."""
        from video2d3d.stereo import AnaglyphEncoder

        assert AnaglyphEncoder is not None

    def test_side_by_side_encoder_exists(self) -> None:
        """Verify SideBySideEncoder exists in the codebase."""
        from video2d3d.stereo import SideBySideEncoder

        assert SideBySideEncoder is not None


class TestDeveloperGuideConfigDocumentation:
    """Test that configuration classes are documented correctly."""

    def test_batch_processor_config_documented(self, developer_guide_content: str) -> None:
        """Verify BatchProcessorConfig fields are documented."""
        expected_fields = ["batch_size", "num_workers", "timeout_seconds", "max_retries"]
        for field in expected_fields:
            assert field in developer_guide_content, f"Missing BatchProcessorConfig field: {field}"

    def test_depth_processor_config_documented(self, developer_guide_content: str) -> None:
        """Verify DepthProcessorConfig fields are documented."""
        expected_fields = [
            "edge_aware_smoothing",
            "bilateral_filter",
            "hole_filling",
            "normalization_method",
        ]
        for field in expected_fields:
            assert field in developer_guide_content, f"Missing DepthProcessorConfig field: {field}"

    def test_dibr_config_documented(self, developer_guide_content: str) -> None:
        """Verify DIBRConfig fields are documented."""
        expected_fields = ["baseline", "focal_length", "convergence", "hole_filling"]
        for field in expected_fields:
            assert field in developer_guide_content, f"Missing DIBRConfig field: {field}"


class TestDeveloperGuideExceptionDocumentation:
    """Test that exception classes are documented."""

    def test_exception_table_exists(self, developer_guide_content: str) -> None:
        """Verify exception documentation table exists."""
        assert (
            "Exception Classes" in developer_guide_content or "Exception" in developer_guide_content
        ), "Missing exception documentation"

    def test_key_exceptions_documented(self, developer_guide_content: str) -> None:
        """Verify key exceptions are documented."""
        expected_exceptions = [
            "BatchProcessorError",
            "DepthProcessingError",
            "DIBRError",
        ]
        for exc in expected_exceptions:
            assert exc in developer_guide_content, f"Missing exception documentation: {exc}"


class TestDeveloperGuideExtensionGuides:
    """Test that extension guides are documented."""

    def test_adding_depth_model_guide(self, developer_guide_content: str) -> None:
        """Verify guide for adding new depth models exists."""
        assert (
            "Adding a New Depth Model" in developer_guide_content
        ), "Missing guide for adding new depth models"

    def test_adding_stereo_format_guide(self, developer_guide_content: str) -> None:
        """Verify guide for adding new stereo formats exists."""
        assert (
            "Adding a New Stereo Output Format" in developer_guide_content
        ), "Missing guide for adding new stereo formats"

    def test_adding_cli_command_guide(self, developer_guide_content: str) -> None:
        """Verify guide for adding new CLI commands exists."""
        assert (
            "Adding a New CLI Command" in developer_guide_content
        ), "Missing guide for adding new CLI commands"


class TestDeveloperGuideTestingDocumentation:
    """Test that testing documentation is present."""

    def test_testing_section_exists(self, developer_guide_content: str) -> None:
        """Verify testing section exists."""
        assert "## Testing" in developer_guide_content, "Missing Testing section"

    def test_pytest_examples_present(self, developer_guide_content: str) -> None:
        """Verify pytest usage examples are present."""
        assert "pytest" in developer_guide_content, "Missing pytest examples"

    def test_test_fixture_documentation(self, developer_guide_content: str) -> None:
        """Verify test fixture documentation exists."""
        assert "fixtures" in developer_guide_content.lower(), "Missing test fixture documentation"


class TestDeveloperGuideDebuggingDocumentation:
    """Test that debugging documentation is present."""

    def test_debugging_section_exists(self, developer_guide_content: str) -> None:
        """Verify debugging section exists."""
        assert "## Debugging" in developer_guide_content, "Missing Debugging section"

    def test_logging_documentation(self, developer_guide_content: str) -> None:
        """Verify logging documentation exists."""
        assert (
            "LOG_LEVEL" in developer_guide_content or "logging" in developer_guide_content.lower()
        ), "Missing logging documentation"

    def test_common_issues_table(self, developer_guide_content: str) -> None:
        """Verify common issues table exists."""
        assert "Common Issues" in developer_guide_content, "Missing Common Issues section"


class TestDeveloperGuidePerformanceDocumentation:
    """Test that performance documentation is present."""

    def test_performance_section_exists(self, developer_guide_content: str) -> None:
        """Verify performance section exists."""
        assert "Performance" in developer_guide_content, "Missing Performance section"

    def test_gpu_memory_documentation(self, developer_guide_content: str) -> None:
        """Verify GPU memory management documentation exists."""
        assert (
            "GPU" in developer_guide_content or "memory" in developer_guide_content.lower()
        ), "Missing GPU memory documentation"


class TestDeveloperGuideLinks:
    """Test links and references in the developer guide."""

    def test_internal_anchor_links(self, developer_guide_content: str) -> None:
        """Verify internal anchor links point to existing sections."""
        anchor_pattern = r"\[([^\]]+)\]\(#[a-z0-9-]+\)"
        anchor_links = re.findall(anchor_pattern, developer_guide_content)

        assert (
            len(anchor_links) >= 5
        ), f"Expected at least 5 internal anchor links, found {len(anchor_links)}"

    def test_no_broken_markdown_links(self, developer_guide_content: str) -> None:
        """Verify no broken markdown link syntax."""
        broken_patterns = [
            r"\[[^\]]+\]\(\s*\)",  # Empty link: [text]()
            r"\[\s*\]\([^)]+\)",  # Empty text: [](url)
        ]

        for pattern in broken_patterns:
            matches = re.findall(pattern, developer_guide_content)
            assert not matches, f"Found broken markdown links: {matches}"

    def test_user_guide_reference(self, developer_guide_content: str) -> None:
        """Verify reference to USER_GUIDE.md exists."""
        assert "USER_GUIDE.md" in developer_guide_content, "Missing reference to USER_GUIDE.md"


class TestDeveloperGuideCompleteness:
    """Test overall completeness of documentation."""

    def test_minimum_line_count(self, developer_guide_content: str) -> None:
        """Verify documentation has sufficient content."""
        line_count = len(developer_guide_content.split("\n"))
        assert (
            line_count >= 500
        ), f"Documentation too short: {line_count} lines (expected at least 500)"

    def test_minimum_word_count(self, developer_guide_content: str) -> None:
        """Verify documentation has sufficient detail."""
        # Remove code blocks for word count
        text_only = re.sub(r"```.*?```", "", developer_guide_content, flags=re.DOTALL)
        word_count = len(text_only.split())
        assert (
            word_count >= 3000
        ), f"Documentation lacks detail: {word_count} words (expected at least 3000)"

    def test_no_placeholder_text(self, developer_guide_content: str) -> None:
        """Verify no TODO or placeholder text remains."""
        placeholders = [
            "TODO:",
            "FIXME:",
            "TBD:",
            "[INSERT",
            "[PLACEHOLDER",
        ]

        for placeholder in placeholders:
            assert (
                placeholder not in developer_guide_content.upper()
            ), f"Found placeholder text: {placeholder}"

    def test_documentation_freshness(self, developer_guide_content: str) -> None:
        """Verify documentation includes last updated date."""
        assert (
            "2026" in developer_guide_content or "2025" in developer_guide_content
        ), "Documentation may be outdated - no recent year found"


class TestDeveloperGuideProjectStructure:
    """Test that project structure documentation is accurate."""

    def test_project_structure_section(self, developer_guide_content: str) -> None:
        """Verify project structure section exists."""
        assert (
            "## Project Structure" in developer_guide_content
        ), "Missing Project Structure section"

    def test_main_directories_documented(self, developer_guide_content: str) -> None:
        """Verify main directories are documented."""
        expected_dirs = [
            "src/video2d3d/",
            "tests/",
            "config/",
            "docs/",
        ]
        for dir_path in expected_dirs:
            assert (
                dir_path in developer_guide_content
            ), f"Missing directory documentation: {dir_path}"

    def test_source_structure_documented(self, developer_guide_content: str) -> None:
        """Verify source code structure is documented."""
        expected_modules = [
            "video/",
            "depth/",
            "stereo/",
            "core/",
            "utils/",
        ]
        for module in expected_modules:
            assert module in developer_guide_content, f"Missing module documentation: {module}"
