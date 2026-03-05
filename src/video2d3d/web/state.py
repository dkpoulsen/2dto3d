"""Application state management.

This module provides a centralized state container for the FastAPI application,
separated from the app module to avoid circular imports.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from video2d3d.batch import BatchVideoQueue


class AppState:
    """Application state container."""

    def __init__(self) -> None:
        self.queue: Optional[BatchVideoQueue] = None
        self.upload_dir: Path = Path("uploads")
        self.output_dir: Path = Path("outputs")
        self.start_time: float = time.time()
        self.max_upload_size_mb: int = 500

    @property
    def uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.start_time


# Global app state instance
app_state = AppState()


__all__ = ["app_state", "AppState"]
