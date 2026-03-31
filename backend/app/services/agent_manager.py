import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator

from app.agents.backend_agent import create_backend_agent
from app.agents.frontend_agent import create_frontend_agent
from app.agents.qa_agent import create_qa_agent
from app.agents.orchestrator import create_orchestrator_agent
from app.core.config import AGENT_CONFIG
from app.core.logging import get_logger
from app.core.event_bus import EventBus
from app.models.agent_session_model import AgentType
from app.models.events import EventType
from app.utils.llm_errors import is_llm_credit_error, classify_llm_error
from app.events import emit_llm_credit_exhausted, emit_llm_rate_limited

logger = get_logger(__name__)


@dataclass
class AgentConfig:
    name: str
    model: str
    system_prompt: str
    tools: list[str]
    max_iterations: int = AGENT_CONFIG["max_iterations"]
    timeout_seconds: int = AGENT_CONFIG["timeout_seconds"]


@dataclass
class HandoffEntry:
    from_agent: str
    to_agent: str
    summary: str
    timestamp: datetime


@dataclass
class AgentContext:
    session_id: str
    ticket_id: str
    agent_type: AgentType
    current_task: str | None = None
    previous_results: list[dict[str, Any]] = field(default_factory=list)
    shared_state: dict[str, Any] = field(default_factory=dict)
    handoff_log: list[HandoffEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_handoff(self, from_agent: str, to_agent: str, summary: str) -> None:
        entry = HandoffEntry(
            from_agent=from_agent,
            to_agent=to_agent,
            summary=summary,
            timestamp=datetime.utcnow(),
        )
        self.handoff_log.append(entry)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "ticket_id": self.ticket_id,
            "agent_type": self.agent_type.value,
            "current_task": self.current_task,
            "previous_results": self.previous_results,
            "shared_state": self.shared_state,
            "handoff_log": [
                {
                    "from_agent": h.from_agent,
                    "to_agent": h.to_agent,
                    "summary": h.summary,
                    "timestamp": h.timestamp.isoformat(),
                }
                for h in self.handoff_log
            ],
            "created_at": self.created_at.isoformat(),
        }


AGENT_CONFIGS: dict[AgentType, AgentConfig] = {
    AgentType.BACKEND: AgentConfig(
        name="Backend Agent",
        model="default",
        system_prompt="You are a backend development agent specialized in Python, APIs, and server-side logic.",
        tools=["file_read", "file_write", "shell", "python_repl"],
    ),
    AgentType.FRONTEND: AgentConfig(
        name="Frontend Agent",
        model="default",
        system_prompt="You are a frontend development agent specialized in React, TypeScript, and UI components.",
        tools=["file_read", "file_write", "shell"],
    ),
    AgentType.QA: AgentConfig(
        name="QA Agent",
        model="default",
        system_prompt="You are a QA agent specialized in testing and quality assurance.",
        tools=["file_read", "shell"],
    ),
    AgentType.ARCHITECT: AgentConfig(
        name="Architect Agent",
        model="default",
        system_prompt="You are an architect agent specialized in system design and technical decisions.",
        tools=["file_read", "file_write"],
    ),
    AgentType.ORCHESTRATOR: AgentConfig(
        name="Orchestrator Agent",
        model="default",
        system_prompt="You are an orchestrator agent that coordinates other agents and manages the overall workflow.",
        tools=["file_read", "file_write", "shell"],
    ),
}


class AgentManager:
    def __init__(self, event_bus: EventBus):
        self._sessions: dict[str, AgentContext] = {}
        self._event_bus = event_bus

    def _generate_session_id(self, ticket_id: str, agent_type: AgentType) -> str:
        return f"{ticket_id}-{agent_type.value}-{uuid.uuid4().hex[:8]}"

    def start_session(self, ticket_id: str, agent_type: AgentType) -> AgentContext:
        session_id = self._generate_session_id(ticket_id, agent_type)
        context = AgentContext(
            session_id=session_id,
            ticket_id=ticket_id,
            agent_type=agent_type,
        )
        self._sessions[session_id] = context
        logger.info(
            f"Started session {session_id} for ticket {ticket_id} with agent {agent_type.value}"
        )
        return context

    def get_session(self, session_id: str) -> AgentContext:
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def cleanup_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")

    async def execute_agent(
        self,
        session_id: str,
        task: str,
        event_bus: EventBus | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        context = self.get_session(session_id)
        context.current_task = task

        logger.info(f"Executing agent for session {session_id}: {task}")

        await (event_bus or self._event_bus).publish_ticket_event(
            event_type=EventType.AGENT_STARTED,
            ticket_id=context.ticket_id,
            agent_id=session_id,
            payload={"task": task, "agent_type": context.agent_type.value},
        )

        agent = self._get_agent_instance(context.agent_type)

        try:
            async for event in agent.stream_async(task):
                yield {"type": "token", "content": event, "session_id": session_id}

            await (event_bus or self._event_bus).publish_ticket_event(
                event_type=EventType.AGENT_COMPLETED,
                ticket_id=context.ticket_id,
                agent_id=session_id,
                payload={"task": task},
            )
        except Exception as e:
            error_msg = str(e)
            error_type = classify_llm_error(error_msg)
            logger.error(
                f"Agent execution failed for session {session_id}: {error_msg} (type: {error_type})"
            )

            if is_llm_credit_error(error_msg):
                logger.critical(
                    f"LLM credit exhausted for session {session_id}, ticket {context.ticket_id}"
                )
                await (event_bus or self._event_bus).publish_ticket_event(
                    event_type=EventType.LLM_CREDIT_EXHAUSTED,
                    ticket_id=context.ticket_id,
                    agent_id=session_id,
                    payload={
                        "error": error_msg,
                        "error_type": error_type,
                        "agent_type": context.agent_type.value,
                        "task": task,
                    },
                )
                await emit_llm_credit_exhausted(
                    session_id=session_id,
                    ticket_id=context.ticket_id,
                    error=error_msg,
                    agent_type=context.agent_type.value,
                )
            elif error_type == "rate_limited":
                logger.warning(
                    f"LLM rate limited for session {session_id}, ticket {context.ticket_id}"
                )
                await (event_bus or self._event_bus).publish_ticket_event(
                    event_type=EventType.LLM_RATE_LIMITED,
                    ticket_id=context.ticket_id,
                    agent_id=session_id,
                    payload={
                        "error": error_msg,
                        "error_type": error_type,
                        "agent_type": context.agent_type.value,
                        "task": task,
                    },
                )
                await emit_llm_rate_limited(
                    session_id=session_id,
                    ticket_id=context.ticket_id,
                    error=error_msg,
                    agent_type=context.agent_type.value,
                )
            else:
                await (event_bus or self._event_bus).publish_ticket_event(
                    event_type=EventType.AGENT_FAILED,
                    ticket_id=context.ticket_id,
                    agent_id=session_id,
                    payload={
                        "task": task,
                        "error": error_msg,
                        "error_type": error_type,
                    },
                )

            yield {
                "type": "error",
                "content": error_msg,
                "session_id": session_id,
                "error_type": error_type,
            }

    def _get_agent_instance(self, agent_type: AgentType):
        agent_factories = {
            AgentType.BACKEND: create_backend_agent,
            AgentType.FRONTEND: create_frontend_agent,
            AgentType.QA: create_qa_agent,
            AgentType.ARCHITECT: create_orchestrator_agent,
            AgentType.ORCHESTRATOR: create_orchestrator_agent,
        }
        agent_factory = agent_factories.get(agent_type, create_orchestrator_agent)
        return agent_factory()

    async def handoff(
        self,
        session_id: str,
        from_agent: str,
        to_agent: AgentType,
        summary: str,
    ) -> AgentContext:
        context = self.get_session(session_id)

        context.add_handoff(
            from_agent=from_agent,
            to_agent=to_agent.value,
            summary=summary,
        )

        context.agent_type = to_agent

        new_session_id = self._generate_session_id(context.ticket_id, to_agent)
        context.session_id = new_session_id
        self._sessions[new_session_id] = context

        logger.info(
            f"Handoff from {from_agent} to {to_agent.value} for ticket {context.ticket_id}"
        )

        await self._event_bus.publish_ticket_event(
            event_type=EventType.AGENT_HANDOFF,
            ticket_id=context.ticket_id,
            agent_id=new_session_id,
            payload={
                "from_agent": from_agent,
                "to_agent": to_agent.value,
                "summary": summary,
            },
        )

        return context

    def get_active_sessions(self) -> list[AgentContext]:
        return list(self._sessions.values())

    def get_session_count(self) -> int:
        return len(self._sessions)


agent_manager = AgentManager(event_bus=None)
