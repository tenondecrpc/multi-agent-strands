from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.database import get_db
from app.models.agent_session_model import (
    AgentSession,
    AgentType,
    AgentSessionStatus,
)
from app.models.events import EventType
from app.services.agent_manager import AgentManager

router = APIRouter(prefix="/sessions", tags=["sessions"])

agent_manager_instance = AgentManager(event_bus)


class CreateSessionRequest(BaseModel):
    ticket_id: str
    agent_type: AgentType


class SessionResponse(BaseModel):
    session_id: str
    ticket_id: str
    agent_type: str
    status: str
    current_task: str | None = None


class ExecuteRequest(BaseModel):
    task: str = Field(..., description="Task description for the agent")


class HandoffRequest(BaseModel):
    from_agent: str = Field(..., description="Source agent name")
    to_agent: AgentType = Field(..., description="Target agent type")
    summary: str = Field(..., description="Handoff summary")


class HandoffResponse(BaseModel):
    session_id: str
    from_agent: str
    to_agent: str
    summary: str
    success: bool


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest, db: AsyncSession = Depends(get_db)
):
    agent_type = AgentType(request.agent_type.value.upper())

    context = agent_manager_instance.start_session(request.ticket_id, agent_type)

    session_model = AgentSession(
        session_id=context.session_id,
        ticket_id=request.ticket_id,
        agent_type=agent_type,
        status=AgentSessionStatus.PENDING,
    )
    db.add(session_model)
    await db.commit()
    await db.refresh(session_model)

    await event_bus.publish_ticket_event(
        event_type=EventType.AGENT_STARTED,
        ticket_id=request.ticket_id,
        agent_id=context.session_id,
        payload={"agent_type": agent_type.value},
    )

    return SessionResponse(
        session_id=context.session_id,
        ticket_id=request.ticket_id,
        agent_type=agent_type.value,
        status=AgentSessionStatus.PENDING.value,
    )


@router.post("/{session_id}/execute")
async def execute_session(
    session_id: str,
    request: ExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentSession).where(AgentSession.session_id == session_id)
    )
    session_model = result.scalar_one_or_none()

    if not session_model:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    session_model.status = AgentSessionStatus.RUNNING
    await db.commit()

    async def generate():
        try:
            agent_manager_instance.get_session(session_id)

            async for chunk in agent_manager_instance.execute_agent(
                session_id, request.task, event_bus
            ):
                if chunk["type"] == "token":
                    yield f"data: {chunk['content']}\n\n"
                elif chunk["type"] == "error":
                    yield f"data: [ERROR] {chunk['content']}\n\n"
                    break
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            session_model.status = AgentSessionStatus.COMPLETED
            await db.commit()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/{session_id}/handoff", response_model=HandoffResponse)
async def handoff_session(
    session_id: str,
    request: HandoffRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentSession).where(AgentSession.session_id == session_id)
    )
    session_model = result.scalar_one_or_none()

    if not session_model:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    try:
        agent_manager_instance.get_session(session_id)

        new_context = await agent_manager_instance.handoff(
            session_id=session_id,
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            summary=request.summary,
        )

        session_model.status = AgentSessionStatus.PENDING
        session_model.agent_type = request.to_agent
        session_model.session_id = new_context.session_id
        await db.commit()

        return HandoffResponse(
            session_id=new_context.session_id,
            from_agent=request.from_agent,
            to_agent=request.to_agent.value,
            summary=request.summary,
            success=True,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        context = agent_manager_instance.get_session(session_id)
        return SessionResponse(
            session_id=context.session_id,
            ticket_id=context.ticket_id,
            agent_type=context.agent_type.value,
            status=AgentSessionStatus.RUNNING.value,
            current_task=context.current_task,
        )
    except KeyError:
        result = await db.execute(
            select(AgentSession).where(AgentSession.session_id == session_id)
        )
        session_model = result.scalar_one_or_none()

        if not session_model:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        return SessionResponse(
            session_id=session_model.session_id,
            ticket_id=session_model.ticket_id,
            agent_type=session_model.agent_type.value,
            status=session_model.status.value,
            current_task=session_model.current_task,
        )


@router.delete("/{session_id}")
async def cleanup_session(session_id: str):
    try:
        agent_manager_instance.cleanup_session(session_id)
        return {"message": f"Session {session_id} cleaned up"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
