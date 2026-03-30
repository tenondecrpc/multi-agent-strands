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
from app.events import sio

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


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started - Jira webhook endpoint available")
    yield
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


app = ASGIApp(sio, app)
logger.info("FastAPI app mounted with Socket.IO")

socketio_url = os.getenv("VITE_SOCKET_URL", "http://localhost:8000")
logger.info(
    f"Socket.IO ready - connect to {socketio_url}/socket.io/?EIO=4&transport=polling"
)
logger.info("Waiting for client connections...")
