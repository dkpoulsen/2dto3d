"""Integration tests for priority-based job scheduling.

Tests cover:
- Full workflow with priority, scheduled, and dependency jobs
- State persistence with scheduler fields
- Edge cases and complex scenarios
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

from video2d3d.batch.config import BatchQueueConfig
from video2d3d.batch.queue import BatchVideoQueue


@pytest.fixture
def temp_queue(tmp_path: Path) -> Generator[BatchVideoQueue, None, None]:
    """Create a temporary queue for testing."""
    config = BatchQueueConfig(
        output_directory=tmp_path / "output",
        state_file=tmp_path / "state.json",
        auto_start=False,
    )
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output").mkdir(parents=True, exist_ok=True)

    with patch("video2d3d.batch.queue.get_logger"):
        queue = BatchVideoQueue(config)
        yield queue

    queue.stop()


@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Create a sample video file for testing."""
    video_path = tmp_path / "input" / "test.mp4"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    video_path.write_bytes(b"fake video content")
    return video_path
