from unittest.mock import MagicMock
from app.core.task_queue import (
    TaskStatus,
    TaskPriority,
    RetryableError,
    NonRetryableError,
    TicketProcessingCeleryTask,
    calculate_retry_wait,
    classify_error,
)


class TestTaskStatus:
    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "PENDING"
        assert TaskStatus.RUNNING.value == "RUNNING"
        assert TaskStatus.COMPLETED.value == "COMPLETED"
        assert TaskStatus.FAILED.value == "FAILED"
        assert TaskStatus.RETRY.value == "RETRY"


class TestTaskPriority:
    def test_task_priority_values(self):
        assert TaskPriority.LOW.value == 0
        assert TaskPriority.NORMAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.CRITICAL.value == 3

    def test_task_priority_ordering(self):
        assert TaskPriority.LOW < TaskPriority.NORMAL
        assert TaskPriority.NORMAL < TaskPriority.HIGH
        assert TaskPriority.HIGH < TaskPriority.CRITICAL


class TestRetryConfiguration:
    def test_calculate_retry_wait(self):
        wait = calculate_retry_wait(1)
        assert wait >= 5

    def test_calculate_retry_wait_increases(self):
        wait1 = calculate_retry_wait(1)
        wait2 = calculate_retry_wait(2)
        assert wait2 > wait1


class TestErrorClassification:
    def test_classify_retryable_timeout(self):
        error = Exception("Connection timeout")
        error_type = classify_error(error)
        assert error_type == RetryableError

    def test_classify_retryable_connection(self):
        error = Exception("Connection refused")
        error_type = classify_error(error)
        assert error_type == RetryableError

    def test_classify_retryable_rate_limit(self):
        error = Exception("Rate limit exceeded")
        error_type = classify_error(error)
        assert error_type == RetryableError

    def test_classify_non_retryable_auth(self):
        error = Exception("Authentication failed")
        error_type = classify_error(error)
        assert error_type == NonRetryableError

    def test_classify_non_retryable_not_found(self):
        error = Exception("Resource not found")
        error_type = classify_error(error)
        assert error_type == NonRetryableError

    def test_classify_non_retryable_invalid(self):
        error = Exception("Invalid input")
        error_type = classify_error(error)
        assert error_type == NonRetryableError


class TestCeleryTask:
    def test_task_on_failure(self):
        task = TicketProcessingCeleryTask()
        task._retry_count = 2
        task.request = MagicMock()
        task.request.id = "test-task-id"

        exc = Exception("Test error")
        task.on_failure(exc, "test-id", [], {}, {})

        assert task._retry_count == 0

    def test_task_on_success(self):
        task = TicketProcessingCeleryTask()
        task._retry_count = 2
        task.request = MagicMock()
        task.request.id = "test-task-id"

        task.on_success({"result": "success"}, "test-id", [], {})

        assert task._retry_count == 0

    def test_task_on_retry(self):
        task = TicketProcessingCeleryTask()
        task._retry_count = 0
        task.request = MagicMock()
        task.request.id = "test-task-id"

        exc = RetryableError("Retry needed")
        task.on_retry(exc, "test-id", [], {}, {})

        assert task._retry_count == 1
