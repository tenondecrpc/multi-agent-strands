from typing import AsyncGenerator

import app.config  # noqa: F401 - ensures .env is loaded

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://agent:agent_local@db:5432/multi_agent"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
