"""Data models for checkpoint and resume system.

This module defines the core data structures for tracking and persisting
video conversion progress at multiple granularity levels:
- Stage-level: Which pipeline stages are complete
- Frame-level: Per-frame processing state
- Full checkpoint: Complete conversion state for resume
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# numpy is imported lazily in manager.py for frame data serialization


class CheckpointState(Enum):
    """State of a checkpoint."""

    IN_PROGRESS = "in_progress"  # Conversion is in progress, checkpoint may be stale
    COMPLETE = "complete"  # Checkpoint represents a clean stopping point
    INTERRUPTED = "interrupted"  # Conversion was interrupted, checkpoint is valid
    FAILED = "failed"  # Conversion failed, checkpoint may be corrupted


@dataclass
class StageCheckpoint:
    """Checkpoint for a single processing stage.

    Tracks completion status and metrics for each stage in the pipeline.

    Attributes:
        name: Stage name (e.g., "extract", "depth", "stereo", "write")
        completed: Whether this stage is complete
        frames_processed: Number of frames processed in this stage
        frames_total: Total frames to process in this stage
        started_at: When this stage started
        completed_at: When this stage completed (if done)
        metadata: Additional stage-specific data
    """

    name: str
    completed: bool = False
    frames_processed: int = 0
    frames_total: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def progress_percent(self) -> float:
        """Get progress percentage for this stage."""
        if self.frames_total == 0:
            return 0.0
        return (self.frames_processed / self.frames_total) * 100

    @property
    def is_started(self) -> bool:
        """Check if this stage has started."""
        return self.started_at is not None

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time for this stage."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "completed": self.completed,
            "frames_processed": self.frames_processed,
            "frames_total": self.frames_total,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StageCheckpoint:
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            completed=data.get("completed", False),
            frames_processed=data.get("frames_processed", 0),
            frames_total=data.get("frames_total", 0),
            started_at=(
                datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FrameCheckpoint:
    """Checkpoint for a single frame's processing state.

    Tracks which processing steps are complete for a specific frame.

    Attributes:
        frame_index: Zero-based frame index in the video
        extracted: Whether frame has been extracted from video
        depth_processed: Whether depth map has been generated
        temporal_smoothed: Whether temporal smoothing has been applied
        stereo_generated: Whether stereo pair has been generated
        written: Whether frame has been written to output
        depth_map_path: Path to saved depth map (if checkpointed)
        left_view_path: Path to saved left view (if checkpointed)
        right_view_path: Path to saved right view (if checkpointed)
        timestamp: When this frame was processed
        processing_time_ms: Time taken to process this frame
    """

    frame_index: int
    extracted: bool = False
    depth_processed: bool = False
    temporal_smoothed: bool = False
    stereo_generated: bool = False
    written: bool = False
    depth_map_path: Optional[str] = None
    left_view_path: Optional[str] = None
    right_view_path: Optional[str] = None
    timestamp: Optional[datetime] = None
    processing_time_ms: float = 0.0

    @property
    def is_complete(self) -> bool:
        """Check if all processing steps are complete for this frame."""
        return self.extracted and self.depth_processed and self.stereo_generated and self.written

    @property
    def can_resume_from(self) -> bool:
        """Check if we can resume processing from this frame.

        A frame is resumable if it has been extracted but not fully processed.
        """
        return self.extracted and not self.is_complete

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "frame_index": self.frame_index,
            "extracted": self.extracted,
            "depth_processed": self.depth_processed,
            "temporal_smoothed": self.temporal_smoothed,
            "stereo_generated": self.stereo_generated,
            "written": self.written,
            "depth_map_path": self.depth_map_path,
            "left_view_path": self.left_view_path,
            "right_view_path": self.right_view_path,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "processing_time_ms": self.processing_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FrameCheckpoint:
        """Deserialize from dictionary."""
        return cls(
            frame_index=data["frame_index"],
            extracted=data.get("extracted", False),
            depth_processed=data.get("depth_processed", False),
            temporal_smoothed=data.get("temporal_smoothed", False),
            stereo_generated=data.get("stereo_generated", False),
            written=data.get("written", False),
            depth_map_path=data.get("depth_map_path"),
            left_view_path=data.get("left_view_path"),
            right_view_path=data.get("right_view_path"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            processing_time_ms=data.get("processing_time_ms", 0.0),
        )


@dataclass
class ConversionCheckpoint:
    """Complete checkpoint for a video conversion job.

    Contains all state needed to resume an interrupted conversion,
    including frame-level progress, stage status, and configuration.

    Attributes:
        job_id: Unique identifier for this conversion job
        input_path: Path to input video file
        output_path: Path to output video file
        state: Current checkpoint state
        created_at: When this checkpoint was created
        updated_at: When this checkpoint was last updated
        total_frames: Total frames in the input video
        current_frame: Current frame being processed
        stages: Checkpoints for each processing stage
        frame_checkpoints: Per-frame processing status (sparse, only for incomplete)
        output_format: 3D output format (side_by_side, anaglyph, etc.)
        depth_model: Depth estimation model used
        config: Conversion configuration
        metadata: Additional checkpoint metadata
        error: Error message if conversion failed
    """

    job_id: str
    input_path: str
    output_path: str
    state: CheckpointState = CheckpointState.IN_PROGRESS
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_frames: int = 0
    current_frame: int = 0
    stages: dict[str, StageCheckpoint] = field(default_factory=dict)
    frame_checkpoints: dict[int, FrameCheckpoint] = field(default_factory=dict)
    output_format: str = "side_by_side"
    depth_model: str = "midas_small"
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize default stages if not present."""
        if not self.stages:
            self.stages = {
                "extract": StageCheckpoint(name="extract"),
                "depth": StageCheckpoint(name="depth"),
                "temporal": StageCheckpoint(name="temporal"),
                "stereo": StageCheckpoint(name="stereo"),
                "write": StageCheckpoint(name="write"),
            }

    @property
    def progress_percent(self) -> float:
        """Get overall progress percentage."""
        if self.total_frames == 0:
            return 0.0
        return (self.current_frame / self.total_frames) * 100

    @property
    def frames_completed(self) -> int:
        """Get number of fully completed frames."""
        return sum(1 for fc in self.frame_checkpoints.values() if fc.is_complete)

    @property
    def is_complete(self) -> bool:
        """Check if conversion is complete."""
        return self.state == CheckpointState.COMPLETE or (
            self.total_frames > 0
            and self.current_frame >= self.total_frames
            and all(stage.completed for stage in self.stages.values())
        )

    @property
    def can_resume(self) -> bool:
        """Check if conversion can be resumed from this checkpoint."""
        return self.state in (CheckpointState.INTERRUPTED, CheckpointState.IN_PROGRESS)

    @property
    def resume_frame(self) -> int:
        """Get the frame index to resume from.

        Returns the first frame that is not complete, or the last processed frame
        if all checked frames are complete.
        """
        if not self.frame_checkpoints:
            return self.current_frame

        # Find first incomplete frame
        for i in sorted(self.frame_checkpoints.keys()):
            if not self.frame_checkpoints[i].is_complete:
                return i

        # All checked frames complete, resume from current
        return self.current_frame

    @property
    def elapsed_seconds(self) -> float:
        """Get total elapsed time."""
        return (self.updated_at - self.created_at).total_seconds()

    def get_stage(self, name: str) -> Optional[StageCheckpoint]:
        """Get a stage checkpoint by name."""
        return self.stages.get(name)

    def update_stage(
        self,
        name: str,
        frames_processed: Optional[int] = None,
        completed: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update a stage checkpoint."""
        if name not in self.stages:
            self.stages[name] = StageCheckpoint(name=name)

        stage = self.stages[name]

        if frames_processed is not None:
            stage.frames_processed = frames_processed

        if completed:
            stage.completed = True
            stage.completed_at = datetime.now()

        if metadata:
            stage.metadata.update(metadata)

        if not stage.started_at:
            stage.started_at = datetime.now()

        self.updated_at = datetime.now()

    def update_frame(self, frame_checkpoint: FrameCheckpoint) -> None:
        """Update or add a frame checkpoint."""
        self.frame_checkpoints[frame_checkpoint.frame_index] = frame_checkpoint
        self.current_frame = max(self.current_frame, frame_checkpoint.frame_index + 1)
        self.updated_at = datetime.now()

    def mark_interrupted(self) -> None:
        """Mark checkpoint as interrupted."""
        self.state = CheckpointState.INTERRUPTED
        self.updated_at = datetime.now()

    def mark_complete(self) -> None:
        """Mark checkpoint as complete."""
        self.state = CheckpointState.COMPLETE
        self.updated_at = datetime.now()
        for stage in self.stages.values():
            stage.completed = True
            if not stage.completed_at:
                stage.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark checkpoint as failed with error."""
        self.state = CheckpointState.FAILED
        self.error = error
        self.updated_at = datetime.now()

    def cleanup_completed_frames(self) -> int:
        """Remove checkpoints for completed frames to save memory.

        Returns:
            Number of checkpoints removed.
        """
        to_remove = [idx for idx, fc in self.frame_checkpoints.items() if fc.is_complete]
        for idx in to_remove:
            del self.frame_checkpoints[idx]
        return len(to_remove)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "job_id": self.job_id,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_frames": self.total_frames,
            "current_frame": self.current_frame,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "frame_checkpoints": {str(k): v.to_dict() for k, v in self.frame_checkpoints.items()},
            "output_format": self.output_format,
            "depth_model": self.depth_model,
            "config": self.config,
            "metadata": self.metadata,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConversionCheckpoint:
        """Deserialize from dictionary."""
        stages = {k: StageCheckpoint.from_dict(v) for k, v in data.get("stages", {}).items()}

        frame_checkpoints = {
            int(k): FrameCheckpoint.from_dict(v)
            for k, v in data.get("frame_checkpoints", {}).items()
        }

        return cls(
            job_id=data["job_id"],
            input_path=data["input_path"],
            output_path=data["output_path"],
            state=CheckpointState(data.get("state", "in_progress")),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            total_frames=data.get("total_frames", 0),
            current_frame=data.get("current_frame", 0),
            stages=stages,
            frame_checkpoints=frame_checkpoints,
            output_format=data.get("output_format", "side_by_side"),
            depth_model=data.get("depth_model", "midas_small"),
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            error=data.get("error"),
        )

    def to_json(self, path: Path) -> None:
        """Save checkpoint to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: Path) -> ConversionCheckpoint:
        """Load checkpoint from JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))


@dataclass
class CheckpointConfig:
    """Configuration for checkpoint behavior.

    Attributes:
        enabled: Whether checkpointing is enabled
        checkpoint_dir: Directory to store checkpoint files
        checkpoint_interval: Save checkpoint every N frames (0 = only on completion/interrupt)
        keep_intermediate: Keep intermediate frame data (depth maps, stereo views)
        max_checkpoints: Maximum number of checkpoint files to keep (0 = unlimited)
        cleanup_on_complete: Remove checkpoint files when conversion completes
        resume_on_start: Automatically resume from checkpoint if available
    """

    enabled: bool = True
    checkpoint_dir: Path = field(default_factory=lambda: Path("checkpoints"))
    checkpoint_interval: int = 30  # Save every 30 frames
    keep_intermediate: bool = False  # Don't keep depth maps by default
    max_checkpoints: int = 10  # Keep last 10 checkpoints
    cleanup_on_complete: bool = True
    resume_on_start: bool = True

    def __post_init__(self) -> None:
        """Normalize path."""
        if isinstance(self.checkpoint_dir, str):
            self.checkpoint_dir = Path(self.checkpoint_dir)

    def get_checkpoint_path(self, job_id: str) -> Path:
        """Get checkpoint file path for a job."""
        return self.checkpoint_dir / f"{job_id}.json"

    def get_frame_data_dir(self, job_id: str) -> Path:
        """Get directory for intermediate frame data."""
        return self.checkpoint_dir / job_id / "frames"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "enabled": self.enabled,
            "checkpoint_dir": str(self.checkpoint_dir),
            "checkpoint_interval": self.checkpoint_interval,
            "keep_intermediate": self.keep_intermediate,
            "max_checkpoints": self.max_checkpoints,
            "cleanup_on_complete": self.cleanup_on_complete,
            "resume_on_start": self.resume_on_start,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckpointConfig:
        """Deserialize from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            checkpoint_dir=Path(data.get("checkpoint_dir", "checkpoints")),
            checkpoint_interval=data.get("checkpoint_interval", 30),
            keep_intermediate=data.get("keep_intermediate", False),
            max_checkpoints=data.get("max_checkpoints", 10),
            cleanup_on_complete=data.get("cleanup_on_complete", True),
            resume_on_start=data.get("resume_on_start", True),
        )


__all__ = [
    "CheckpointState",
    "StageCheckpoint",
    "FrameCheckpoint",
    "ConversionCheckpoint",
    "CheckpointConfig",
]
