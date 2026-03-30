import pytest
from app.core.task_queue import (
    RetryableError,
    NonRetryableError,
    AgentExecutionError,
    calculate_retry_wait,
    classify_error,
    RETRY_CONFIG,
)


class TestRetryConfig:
    def test_default_retry_config(self):
        assert RETRY_CONFIG["max_attempts"] == 3
        assert RETRY_CONFIG["initial_wait"] == 5
        assert RETRY_CONFIG["max_wait"] == 60
        assert RETRY_CONFIG["multiplier"] == 2


class TestCalculateRetryWait:
    def test_wait_increases_with_attempts(self):
        wait_1 = calculate_retry_wait(1)
        wait_2 = calculate_retry_wait(2)
        wait_3 = calculate_retry_wait(3)

        assert wait_2 > wait_1
        assert wait_3 > wait_2

    def test_wait_respects_max(self):
        wait_10 = calculate_retry_wait(10)

        assert wait_10 <= RETRY_CONFIG["max_wait"]


class TestErrorTypes:
    def test_retryable_error(self):
        error = RetryableError("Temporary failure")
        assert str(error) == "Temporary failure"

    def test_non_retryable_error(self):
        error = NonRetryableError("Permanent failure")
        assert str(error) == "Permanent failure"

    def test_agent_execution_error(self):
        original = Exception("Connection lost")
        error = AgentExecutionError(
            agent_name="Backend Agent",
            task_description="Process ticket",
            original_error=original,
        )

        assert error.agent_name == "Backend Agent"
        assert error.task_description == "Process ticket"
        assert error.original_error == original
        assert "Backend Agent" in str(error)
        assert "Process ticket" in str(error)


class TestClassifyError:
    def test_timeout_is_retryable(self):
        error = Exception("Request timeout after 30s")
        result = classify_error(error)
        assert result == RetryableError

    def test_connection_error_is_retryable(self):
        error = Exception("Connection reset by peer")
        result = classify_error(error)
        assert result == RetryableError

    def test_rate_limit_is_retryable(self):
        error = Exception("Rate limit: 429")
        result = classify_error(error)
        assert result == RetryableError

    def test_auth_error_is_non_retryable(self):
        error = Exception("Invalid API key")
        result = classify_error(error)
        assert result == NonRetryableError

    def test_not_found_is_non_retryable(self):
        error = Exception("Resource not found: /api/tickets")
        result = classify_error(error)
        assert result == NonRetryableError

    def test_invalid_input_is_non_retryable(self):
        error = Exception("Invalid ticket format")
        result = classify_error(error)
        assert result == NonRetryableError

    def test_unknown_error_defaults_to_retryable(self):
        error = Exception("Something went wrong")
        result = classify_error(error)
        assert result == RetryableError


class TestErrorPropagation:
    def test_retryable_error_can_be_raised_and_caught(self):
        with pytest.raises(RetryableError):
            raise RetryableError("Test retryable")

    def test_non_retryable_error_can_be_raised_and_caught(self):
        with pytest.raises(NonRetryableError):
            raise NonRetryableError("Test non-retryable")

    def test_agent_execution_error_contains_context(self):
        original = ValueError("Invalid value")
        error = AgentExecutionError(
            agent_name="Test Agent",
            task_description="Test task",
            original_error=original,
        )

        caught = False
        try:
            raise error
        except AgentExecutionError as e:
            caught = True
            assert e.agent_name == "Test Agent"
            assert e.task_description == "Test task"

        assert caught
