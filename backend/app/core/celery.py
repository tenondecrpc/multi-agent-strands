from celery import Celery

from app.core.config import (
    CELERY_ACCEPT_CONTENT,
    CELERY_BROKER_URL,
    CELERY_ENABLE_UTC,
    CELERY_RESULT_BACKEND,
    CELERY_RESULT_EXTENDED,
    CELERY_TASK_REJECT_ON_WORKER_LOST,
    CELERY_TASK_SERIALIZER,
    CELERY_TIMEZONE,
    CELERY_RESULT_SERIALIZER,
    CELERY_TASK_ACKS_LATE,
)

celery_app = Celery(
    "multi_agent_strands",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.core.task_queue"],
)

celery_app.conf.update(
    task_serializer=CELERY_TASK_SERIALIZER,
    result_serializer=CELERY_RESULT_SERIALIZER,
    accept_content=CELERY_ACCEPT_CONTENT,
    timezone=CELERY_TIMEZONE,
    enable_utc=CELERY_ENABLE_UTC,
    task_acks_late=CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=CELERY_TASK_REJECT_ON_WORKER_LOST,
    result_extended=CELERY_RESULT_EXTENDED,
)

if __name__ == "__main__":
    celery_app.start()
