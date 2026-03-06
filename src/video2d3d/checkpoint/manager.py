"""Checkpoint manager for saving, loading, and managing conversion checkpoints.

This module provides the CheckpointManager class which handles:
- Persisting checkpoints to disk
- Loading and validating checkpoints for resume
- Cleanup of old checkpoint files
- Thread-safe checkpoint operations
"""

from __future__ import annotations

import json
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from video2d3d.checkpoint.models import (
    CheckpointConfig,
    CheckpointState,
    ConversionCheckpoint,
    FrameCheckpoint,
)
from video2d3d.utils.logger import get_logger


class CheckpointManager:
    """Manages checkpoint lifecycle for video conversion jobs.

    This class provides thread-safe checkpoint operations including
    saving, loading, cleanup, and resume detection.

    Example:
        config = CheckpointConfig(checkpoint_dir=Path("checkpoints"))
        manager = CheckpointManager(config)

        # Create new checkpoint
        checkpoint = manager.create_checkpoint(
            job_id="abc123",
            input_path="input.mp4",
            output_path="output_3d.mp4",
            total_frames=1000,
        )

        # Update and save
        checkpoint.update_stage("depth", frames_processed=100)
        manager.save(checkpoint)

        # Resume from checkpoint
        existing = manager.load(job_id="abc123")
        if existing and existing.can_resume:
            resume_from = existing.resume_frame
    """

    def __init__(
        self,
        config: CheckpointConfig | None = None,
        *,
        checkpoint_dir: Path | str | None = None,
    ) -> None:
        if config is not None:
            self.config = config
        elif checkpoint_dir is not None:
            self.config = CheckpointConfig(checkpoint_dir=Path(checkpoint_dir))
        else:
            self.config = CheckpointConfig()

        self._logger = get_logger("checkpoint_manager")
        self._lock = threading.Lock()
        self._checkpoints: dict[str, ConversionCheckpoint] = {}

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.config.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def create_checkpoint(
        self,
        job_id: str,
        input_path: str | Path,
        output_path: str | Path,
        total_frames: int = 0,
        output_format: str = "side_by_side",
        depth_model: str = "midas_small",
        config: dict | None = None,
    ) -> ConversionCheckpoint:
        checkpoint = ConversionCheckpoint(
            job_id=job_id,
            input_path=str(input_path),
            output_path=str(output_path),
            total_frames=total_frames,
            output_format=output_format,
            depth_model=depth_model,
            config=config or {},
        )

        with self._lock:
            self._checkpoints[job_id] = checkpoint

        self._logger.debug(
            f"Created checkpoint for job {job_id}: "
            f"{input_path} -> {output_path}, {total_frames} frames"
        )

        return checkpoint

    def get_checkpoint(self, job_id: str) -> ConversionCheckpoint | None:
        with self._lock:
            if job_id in self._checkpoints:
                return self._checkpoints[job_id]

        return self.load(job_id)

    def load(self, job_id: str) -> ConversionCheckpoint | None:
        path = self.config.get_checkpoint_path(job_id)

        if not path.exists():
            return None

        try:
            checkpoint = ConversionCheckpoint.from_json(path)

            with self._lock:
                self._checkpoints[job_id] = checkpoint

            self._logger.info(
                f"Loaded checkpoint for job {job_id}: "
                f"state={checkpoint.state.value}, frame={checkpoint.current_frame}/{checkpoint.total_frames}"
            )

            return checkpoint

        except json.JSONDecodeError as e:
            self._logger.error(f"Failed to parse checkpoint {path}: {e}")
            return None
        except KeyError as e:
            self._logger.error(f"Invalid checkpoint format {path}: missing {e}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to load checkpoint {path}: {e}")
            return None

    def save(self, checkpoint: ConversionCheckpoint) -> None:
        if not self.config.enabled:
            return

        checkpoint.updated_at = datetime.now()
        path = self.config.get_checkpoint_path(checkpoint.job_id)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.to_json(path)

            with self._lock:
                self._checkpoints[checkpoint.job_id] = checkpoint

            self._logger.debug(
                f"Saved checkpoint for job {checkpoint.job_id}: "
                f"frame {checkpoint.current_frame}/{checkpoint.total_frames}"
            )

        except Exception as e:
            self._logger.error(f"Failed to save checkpoint: {e}")
            raise

    def delete(self, job_id: str) -> bool:
        path = self.config.get_checkpoint_path(job_id)
        deleted = False

        with self._lock:
            if job_id in self._checkpoints:
                del self._checkpoints[job_id]

        if path.exists():
            try:
                path.unlink()
                deleted = True
                self._logger.debug(f"Deleted checkpoint file: {path}")
            except OSError as e:
                self._logger.warning(f"Failed to delete checkpoint file {path}: {e}")

        frame_dir = self.config.get_frame_data_dir(job_id)
        if frame_dir.exists():
            try:
                shutil.rmtree(frame_dir)
                deleted = True
                self._logger.debug(f"Deleted frame data directory: {frame_dir}")
            except OSError as e:
                self._logger.warning(f"Failed to delete frame data {frame_dir}: {e}")

        return deleted

    def cleanup_old_checkpoints(self, max_to_keep: int | None = None) -> int:
        max_checkpoints = (
            max_to_keep if max_to_keep is not None else self.config.max_checkpoints
        )
        if max_checkpoints <= 0:
            return 0

        checkpoint_files = list(self.config.checkpoint_dir.glob("*.json"))
        checkpoint_files = list(self.config.checkpoint_dir.glob("*.json"))

        if len(checkpoint_files) <= max_checkpoints:
            return 0

        def get_mtime(p: Path) -> float:
            return p.stat().st_mtime

        checkpoint_files.sort(key=get_mtime, reverse=True)

        to_delete = checkpoint_files[max_checkpoints:]
        deleted_count = 0

        for path in to_delete:
            try:
                job_id = path.stem
                self.delete(job_id)
                deleted_count += 1
            except Exception as e:
                self._logger.warning(f"Failed to cleanup checkpoint {path}: {e}")

        if deleted_count > 0:
            self._logger.info(f"Cleaned up {deleted_count} old checkpoint(s)")

        return deleted_count

    def can_resume(self, job_id: str) -> bool:
        checkpoint = self.get_checkpoint(job_id)
        return checkpoint is not None and checkpoint.can_resume

    def get_resume_info(self, job_id: str) -> dict | None:
        checkpoint = self.get_checkpoint(job_id)

        if checkpoint is None or not checkpoint.can_resume:
            return None

        return {
            "job_id": checkpoint.job_id,
            "resume_frame": checkpoint.resume_frame,
            "progress_percent": checkpoint.progress_percent,
            "state": checkpoint.state.value,
            "last_updated": checkpoint.updated_at.isoformat(),
            "input_path": checkpoint.input_path,
            "output_path": checkpoint.output_path,
        }

    def mark_interrupted(self, job_id: str) -> None:
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint:
            checkpoint.mark_interrupted()
            self.save(checkpoint)

    def mark_complete(self, job_id: str) -> None:
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint:
            checkpoint.mark_complete()
            self.save(checkpoint)

            if self.config.cleanup_on_complete:
                self.delete(job_id)

    def mark_failed(self, job_id: str, error: str) -> None:
        checkpoint = self.get_checkpoint(job_id)
        if checkpoint:
            checkpoint.mark_failed(error)
            self.save(checkpoint)

    def update_frame(
        self,
        job_id: str,
        frame_checkpoint: FrameCheckpoint,
        force_save: bool = False,
    ) -> None:
        checkpoint = self.get_checkpoint(job_id)

        if checkpoint is None:
            self._logger.warning(f"Cannot update frame: no checkpoint for job {job_id}")
            return

        checkpoint.update_frame(frame_checkpoint)

        should_save = force_save or (
            self.config.checkpoint_interval > 0
            and frame_checkpoint.frame_index % self.config.checkpoint_interval == 0
        )

        if should_save:
            self.save(checkpoint)

    def list_checkpoints(self) -> list[dict]:
        checkpoint_files = list(self.config.checkpoint_dir.glob("*.json"))
        results = []

        for path in checkpoint_files:
            try:
                checkpoint = ConversionCheckpoint.from_json(path)
                results.append(
                    {
                        "job_id": checkpoint.job_id,
                        "input_path": checkpoint.input_path,
                        "output_path": checkpoint.output_path,
                        "state": checkpoint.state.value,
                        "progress_percent": checkpoint.progress_percent,
                        "current_frame": checkpoint.current_frame,
                        "total_frames": checkpoint.total_frames,
                        "updated_at": checkpoint.updated_at.isoformat(),
                        "can_resume": checkpoint.can_resume,
                    }
                )
            except Exception as e:
                self._logger.warning(f"Failed to read checkpoint {path}: {e}")

        results.sort(key=lambda x: x["updated_at"], reverse=True)
        return results

    def get_frame_data_path(self, job_id: str, frame_index: int, data_type: str) -> Path:
        frame_dir = self.config.get_frame_data_dir(job_id)
        return frame_dir / f"frame_{frame_index:06d}_{data_type}.npy"

    def save_frame_data(
        self,
        job_id: str,
        frame_index: int,
        data_type: str,
        data,
    ) -> Path | None:
        if not self.config.keep_intermediate:
            return None

        import numpy as np

        path = self.get_frame_data_path(job_id, frame_index, data_type)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            np.save(path, data)
            self._logger.debug(f"Saved frame data: {path}")
            return path
        except Exception as e:
            self._logger.error(f"Failed to save frame data {path}: {e}")
            return None

    def load_frame_data(self, path: str | Path):
        import numpy as np

        path = Path(path)
        if not path.exists():
            return None

        try:
            return np.load(path)
        except Exception as e:
            self._logger.error(f"Failed to load frame data {path}: {e}")
            return None


__all__ = ["CheckpointManager"]
