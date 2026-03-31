import logging
import os
from contextlib import asynccontextmanager

import app.config  # noqa: F401 - loads .env at import

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp

from app.api.agents import router as agents_router
from app.api.sessions import router as sessions_router
from app.api.tickets import router as tickets_router
from app.core.logging import setup_structlog
from app.core.redis_bridge import RedisEventSubscriber
from app.events import NAMESPACE, sio

setup_structlog()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Socket.IO server initializing...")
logger.info("  - Async mode: asgi")
logger.info("  - CORS: *")
logger.info("  - Namespaces: /pipeline")

_subscriber: RedisEventSubscriber | None = None


async def _forward_redis_event(event_data: dict) -> None:
    """Forward events from Redis pub/sub to all Socket.IO clients."""
    event_name = event_data.get("event_name")
    data = event_data.get("data", event_data)

    logger.info(f"Forwarding event {event_name}")

    try:
        await sio.emit(
            event_name,
            data,
            namespace=NAMESPACE,
        )
        logger.info(f"Event {event_name} broadcast successfully")
    except Exception:
        logger.exception(f"Failed to forward event {event_name}")


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _subscriber

    logger.info("Application started - Jira webhook endpoint available")
    from app.core.jira_polling import start_jira_polling

    start_jira_polling()

    _subscriber = RedisEventSubscriber(_forward_redis_event)
    await _subscriber.start()

    yield

    if _subscriber:
        await _subscriber.stop()
    logger.info("Shutting down...")


app = FastAPI(title="Multi-Agent Strands API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(tickets_router)
app.include_router(agents_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/debug/subscriber")
async def debug_subscriber():
    global _subscriber
    if _subscriber is None:
        return {"subscriber": "not_initialized"}

    task = _subscriber._task
    if task is None:
        return {"subscriber": "no_task"}

    return {
        "subscriber": "running",
        "task_done": task.done(),
        "task_cancelled": task.cancelled(),
        "task_result": task.result() if task.done() else None,
        "running_flag": _subscriber._running,
    }


app = ASGIApp(sio, app)
logger.info("FastAPI app mounted with Socket.IO")

socketio_url = os.getenv("VITE_SOCKET_URL", "http://localhost:8000")
logger.info(
    f"Socket.IO ready - connect to {socketio_url}/socket.io/?EIO=4&transport=polling"
)
logger.info("Waiting for client connections...")
