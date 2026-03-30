import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

TASK_QUEUE_NAME = "ticket_processing"
EVENT_QUEUE_NAME = "event_processing"

CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_RESULT_EXTENDED = True

DEFAULT_RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_wait": 5,
    "max_wait": 60,
    "multiplier": 2,
}

RETRY_CONFIG = {
    "max_attempts": int(
        os.getenv("CELERY_MAX_ATTEMPTS", DEFAULT_RETRY_CONFIG["max_attempts"])
    ),
    "initial_wait": int(
        os.getenv("CELERY_INITIAL_WAIT", DEFAULT_RETRY_CONFIG["initial_wait"])
    ),
    "max_wait": int(os.getenv("CELERY_MAX_WAIT", DEFAULT_RETRY_CONFIG["max_wait"])),
    "multiplier": int(
        os.getenv("CELERY_MULTIPLIER", DEFAULT_RETRY_CONFIG["multiplier"])
    ),
}

EVENT_RETENTION_LIMIT = int(os.getenv("EVENT_RETENTION_LIMIT", "1000"))

AGENT_CONFIG = {
    "max_iterations": int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
    "timeout_seconds": int(os.getenv("AGENT_TIMEOUT_SECONDS", "300")),
}
