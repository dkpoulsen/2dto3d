"""Preset manager for managing processing presets.

This module provides the PresetManager class which offers a high-level
interface for creating, reading, updating, and deleting presets.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from video2d3d.presets.models import (
    DepthEstimationSettings,
    Preset,
    PresetCategory,
    PresetSettings,
    ProcessingSettings,
    QualitySettings,
    StereoGenerationSettings,
    VideoOutputSettings,
)
from video2d3d.presets.storage import PresetStorage, PresetStorageError
from video2d3d.utils.config import (
    Config,
    DepthEstimationConfig,
    ProcessingConfig,
    QualityConfig,
    StereoGenerationConfig,
    VideoOutputConfig,
)
from video2d3d.utils.logger import get_logger

logger = get_logger("presets.manager")


class PresetManagerError(Exception):
    """Exception raised for preset manager errors."""

    pass


class PresetManager:
    """High-level manager for processing presets.

    Provides a unified interface for managing presets, including:
    - Creating, reading, updating, and deleting presets
    - Applying presets to job configurations
    - Importing and exporting presets
    - Searching and filtering presets
    """

    def __init__(
        self,
        presets_dir: Optional[Path] = None,
        storage: Optional[PresetStorage] = None,
    ):
        """Initialize the preset manager.

        Args:
            presets_dir: Directory for storing presets.
            storage: Custom preset storage instance.
        """
        self.storage = storage or PresetStorage(presets_dir=presets_dir)
        self._cache: Optional[Dict[str, Preset]] = None

    def _invalidate_cache(self) -> None:
        """Invalidate the preset cache."""
        self._cache = None

    def _get_cached_presets(self) -> Dict[str, Preset]:
        """Get cached presets, loading if necessary."""
        if self._cache is None:
            presets = self.storage.list_all(include_builtins=True)
            self._cache = {p.id: p for p in presets}
        return self._cache

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create(
        self,
        name: str,
        settings: Optional[PresetSettings] = None,
        category: PresetCategory = PresetCategory.CUSTOM,
        description: str = "",
        tags: Optional[List[str]] = None,
        author: str = "",
    ) -> Preset:
        """Create a new preset.

        Args:
            name: Preset name (must be unique among user presets).
            settings: Preset settings. Uses defaults if not provided.
            category: Preset category.
            description: Preset description.
            tags: List of tags for filtering.
            author: Author name.

        Returns:
            The created preset.

        Raises:
            PresetManagerError: If a preset with the same name already exists.
        """
        # Check for duplicate name
        existing = self.get_by_name(name)
        if existing:
            raise PresetManagerError(f"Preset with name '{name}' already exists (id={existing.id})")

        preset = Preset(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            settings=settings or PresetSettings(),
            author=author,
            is_builtin=False,
        )

        self.storage.save(preset)
        self._invalidate_cache()

        logger.info(f"Created preset '{name}' (id={preset.id})")
        return preset

    def get(self, preset_id: str) -> Optional[Preset]:
        """Get a preset by ID.

        Args:
            preset_id: The preset ID.

        Returns:
            The preset, or None if not found.
        """
        return self.storage.load(preset_id)

    def get_by_name(self, name: str) -> Optional[Preset]:
        """Get a preset by name.

        Args:
            name: The preset name (case-insensitive).

        Returns:
            The preset, or None if not found.
        """
        all_presets = self._get_cached_presets()
        name_lower = name.lower()

        for preset in all_presets.values():
            if preset.name.lower() == name_lower:
                return preset

        return None

    def update(
        self,
        preset_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[PresetCategory] = None,
        tags: Optional[List[str]] = None,
        settings: Optional[PresetSettings] = None,
    ) -> Preset:
        """Update an existing preset.

        Args:
            preset_id: The preset ID to update.
            name: New name (optional).
            description: New description (optional).
            category: New category (optional).
            tags: New tags (optional).
            settings: New settings (optional).

        Returns:
            The updated preset.

        Raises:
            PresetManagerError: If preset not found or new name conflicts.
        """
        preset = self.get(preset_id)
        if not preset:
            raise PresetManagerError(f"Preset '{preset_id}' not found")

        if preset.is_builtin:
            raise PresetManagerError(
                f"Cannot update built-in preset '{preset.name}'. Create a copy to modify it."
            )

        # Check for name conflict
        if name and name != preset.name:
            existing = self.get_by_name(name)
            if existing and existing.id != preset_id:
                raise PresetManagerError(f"Preset with name '{name}' already exists")
            preset.name = name

        if description is not None:
            preset.description = description
        if category is not None:
            preset.category = category
        if tags is not None:
            preset.tags = tags
        if settings is not None:
            preset.settings = settings

        preset.update_timestamp()
        self.storage.save(preset)
        self._invalidate_cache()

        logger.info(f"Updated preset '{preset.name}' (id={preset_id})")
        return preset

    def delete(self, preset_id: str) -> bool:
        """Delete a preset.

        Args:
            preset_id: The preset ID to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            PresetManagerError: If trying to delete a built-in preset.
        """
        preset = self.get(preset_id)
        if not preset:
            return False

        result = self.storage.delete(preset_id)
        self._invalidate_cache()

        if result:
            logger.info(f"Deleted preset '{preset.name}' (id={preset_id})")

        return result

    def duplicate(self, preset_id: str, new_name: Optional[str] = None) -> Preset:
        """Create a copy of an existing preset.

        Args:
            preset_id: The preset ID to duplicate.
            new_name: Name for the copy. Defaults to "{original} (copy)".

        Returns:
            The duplicated preset.

        Raises:
            PresetManagerError: If preset not found or name conflicts.
        """
        preset = self.get(preset_id)
        if not preset:
            raise PresetManagerError(f"Preset '{preset_id}' not found")

        name = new_name or f"{preset.name} (copy)"

        # Deep copy the settings using serialization to ensure independent copy
        settings_copy = PresetSettings.from_dict(preset.settings.to_dict())

        return self.create(
            name=name,
            settings=settings_copy,
            category=preset.category,
            description=preset.description,
            tags=preset.tags.copy(),
            author=preset.author,
        )

    # =========================================================================
    # Listing and Searching
    # =========================================================================

    def list_all(self, include_builtins: bool = True) -> List[Preset]:
        """List all presets.

        Args:
            include_builtins: Whether to include built-in presets.

        Returns:
            List of all presets.
        """
        return self.storage.list_all(include_builtins=include_builtins)

    def list_by_category(
        self, category: PresetCategory, include_builtins: bool = True
    ) -> List[Preset]:
        """List presets by category.

        Args:
            category: The category to filter by.
            include_builtins: Whether to include built-in presets.

        Returns:
            List of presets in the category.
        """
        return self.storage.list_by_category(category.value, include_builtins=include_builtins)

    def search(
        self,
        query: str,
        category: Optional[PresetCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Preset]:
        """Search presets by query, category, and/or tags.

        Args:
            query: Search query (searches name and description).
            category: Optional category filter.
            tags: Optional tags filter (matches any tag).

        Returns:
            List of matching presets.
        """
        all_presets = self.list_all()
        query_lower = query.lower()

        results = []
        for preset in all_presets:
            # Category filter
            if category and preset.category != category:
                continue

            # Tags filter
            if tags and not any(tag in preset.tags for tag in tags):
                continue

            # Query filter
            if query:
                if (
                    query_lower not in preset.name.lower()
                    and query_lower not in preset.description.lower()
                ):
                    continue

            results.append(preset)

        return results

    # =========================================================================
    # Import/Export
    # =========================================================================

    def export_preset(self, preset_id: str, export_path: Path) -> Path:
        """Export a preset to a file.

        Args:
            preset_id: The preset ID to export.
            export_path: Path to export the preset to.

        Returns:
            Path to the exported file.

        Raises:
            PresetManagerError: If preset not found or export fails.
        """
        try:
            return self.storage.export_preset(preset_id, export_path)
        except PresetStorageError as e:
            raise PresetManagerError(str(e)) from e

    def import_preset(self, import_path: Path, overwrite: bool = False) -> Preset:
        """Import a preset from a file.

        Args:
            import_path: Path to the preset file to import.
            overwrite: Whether to overwrite existing preset with same ID.

        Returns:
            The imported preset.

        Raises:
            PresetManagerError: If import fails.
        """
        try:
            preset = self.storage.import_preset(import_path, overwrite=overwrite)
            self._invalidate_cache()
            return preset
        except PresetStorageError as e:
            raise PresetManagerError(str(e)) from e

    # =========================================================================
    # Configuration Integration
    # =========================================================================

    def apply_preset_to_config(self, preset: Preset, config: Config) -> Config:
        """Apply preset settings to a Config object.

        Creates a new Config with the preset's settings applied.
        Does not modify the original config.

        Args:
            preset: The preset to apply.
            config: The base configuration.

        Returns:
            A new Config with preset settings applied.
        """
        # Create new config objects with preset settings
        processing = ProcessingConfig(
            batch_size=preset.settings.processing.batch_size,
            num_workers=preset.settings.processing.num_workers,
            use_gpu=preset.settings.processing.use_gpu,
            gpu_device=preset.settings.processing.gpu_device,
            mixed_precision=preset.settings.processing.mixed_precision,
            max_memory_percent=preset.settings.processing.max_memory_percent,
        )

        depth_estimation = DepthEstimationConfig(
            model=preset.settings.depth_estimation.model,
            output_width=preset.settings.depth_estimation.output_width,
            output_height=preset.settings.depth_estimation.output_height,
            min_depth=preset.settings.depth_estimation.min_depth,
            max_depth=preset.settings.depth_estimation.max_depth,
            temporal_consistency=preset.settings.depth_estimation.temporal_consistency,
            temporal_smoothing_factor=preset.settings.depth_estimation.temporal_smoothing_factor,
        )

        from video2d3d.utils.config import AnaglyphConfig, SideBySideConfig

        stereo_generation = StereoGenerationConfig(
            format=preset.settings.stereo_generation.format,
            baseline=preset.settings.stereo_generation.baseline,
            focal_length=preset.settings.stereo_generation.focal_length,
            convergence=preset.settings.stereo_generation.convergence,
            anaglyph=AnaglyphConfig(
                type=preset.settings.stereo_generation.anaglyph_type,
                color_method=preset.settings.stereo_generation.anaglyph_color_method,
            ),
            side_by_side=SideBySideConfig(
                layout=preset.settings.stereo_generation.sbs_layout,
                swap_eyes=preset.settings.stereo_generation.sbs_swap_eyes,
                half_width=preset.settings.stereo_generation.sbs_half_width,
            ),
        )

        video_output = VideoOutputConfig(
            format=preset.settings.video_output.format,
            codec=preset.settings.video_output.codec,
            preset=preset.settings.video_output.preset,
            crf=preset.settings.video_output.crf,
            pixel_format=preset.settings.video_output.pixel_format,
        )

        quality = QualityConfig(
            preset=preset.settings.quality.preset,
            post_processing=preset.settings.quality.post_processing,
            calculate_metrics=preset.settings.quality.calculate_metrics,
        )

        # Create new config with updated sections
        config.processing = processing
        config.depth_estimation = depth_estimation
        config.stereo_generation = stereo_generation
        config.video_output = video_output
        config.quality = quality

        return config

    def create_preset_from_config(
        self,
        name: str,
        config: Config,
        category: PresetCategory = PresetCategory.CUSTOM,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Preset:
        """Create a preset from a Config object.

        Args:
            name: Preset name.
            config: Configuration to create preset from.
            category: Preset category.
            description: Preset description.
            tags: List of tags.

        Returns:
            The created preset.
        """
        # Import settings classes directly to avoid hacky field access
        settings = PresetSettings(
            depth_estimation=DepthEstimationSettings(
                model=config.depth_estimation.model,
                output_width=config.depth_estimation.output_width,
                output_height=config.depth_estimation.output_height,
                min_depth=config.depth_estimation.min_depth,
                max_depth=config.depth_estimation.max_depth,
                temporal_consistency=config.depth_estimation.temporal_consistency,
                temporal_smoothing_factor=config.depth_estimation.temporal_smoothing_factor,
            ),
            stereo_generation=StereoGenerationSettings(
                format=config.stereo_generation.format,
                baseline=config.stereo_generation.baseline,
                focal_length=config.stereo_generation.focal_length,
                convergence=config.stereo_generation.convergence,
                anaglyph_type=config.stereo_generation.anaglyph.type,
                anaglyph_color_method=config.stereo_generation.anaglyph.color_method,
                sbs_layout=config.stereo_generation.side_by_side.layout,
                sbs_swap_eyes=config.stereo_generation.side_by_side.swap_eyes,
                sbs_half_width=config.stereo_generation.side_by_side.half_width,
            ),
            video_output=VideoOutputSettings(
                format=config.video_output.format,
                codec=config.video_output.codec,
                preset=config.video_output.preset,
                crf=config.video_output.crf,
                pixel_format=config.video_output.pixel_format,
            ),
            processing=ProcessingSettings(
                batch_size=config.processing.batch_size,
                num_workers=config.processing.num_workers,
                use_gpu=config.processing.use_gpu,
                gpu_device=config.processing.gpu_device,
                mixed_precision=config.processing.mixed_precision,
                max_memory_percent=config.processing.max_memory_percent,
            ),
            quality=QualitySettings(
                preset=config.quality.preset,
                post_processing=config.quality.post_processing,
                calculate_metrics=config.quality.calculate_metrics,
            ),
        )

        return self.create(
            name=name,
            settings=settings,
            category=category,
            description=description,
            tags=tags,
        )


# Singleton instance for convenience
_manager: Optional[PresetManager] = None


def get_preset_manager(reload: bool = False) -> PresetManager:
    """Get the global PresetManager instance.

    Args:
        reload: Force reload of the manager.

    Returns:
        The PresetManager instance.
    """
    global _manager
    if _manager is None or reload:
        _manager = PresetManager()
    return _manager


__all__ = [
    "PresetManagerError",
    "PresetManager",
    "get_preset_manager",
]
