from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_session import AgentSession
from app.schemas.session import SessionResponse, SessionListResponse, SessionAgent

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentSession).order_by(AgentSession.created_at.desc())
    )
    sessions = result.scalars().all()

    session_responses = []
    for session in sessions:
        agents = [
            SessionAgent(
                id="orchestrator",
                name="Orchestrator",
                role="orchestrator",
                state="idle",
            ),
            SessionAgent(
                id="backend_agent", name="Backend Agent", role="backend", state="idle"
            ),
            SessionAgent(
                id="frontend_agent",
                name="Frontend Agent",
                role="frontend",
                state="idle",
            ),
            SessionAgent(id="qa_agent", name="QA Agent", role="qa", state="idle"),
        ]
        session_responses.append(
            SessionResponse(
                session_id=str(session.id),
                ticket_id=session.ticket_id,
                status=session.status.value,
                created_at=session.created_at,
                agents=agents,
            )
        )

    return SessionListResponse(sessions=session_responses)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentSession).where(AgentSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agents = [
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

    return SessionResponse(
        session_id=str(session.id),
        ticket_id=session.ticket_id,
        status=session.status.value,
        created_at=session.created_at,
        agents=agents,
    )
