from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models.agent_session_model import AgentSession
from app.models.agent_event import AgentEvent
from app.models.ticket_state import TicketState
from app.schemas.session import (
    SessionResponse,
    SessionListResponse,
    SessionAgent,
    SessionMetrics,
    AgentLog,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_default_agents() -> list[SessionAgent]:
    return [
        SessionAgent(
            id="orchestrator", name="Orchestrator", role="orchestrator", state="idle"
        ),
        SessionAgent(
            id="backend_agent", name="Backend Agent", role="backend", state="idle"
        ),
        SessionAgent(
            id="frontend_agent", name="Frontend Agent", role="frontend", state="idle"
        ),
        SessionAgent(id="qa_agent", name="QA Agent", role="qa", state="idle"),
    ]


async def _get_session_logs(db: AsyncSession, session_uuid: UUID) -> list[AgentLog]:
    result = await db.execute(
        select(AgentEvent)
        .where(AgentEvent.session_id == session_uuid)
        .order_by(AgentEvent.created_at.desc())
        .limit(100)
    )
    events = result.scalars().all()
    logs = []
    for event in events:
        if event.payload and isinstance(event.payload, dict):
            message = event.payload.get(
                "message", event.payload.get("error", str(event.payload))
            )
            level = event.payload.get("level", "info")
        else:
            message = str(event.payload) if event.payload else ""
            level = "info"
        logs.append(
            AgentLog(
                id=str(event.id),
                agent_id=event.agent_id,
                message=message,
                level=level,
                timestamp=event.created_at,
            )
        )
    return logs


@router.get("", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TicketState).where(TicketState.active_session_id.isnot(None))
    )
    ticket_states = result.scalars().all()

    session_responses = []
    for ts in ticket_states:
        session_result = await db.execute(
            select(AgentSession).where(AgentSession.id == UUID(ts.active_session_id))
        )
        session = session_result.scalar_one_or_none()

        if session:
            session_responses.append(
                SessionResponse(
                    session_id=str(session.id),
                    ticket_id=session.ticket_id,
                    status=session.status.value,
                    started_at=session.started_at,
                    agents=_get_default_agents(),
                    error=session.error,
                )
            )

    return SessionListResponse(sessions=session_responses)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    logs = await _get_session_logs(db, session_uuid)

    return SessionResponse(
        session_id=str(session.id),
        ticket_id=session.ticket_id,
        status=session.status.value,
        started_at=session.started_at,
        agents=_get_default_agents(),
        logs=logs,
        metrics=SessionMetrics(),
        error=session.error,
    )


@router.get("/{session_id}/logs")
async def get_session_logs(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    logs = await _get_session_logs(db, session_uuid)
    return {"logs": logs}


@router.get("/ticket/{ticket_id}/active")
async def get_active_session_for_ticket(
    ticket_id: str, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TicketState).where(TicketState.ticket_id == ticket_id)
    )
    ticket_state = result.scalar_one_or_none()

    if not ticket_state or not ticket_state.active_session_id:
        raise HTTPException(status_code=404, detail="No active session for this ticket")

    try:
        session_uuid = UUID(ticket_state.active_session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    session_result = await db.execute(
        select(AgentSession).where(AgentSession.id == session_uuid)
    )
    session = session_result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session_id": str(session.id), "ticket_id": ticket_id}
