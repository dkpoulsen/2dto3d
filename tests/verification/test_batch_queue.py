#!/usr/bin/env python3
"""Verification test for batch video queue feature.

This test verifies the batch queue functionality works correctly:
- Job creation and management
- File discovery with patterns
- Queue statistics
- Job lifecycle (pending -> running -> completed)
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from video2d3d.batch import (
    BatchJob,
    BatchJobResult,
    BatchQueueConfig,
    BatchVideoQueue,
    FileDiscovery,
    FileDiscoveryConfig,
    JobPriority,
    JobStatus,
)


def create_test_files(directory: Path, count: int = 3) -> list[Path]:
    files = []
    for i in range(count):
        file_path = directory / f"video_{i}.mp4"
        file_path.write_text(f"test video {i}")
        files.append(file_path)
    return files


def test_batch_job_creation():
    print("Testing BatchJob creation...")
    job = BatchJob(
        input_path=Path("/tmp/test.mp4"),
        output_path=Path("/tmp/test_3d.mp4"),
        priority=JobPriority.HIGH,
    )
    assert job.status == JobStatus.PENDING
    assert job.priority == JobPriority.HIGH
    assert job.progress == 0.0
    print("  [PASS] BatchJob creation")


def test_batch_job_lifecycle():
    print("Testing BatchJob lifecycle...")
    job = BatchJob(
        input_path=Path("/tmp/test.mp4"),
        max_retries=2,
    )

    assert job.status == JobStatus.PENDING
    assert not job.is_retryable

    job.mark_started()
    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None

    job.update_progress(0.5, "Processing frames")
    assert job.progress == 0.5
    assert job.current_stage == "Processing frames"

    result = BatchJobResult(success=True, frames_processed=100)
    job.mark_completed(result)
    assert job.status == JobStatus.COMPLETED
    assert job.result.success
    print("  [PASS] BatchJob lifecycle")


def test_batch_job_retry():
    print("Testing BatchJob retry...")
    job = BatchJob(
        input_path=Path("/tmp/test.mp4"),
        max_retries=2,
    )

    job.mark_failed(Exception("Test error"))
    assert job.status == JobStatus.FAILED
    assert job.is_retryable

    can_retry = job.increment_retry()
    assert can_retry
    assert job.retry_count == 1
    assert job.status == JobStatus.RETRYING

    job.mark_failed(Exception("Test error 2"))
    can_retry = job.increment_retry()
    assert can_retry
    assert job.retry_count == 2

    job.mark_failed(Exception("Test error 3"))
    can_retry = job.increment_retry()
    assert not can_retry
    print("  [PASS] BatchJob retry")


def test_batch_job_serialization():
    print("Testing BatchJob serialization...")
    job = BatchJob(
        input_path=Path("/tmp/test.mp4"),
        output_path=Path("/tmp/test_3d.mp4"),
        priority=JobPriority.HIGH,
        max_retries=3,
    )

    job_dict = job.to_dict()
    assert job_dict["input_path"] == "/tmp/test.mp4"
    assert job_dict["output_path"] == "/tmp/test_3d.mp4"
    assert job_dict["status"] == "pending"
    assert job_dict["priority"] == 10

    restored_job = BatchJob.from_dict(job_dict)
    assert restored_job.input_path == job.input_path
    assert restored_job.output_path == job.output_path
    assert restored_job.status == job.status
    assert restored_job.priority == job.priority
    print("  [PASS] BatchJob serialization")


def test_file_discovery():
    print("Testing FileDiscovery...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        (tmpdir / "video1.mp4").write_text("test")
        (tmpdir / "video2.avi").write_text("test")
        (tmpdir / "video3.mkv").write_text("test")
        (tmpdir / "readme.txt").write_text("test")

        subdir = tmpdir / "subdir"
        subdir.mkdir()
        (subdir / "video4.mp4").write_text("test")

        config = FileDiscoveryConfig(
            patterns=["*.mp4", "*.avi"],
            recursive=True,
        )
        discovery = FileDiscovery(config)

        files = list(discovery.discover(tmpdir))
        file_names = [f.name for f in files]

        assert "video1.mp4" in file_names
        assert "video2.avi" in file_names
        assert "video4.mp4" in file_names
        assert "video3.mkv" not in file_names
        assert "readme.txt" not in file_names
    print("  [PASS] FileDiscovery")


def test_batch_queue_config():
    print("Testing BatchQueueConfig...")
    config = BatchQueueConfig(
        max_concurrent_jobs=2,
        max_retries=3,
        skip_existing=True,
    )

    assert config.max_concurrent_jobs == 2
    assert config.max_retries == 3

    input_path = Path("/videos/input.mp4")
    output_path = config.get_output_path(input_path)
    assert output_path.name == "input_3d.mp4"
    print("  [PASS] BatchQueueConfig")


def test_batch_video_queue():
    print("Testing BatchVideoQueue...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_dir = tmpdir / "input"
        output_dir = tmpdir / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        create_test_files(input_dir, 3)

        processed_files = []

        def mock_processor(input_path: Path, output_path: Path) -> BatchJobResult:
            processed_files.append(input_path)
            output_path.write_text("processed")
            return BatchJobResult(
                success=True,
                output_path=output_path,
                frames_processed=100,
            )

        config = BatchQueueConfig(
            max_concurrent_jobs=1,
            auto_start=False,
            output_directory=output_dir,
            skip_existing=False,
        )

        queue = BatchVideoQueue(config=config, processor=mock_processor)

        jobs = queue.add_jobs_from_directory(input_dir, recursive=False)
        assert len(jobs) == 3
        assert queue.pending_count == 3

        stats = queue.get_stats()
        assert stats.total_jobs == 3
        assert stats.pending_jobs == 3

        queue.start()

        import time

        max_wait = 10
        elapsed = 0
        while queue.running_count > 0 or queue.pending_count > 0:
            time.sleep(0.1)
            elapsed += 0.1
            if elapsed > max_wait:
                break

        queue.stop()

        assert len(processed_files) == 3
        stats = queue.get_stats()
        assert stats.completed_jobs == 3
        assert stats.success_rate == 100.0

    print("  [PASS] BatchVideoQueue")


def test_batch_queue_skip_existing():
    print("Testing BatchVideoQueue skip_existing...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_file = tmpdir / "test.mp4"
        input_file.write_text("test")

        output_file = tmpdir / "test_3d.mp4"
        output_file.write_text("already exists")

        def processor(input_path: Path, output_path: Path) -> BatchJobResult:
            return BatchJobResult(success=True, output_path=output_path)

        config = BatchQueueConfig(
            skip_existing=True,
            output_directory=tmpdir,
        )

        queue = BatchVideoQueue(config=config, processor=processor)
        job = queue.add_job(input_file)

        assert job.status == JobStatus.SKIPPED
    print("  [PASS] BatchVideoQueue skip_existing")


def main():
    print("\n" + "=" * 60)
    print("Batch Video Queue Feature Verification")
    print("=" * 60 + "\n")

    tests = [
        test_batch_job_creation,
        test_batch_job_lifecycle,
        test_batch_job_retry,
        test_batch_job_serialization,
        test_file_discovery,
        test_batch_queue_config,
        test_batch_video_queue,
        test_batch_queue_skip_existing,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
