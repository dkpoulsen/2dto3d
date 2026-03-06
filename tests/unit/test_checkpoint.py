"""Unit tests for checkpoint and resume system.

Tests cover:
- CheckpointState enum
- StageCheckpoint dataclass
- FrameCheckpoint dataclass
- ConversionCheckpoint dataclass
- CheckpointConfig dataclass
- CheckpointManager class
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from video2d3d.checkpoint import (
    CheckpointConfig,
    CheckpointManager,
    CheckpointState,
    ConversionCheckpoint,
    FrameCheckpoint,
    StageCheckpoint,
)


@pytest.fixture
def temp_checkpoint_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def checkpoint_config(temp_checkpoint_dir: Path) -> CheckpointConfig:
    return CheckpointConfig(
        enabled=True,
        checkpoint_dir=temp_checkpoint_dir,
        checkpoint_interval=10,
        keep_intermediate=True,
        max_checkpoints=5,
        cleanup_on_complete=False,
        resume_on_start=True,
    )


@pytest.fixture
def checkpoint_manager(checkpoint_config: CheckpointConfig) -> CheckpointManager:
    with patch("video2d3d.checkpoint.manager.get_logger"):
        return CheckpointManager(checkpoint_config)


class TestCheckpointState:
    def test_state_values(self) -> None:
        assert CheckpointState.IN_PROGRESS.value == "in_progress"
        assert CheckpointState.COMPLETE.value == "complete"
        assert CheckpointState.INTERRUPTED.value == "interrupted"
        assert CheckpointState.FAILED.value == "failed"

    def test_state_from_string(self) -> None:
        assert CheckpointState("in_progress") == CheckpointState.IN_PROGRESS
        assert CheckpointState("complete") == CheckpointState.COMPLETE


class TestStageCheckpoint:
    def test_default_values(self) -> None:
        stage = StageCheckpoint(name="test")
        assert stage.name == "test"
        assert stage.completed is False
        assert stage.frames_processed == 0
        assert stage.frames_total == 0
        assert stage.started_at is None
        assert stage.completed_at is None
        assert stage.metadata == {}

    def test_progress_percent(self) -> None:
        stage = StageCheckpoint(name="test", frames_processed=50, frames_total=100)
        assert stage.progress_percent == 50.0

    def test_progress_percent_zero_total(self) -> None:
        stage = StageCheckpoint(name="test", frames_processed=50, frames_total=0)
        assert stage.progress_percent == 0.0

    def test_is_started(self) -> None:
        stage = StageCheckpoint(name="test")
        assert stage.is_started is False
        stage.started_at = datetime.now()
        assert stage.is_started is True

    def test_serialization_roundtrip(self) -> None:
        original = StageCheckpoint(
            name="depth",
            completed=True,
            frames_processed=100,
            frames_total=100,
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 1, 12, 30, 0),
            metadata={"model": "midas_small"},
        )
        data = original.to_dict()
        restored = StageCheckpoint.from_dict(data)

        assert restored.name == original.name
        assert restored.completed == original.completed
        assert restored.frames_processed == original.frames_processed
        assert restored.frames_total == original.frames_total
        assert restored.metadata == original.metadata


class TestFrameCheckpoint:
    def test_default_values(self) -> None:
        frame = FrameCheckpoint(frame_index=5)
        assert frame.frame_index == 5
        assert frame.extracted is False
        assert frame.depth_processed is False
        assert frame.temporal_smoothed is False
        assert frame.stereo_generated is False
        assert frame.written is False
        assert frame.depth_map_path is None
        assert frame.processing_time_ms == 0.0

    def test_is_complete(self) -> None:
        frame = FrameCheckpoint(frame_index=0)
        assert frame.is_complete is False

        frame.extracted = True
        frame.depth_processed = True
        frame.stereo_generated = True
        frame.written = True
        assert frame.is_complete is True

    def test_can_resume_from(self) -> None:
        frame = FrameCheckpoint(frame_index=0)
        assert frame.can_resume_from is False

        frame.extracted = True
        assert frame.can_resume_from is True

        frame.depth_processed = True
        frame.stereo_generated = True
        frame.written = True
        assert frame.can_resume_from is False

    def test_serialization_roundtrip(self) -> None:
        original = FrameCheckpoint(
            frame_index=42,
            extracted=True,
            depth_processed=True,
            temporal_smoothed=False,
            stereo_generated=True,
            written=False,
            depth_map_path="/path/to/depth.npy",
            processing_time_ms=150.5,
        )
        data = original.to_dict()
        restored = FrameCheckpoint.from_dict(data)

        assert restored.frame_index == original.frame_index
        assert restored.extracted == original.extracted
        assert restored.depth_processed == original.depth_processed
        assert restored.stereo_generated == original.stereo_generated
        assert restored.written == original.written
        assert restored.depth_map_path == original.depth_map_path
        assert restored.processing_time_ms == original.processing_time_ms


class TestConversionCheckpoint:
    def test_default_values(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test-job",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        assert checkpoint.job_id == "test-job"
        assert checkpoint.state == CheckpointState.IN_PROGRESS
        assert checkpoint.total_frames == 0
        assert checkpoint.current_frame == 0
        assert len(checkpoint.stages) == 5
        assert "extract" in checkpoint.stages
        assert "depth" in checkpoint.stages

    def test_progress_percent(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
            total_frames=100,
            current_frame=25,
        )
        assert checkpoint.progress_percent == 25.0

    def test_is_complete(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
            state=CheckpointState.COMPLETE,
        )
        assert checkpoint.is_complete is True

    def test_can_resume(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
            state=CheckpointState.INTERRUPTED,
        )
        assert checkpoint.can_resume is True

        checkpoint.state = CheckpointState.COMPLETE
        assert checkpoint.can_resume is False

    def test_resume_frame(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
            current_frame=50,
        )
        assert checkpoint.resume_frame == 50

        checkpoint.frame_checkpoints[40] = FrameCheckpoint(
            frame_index=40, extracted=True, depth_processed=True, stereo_generated=True, written=True
        )
        checkpoint.frame_checkpoints[41] = FrameCheckpoint(
            frame_index=41, extracted=True, depth_processed=False
        )
        assert checkpoint.resume_frame == 41


    def test_update_stage(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.update_stage("depth", frames_processed=50, completed=False)


    def test_update_stage(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.update_stage("depth", frames_processed=50, completed=False)

        assert checkpoint.stages["depth"].frames_processed == 50
        assert checkpoint.stages["depth"].completed is False
        assert checkpoint.stages["depth"].started_at is not None

    def test_update_frame(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        frame = FrameCheckpoint(frame_index=10, extracted=True)
        checkpoint.update_frame(frame)

        assert 10 in checkpoint.frame_checkpoints
        assert checkpoint.current_frame == 11

    def test_mark_interrupted(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.mark_interrupted()

        assert checkpoint.state == CheckpointState.INTERRUPTED

    def test_mark_complete(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.mark_complete()

        assert checkpoint.state == CheckpointState.COMPLETE
        assert all(s.completed for s in checkpoint.stages.values())

    def test_mark_failed(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.mark_failed("Test error")

        assert checkpoint.state == CheckpointState.FAILED
        assert checkpoint.error == "Test error"

    def test_cleanup_completed_frames(self) -> None:
        checkpoint = ConversionCheckpoint(
            job_id="test",
            input_path="input.mp4",
            output_path="output.mp4",
        )

        checkpoint.frame_checkpoints[0] = FrameCheckpoint(
            frame_index=0, extracted=True, depth_processed=True, stereo_generated=True, written=True
        )
        checkpoint.frame_checkpoints[1] = FrameCheckpoint(
            frame_index=1, extracted=True, depth_processed=False
        )

        removed = checkpoint.cleanup_completed_frames()

        assert removed == 1
        assert 0 not in checkpoint.frame_checkpoints
        assert 1 in checkpoint.frame_checkpoints

    def test_serialization_roundtrip(self) -> None:
        original = ConversionCheckpoint(
            job_id="test-job",
            input_path="/input/video.mp4",
            output_path="/output/video_3d.mp4",
            state=CheckpointState.INTERRUPTED,
            total_frames=1000,
            current_frame=500,
            output_format="side_by_side",
            depth_model="midas_small",
            config={"batch_size": 4},
        )
        original.update_stage("depth", frames_processed=500)

        data = original.to_dict()
        restored = ConversionCheckpoint.from_dict(data)

        assert restored.job_id == original.job_id
        assert restored.input_path == original.input_path
        assert restored.output_path == original.output_path
        assert restored.state == original.state
        assert restored.total_frames == original.total_frames
        assert restored.current_frame == original.current_frame
        assert restored.output_format == original.output_format
        assert restored.depth_model == original.depth_model
        assert "depth" in restored.stages

    def test_json_file_roundtrip(self, temp_checkpoint_dir: Path) -> None:
        original = ConversionCheckpoint(
            job_id="file-test",
            input_path="input.mp4",
            output_path="output.mp4",
            total_frames=100,
        )

        json_path = temp_checkpoint_dir / "checkpoint.json"
        original.to_json(json_path)

        assert json_path.exists()

        restored = ConversionCheckpoint.from_json(json_path)
        assert restored.job_id == original.job_id
        assert restored.total_frames == original.total_frames


class TestCheckpointConfig:
    def test_default_values(self) -> None:
        config = CheckpointConfig()
        assert config.enabled is True
        assert config.checkpoint_interval == 30
        assert config.keep_intermediate is False
        assert config.max_checkpoints == 10
        assert config.cleanup_on_complete is True
        assert config.resume_on_start is True

    def test_path_normalization(self) -> None:
        config = CheckpointConfig(checkpoint_dir="/tmp/checkpoints")
        assert isinstance(config.checkpoint_dir, Path)
        assert config.checkpoint_dir == Path("/tmp/checkpoints")

    def test_get_checkpoint_path(self) -> None:
        config = CheckpointConfig(checkpoint_dir=Path("/checkpoints"))
        path = config.get_checkpoint_path("job-123")
        assert path == Path("/checkpoints/job-123.json")

    def test_get_frame_data_dir(self) -> None:
        config = CheckpointConfig(checkpoint_dir=Path("/checkpoints"))
        path = config.get_frame_data_dir("job-123")
        assert path == Path("/checkpoints/job-123/frames")

    def test_serialization_roundtrip(self) -> None:
        original = CheckpointConfig(
            enabled=False,
            checkpoint_dir=Path("/custom/checkpoints"),
            checkpoint_interval=60,
            keep_intermediate=True,
            max_checkpoints=20,
            cleanup_on_complete=False,
            resume_on_start=False,
        )

        data = original.to_dict()
        restored = CheckpointConfig.from_dict(data)

        assert restored.enabled == original.enabled
        assert str(restored.checkpoint_dir) == str(original.checkpoint_dir)
        assert restored.checkpoint_interval == original.checkpoint_interval
        assert restored.keep_intermediate == original.keep_intermediate
        assert restored.max_checkpoints == original.max_checkpoints


class TestCheckpointManager:
    def test_create_checkpoint(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="test-job",
            input_path="input.mp4",
            output_path="output.mp4",
            total_frames=100,
        )

        assert checkpoint.job_id == "test-job"
        assert checkpoint.total_frames == 100

    def test_save_and_load(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="save-test",
            input_path="input.mp4",
            output_path="output.mp4",
            total_frames=200,
        )
        checkpoint.update_stage("depth", frames_processed=100)

        checkpoint_manager.save(checkpoint)

        loaded = checkpoint_manager.load("save-test")

        assert loaded is not None
        assert loaded.job_id == "save-test"
        assert loaded.stages["depth"].frames_processed == 100

    def test_load_nonexistent(self, checkpoint_manager: CheckpointManager) -> None:
        loaded = checkpoint_manager.load("nonexistent")
        assert loaded is None

    def test_delete(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="delete-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint_manager.save(checkpoint)

        deleted = checkpoint_manager.delete("delete-test")

        assert deleted is True
        assert checkpoint_manager.load("delete-test") is None

    def test_can_resume(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="resume-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint.state = CheckpointState.INTERRUPTED
        checkpoint_manager.save(checkpoint)

        assert checkpoint_manager.can_resume("resume-test") is True

    def test_get_resume_info(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="info-test",
            input_path="input.mp4",
            output_path="output.mp4",
            total_frames=100,
        )
        checkpoint.current_frame = 50
        checkpoint.state = CheckpointState.INTERRUPTED
        checkpoint_manager.save(checkpoint)

        info = checkpoint_manager.get_resume_info("info-test")

        assert info is not None
        assert info["job_id"] == "info-test"
        assert info["resume_frame"] == 50
        assert info["progress_percent"] == 50.0

    def test_mark_interrupted(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="interrupt-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint_manager.save(checkpoint)

        checkpoint_manager.mark_interrupted("interrupt-test")

        loaded = checkpoint_manager.load("interrupt-test")
        assert loaded is not None
        assert loaded.state == CheckpointState.INTERRUPTED

    def test_mark_complete(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="complete-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint_manager.save(checkpoint)

        checkpoint_manager.mark_complete("complete-test")

        loaded = checkpoint_manager.load("complete-test")
        assert loaded is not None
        assert loaded.state == CheckpointState.COMPLETE

    def test_mark_failed(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="fail-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint_manager.save(checkpoint)

        checkpoint_manager.mark_failed("fail-test", "Test error message")

        loaded = checkpoint_manager.load("fail-test")
        assert loaded is not None
        assert loaded.state == CheckpointState.FAILED
        assert loaded.error == "Test error message"

    def test_update_frame_interval_save(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint_manager.config.checkpoint_interval = 5

        checkpoint = checkpoint_manager.create_checkpoint(
            job_id="interval-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        checkpoint_manager.save(checkpoint)

        for i in range(12):
            frame = FrameCheckpoint(frame_index=i, extracted=True)
            checkpoint_manager.update_frame("interval-test", frame)

        loaded = checkpoint_manager.load("interval-test")
        assert loaded is not None
        assert loaded.current_frame == 11


    def test_list_checkpoints(self, checkpoint_manager: CheckpointManager) -> None:
        for i in range(3):
            checkpoint = checkpoint_manager.create_checkpoint(
                job_id=f"list-test-{i}",
                input_path=f"input{i}.mp4",
                output_path=f"output{i}.mp4",
                total_frames=100 * (i + 1),
            )
            checkpoint.current_frame = 50 * (i + 1)
            checkpoint_manager.save(checkpoint)

        checkpoints = checkpoint_manager.list_checkpoints()

        assert len(checkpoints) == 3
        assert all("job_id" in c for c in checkpoints)
        assert all("progress_percent" in c for c in checkpoints)

    def test_cleanup_old_checkpoints(self, checkpoint_manager: CheckpointManager) -> None:
        checkpoint_manager.config.max_checkpoints = 2

        for i in range(5):
            checkpoint = checkpoint_manager.create_checkpoint(
                job_id=f"cleanup-test-{i}",
                input_path=f"input{i}.mp4",
                output_path=f"output{i}.mp4",
            )
            checkpoint_manager.save(checkpoint)

        deleted = checkpoint_manager.cleanup_old_checkpoints()

        assert deleted == 3
        remaining = checkpoint_manager.list_checkpoints()
        assert len(remaining) == 2

    def test_disabled_checkpointing(self, temp_checkpoint_dir: Path) -> None:
        config = CheckpointConfig(
            enabled=False,
            checkpoint_dir=temp_checkpoint_dir,
        )
        with patch("video2d3d.checkpoint.manager.get_logger"):
            manager = CheckpointManager(config)

        checkpoint = manager.create_checkpoint(
            job_id="disabled-test",
            input_path="input.mp4",
            output_path="output.mp4",
        )
        manager.save(checkpoint)

        path = config.get_checkpoint_path("disabled-test")
        assert not path.exists()
