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
    emit_llm_credit_exhausted,
    emit_llm_rate_limited,
)
from app.models.agent_session_model import AgentSession, AgentSessionStatus, AgentType
from app.models.agent_event import AgentEvent, EventType
from app.utils.llm_errors import is_llm_credit_error, classify_llm_error

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


async def get_or_create_session(ticket_id: str, session_uuid: UUID) -> AgentSession:
    async with async_session_maker() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(AgentSession).where(AgentSession.id == session_uuid)
        )
        agent_session = result.scalar_one_or_none()
        if agent_session:
            session.expunge(agent_session)
            return agent_session
        return await create_session(ticket_id)


async def _resolve_session(ticket_id: str, session_uuid: UUID | None) -> AgentSession:
    if session_uuid:
        async with async_session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(AgentSession).where(AgentSession.id == session_uuid)
            )
            agent_session = result.scalar_one_or_none()
            if agent_session:
                session.expunge(agent_session)
                return agent_session
    return await create_session(ticket_id)


async def update_session_status(
    session_id: UUID, status: AgentSessionStatus, error: str | None = None
) -> None:
    async with async_session_maker() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        agent_session = result.scalar_one_or_none()
        if agent_session:
            agent_session.status = status
            if error:
                agent_session.error = error[:1000]
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
    logger.info(f"Emitting event {event_type.value} for session {session_id_str}")
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
    elif event_type == EventType.LLM_CREDIT_EXHAUSTED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "llm_credit_exhausted",
            payload,
        )
    elif event_type == EventType.LLM_RATE_LIMITED:
        await emit_agent_event(
            session_id_str,
            agent_id,
            "llm_rate_limited",
            payload,
        )

    return event


async def launch_agent_pipeline(
    ticket_id: str, existing_session_id: UUID | None = None
) -> dict[str, Any]:
    logger.info(f"Launching agent pipeline for ticket: {ticket_id}")

    session = await _resolve_session(ticket_id, existing_session_id)
    session_id_str = str(session.id)

    await create_event(
        session.id, "orchestrator", EventType.AGENT_STARTED, {"ticket_id": ticket_id}
    )

    await emit_pipeline_started(session_id_str, ticket_id)

    guardrails = PipelineGuardrails()
    guardrails.start()

    try:
        agent = await create_orchestrator_agent(
            ticket_id=ticket_id, session_id=session_id_str
        )

        prompt = f"Process Jira ticket {ticket_id}. Get the issue details, understand the requirements, and coordinate the development pipeline."

        async def _run_with_streaming():
            result_text = []
            pending_tools: set[str] = set()
            emitted_started: set[str] = set()
            emitted_completed: set[str] = set()

            async def _emit_tool_completed(tool_name: str):
                if tool_name in emitted_completed:
                    return
                emitted_completed.add(tool_name)
                await create_event(
                    session.id,
                    "orchestrator",
                    EventType.TOOL_CALL,
                    {"tool_name": tool_name, "status": "completed"},
                )
                await emit_agent_event(
                    session_id_str,
                    "orchestrator",
                    "agent_log",
                    {
                        "message": f"Tool result: {tool_name} (completed)",
                        "level": "info",
                        "progress": 0.5,
                    },
                )

            async for event in agent.stream_async(prompt):
                logger.debug(
                    f"Stream event: {type(event).__name__} | keys: {list(event.keys()) if isinstance(event, dict) else 'N/A'}"
                )

                if not isinstance(event, dict):
                    continue

                if "current_tool_use" in event:
                    tool_use = event["current_tool_use"]
                    tool_name = tool_use.get("name", "unknown")

                    for pending_name in list(pending_tools):
                        if pending_name != tool_name:
                            await _emit_tool_completed(pending_name)
                    pending_tools.clear()

                    pending_tools.add(tool_name)

                    if tool_name not in emitted_started:
                        emitted_started.add(tool_name)
                        await create_event(
                            session.id,
                            "orchestrator",
                            EventType.TOOL_CALL,
                            {"tool_name": tool_name, "status": "started"},
                        )
                        await emit_agent_event(
                            session_id_str,
                            "orchestrator",
                            "agent_log",
                            {
                                "message": f"Tool call: {tool_name}",
                                "level": "info",
                                "progress": 0.2,
                            },
                        )

                elif "text" in event:
                    text = event.get("text", "")
                    if text:
                        result_text.append(text)

                elif "delta_data" in event:
                    delta = event.get("delta_data", {})
                    if isinstance(delta, dict):
                        for choice in delta.get("choices", []):
                            content_block = choice.get("delta", {}).get("content", "")
                            if content_block:
                                result_text.append(str(content_block))

                elif "init_event_loop" in event:
                    await create_event(
                        session.id,
                        "orchestrator",
                        EventType.AGENT_STARTED,
                        {"ticket_id": ticket_id},
                    )

                elif "result" in event:
                    result_text.append(str(event.get("result", "")))

            for tool_name in list(pending_tools):
                await _emit_tool_completed(tool_name)
            pending_tools.clear()

            return "".join(result_text) if result_text else "No result"

        result = await asyncio.wait_for(
            _run_with_streaming(),
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
        await update_session_status(
            session.id, AgentSessionStatus.FAILED, error=error_msg
        )
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
        await update_session_status(
            session.id, AgentSessionStatus.FAILED, error=error_msg
        )
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
        error_type = classify_llm_error(str(e))
        logger.error(error_msg)
        await update_session_status(
            session.id, AgentSessionStatus.FAILED, error=error_msg
        )

        if is_llm_credit_error(str(e)):
            logger.critical(f"LLM credit exhausted for ticket {ticket_id}: {error_msg}")
            await create_event(
                session.id,
                "orchestrator",
                EventType.LLM_CREDIT_EXHAUSTED,
                {"error": error_msg, "error_type": error_type},
            )
            await emit_llm_credit_exhausted(
                session_id=session_id_str,
                ticket_id=ticket_id,
                error=error_msg,
                agent_type="orchestrator",
            )
        elif error_type == "rate_limited":
            logger.warning(f"LLM rate limited for ticket {ticket_id}: {error_msg}")
            await create_event(
                session.id,
                "orchestrator",
                EventType.LLM_RATE_LIMITED,
                {"error": error_msg, "error_type": error_type},
            )
            await emit_llm_rate_limited(
                session_id=session_id_str,
                ticket_id=ticket_id,
                error=error_msg,
                agent_type="orchestrator",
            )
        else:
            await create_event(
                session.id,
                "orchestrator",
                EventType.AGENT_FAILED,
                {"error": error_msg, "error_type": error_type},
            )
            await emit_pipeline_error(session_id_str, ticket_id, error_msg)

        return {
            "ticket_id": ticket_id,
            "status": "error",
            "session_id": session_id_str,
            "error": error_msg,
            "error_type": error_type,
        }
