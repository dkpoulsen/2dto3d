"""Tests for preset storage functionality.

This module tests the PresetStorage class including:
- Saving and loading presets
- Atomic writes
- Import/export functionality
- Listing and searching presets
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.presets.models import (
    Preset,
    PresetCategory,
    PresetSettings,
    DepthEstimationSettings,
)
from video2d3d.presets.storage import PresetStorage, PresetStorageError


class TestPresetStorageInit:
    """Tests for PresetStorage initialization."""

    def test_init_creates_presets_directory(self, tmp_path: Path):
        """Test that initialization creates the presets directory."""
        presets_dir = tmp_path / "presets"
        assert not presets_dir.exists()

        storage = PresetStorage(presets_dir=presets_dir)
        assert presets_dir.exists()
        assert storage.presets_dir == presets_dir

    def test_init_with_custom_directories(self, tmp_path: Path):
        """Test initialization with custom directories."""
        presets_dir = tmp_path / "user_presets"
        builtin_dir = tmp_path / "builtins"

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )
        assert storage.presets_dir == presets_dir
        assert storage.builtin_presets_dir == builtin_dir

    def test_default_directories(self):
        """Test that default directories are set correctly."""
        storage = PresetStorage()
        assert storage.presets_dir is not None
        assert storage.builtin_presets_dir is not None


class TestPresetStorageSave:
    """Tests for saving presets."""

    def test_save_creates_file(self, tmp_path: Path):
        """Test that save creates a JSON file."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Test Preset", description="A test")

        file_path = storage.save(preset)

        assert file_path.exists()
        assert file_path.suffix == ".json"

    def test_save_file_contains_preset_data(self, tmp_path: Path):
        """Test that saved file contains preset data."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(
            name="My Preset",
            description="Test description",
            category=PresetCategory.VR,
        )

        file_path = storage.save(preset)

        with open(file_path) as f:
            data = json.load(f)

        assert data["name"] == "My Preset"
        assert data["description"] == "Test description"
        assert data["category"] == "vr"

    def test_save_builtin_preset_raises_error(self, tmp_path: Path):
        """Test that saving a built-in preset raises an error."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Built-in", is_builtin=True)

        with pytest.raises(PresetStorageError, match="Cannot save built-in preset"):
            storage.save(preset)

    def test_save_overwrites_existing(self, tmp_path: Path):
        """Test that save overwrites existing preset with same ID."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(id="same-id", name="Original")

        storage.save(preset)

        # Modify and save again
        preset.name = "Updated"
        file_path = storage.save(preset)

        # Load and verify
        with open(file_path) as f:
            data = json.load(f)
        assert data["name"] == "Updated"

    def test_atomic_write_prevents_corruption(self, tmp_path: Path):
        """Test that atomic write prevents partial file corruption."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Test that _atomic_write creates file correctly
        test_path = tmp_path / "presets" / "test.json"
        content = '{"test": "data"}'
        storage._atomic_write(test_path, content)

        assert test_path.exists()
        with open(test_path) as f:
            assert f.read() == content

    def test_atomic_write_cleanup_on_error(self, tmp_path: Path):
        """Test that atomic write cleans up temp files on error."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Simulate a write error
        with patch("builtins.open", side_effect=IOError("Write failed")):
            with pytest.raises(PresetStorageError, match="Atomic write failed"):
                storage._atomic_write(tmp_path / "presets" / "test.json", '{"test": "data"}')


class TestPresetStorageLoad:
    """Tests for loading presets."""

    def test_load_existing_preset(self, tmp_path: Path):
        """Test loading an existing preset."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Test", description="Load test")
        storage.save(preset)

        loaded = storage.load(preset.id)

        assert loaded is not None
        assert loaded.name == "Test"
        assert loaded.description == "Load test"

    def test_load_nonexistent_preset_returns_none(self, tmp_path: Path):
        """Test loading a nonexistent preset returns None."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        result = storage.load("nonexistent-id")

        assert result is None

    def test_load_sets_is_builtin_false_for_user_preset(self, tmp_path: Path):
        """Test that loaded user preset has is_builtin=False."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="User Preset")
        storage.save(preset)

        loaded = storage.load(preset.id)

        assert loaded.is_builtin is False

    def test_load_malformed_json_returns_none(self, tmp_path: Path):
        """Test that malformed JSON file returns None."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        presets_dir = tmp_path / "presets"
        presets_dir.mkdir(exist_ok=True)

        # Create malformed JSON file
        bad_file = presets_dir / "bad-preset.json"
        bad_file.write_text("{invalid json}")

        result = storage.load("bad-preset")

        assert result is None

    def test_load_from_builtin_dir(self, tmp_path: Path):
        """Test loading a preset from built-in directory."""
        presets_dir = tmp_path / "presets"
        builtin_dir = tmp_path / "builtins"
        builtin_dir.mkdir(parents=True)

        # Create a built-in preset file
        builtin_preset = Preset(
            id="builtin-test",
            name="Built-in Test",
            is_builtin=True,
        )
        with open(builtin_dir / "builtin-test.json", "w") as f:
            json.dump(builtin_preset.to_dict(), f)

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )

        loaded = storage.load("builtin-test")

        assert loaded is not None
        assert loaded.name == "Built-in Test"
        assert loaded.is_builtin is True


class TestPresetStorageDelete:
    """Tests for deleting presets."""

    def test_delete_existing_preset(self, tmp_path: Path):
        """Test deleting an existing preset."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="To Delete")
        storage.save(preset)

        result = storage.delete(preset.id)

        assert result is True
        assert storage.load(preset.id) is None

    def test_delete_nonexistent_preset_returns_false(self, tmp_path: Path):
        """Test deleting a nonexistent preset returns False."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        result = storage.delete("nonexistent-id")

        assert result is False

    def test_delete_builtin_preset_raises_error(self, tmp_path: Path):
        """Test that deleting a built-in preset raises an error."""
        presets_dir = tmp_path / "presets"
        builtin_dir = tmp_path / "builtins"
        builtin_dir.mkdir(parents=True)

        # Create a built-in preset file
        builtin_preset = Preset(
            id="builtin-delete-test",
            name="Built-in",
            is_builtin=True,
        )
        with open(builtin_dir / "builtin-delete-test.json", "w") as f:
            json.dump(builtin_preset.to_dict(), f)

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )

        with pytest.raises(PresetStorageError, match="Cannot delete built-in preset"):
            storage.delete("builtin-delete-test")


class TestPresetStorageList:
    """Tests for listing presets."""

    def test_list_all_empty(self, tmp_path: Path):
        """Test listing when no presets exist."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        presets = storage.list_all()

        assert presets == []

    def test_list_all_returns_all_presets(self, tmp_path: Path):
        """Test that list_all returns all presets."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset1 = Preset(name="Preset 1")
        preset2 = Preset(name="Preset 2")
        storage.save(preset1)
        storage.save(preset2)

        presets = storage.list_all()

        assert len(presets) == 2
        names = [p.name for p in presets]
        assert "Preset 1" in names
        assert "Preset 2" in names

    def test_list_all_excludes_builtins_when_false(self, tmp_path: Path):
        """Test that list_all can exclude built-in presets."""
        presets_dir = tmp_path / "presets"
        builtin_dir = tmp_path / "builtins"
        builtin_dir.mkdir(parents=True)

        # Create user preset
        user_preset = Preset(id="user-1", name="User Preset")
        with open(presets_dir / "user-1.json", "w") as f:
            json.dump(user_preset.to_dict(), f)

        # Create built-in preset
        builtin_preset = Preset(id="builtin-1", name="Built-in", is_builtin=True)
        with open(builtin_dir / "builtin-1.json", "w") as f:
            json.dump(builtin_preset.to_dict(), f)

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )

        all_presets = storage.list_all(include_builtins=True)
        user_only = storage.list_all(include_builtins=False)

        assert len(all_presets) == 2
        assert len(user_only) == 1
        assert user_only[0].name == "User Preset"

    def test_list_by_category(self, tmp_path: Path):
        """Test listing presets by category."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        cinema = Preset(name="Cinema", category=PresetCategory.CINEMA)
        vr = Preset(name="VR", category=PresetCategory.VR)
        web = Preset(name="Web", category=PresetCategory.WEB)
        storage.save(cinema)
        storage.save(vr)
        storage.save(web)

        vr_presets = storage.list_by_category("vr")

        assert len(vr_presets) == 1
        assert vr_presets[0].name == "VR"

    def test_list_by_category_case_insensitive(self, tmp_path: Path):
        """Test that category filtering is case-insensitive."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Cinema", category=PresetCategory.CINEMA)
        storage.save(preset)

        # Should work with uppercase
        presets = storage.list_by_category("CINEMA")
        assert len(presets) == 1

    def test_user_preset_overrides_builtin_by_id(self, tmp_path: Path):
        """Test that user preset with same ID overrides built-in."""
        presets_dir = tmp_path / "presets"
        builtin_dir = tmp_path / "builtins"
        builtin_dir.mkdir(parents=True)
        presets_dir.mkdir(parents=True)

        # Create built-in preset
        builtin = Preset(id="shared-id", name="Built-in", is_builtin=True)
        with open(builtin_dir / "shared-id.json", "w") as f:
            json.dump(builtin.to_dict(), f)

        # Create user preset with same ID
        user = Preset(id="shared-id", name="User Override", is_builtin=False)
        with open(presets_dir / "shared-id.json", "w") as f:
            json.dump(user.to_dict(), f)

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )

        presets = storage.list_all()
        assert len(presets) == 1
        assert presets[0].name == "User Override"
        assert presets[0].is_builtin is False


class TestPresetStorageExists:
    """Tests for checking preset existence."""

    def test_exists_returns_true_for_existing(self, tmp_path: Path):
        """Test exists returns True for existing preset."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Test")
        storage.save(preset)

        assert storage.exists(preset.id) is True

    def test_exists_returns_false_for_nonexistent(self, tmp_path: Path):
        """Test exists returns False for nonexistent preset."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        assert storage.exists("nonexistent-id") is False

    def test_exists_checks_both_directories(self, tmp_path: Path):
        """Test exists checks both user and built-in directories."""
        presets_dir = tmp_path / "presets"
        builtin_dir = tmp_path / "builtins"
        builtin_dir.mkdir(parents=True)

        # Create built-in preset only
        builtin = Preset(id="builtin-only", name="Built-in", is_builtin=True)
        with open(builtin_dir / "builtin-only.json", "w") as f:
            json.dump(builtin.to_dict(), f)

        storage = PresetStorage(
            presets_dir=presets_dir,
            builtin_presets_dir=builtin_dir,
        )

        assert storage.exists("builtin-only") is True


class TestPresetStorageImportExport:
    """Tests for import/export functionality."""

    def test_export_preset(self, tmp_path: Path):
        """Test exporting a preset to a file."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(
            name="Export Test",
            description="Testing export",
            category=PresetCategory.WEB,
        )
        storage.save(preset)

        export_path = tmp_path / "exports" / "exported.json"
        result = storage.export_preset(preset.id, export_path)

        assert result.exists()
        with open(result) as f:
            data = json.load(f)
        assert data["name"] == "Export Test"

    def test_export_nonexistent_preset_raises_error(self, tmp_path: Path):
        """Test exporting a nonexistent preset raises error."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        export_path = tmp_path / "export.json"

        with pytest.raises(PresetStorageError, match="not found"):
            storage.export_preset("nonexistent-id", export_path)

    def test_import_preset(self, tmp_path: Path):
        """Test importing a preset from a file."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Create a preset file to import
        import_preset = Preset(
            id="imported-id",
            name="Imported Preset",
            description="Imported from file",
        )
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(import_preset.to_dict(), f)

        result = storage.import_preset(import_path)

        assert result.id == "imported-id"
        assert result.name == "Imported Preset"
        assert storage.exists("imported-id")

    def test_import_preset_sets_is_builtin_false(self, tmp_path: Path):
        """Test that imported preset has is_builtin=False."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Create a preset file marked as built-in
        import_preset = Preset(
            id="imported-builtin",
            name="Was Built-in",
            is_builtin=True,  # This should be ignored
        )
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(import_preset.to_dict(), f)

        result = storage.import_preset(import_path)

        assert result.is_builtin is False

    def test_import_duplicate_raises_error(self, tmp_path: Path):
        """Test that importing duplicate preset raises error."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Create existing preset
        existing = Preset(id="duplicate-id", name="Existing")
        storage.save(existing)

        # Try to import preset with same ID
        import_preset = Preset(id="duplicate-id", name="Import")
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(import_preset.to_dict(), f)

        with pytest.raises(PresetStorageError, match="already exists"):
            storage.import_preset(import_path)

    def test_import_duplicate_with_overwrite(self, tmp_path: Path):
        """Test that importing with overwrite replaces existing."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")

        # Create existing preset
        existing = Preset(id="overwrite-id", name="Original")
        storage.save(existing)

        # Import with overwrite
        import_preset = Preset(id="overwrite-id", name="Replacement")
        import_path = tmp_path / "import.json"
        with open(import_path, "w") as f:
            json.dump(import_preset.to_dict(), f)

        result = storage.import_preset(import_path, overwrite=True)

        assert result.name == "Replacement"
        loaded = storage.load("overwrite-id")
        assert loaded.name == "Replacement"

    def test_import_invalid_json_raises_error(self, tmp_path: Path):
        """Test that importing invalid JSON raises error."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        import_path = tmp_path / "invalid.json"
        import_path.write_text("{invalid json}")

        with pytest.raises(PresetStorageError, match="Invalid preset file format"):
            storage.import_preset(import_path)


class TestPresetStorageBackup:
    """Tests for backup functionality."""

    def test_backup_to_directory(self, tmp_path: Path):
        """Test creating backup to a directory."""
        storage = PresetStorage(presets_dir=tmp_path / "presets")
        preset = Preset(name="Backup Test")
        storage.save(preset)

        backup_dir = tmp_path / "backups"
        result = storage.backup_presets(backup_dir)

        assert backup_dir.exists()
        assert (backup_dir / "presets").exists()
