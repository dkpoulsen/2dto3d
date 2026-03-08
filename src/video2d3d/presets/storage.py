"""Preset storage for persisting presets to JSON files.

This module provides classes for storing and retrieving presets from
the filesystem, supporting both user presets and built-in presets.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from video2d3d.presets.models import Preset
from video2d3d.utils.logger import get_logger

logger = get_logger("presets.storage")


class PresetStorageError(Exception):
    """Exception raised for preset storage errors."""

    pass


class PresetStorage:
    """Manages persistent storage of presets in JSON files.

    Presets are stored in a dedicated directory with each preset as a
    separate JSON file. Built-in presets are stored separately from
    user-created presets.
    """

    def __init__(
        self,
        presets_dir: Path | None = None,
        builtin_presets_dir: Path | None = None,
    ):
        """Initialize preset storage.

        Args:
            presets_dir: Directory for user presets. Defaults to 'presets/' in project root.
            builtin_presets_dir: Directory for built-in presets. Defaults to package presets.
        """
        if presets_dir is None:
            # Default to 'presets/' directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            presets_dir = project_root / "presets"

        if builtin_presets_dir is None:
            # Default to 'builtins' subdirectory in presets module
            builtin_presets_dir = Path(__file__).parent / "builtins"

        self.presets_dir = Path(presets_dir)
        self.builtin_presets_dir = Path(builtin_presets_dir)

        # Ensure directories exist
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"PresetStorage initialized: user_dir={self.presets_dir}, "
            f"builtin_dir={self.builtin_presets_dir}"
        )

    def _get_preset_path(self, preset_id: str, is_builtin: bool = False) -> Path:
        """Get the file path for a preset.

        Args:
            preset_id: The preset ID.
            is_builtin: Whether the preset is built-in.

        Returns:
            Path to the preset JSON file.
        """
        base_dir = self.builtin_presets_dir if is_builtin else self.presets_dir
        return base_dir / f"{preset_id}.json"

    def save(self, preset: Preset) -> Path:
        """Save a preset to storage.

        Args:
            preset: The preset to save.

        Returns:
            Path to the saved preset file.

        Raises:
            PresetStorageError: If saving fails.
        """
        try:
            # Built-in presets should not be overwritten
            if preset.is_builtin:
                raise PresetStorageError(
                    f"Cannot save built-in preset '{preset.name}'. Create a copy to modify it."
                )

            file_path = self._get_preset_path(preset.id, is_builtin=False)
            content = json.dumps(preset.to_dict(), indent=2)
            self._atomic_write(file_path, content)

            logger.info(f"Saved preset '{preset.name}' to {file_path}")
            return file_path

        except PresetStorageError:
            raise  # Re-raise our own errors
        except OSError as e:
            logger.error(f"Failed to save preset '{preset.name}': {e}")
            raise PresetStorageError(f"Failed to save preset: {e}") from e

    def _atomic_write(self, file_path: Path, content: str) -> None:
        """Write content to a file atomically using temp file + rename.

        This prevents data corruption if the write is interrupted mid-way.

        Args:
            file_path: Target file path.
            content: Content to write.

        Raises:
            PresetStorageError: If write fails.
        """
        try:
            # Write to temp file in same directory for atomic rename
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.stem}_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    f.write(content)
                # Atomic rename (on POSIX systems)
                os.replace(temp_path, file_path)
            except Exception:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        except OSError as e:
            raise PresetStorageError(f"Atomic write failed: {e}") from e

    def load(self, preset_id: str, is_builtin: bool = False) -> Preset | None:
        """Load a preset by ID.

        Args:
            preset_id: The preset ID to load.
            is_builtin: Whether to look for a built-in preset.

        Returns:
            The loaded preset, or None if not found.
        """
        # Try user presets first, then built-in
        for builtin in [False, True] if not is_builtin else [True]:
            file_path = self._get_preset_path(preset_id, is_builtin=builtin)

            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                    preset = Preset.from_dict(data)
                    preset.is_builtin = builtin
                    logger.debug(f"Loaded preset '{preset.name}' from {file_path}")
                    return preset

                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to parse preset file {file_path}: {e}")
                    continue

        logger.warning(f"Preset '{preset_id}' not found")
        return None

    def delete(self, preset_id: str) -> bool:
        """Delete a preset by ID.

        Args:
            preset_id: The preset ID to delete.

        Returns:
            True if deleted, False if not found.

        Raises:
            PresetStorageError: If trying to delete a built-in preset.
        """
        # Check if it's a built-in preset
        preset = self.load(preset_id)
        if preset and preset.is_builtin:
            raise PresetStorageError(f"Cannot delete built-in preset '{preset.name}'.")

        file_path = self._get_preset_path(preset_id, is_builtin=False)

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted preset {preset_id}")
            return True

        return False

    def list_all(self, include_builtins: bool = True) -> list[Preset]:
        """List all presets.

        Args:
            include_builtins: Whether to include built-in presets.

        Returns:
            List of all presets.
        """
        presets: dict[str, Preset] = {}

        # Load built-in presets first (lower priority)
        if include_builtins and self.builtin_presets_dir.exists():
            for file_path in self.builtin_presets_dir.glob("*.json"):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                    preset = Preset.from_dict(data)
                    preset.is_builtin = True
                    presets[preset.id] = preset
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to load built-in preset {file_path}: {e}")

        # Load user presets (higher priority, can override built-ins by ID)
        if self.presets_dir.exists():
            for file_path in self.presets_dir.glob("*.json"):
                try:
                    with open(file_path, encoding="utf-8") as f:
                        data = json.load(f)
                    preset = Preset.from_dict(data)
                    preset.is_builtin = False
                    presets[preset.id] = preset
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to load user preset {file_path}: {e}")

        return list(presets.values())

    def list_by_category(self, category: str, include_builtins: bool = True) -> list[Preset]:
        """List presets by category.

        Args:
            category: The category to filter by.
            include_builtins: Whether to include built-in presets.

        Returns:
            List of presets in the category.
        """
        all_presets = self.list_all(include_builtins=include_builtins)
        return [p for p in all_presets if p.category.value == category.lower()]

    def exists(self, preset_id: str) -> bool:
        """Check if a preset exists.

        Args:
            preset_id: The preset ID to check.

        Returns:
            True if the preset exists.
        """
        return (
            self._get_preset_path(preset_id, is_builtin=False).exists()
            or self._get_preset_path(preset_id, is_builtin=True).exists()
        )

    def export_preset(self, preset_id: str, export_path: Path) -> Path:
        """Export a preset to a file.

        Args:
            preset_id: The preset ID to export.
            export_path: Path to export the preset to.

        Returns:
            Path to the exported file.

        Raises:
            PresetStorageError: If preset not found or export fails.
        """
        preset = self.load(preset_id)
        if not preset:
            raise PresetStorageError(f"Preset '{preset_id}' not found")

        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(preset.to_dict(), f, indent=2)

            logger.info(f"Exported preset '{preset.name}' to {export_path}")
            return export_path

        except OSError as e:
            logger.error(f"Failed to export preset: {e}")
            raise PresetStorageError(f"Failed to export preset: {e}") from e

    def import_preset(self, import_path: Path, overwrite: bool = False) -> Preset:
        """Import a preset from a file.

        Args:
            import_path: Path to the preset file to import.
            overwrite: Whether to overwrite existing preset with same ID.

        Returns:
            The imported preset.

        Raises:
            PresetStorageError: If import fails or preset already exists.
        """
        try:
            with open(import_path, encoding="utf-8") as f:
                data = json.load(f)

            preset = Preset.from_dict(data)
            preset.is_builtin = False  # Imported presets are never built-in

            # Check if preset already exists
            if self.exists(preset.id) and not overwrite:
                raise PresetStorageError(
                    f"Preset with ID '{preset.id}' already exists. "
                    "Use overwrite=True to replace it."
                )

            # Save the imported preset
            self.save(preset)

            logger.info(f"Imported preset '{preset.name}' from {import_path}")
            return preset

        except json.JSONDecodeError as e:
            logger.error(f"Invalid preset file format: {e}")
            raise PresetStorageError(f"Invalid preset file format: {e}") from e
        except OSError as e:
            logger.error(f"Failed to import preset: {e}")
            raise PresetStorageError(f"Failed to import preset: {e}") from e

    def backup_presets(self, backup_path: Path) -> Path:
        """Create a backup of all user presets.

        Args:
            backup_path: Path for the backup directory or archive.

        Returns:
            Path to the backup.
        """
        if backup_path.is_dir():
            # Copy entire presets directory
            shutil.copytree(self.presets_dir, backup_path / "presets", dirs_exist_ok=True)
        else:
            # Create archive
            shutil.make_archive(str(backup_path), "zip", self.presets_dir)

        logger.info(f"Created preset backup at {backup_path}")
        return backup_path


__all__ = [
    "PresetStorageError",
    "PresetStorage",
]
