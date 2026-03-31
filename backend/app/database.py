from typing import AsyncGenerator

import app.config  # noqa: F401 - ensures .env is loaded

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import asyncio
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://agent:agent_local@db:5432/multi_agent"
)


class _LazyDatabase:
    def __init__(self):
        self._engine = None
        self._session_maker = None
        self._loop_id = None

    def _resolve(self):
        try:
            current_loop_id = id(asyncio.get_running_loop())
        except RuntimeError:
            current_loop_id = id(asyncio.new_event_loop())
        if self._engine is None or self._loop_id != current_loop_id:
            self._engine = create_async_engine(
                DATABASE_URL,
                echo=False,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            self._session_maker = sessionmaker(
                self._engine, class_=AsyncSession, expire_on_commit=False
            )
            self._loop_id = current_loop_id
        return self._engine, self._session_maker

    @property
    def engine(self):
        return self._resolve()[0]

    @property
    def async_session_maker(self):
        return self._resolve()[1]


_db = _LazyDatabase()
engine = _db.engine
async_session_maker = _db.async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
