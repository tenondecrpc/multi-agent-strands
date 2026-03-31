import logging
import socketio

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
)

NAMESPACE = "/pipeline"


class PipelineNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        logger.info(f"Client connected to /pipeline: {sid}")

    async def on_disconnect(self, sid):
        logger.info(f"Client disconnected from /pipeline: {sid}")

    async def on_join_session(self, sid, data):
        session_id = data.get("session_id")
        if session_id:
            await self.enter_room(sid, session_id)
            logger.info(f"Client {sid} joined session {session_id}")

    async def on_leave_session(self, sid, data):
        session_id = data.get("session_id")
        if session_id:
            await self.leave_room(sid, session_id)
            logger.info(f"Client {sid} left session {session_id}")


sio.register_namespace(PipelineNamespace(NAMESPACE))


async def emit_pipeline_started(session_id: str, ticket_id: str) -> None:
    await sio.emit(
        "pipeline_started",
        {"session_id": session_id, "ticket_id": ticket_id},
        namespace=NAMESPACE,
    )


async def emit_pipeline_completed(
    session_id: str, ticket_id: str, result: dict
) -> None:
    await sio.emit(
        "pipeline_completed",
        {"session_id": session_id, "ticket_id": ticket_id, "result": result},
        namespace=NAMESPACE,
    )


async def emit_pipeline_error(session_id: str, ticket_id: str, error: str) -> None:
    await sio.emit(
        "pipeline_error",
        {"session_id": session_id, "ticket_id": ticket_id, "error": error},
        namespace=NAMESPACE,
    )


async def emit_agent_event(
    session_id: str,
    agent_id: str,
    event_type: str,
    payload: dict | None = None,
) -> None:
    event_data = {
        "type": event_type,
        "session_id": session_id,
        "payload": (payload or {}) | {"agent_id": agent_id},
    }
    await sio.emit(
        "agent_event",
        event_data,
        namespace=NAMESPACE,
    )


async def emit_llm_credit_exhausted(
    session_id: str,
    ticket_id: str,
    error: str,
    agent_type: str | None = None,
) -> None:
    logger.warning(
        f"LLM credit exhausted: session={session_id}, ticket={ticket_id}, agent_type={agent_type}"
    )
    await sio.emit(
        "llm_credit_exhausted",
        {
            "session_id": session_id,
            "ticket_id": ticket_id,
            "error": error,
            "agent_type": agent_type,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        },
        namespace=NAMESPACE,
    )


async def emit_llm_rate_limited(
    session_id: str,
    ticket_id: str,
    error: str,
    agent_type: str | None = None,
    retry_count: int = 0,
) -> None:
    logger.warning(
        f"LLM rate limited: session={session_id}, ticket={ticket_id}, agent_type={agent_type}, retry={retry_count}"
    )
    await sio.emit(
        "llm_rate_limited",
        {
            "session_id": session_id,
            "ticket_id": ticket_id,
            "error": error,
            "agent_type": agent_type,
            "retry_count": retry_count,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        },
        namespace=NAMESPACE,
    )
