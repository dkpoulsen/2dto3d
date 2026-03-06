"""Unit tests for batch video processing exceptions.

Tests cover:
- BatchQueueError base exception
- JobNotFoundError exception
- JobAlreadyExistsError exception
- QueueFullError exception
- QueueNotRunningError exception
- JobValidationError exception
- FileDiscoveryError exception
- FolderWatcherError exception
- CircularDependencyError exception
- DependencyFailedError exception
"""

import pytest

from video2d3d.batch.exceptions import (
    BatchQueueError,
    CircularDependencyError,
    DependencyFailedError,
    FileDiscoveryError,
    FolderWatcherError,
    JobAlreadyExistsError,
    JobNotFoundError,
    JobValidationError,
    QueueFullError,
    QueueNotRunningError,
    StatePersistenceError,
)


class TestBatchQueueError:
    """Tests for BatchQueueError base exception."""

    def test_is_exception(self) -> None:
        """Test that BatchQueueError is an Exception."""
        error = BatchQueueError("test error")
        assert isinstance(error, Exception)

    def test_message(self) -> None:
        """Test error message is set correctly."""
        error = BatchQueueError("test error message")
        assert str(error) == "test error message"

    def test_can_be_raised(self) -> None:
        """Test that the exception can be raised and caught."""
        with pytest.raises(BatchQueueError, match="test error"):
            raise BatchQueueError("test error")


class TestJobNotFoundError:
    """Tests for JobNotFoundError exception."""

    def test_message_format(self) -> None:
        """Test error message includes job_id."""
        error = JobNotFoundError("job-123")
        assert "job-123" in str(error)
        assert "not found" in str(error).lower()

    def test_job_id_attribute(self) -> None:
        """Test job_id attribute is set correctly."""
        error = JobNotFoundError("job-456")
        assert error.job_id == "job-456"

    def test_inheritance(self) -> None:
        """Test that JobNotFoundError inherits from BatchQueueError."""
        error = JobNotFoundError("job-789")
        assert isinstance(error, BatchQueueError)

    def test_can_be_caught_as_base_type(self) -> None:
        """Test that exception can be caught as BatchQueueError."""
        with pytest.raises(BatchQueueError):
            raise JobNotFoundError("job-123")


class TestJobAlreadyExistsError:
    """Tests for JobAlreadyExistsError exception."""

    def test_message_format(self) -> None:
        """Test error message includes job_id."""
        error = JobAlreadyExistsError("job-123")
        assert "job-123" in str(error)
        assert "already exists" in str(error).lower()

    def test_job_id_attribute(self) -> None:
        """Test job_id attribute is set correctly."""
        error = JobAlreadyExistsError("job-456")
        assert error.job_id == "job-456"

    def test_inheritance(self) -> None:
        """Test that JobAlreadyExistsError inherits from BatchQueueError."""
        error = JobAlreadyExistsError("job-789")
        assert isinstance(error, BatchQueueError)


class TestQueueFullError:
    """Tests for QueueFullError exception."""

    def test_message_format(self) -> None:
        """Test error message includes max_size."""
        error = QueueFullError(100)
        assert "100" in str(error)
        assert "full" in str(error).lower()

    def test_max_size_attribute(self) -> None:
        """Test max_size attribute is set correctly."""
        error = QueueFullError(50)
        assert error.max_size == 50

    def test_inheritance(self) -> None:
        """Test that QueueFullError inherits from BatchQueueError."""
        error = QueueFullError(100)
        assert isinstance(error, BatchQueueError)


class TestQueueNotRunningError:
    """Tests for QueueNotRunningError exception."""

    def test_message_format(self) -> None:
        """Test error message is correct."""
        error = QueueNotRunningError()
        assert "not running" in str(error).lower()

    def test_inheritance(self) -> None:
        """Test that QueueNotRunningError inherits from BatchQueueError."""
        error = QueueNotRunningError()
        assert isinstance(error, BatchQueueError)


class TestJobValidationError:
    """Tests for JobValidationError exception."""

    def test_message_only(self) -> None:
        """Test error with message only."""
        error = JobValidationError("Invalid job configuration")
        assert str(error) == "Invalid job configuration"
        assert error.input_path is None

    def test_message_with_input_path(self) -> None:
        """Test error with message and input_path."""
        error = JobValidationError("File not found", input_path="/path/to/file.mp4")
        assert str(error) == "File not found"
        assert error.input_path == "/path/to/file.mp4"

    def test_inheritance(self) -> None:
        """Test that JobValidationError inherits from BatchQueueError."""
        error = JobValidationError("test")
        assert isinstance(error, BatchQueueError)


class TestFileDiscoveryError:
    """Tests for FileDiscoveryError exception."""

    def test_message_only(self) -> None:
        """Test error with message only."""
        error = FileDiscoveryError("Pattern matching failed")
        assert str(error) == "Pattern matching failed"
        assert error.path is None

    def test_message_with_path(self) -> None:
        """Test error with message and path."""
        error = FileDiscoveryError("Permission denied", path="/restricted/dir")
        assert str(error) == "Permission denied"
        assert error.path == "/restricted/dir"

    def test_inheritance(self) -> None:
        """Test that FileDiscoveryError inherits from BatchQueueError."""
        error = FileDiscoveryError("test")
        assert isinstance(error, BatchQueueError)


class TestFolderWatcherError:
    """Tests for FolderWatcherError exception."""

    def test_message_only(self) -> None:
        """Test error with message only."""
        error = FolderWatcherError("Watch failed")
        assert str(error) == "Watch failed"
        assert error.watch_path is None

    def test_message_with_watch_path(self) -> None:
        """Test error with message and watch_path."""
        error = FolderWatcherError("Cannot watch directory", watch_path="/watch/dir")
        assert str(error) == "Cannot watch directory"
        assert error.watch_path == "/watch/dir"

    def test_inheritance(self) -> None:
        """Test that FolderWatcherError inherits from BatchQueueError."""
        error = FolderWatcherError("test")
        assert isinstance(error, BatchQueueError)


class TestStatePersistenceError:
    """Tests for StatePersistenceError exception."""

    def test_message_only(self) -> None:
        """Test error with message only."""
        error = StatePersistenceError("Failed to save state")
        assert str(error) == "Failed to save state"
        assert error.state_file is None

    def test_message_with_state_file(self) -> None:
        """Test error with message and state_file."""
        error = StatePersistenceError(
            "Failed to load state",
            state_file="/path/to/state.json",
        )
        assert str(error) == "Failed to load state"
        assert error.state_file == "/path/to/state.json"

    def test_inheritance(self) -> None:
        """Test that StatePersistenceError inherits from BatchQueueError."""
        error = StatePersistenceError("test")
        assert isinstance(error, BatchQueueError)


class TestExceptionHierarchy:
    """Tests for the exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self) -> None:
        """Test that all custom exceptions inherit from BatchQueueError."""
        exceptions = [
            JobNotFoundError("job-1"),
            JobAlreadyExistsError("job-2"),
            QueueFullError(100),
            QueueNotRunningError(),
            JobValidationError("validation failed"),
            FileDiscoveryError("discovery failed"),
            FolderWatcherError("watcher failed"),
            StatePersistenceError("persistence failed"),
        ]

        for exc in exceptions:
            assert isinstance(exc, BatchQueueError)
            assert isinstance(exc, Exception)

    def test_catching_base_catches_all(self) -> None:
        """Test that catching BatchQueueError catches all derived exceptions."""
        exceptions_to_raise = [
            JobNotFoundError("job-1"),
            FileDiscoveryError("discovery failed"),
            StatePersistenceError("persistence failed"),
        ]

        for exc in exceptions_to_raise:
            try:
                raise exc
            except BatchQueueError as e:
                assert e is exc
            else:
    def test_exception_can_be_chained(self) -> None:
        """Test that exceptions can be chained with 'from'."""
        original = ValueError("original error")
        try:
            raise FileDiscoveryError("discovery failed", path="/test") from original
        except FileDiscoveryError as e:
            assert e.__cause__ is original
            assert e.path == "/test"


class TestCircularDependencyError:
    """Tests for CircularDependencyError exception."""

    def test_message_format(self) -> None:
        """Test error message includes job_ids."""
        error = CircularDependencyError("job-123", "job-456")
        assert "job-123" in str(error)
        assert "job-456" in str(error)
        assert "circular dependency" in str(error).lower()

    def test_job_id_attributes(self) -> None:
        """Test job_id and dependency_id attributes are set correctly."""
        error = CircularDependencyError("job-a", "job-b")
        assert error.job_id == "job-a"
        assert error.dependency_id == "job-b"

    def test_inheritance(self) -> None:
        """Test that CircularDependencyError inherits from BatchQueueError."""
        error = CircularDependencyError("job-1", "job-2")
        assert isinstance(error, BatchQueueError)
        assert isinstance(error, Exception)

    def test_can_be_caught_as_base_type(self) -> None:
        """Test that exception can be caught as BatchQueueError."""
        with pytest.raises(BatchQueueError):
            raise CircularDependencyError("job-1", "job-2")


class TestDependencyFailedError:
    """Tests for DependencyFailedError exception."""

    def test_message_format_failed(self) -> None:
        """Test error message for failed dependency."""
        error = DependencyFailedError("job-123", "job-456", "failed")
        assert "job-123" in str(error)
        assert "job-456" in str(error)
        assert "failed" in str(error).lower()
        assert "cannot run" in str(error).lower()

    def test_message_format_cancelled(self) -> None:
        """Test error message for cancelled dependency."""
        error = DependencyFailedError("job-123", "job-456", "cancelled")
        assert "cancelled" in str(error).lower()

    def test_job_id_attributes(self) -> None:
        """Test job_id, dependency_id, and dependency_status attributes."""
        error = DependencyFailedError("job-a", "job-b", "failed")
        assert error.job_id == "job-a"
        assert error.dependency_id == "job-b"
        assert error.dependency_status == "failed"

    def test_inheritance(self) -> None:
        """Test that DependencyFailedError inherits from BatchQueueError."""
        error = DependencyFailedError("job-1", "job-2", "failed")
        assert isinstance(error, BatchQueueError)
        assert isinstance(error, Exception)

    def test_can_be_caught_as_base_type(self) -> None:
        """Test that exception can be caught as BatchQueueError."""
        with pytest.raises(BatchQueueError):
            raise DependencyFailedError("job-1", "job-2", "failed")


class TestSchedulerExceptionHierarchy:
    """Tests for scheduler exception hierarchy."""

    def test_scheduler_exceptions_inherit_from_base(self) -> None:
        """Test that scheduler exceptions inherit from BatchQueueError."""
        exceptions = [
            CircularDependencyError("job-1", "job-2"),
            DependencyFailedError("job-1", "job-2", "failed"),
        ]
        for exc in exceptions:
            assert isinstance(exc, BatchQueueError)
            assert isinstance(exc, Exception)

    def test_catching_base_catches_scheduler_exceptions(self) -> None:
        """Test that catching BatchQueueError catches scheduler exceptions."""
        exceptions_to_raise = [
            CircularDependencyError("job-1", "job-2"),
            DependencyFailedError("job-3", "job-4", "cancelled"),
        ]
        for exc in exceptions_to_raise:
            try:
                raise exc
            except BatchQueueError as e:
                assert e is exc
            else:
                pytest.fail(f"Exception {type(exc).__name__} was not caught")

    def test_scheduler_exceptions_can_be_chained(self) -> None:
        """Test that scheduler exceptions can be chained with 'from'."""
        original = ValueError("original error")
        try:
            raise CircularDependencyError("job-1", "job-2") from original
        except CircularDependencyError as e:
            assert e.__cause__ is original
            assert e.job_id == "job-1"
