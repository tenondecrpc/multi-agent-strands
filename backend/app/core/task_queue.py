import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from celery import Task
from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.celery import celery_app
from app.core.config import RETRY_CONFIG
from app.core.logging import get_logger


logger = get_logger(__name__)


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class RetryableError(Exception):
    pass


class NonRetryableError(Exception):
    pass


class AgentExecutionError(Exception):
    def __init__(
        self, agent_name: str, task_description: str, original_error: Exception
    ):
        self.agent_name = agent_name
        self.task_description = task_description
        self.original_error = original_error
        super().__init__(
            f"Agent {agent_name} failed on task '{task_description}': {original_error}"
        )


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0


@dataclass
class TicketProcessingTask:
    ticket_id: str
    agent_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)


def calculate_retry_wait(attempt: int) -> float:
    wait_time = RETRY_CONFIG["initial_wait"] * (
        RETRY_CONFIG["multiplier"] ** (attempt - 1)
    )
    return min(wait_time, RETRY_CONFIG["max_wait"])


def tenacity_retry_condition(retry_state: RetryCallState) -> bool:
    exception = retry_state.outcome.exception()
    return isinstance(exception, RetryableError)


celery_task_retry = {
    "stop": stop_after_attempt(RETRY_CONFIG["max_attempts"]),
    "wait": wait_exponential(
        multiplier=RETRY_CONFIG["multiplier"],
        min=RETRY_CONFIG["initial_wait"],
        max=RETRY_CONFIG["max_wait"],
    ),
    "retry": retry_if_exception_type(RetryableError),
    "before_sleep": before_sleep_log(logger, logging.WARNING),
    "reraise": True,
}


class TicketProcessingCeleryTask(Task):
    def __init__(self):
        super().__init__()
        self._retry_count = 0

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        self._retry_count = 0

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {task_id} retrying due to: {exc}")
        self._retry_count += 1

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded")
        self._retry_count = 0


@celery_app.task(
    bind=True,
    base=TicketProcessingCeleryTask,
    max_retries=RETRY_CONFIG["max_attempts"],
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_ticket_task(
    self, ticket_id: str, agent_type: str, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    logger.info(f"Processing ticket {ticket_id} with agent {agent_type}")

    task_data = TicketProcessingTask(
        ticket_id=ticket_id,
        agent_type=agent_type,
        metadata=metadata or {},
    )

    try:
        result = _execute_ticket_processing(task_data)
        return {
            "task_id": self.request.id,
            "status": TaskStatus.COMPLETED.value,
            "result": result,
        }
    except RetryableError as e:
        logger.warning(f"Retryable error for ticket {ticket_id}: {e}")
        raise self.retry(
            exc=e, countdown=calculate_retry_wait(self.request.retries + 1)
        )
    except NonRetryableError as e:
        logger.error(f"Non-retryable error for ticket {ticket_id}: {e}")
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }
    except Exception as e:
        logger.exception(f"Unexpected error processing ticket {ticket_id}")
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }


def _execute_ticket_processing(task_data: TicketProcessingTask) -> dict[str, Any]:
    return {
        "ticket_id": task_data.ticket_id,
        "agent_type": task_data.agent_type,
        "processed": True,
    }


@celery_app.task(
    bind=True,
    base=TicketProcessingCeleryTask,
    max_retries=RETRY_CONFIG["max_attempts"],
)
def enrich_ticket_task(self, ticket_id: str, jira_key: str) -> dict[str, Any]:
    logger.info(f"Enriching ticket {ticket_id} from Jira {jira_key}")

    try:
        result = _execute_ticket_enrichment(ticket_id, jira_key)
        return {
            "task_id": self.request.id,
            "status": TaskStatus.COMPLETED.value,
            "result": result,
        }
    except RetryableError as e:
        raise self.retry(
            exc=e, countdown=calculate_retry_wait(self.request.retries + 1)
        )
    except NonRetryableError as e:
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }
    except Exception as e:
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }


def _execute_ticket_enrichment(ticket_id: str, jira_key: str) -> dict[str, Any]:
    return {
        "ticket_id": ticket_id,
        "jira_key": jira_key,
        "enriched": True,
    }


@celery_app.task(
    bind=True,
    base=TicketProcessingCeleryTask,
    max_retries=RETRY_CONFIG["max_attempts"],
)
def triage_ticket_task(
    self, ticket_id: str, ticket_data: dict[str, Any]
) -> dict[str, Any]:
    logger.info(f"Triaging ticket {ticket_id}")

    try:
        result = _execute_triage(ticket_id, ticket_data)
        return {
            "task_id": self.request.id,
            "status": TaskStatus.COMPLETED.value,
            "result": result,
        }
    except RetryableError as e:
        raise self.retry(
            exc=e, countdown=calculate_retry_wait(self.request.retries + 1)
        )
    except NonRetryableError as e:
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }
    except Exception as e:
        return {
            "task_id": self.request.id,
            "status": TaskStatus.FAILED.value,
            "error": str(e),
        }


def _execute_triage(ticket_id: str, ticket_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "ticket_id": ticket_id,
        "suggested_agent": "backend",
        "confidence": 0.85,
    }


def classify_error(
    error: Exception,
) -> tuple[type[RetryableError], type[NonRetryableError]]:
    if isinstance(error, (RetryableError, NonRetryableError)):
        return type(error)

    error_messages = {
        "connection": RetryableError,
        "timeout": RetryableError,
        "rate limit": RetryableError,
        "authentication": NonRetryableError,
        "not found": NonRetryableError,
        "invalid": NonRetryableError,
    }

    error_str = str(error).lower()
    for pattern, error_type in error_messages.items():
        if pattern in error_str:
            return error_type

    return RetryableError
