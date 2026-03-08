"""File discovery utilities for batch video processing.

Provides pattern-based file discovery with wildcard matching, recursive search,
and file filtering capabilities.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Generator
from pathlib import Path

from video2d3d.batch.config import FileDiscoveryConfig
from video2d3d.batch.exceptions import FileDiscoveryError
from video2d3d.utils.logger import get_logger


class FileDiscovery:
    """Discover video files using patterns and filters."""

    def __init__(self, config: FileDiscoveryConfig | None = None) -> None:
        self.config = config or FileDiscoveryConfig()
        self._logger = get_logger("file_discovery")

    def discover(
        self,
        paths: Path | list[Path],
        patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> Generator[Path, None, None]:
        """Discover files matching patterns in given paths.

        Args:
            paths: Single path or list of paths to search.
            patterns: Override patterns (uses config if not provided).
            exclude_patterns: Override exclude patterns (uses config if not provided).

        Yields:
            Path objects for each discovered file.
        """
        if isinstance(paths, (str, Path)):
            paths = [Path(paths)]
        paths = [Path(p) for p in paths]

        patterns = patterns or self.config.patterns
        exclude_patterns = exclude_patterns or self.config.exclude_patterns

        for base_path in paths:
            if not base_path.exists():
                self._logger.warning(f"Path does not exist: {base_path}")
                continue

            if base_path.is_file():
                if self._matches_patterns(base_path, patterns, exclude_patterns):
                    if self._passes_filters(base_path):
                        yield base_path
            elif base_path.is_dir():
                yield from self._discover_in_directory(base_path, patterns, exclude_patterns)

    def _discover_in_directory(
        self,
        directory: Path,
        patterns: list[str],
        exclude_patterns: list[str],
    ) -> Generator[Path, None, None]:
        """Recursively discover files in a directory."""
        try:
            for root, dirs, files in os.walk(
                directory,
                followlinks=self.config.follow_symlinks,
            ):
                root_path = Path(root)

                depth = len(root_path.relative_to(directory).parts)
                if depth > self.config.max_depth:
                    dirs.clear()
                    continue

                for filename in files:
                    file_path = root_path / filename

                    if self._matches_patterns(file_path, patterns, exclude_patterns):
                        if self._passes_filters(file_path):
                            yield file_path

        except PermissionError as e:
            self._logger.warning(f"Permission denied: {directory}")
            raise FileDiscoveryError(
                f"Permission denied accessing directory: {directory}",
                path=str(directory),
            ) from e
        except OSError as e:
            raise FileDiscoveryError(
                f"Error accessing directory {directory}: {e}",
                path=str(directory),
            ) from e

    def _matches_patterns(
        self,
        file_path: Path,
        patterns: list[str],
        exclude_patterns: list[str],
    ) -> bool:
        """Check if file matches include patterns and not exclude patterns."""
        filename = file_path.name
        if not self.config.case_sensitive:
            filename = filename.lower()
            patterns = [p.lower() for p in patterns]
            exclude_patterns = [p.lower() for p in exclude_patterns]

        matches_include = any(fnmatch.fnmatch(filename, p) for p in patterns)
        matches_exclude = any(fnmatch.fnmatch(filename, p) for p in exclude_patterns)

        return matches_include and not matches_exclude

    def _passes_filters(self, file_path: Path) -> bool:
        """Apply additional filters (size, etc.)."""
        if self.config.min_file_size_mb > 0 or self.config.max_file_size_mb > 0:
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)

                if self.config.min_file_size_mb > 0 and size_mb < self.config.min_file_size_mb:
                    return False

                if self.config.max_file_size_mb > 0 and size_mb > self.config.max_file_size_mb:
                    return False

            except OSError:
                return False

        return True

    def discover_by_wildcard(
        self,
        pattern: str,
        base_dir: Path | None = None,
    ) -> Generator[Path, None, None]:
        """Discover files using a wildcard pattern.

        Supports patterns like:
        - "*.mp4" - all mp4 files
        - "video_*.mp4" - mp4 files starting with video_
        - "**/videos/*.mp4" - mp4 files in any videos directory
        - "/path/to/videos/**/*.mp4" - all mp4 files recursively

        Args:
            pattern: Wildcard pattern (glob or fnmatch style).
            base_dir: Base directory for relative patterns.

        Yields:
            Path objects for each matching file.
        """
        pattern_path = Path(pattern)

        if pattern.is_absolute() or base_dir is None:
            base = pattern_path.parent if pattern_path.parent.exists() else Path(".")
            glob_pattern = pattern_path.name
        else:
            base = Path(base_dir)
            glob_pattern = pattern

        recursive = "**" in glob_pattern or self.config.recursive

        if recursive:
            for match in base.rglob(glob_pattern.replace("**/", "")):
                if match.is_file():
                    if self._passes_filters(match):
                        yield match
        else:
            for match in base.glob(glob_pattern):
                if match.is_file():
                    if self._passes_filters(match):
                        yield match

    def discover_from_list(
        self,
        file_list: list[str] | list[Path],
        validate: bool = True,
    ) -> Generator[Path, None, None]:
        """Discover files from a list of paths.

        Args:
            file_list: List of file paths.
            validate: Whether to validate files exist.

        Yields:
            Path objects for each valid file.
        """
        for file_path in file_list:
            path = Path(file_path)

            if validate and not path.exists():
                self._logger.warning(f"File not found: {path}")
                continue

            if validate and not path.is_file():
                self._logger.warning(f"Not a file: {path}")
                continue

            if self._passes_filters(path):
                yield path

    def discover_from_text_file(
        self,
        list_file: Path,
        base_dir: Path | None = None,
    ) -> Generator[Path, None, None]:
        """Discover files listed in a text file.

        Args:
            list_file: Path to text file containing file paths (one per line).
            base_dir: Base directory for relative paths.

        Yields:
            Path objects for each file.
        """
        list_path = Path(list_file)

        if not list_path.exists():
            raise FileDiscoveryError(
                f"List file not found: {list_path}",
                path=str(list_path),
            )

        try:
            with open(list_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if base_dir and not Path(line).is_absolute():
                        file_path = base_dir / line
                    else:
                        file_path = Path(line)

                    if file_path.exists() and file_path.is_file():
                        if self._passes_filters(file_path):
                            yield file_path
                    else:
                        self._logger.warning(f"File not found: {file_path}")

        except OSError as e:
            raise FileDiscoveryError(
                f"Error reading list file: {e}",
                path=str(list_path),
            ) from e

    def group_by_directory(
        self,
        files: list[Path],
    ) -> dict[Path, list[Path]]:
        """Group discovered files by their parent directory.

        Args:
            files: List of file paths.

        Returns:
            Dictionary mapping directories to lists of files.
        """
        groups: dict[Path, list[Path]] = {}

        for file_path in files:
            parent = file_path.parent
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(file_path)

        return groups


def discover_videos(
    paths: Path | list[Path],
    patterns: list[str] | None = None,
    recursive: bool = True,
) -> list[Path]:
    """Convenience function to discover video files.

    Args:
        paths: Path(s) to search.
        patterns: File patterns to match.
        recursive: Search recursively.

    Returns:
        List of discovered file paths.
    """
    config = FileDiscoveryConfig(
        patterns=patterns or ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"],
        recursive=recursive,
    )
    discovery = FileDiscovery(config)
    return list(discovery.discover(paths))


__all__ = [
    "FileDiscovery",
    "discover_videos",
]
