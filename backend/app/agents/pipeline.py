from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any
from uuid import UUID
import uuid

import app.config  # noqa: F401 - ensures .env is loaded

from app.agents.orchestrator import create_orchestrator_agent
from app.database import async_session_maker
from app.events import (
    emit_agent_event,
    emit_pipeline_completed,
    emit_pipeline_error,
    emit_pipeline_started,
)
from app.models.agent_session_model import AgentSession, AgentSessionStatus, AgentType
from app.models.agent_event import AgentEvent, EventType

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = int(os.getenv("MAX_TOOL_CALLS", "100"))
MAX_TOKEN_BUDGET = int(os.getenv("MAX_TOKEN_BUDGET", "100000"))
PIPELINE_TIMEOUT_SECONDS = int(os.getenv("PIPELINE_TIMEOUT_SECONDS", "600"))


class TokenTracker:
    def __init__(self, max_tokens: int = MAX_TOKEN_BUDGET):
        self.max_tokens = max_tokens
        self.tokens_used = 0

    def add_usage(self, tokens: int) -> None:
        self.tokens_used += tokens
        if self.tokens_used > self.max_tokens:
            raise RuntimeError(
                f"Token budget exceeded: {self.tokens_used}/{self.max_tokens}"
            )


class ToolCallTracker:
    def __init__(self, max_calls: int = MAX_TOOL_CALLS):
        self.max_calls = max_calls
        self.call_count = 0

    def increment(self) -> None:
        self.call_count += 1
        if self.call_count > self.max_calls:
            raise RuntimeError(
                f"Max tool calls exceeded: {self.call_count}/{self.max_calls}"
            )


class PipelineGuardrails:
    def __init__(
        self,
        token_tracker: TokenTracker | None = None,
        tool_call_tracker: ToolCallTracker | None = None,
        timeout_seconds: int = PIPELINE_TIMEOUT_SECONDS,
    ):
        self.token_tracker = token_tracker or TokenTracker()
        self.tool_call_tracker = tool_call_tracker or ToolCallTracker()
        self.timeout_seconds = timeout_seconds
        self.start_time: float | None = None

    def start(self) -> None:
        self.start_time = time.time()

    def check_timeout(self) -> None:
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            raise RuntimeError(
                f"Pipeline timeout exceeded: {elapsed:.1f}s/{self.timeout_seconds}s"
            )

    def check(self) -> None:
        self.tool_call_tracker.increment()
        self.check_timeout()


async def create_session(ticket_id: str) -> AgentSession:
    async with async_session_maker() as session:
        agent_session = AgentSession(
            session_id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            agent_type=AgentType.ORCHESTRATOR,
            status=AgentSessionStatus.RUNNING,
        )
        session.add(agent_session)
        await session.commit()
        await session.refresh(agent_session)
        return agent_session


async def update_session_status(session_id: UUID, status: AgentSessionStatus) -> None:
    async with async_session_maker() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        agent_session = result.scalar_one_or_none()
        if agent_session:
            agent_session.status = status
            await session.commit()


async def create_event(
    session_id: UUID,
    agent_id: str,
    event_type: EventType,
    payload: dict[str, Any] | None = None,
) -> AgentEvent:
    async with async_session_maker() as session:
        event = AgentEvent(
            session_id=session_id,
            agent_id=agent_id,
            event_type=event_type,
            payload=payload,
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)

    session_id_str = str(session_id)
    if event_type == EventType.AGENT_STARTED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_state_change",
            {
                "new_state": "working",
                "task": payload.get("ticket_id", "") if payload else "",
                "progress": 0.1,
            },
        )
    elif event_type == EventType.AGENT_COMPLETED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_state_change",
            {"new_state": "success", "progress": 1},
        )
    elif event_type == EventType.AGENT_FAILED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_state_change",
            {
                "new_state": "error",
                "error": payload.get("error", "") if payload else "",
            },
        )
    elif event_type == EventType.LOG:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_log",
            payload,
        )
    elif event_type == EventType.TOOL_CALL:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_log",
            {
                "message": f"Tool call: {payload.get('tool_name', 'unknown')}",
                "level": "info",
            },
        )
    elif event_type == EventType.AGENT_COMPLETED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_state_change",
            {"new_state": "success", "progress": 1},
        )
    elif event_type == EventType.AGENT_FAILED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_state_change",
            {
                "new_state": "error",
                "error": payload.get("error", "") if payload else "",
            },
        )
    elif event_type == EventType.LOG:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "agent_log",
            payload,
        )

    return event


async def launch_agent_pipeline(ticket_id: str) -> dict[str, Any]:
    logger.info(f"Launching agent pipeline for ticket: {ticket_id}")

    session = await create_session(ticket_id)
    session_id_str = str(session.id)

    await create_event(
        session.id, "orchestrator", EventType.AGENT_STARTED, {"ticket_id": ticket_id}
    )

    await emit_pipeline_started(session_id_str, ticket_id)

    guardrails = PipelineGuardrails()
    guardrails.start()

    try:
        agent = await create_orchestrator_agent()

        result = await asyncio.wait_for(
            agent(
                f"Process Jira ticket {ticket_id}. Get the issue details, understand the requirements, and coordinate the development pipeline."
            ),
            timeout=guardrails.timeout_seconds,
        )

        await update_session_status(session.id, AgentSessionStatus.COMPLETED)
        await create_event(
            session.id,
            "orchestrator",
            EventType.AGENT_COMPLETED,
            {"result": str(result)},
        )

        await emit_pipeline_completed(
            session_id_str, ticket_id, {"status": "completed"}
        )

        logger.info(f"Pipeline completed for ticket: {ticket_id}")
        return {
            "ticket_id": ticket_id,
            "status": "completed",
            "session_id": session_id_str,
            "result": str(result),
        }

    except asyncio.TimeoutError:
        error_msg = f"Pipeline timed out after {guardrails.timeout_seconds} seconds"
        logger.error(error_msg)
        await update_session_status(session.id, AgentSessionStatus.FAILED)
        await create_event(
            session.id, "orchestrator", EventType.AGENT_FAILED, {"error": error_msg}
        )

        await emit_pipeline_error(session_id_str, ticket_id, error_msg)

        return {
            "ticket_id": ticket_id,
            "status": "timeout",
            "session_id": session_id_str,
            "error": error_msg,
        }

    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"Pipeline guardrail triggered: {error_msg}")
        await update_session_status(session.id, AgentSessionStatus.FAILED)
        await create_event(
            session.id, "orchestrator", EventType.AGENT_FAILED, {"error": error_msg}
        )

        await emit_pipeline_error(session_id_str, ticket_id, error_msg)

        return {
            "ticket_id": ticket_id,
            "status": "guardrail",
            "session_id": session_id_str,
            "error": error_msg,
        }

    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        logger.error(error_msg)
        await update_session_status(session.id, AgentSessionStatus.FAILED)
        await create_event(
            session.id, "orchestrator", EventType.AGENT_FAILED, {"error": error_msg}
        )

        await emit_pipeline_error(session_id_str, ticket_id, error_msg)

        return {
            "ticket_id": ticket_id,
            "status": "error",
            "session_id": session_id_str,
            "error": error_msg,
        }
