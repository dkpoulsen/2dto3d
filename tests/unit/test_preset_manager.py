"""Tests for preset manager functionality.

This module tests the PresetManager class including:
- CRUD operations (create, read, update, delete)
- Search and filtering
- Import/export
- Config integration
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video2d3d.presets.manager import (
    PresetManager,
    PresetManagerError,
    get_preset_manager,
)
from video2d3d.presets.models import (
    Preset,
    PresetCategory,
    PresetSettings,
    DepthEstimationSettings,
    StereoGenerationSettings,
    VideoOutputSettings,
    ProcessingSettings,
    QualitySettings,
)


class TestPresetManagerInit:
    """Tests for PresetManager initialization."""

    def test_init_with_default_storage(self):
        """Test initialization with default storage."""
        manager = PresetManager()
        assert manager.storage is not None

    def test_init_with_custom_storage(self, tmp_path: Path):
        """Test initialization with custom storage."""
        from video2d3d.presets.storage import PresetStorage

        storage = PresetStorage(presets_dir=tmp_path / "presets")
        manager = PresetManager(storage=storage)
        assert manager.storage == storage

    def test_init_with_presets_dir(self, tmp_path: Path):
        """Test initialization with custom presets directory."""
        manager = PresetManager(presets_dir=tmp_path / "custom_presets")
        assert manager.storage.presets_dir == tmp_path / "custom_presets"


class TestPresetManagerCreate:
    """Tests for creating presets."""

    def test_create_basic_preset(self, tmp_path: Path):
        """Test creating a basic preset."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        preset = manager.create(name="Test Preset")

        assert preset.id is not None
        assert preset.name == "Test Preset"
        assert preset.category == PresetCategory.CUSTOM

    def test_create_preset_with_all_options(self, tmp_path: Path):
        """Test creating a preset with all options."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        settings = PresetSettings(depth_estimation=DepthEstimationSettings(model="dpt_large"))

        preset = manager.create(
            name="Full Preset",
            settings=settings,
            category=PresetCategory.CINEMA,
            description="A complete preset",
            tags=["4k", "hdr"],
            author="Test Author",
        )

        assert preset.name == "Full Preset"
        assert preset.category == PresetCategory.CINEMA
        assert preset.description == "A complete preset"
        assert "4k" in preset.tags
        assert preset.author == "Test Author"
        assert preset.settings.depth_estimation.model == "dpt_large"

    def test_create_duplicate_name_raises_error(self, tmp_path: Path):
        """Test that creating preset with duplicate name raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Unique Name")

        with pytest.raises(PresetManagerError, match="already exists"):
            manager.create(name="Unique Name")

    def test_create_duplicate_name_case_insensitive(self, tmp_path: Path):
        """Test that duplicate name check is case-insensitive."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Test Preset")

        with pytest.raises(PresetManagerError, match="already exists"):
            manager.create(name="TEST PRESET")

    def test_create_increments_cache(self, tmp_path: Path):
        """Test that creating updates the cache."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        manager.create(name="Cache Test")
        presets = manager._get_cached_presets()

        assert len(presets) == 1


class TestPresetManagerGet:
    """Tests for getting presets."""

    def test_get_by_id(self, tmp_path: Path):
        """Test getting a preset by ID."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        created = manager.create(name="Get Test")

        loaded = manager.get(created.id)

        assert loaded is not None
        assert loaded.id == created.id
        assert loaded.name == "Get Test"

    def test_get_by_id_nonexistent_returns_none(self, tmp_path: Path):
        """Test getting nonexistent preset returns None."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        result = manager.get("nonexistent-id")

        assert result is None

    def test_get_by_name(self, tmp_path: Path):
        """Test getting a preset by name."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Find By Name")

        preset = manager.get_by_name("Find By Name")

        assert preset is not None
        assert preset.name == "Find By Name"

    def test_get_by_name_case_insensitive(self, tmp_path: Path):
        """Test that get_by_name is case-insensitive."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Case Test")

        preset = manager.get_by_name("CASE TEST")

        assert preset is not None
        assert preset.name == "Case Test"

    def test_get_by_name_nonexistent_returns_none(self, tmp_path: Path):
        """Test getting nonexistent preset by name returns None."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        result = manager.get_by_name("Nonexistent")

        assert result is None


class TestPresetManagerUpdate:
    """Tests for updating presets."""

    def test_update_name(self, tmp_path: Path):
        """Test updating preset name."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Original Name")

        updated = manager.update(preset.id, name="New Name")

        assert updated.name == "New Name"

    def test_update_description(self, tmp_path: Path):
        """Test updating preset description."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Update Test")

        updated = manager.update(preset.id, description="New description")

        assert updated.description == "New description"

    def test_update_category(self, tmp_path: Path):
        """Test updating preset category."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Category Test")

        updated = manager.update(preset.id, category=PresetCategory.VR)

        assert updated.category == PresetCategory.VR

    def test_update_settings(self, tmp_path: Path):
        """Test updating preset settings."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Settings Update")
        new_settings = PresetSettings(video_output=VideoOutputSettings(crf=18))

        updated = manager.update(preset.id, settings=new_settings)

        assert updated.settings.video_output.crf == 18

    def test_update_nonexistent_raises_error(self, tmp_path: Path):
        """Test updating nonexistent preset raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        with pytest.raises(PresetManagerError, match="not found"):
            manager.update("nonexistent-id", name="New Name")

    def test_update_builtin_raises_error(self, tmp_path: Path):
        """Test updating built-in preset raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        # Create a preset and mark as built-in
        preset = manager.create(name="Built-in Test")
        # Manually mark as builtin in storage
        loaded = manager.get(preset.id)
        loaded.is_builtin = True
        manager.storage.save = lambda p: None  # Mock save to prevent overwrite

        with pytest.raises(PresetManagerError, match="Cannot update built-in preset"):
            manager.update(preset.id, name="New Name")

    def test_update_duplicate_name_raises_error(self, tmp_path: Path):
        """Test updating to duplicate name raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset1 = manager.create(name="First")
        preset2 = manager.create(name="Second")

        with pytest.raises(PresetManagerError, match="already exists"):
            manager.update(preset2.id, name="First")

    def test_update_updates_timestamp(self, tmp_path: Path):
        """Test that update changes updated_at timestamp."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Timestamp Test")
        original_updated = preset.updated_at

        import time

        time.sleep(0.01)  # Ensure timestamp difference
        updated = manager.update(preset.id, description="Changed")

        assert updated.updated_at != original_updated


class TestPresetManagerDelete:
    """Tests for deleting presets."""

    def test_delete_existing_preset(self, tmp_path: Path):
        """Test deleting an existing preset."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="To Delete")

        result = manager.delete(preset.id)

        assert result is True
        assert manager.get(preset.id) is None

    def test_delete_nonexistent_returns_false(self, tmp_path: Path):
        """Test deleting nonexistent preset returns False."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        result = manager.delete("nonexistent-id")

        assert result is False


class TestPresetManagerDuplicate:
    """Tests for duplicating presets."""

    def test_duplicate_creates_copy(self, tmp_path: Path):
        """Test that duplicate creates a copy with different ID."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        original = manager.create(
            name="Original",
            description="Original description",
            category=PresetCategory.VR,
            tags=["test"],
        )

        duplicate = manager.duplicate(original.id)

        assert duplicate.id != original.id
        assert duplicate.name == "Original (copy)"
        assert duplicate.description == original.description
        assert duplicate.category == original.category
        assert duplicate.tags == original.tags

    def test_duplicate_with_custom_name(self, tmp_path: Path):
        """Test duplicate with custom name."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        original = manager.create(name="Original")

        duplicate = manager.duplicate(original.id, new_name="Custom Copy Name")

        assert duplicate.name == "Custom Copy Name"

    def test_duplicate_creates_independent_settings(self, tmp_path: Path):
        """Test that duplicate creates independent settings copy."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        original = manager.create(
            name="Settings Test",
            settings=PresetSettings(video_output=VideoOutputSettings(crf=20)),
        )

        duplicate = manager.duplicate(original.id)

        # Modify original should not affect duplicate
        manager.update(
            original.id, settings=PresetSettings(video_output=VideoOutputSettings(crf=30))
        )

        # Reload duplicate to verify independence
        reloaded = manager.get(duplicate.id)
        assert reloaded.settings.video_output.crf == 20

    def test_duplicate_nonexistent_raises_error(self, tmp_path: Path):
        """Test duplicating nonexistent preset raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        with pytest.raises(PresetManagerError, match="not found"):
            manager.duplicate("nonexistent-id")


class TestPresetManagerList:
    """Tests for listing presets."""

    def test_list_all(self, tmp_path: Path):
        """Test listing all presets."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Preset 1")
        manager.create(name="Preset 2")
        manager.create(name="Preset 3")

        presets = manager.list_all()

        assert len(presets) == 3

    def test_list_by_category(self, tmp_path: Path):
        """Test listing presets by category."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Cinema 1", category=PresetCategory.CINEMA)
        manager.create(name="Cinema 2", category=PresetCategory.CINEMA)
        manager.create(name="VR 1", category=PresetCategory.VR)

        cinema = manager.list_by_category(PresetCategory.CINEMA)

        assert len(cinema) == 2
        names = [p.name for p in cinema]
        assert "Cinema 1" in names
        assert "Cinema 2" in names


class TestPresetManagerSearch:
    """Tests for searching presets."""

    def test_search_by_name(self, tmp_path: Path):
        """Test searching by name."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Cinema Quality")
        manager.create(name="VR Optimized")
        manager.create(name="Web Streaming")

        results = manager.search("cinema")

        assert len(results) == 1
        assert results[0].name == "Cinema Quality"

    def test_search_by_description(self, tmp_path: Path):
        """Test searching by description."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Preset 1", description="For high quality output")
        manager.create(name="Preset 2", description="For fast processing")

        results = manager.search("high quality")

        assert len(results) == 1
        assert results[0].name == "Preset 1"

    def test_search_case_insensitive(self, tmp_path: Path):
        """Test that search is case-insensitive."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Test Preset")

        results = manager.search("TEST")

        assert len(results) == 1

    def test_search_with_category_filter(self, tmp_path: Path):
        """Test search with category filter."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(
            name="Cinema Test",
            description="Test preset",
            category=PresetCategory.CINEMA,
        )
        manager.create(
            name="VR Test",
            description="Test preset",
            category=PresetCategory.VR,
        )

        results = manager.search("Test", category=PresetCategory.VR)

        assert len(results) == 1
        assert results[0].name == "VR Test"

    def test_search_with_tags_filter(self, tmp_path: Path):
        """Test search with tags filter."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="HD Preset", tags=["hd", "quality"])
        manager.create(name="4K Preset", tags=["4k", "quality"])

        results = manager.search("", tags=["4k"])

        assert len(results) == 1
        assert results[0].name == "4K Preset"

    def test_search_no_results(self, tmp_path: Path):
        """Test search with no matching results."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        manager.create(name="Test Preset")

        results = manager.search("nonexistent")

        assert results == []


class TestPresetManagerImportExport:
    """Tests for import/export functionality."""

    def test_export_preset(self, tmp_path: Path):
        """Test exporting a preset."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Export Test")

        export_path = tmp_path / "exports" / "exported.json"
        result = manager.export_preset(preset.id, export_path)

        assert result.exists()

    def test_export_nonexistent_raises_error(self, tmp_path: Path):
        """Test exporting nonexistent preset raises error."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        export_path = tmp_path / "export.json"

        with pytest.raises(PresetManagerError, match="not found"):
            manager.export_preset("nonexistent-id", export_path)

    def test_import_preset(self, tmp_path: Path):
        """Test importing a preset."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        # Create import file
        import_preset = Preset(
            id="imported-id",
            name="Imported",
            category=PresetCategory.WEB,
        )
        import_path = tmp_path / "import.json"
        import_path.write_text(import_preset.to_json())

        result = manager.import_preset(import_path)

        assert result.id == "imported-id"
        assert manager.get("imported-id") is not None


class TestPresetManagerConfigIntegration:
    """Tests for config integration."""

    def test_apply_preset_to_config(self, tmp_path: Path):
        """Test applying preset settings to config."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        settings = PresetSettings(
            depth_estimation=DepthEstimationSettings(model="dpt_large"),
            stereo_generation=StereoGenerationSettings(
                format="anaglyph",
                baseline=0.08,
            ),
            video_output=VideoOutputSettings(crf=18),
            processing=ProcessingSettings(batch_size=2),
            quality=QualitySettings(preset="quality"),
        )
        preset = manager.create(name="Config Test", settings=settings)

        # Create a mock config
        from video2d3d.utils.config import Config

        config = Config()

        updated_config = manager.apply_preset_to_config(preset, config)

        assert updated_config.depth_estimation.model == "dpt_large"
        assert updated_config.stereo_generation.format == "anaglyph"
        assert updated_config.video_output.crf == 18
        assert updated_config.processing.batch_size == 2
        assert updated_config.quality.preset == "quality"

    def test_create_preset_from_config(self, tmp_path: Path):
        """Test creating preset from config."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        # Create a mock config
        from video2d3d.utils.config import Config

        config = Config()
        config.depth_estimation.model = "dpt_hybrid"
        config.video_output.crf = 20
        config.processing.batch_size = 8

        preset = manager.create_preset_from_config(
            name="From Config",
            config=config,
            category=PresetCategory.CUSTOM,
            description="Created from config",
            tags=["config"],
        )

        assert preset.name == "From Config"
        assert preset.settings.depth_estimation.model == "dpt_hybrid"
        assert preset.settings.video_output.crf == 20
        assert preset.settings.processing.batch_size == 8


class TestGetPresetManager:
    """Tests for get_preset_manager singleton."""

    def test_returns_manager_instance(self):
        """Test that get_preset_manager returns PresetManager."""
        manager = get_preset_manager()
        assert isinstance(manager, PresetManager)

    def test_returns_same_instance(self):
        """Test that get_preset_manager returns same instance."""
        manager1 = get_preset_manager()
        manager2 = get_preset_manager()
        assert manager1 is manager2

    def test_reload_creates_new_instance(self):
        """Test that reload=True creates new instance."""
        manager1 = get_preset_manager()
        manager2 = get_preset_manager(reload=True)
        assert manager1 is not manager2


class TestPresetManagerCache:
    """Tests for caching functionality."""

    def test_cache_invalidated_on_create(self, tmp_path: Path):
        """Test that cache is invalidated on create."""
        manager = PresetManager(presets_dir=tmp_path / "presets")

        # Prime the cache
        manager._get_cached_presets()
        manager.create(name="Cache Test")

        # Cache should be updated
        cached = manager._get_cached_presets()
        assert "Cache Test" in [p.name for p in cached.values()]

    def test_cache_invalidated_on_update(self, tmp_path: Path):
        """Test that cache is invalidated on update."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Update Cache")

        manager.update(preset.id, name="Updated Name")

        # Cache should reflect update
        cached = manager._get_cached_presets()
        found = [p for p in cached.values() if p.id == preset.id]
        assert found[0].name == "Updated Name"

    def test_cache_invalidated_on_delete(self, tmp_path: Path):
        """Test that cache is invalidated on delete."""
        manager = PresetManager(presets_dir=tmp_path / "presets")
        preset = manager.create(name="Delete Cache")

        manager.delete(preset.id)

        # Cache should not contain deleted preset
        cached = manager._get_cached_presets()
        assert preset.id not in cached
