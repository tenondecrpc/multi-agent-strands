import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from socketio import ASGIApp

from app.events import sio

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

logger.info("Socket.IO server initializing...")
logger.info(f"  - Async mode: asgi")
logger.info(f"  - CORS: *")
logger.info(f"  - Namespaces: /pipeline")


@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Jira polling service...")
    try:
        from app.mcp.polling import start_jira_polling

        polling_task = start_jira_polling()
        logger.info("Jira polling started successfully")
    except Exception as e:
        logger.error(f"Failed to start Jira polling: {e}")
    yield
    logger.info("Shutting down...")


app = FastAPI(title="Multi-Agent Strands API", lifespan=lifespan)


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
