"""Tests for CLI configuration import/export commands."""

import json
import re
from pathlib import Path

import yaml
from typer.testing import CliRunner

from video2d3d.cli import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    """Strip ANSI escape codes so assertions survive colored output."""
    return _ANSI_RE.sub("", text)


class TestConfigExportCLI:
    """Tests for config-export CLI command."""

    def test_export_to_json_auto_detect(self, tmp_path: Path):
        """Test config export with auto-detected JSON format."""
        output_file = tmp_path / "exported_config.json"

        result = runner.invoke(app, ["config-export", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Configuration exported to" in result.stdout

        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
        assert "project_name" in data
        assert "processing" in data

    def test_export_to_yaml_auto_detect(self, tmp_path: Path):
        """Test config export with auto-detected YAML format."""
        output_file = tmp_path / "exported_config.yaml"

        result = runner.invoke(app, ["config-export", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Configuration exported to" in result.stdout

        # Verify YAML content
        with open(output_file) as f:
            data = yaml.safe_load(f)
        assert "project_name" in data

    def test_export_to_yml_extension(self, tmp_path: Path):
        """Test config export with .yml extension."""
        output_file = tmp_path / "config.yml"

        result = runner.invoke(app, ["config-export", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_with_explicit_json_format(self, tmp_path: Path):
        """Test config export with explicit JSON format flag."""
        output_file = tmp_path / "config.txt"  # Ambiguous extension

        result = runner.invoke(app, ["config-export", str(output_file), "--format", "json"])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = json.load(f)
        assert "project_name" in data

    def test_export_with_explicit_yaml_format(self, tmp_path: Path):
        """Test config export with explicit YAML format flag."""
        output_file = tmp_path / "config.txt"  # Ambiguous extension

        result = runner.invoke(app, ["config-export", str(output_file), "--format", "yaml"])

        assert result.exit_code == 0
        assert output_file.exists()

        with open(output_file) as f:
            data = yaml.safe_load(f)
        assert "project_name" in data

    def test_export_auto_detect_unknown_extension_fails(self, tmp_path: Path):
        """Test export fails gracefully for unknown file extension without --format."""
        output_file = tmp_path / "config.xyz"

        result = runner.invoke(app, ["config-export", str(output_file)])

        assert result.exit_code == 1
        assert "Cannot auto-detect format" in result.stdout

    def test_export_invalid_format_fails(self, tmp_path: Path):
        """Test export fails for invalid format."""
        output_file = tmp_path / "config.json"

        result = runner.invoke(app, ["config-export", str(output_file), "--format", "xml"])

        assert result.exit_code == 1
        assert "Unsupported format" in result.stdout
        assert "json" in result.stdout
        assert "yaml" in result.stdout

    def test_export_creates_parent_directories(self, tmp_path: Path):
        """Test that export creates parent directories if they don't exist."""
        output_file = tmp_path / "nested" / "deep" / "dir" / "config.json"

        result = runner.invoke(app, ["config-export", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_format_short_flag(self, tmp_path: Path):
        """Test export with short -f flag for format."""
        output_file = tmp_path / "config.dat"

        result = runner.invoke(app, ["config-export", str(output_file), "-f", "json"])

        assert result.exit_code == 0
        assert output_file.exists()


class TestConfigImportCLI:
    """Tests for config-import CLI command."""

    def test_import_from_json(self, tmp_path: Path):
        """Test config import from JSON file."""
        # Create test config
        config_data = {
            "project_name": "CLIImportTest",
            "version": "4.0.0",
            "processing": {"batch_size": 64},
        }
        config_file = tmp_path / "import_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 0
        assert "Configuration imported" in result.stdout
        assert "CLIImportTest" in result.stdout
        assert "batch_size=64" in result.stdout

    def test_import_from_yaml(self, tmp_path: Path):
        """Test config import from YAML file."""
        yaml_content = """
project_name: YAMLCLIImport
version: "5.0.0"
processing:
  batch_size: 32
"""
        config_file = tmp_path / "import_config.yaml"
        config_file.write_text(yaml_content)

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 0
        assert "Configuration imported" in result.stdout
        assert "YAMLCLIImport" in result.stdout

    def test_import_from_yml_extension(self, tmp_path: Path):
        """Test config import from .yml extension."""
        config_data = {"project_name": "YMLImport"}
        config_file = tmp_path / "config.yml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 0
        assert "YMLImport" in result.stdout

    def test_import_with_apply_flag(self, tmp_path: Path):
        """Test config import with --apply flag."""
        config_data = {
            "project_name": "AppliedCLIConfig",
            "processing": {"batch_size": 128},
        }
        config_file = tmp_path / "apply_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(app, ["config-import", str(config_file), "--apply"])

        assert result.exit_code == 0
        assert "imported and applied" in result.stdout
        assert "AppliedCLIConfig" in result.stdout

    def test_import_apply_short_flag(self, tmp_path: Path):
        """Test config import with short -a flag."""
        config_data = {"project_name": "ShortFlagApply"}
        config_file = tmp_path / "short_apply.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(app, ["config-import", str(config_file), "-a"])

        assert result.exit_code == 0
        assert "imported and applied" in result.stdout

    def test_import_missing_file_fails(self, tmp_path: Path):
        """Test import fails gracefully for missing file."""
        missing_file = tmp_path / "nonexistent.json"

        result = runner.invoke(app, ["config-import", str(missing_file)])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    def test_import_invalid_json_fails(self, tmp_path: Path):
        """Test import fails gracefully for invalid JSON."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{ bad json }")

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_import_unsupported_format_fails(self, tmp_path: Path):
        """Test import fails for unsupported file format."""
        config_file = tmp_path / "config.xml"
        config_file.write_text("<config></config>")

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 1

    def test_import_without_apply_shows_hint(self, tmp_path: Path):
        """Test import without --apply shows hint to use --apply."""
        config_data = {"project_name": "NoApplyTest"}
        config_file = tmp_path / "no_apply.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = runner.invoke(app, ["config-import", str(config_file)])

        assert result.exit_code == 0
        assert "--apply" in result.stdout


class TestConfigExportImportRoundTripCLI:
    """Integration tests for CLI export/import round-trip."""

    def test_cli_roundtrip_json(self, tmp_path: Path):
        """Test round-trip export and import via CLI."""
        # Export
        export_file = tmp_path / "roundtrip.json"
        export_result = runner.invoke(app, ["config-export", str(export_file)])
        assert export_result.exit_code == 0

        # Modify the exported config
        with open(export_file) as f:
            data = json.load(f)
        data["project_name"] = "RoundTripCLI"
        data["processing"]["batch_size"] = 99
        with open(export_file, "w") as f:
            json.dump(data, f)

        # Import with apply
        import_result = runner.invoke(app, ["config-import", str(export_file), "--apply"])
        assert import_result.exit_code == 0
        assert "RoundTripCLI" in import_result.stdout
        assert "batch_size=99" in import_result.stdout

    def test_cli_roundtrip_yaml(self, tmp_path: Path):
        """Test round-trip export and import via CLI with YAML."""
        # Export to YAML
        export_file = tmp_path / "roundtrip.yaml"
        export_result = runner.invoke(app, ["config-export", str(export_file)])
        assert export_result.exit_code == 0

        # Import
        import_result = runner.invoke(app, ["config-import", str(export_file)])
        assert import_result.exit_code == 0
        assert "Configuration imported" in import_result.stdout


class TestCLIHelpAndUsage:
    """Tests for CLI help and usage messages."""

    def test_config_export_help(self):
        """Test config-export help message."""
        result = runner.invoke(app, ["config-export", "--help"])

        assert result.exit_code == 0
        plain = _plain(result.stdout)
        assert "Export the current configuration" in plain
        assert "OUTPUT_FILE" in plain
        assert "--format" in plain

    def test_config_import_help(self):
        """Test config-import help message."""
        result = runner.invoke(app, ["config-import", "--help"])

        assert result.exit_code == 0
        plain = _plain(result.stdout)
        assert "Import configuration" in plain
        assert "INPUT_FILE" in plain
        assert "--apply" in plain

    def test_main_help_shows_config_commands(self):
        """Test that main help shows config commands."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Commands should be listed
        assert "config-export" in result.stdout or "Commands" in result.stdout
