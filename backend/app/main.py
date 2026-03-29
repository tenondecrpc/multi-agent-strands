from contextlib import asynccontextmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Multi-Agent Strands API", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
