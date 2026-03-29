import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
