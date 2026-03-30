from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.core.task_queue import process_ticket_task
from app.database import get_db
from app.models.events import EventType
from app.models.ticket_state import TicketStage, TicketState
from app.services.ticket_pipeline import TicketPipeline
from app.events import emit_pipeline_started, emit_agent_event

router = APIRouter(prefix="/tickets", tags=["tickets"])


async def emit_ticket_started(ticket_id: str, session_uuid: str):
    import logging

    logger = logging.getLogger(__name__)
    try:
        logger.info(
            f"Emitting socket events for {ticket_id} with session {session_uuid}"
        )
        from app.events import sio

        await sio.emit(
            "pipeline_started",
            {"session_id": session_uuid, "ticket_id": ticket_id},
            namespace="/pipeline",
        )
        await sio.emit(
            "agent_event",
            {
                "type": "agent_state_change",
                "session_id": session_uuid,
                "payload": {
                    "agent_id": "orchestrator",
                    "new_state": "working",
                    "task": f"Processing {ticket_id}",
                    "progress": 0.1,
                },
            },
            namespace="/pipeline",
        )
        logger.info(f"Emitted socket events successfully")
    except Exception as e:
        logger.warning(f"Could not emit socket events: {e}")


class ProcessTicketRequest(BaseModel):
    agent_type: str = Field(
        default="backend", description="Agent type to process the ticket"
    )
    priority: int = Field(default=1, ge=0, le=3, description="Task priority (0-3)")
    session_id: str | None = Field(
        default=None,
        description="Optional session ID to use (uses existing session if provided)",
    )


class StageTransitionRequest(BaseModel):
    stage: TicketStage
    blocked_reason: str | None = None


class ProcessResponse(BaseModel):
    ticket_id: str
    task_id: str | None = None
    status: str
    message: str


class StageTransitionResponse(BaseModel):
    ticket_id: str
    old_stage: TicketStage
    new_stage: TicketStage
    success: bool
    message: str


async def process_ticket_background(ticket_id: str, agent_type: str = "backend") -> str:
    import uuid
    from app.database import async_session_maker
    from app.models.agent_session_model import (
        AgentSession,
        AgentSessionStatus,
        AgentType,
    )

    async with async_session_maker() as db:
        result = await db.execute(
            select(TicketState).where(TicketState.ticket_id == ticket_id)
        )
        ticket_state = result.scalar_one_or_none()

        if not ticket_state:
            ticket_state = TicketState(
                ticket_id=ticket_id, current_stage=TicketStage.NEW
            )
            db.add(ticket_state)
            await db.commit()
            await db.refresh(ticket_state)

        session_uuid = str(uuid.uuid4())
        session_id = f"{ticket_id}-{agent_type}-{uuid.uuid4().hex[:8]}"

        agent_session = AgentSession(
            id=session_uuid,
            session_id=session_id,
            ticket_id=ticket_id,
            agent_type=AgentType(agent_type),
            status=AgentSessionStatus.RUNNING,
        )
        db.add(agent_session)

        ticket_state.active_session_id = session_uuid
        db.add(ticket_state)

        await db.commit()

        task = process_ticket_task.apply_async(
            args=[ticket_id, agent_type],
            kwargs={"metadata": {"priority": 1, "session_id": session_uuid}},
        )

        await emit_ticket_started(ticket_id, session_uuid)

        await event_bus.publish_ticket_event(
            event_type=EventType.TICKET_RECEIVED,
            ticket_id=ticket_id,
            payload={"agent_type": agent_type, "task_id": task.id},
        )

        return session_uuid


@router.post("/{ticket_id}/process", response_model=ProcessResponse)
async def process_ticket(
    ticket_id: str,
    request: ProcessTicketRequest,
    db: AsyncSession = Depends(get_db),
):
    import uuid
    from app.models.agent_session_model import (
        AgentSession,
        AgentSessionStatus,
        AgentType,
    )

    result = await db.execute(
        select(TicketState).where(TicketState.ticket_id == ticket_id)
    )
    ticket_state = result.scalar_one_or_none()

    if not ticket_state:
        ticket_state = TicketState(ticket_id=ticket_id, current_stage=TicketStage.NEW)
        db.add(ticket_state)
        await db.commit()
        await db.refresh(ticket_state)

    session_uuid = request.session_id or str(uuid.uuid4())
    session_id = (
        f"{ticket_id}-{request.agent_type}-{uuid.uuid4().hex[:8]}"
        if not request.session_id
        else f"{ticket_id}-{request.agent_type}"
    )

    agent_session = AgentSession(
        id=session_uuid,
        session_id=session_id,
        ticket_id=ticket_id,
        agent_type=AgentType(request.agent_type),
        status=AgentSessionStatus.RUNNING,
    )
    db.add(agent_session)
    await db.commit()

    task = process_ticket_task.apply_async(
        args=[ticket_id, request.agent_type],
        kwargs={"metadata": {"priority": request.priority, "session_id": session_uuid}},
    )

    await emit_ticket_started(ticket_id, session_uuid)

    await event_bus.publish_ticket_event(
        event_type=EventType.TICKET_RECEIVED,
        ticket_id=ticket_id,
        payload={"agent_type": request.agent_type, "task_id": task.id},
    )

    return ProcessResponse(
        ticket_id=ticket_id,
        task_id=task.id,
        status="queued",
        message=f"Ticket processing queued with task {task.id}",
    )


@router.post("/{ticket_id}/stage", response_model=StageTransitionResponse)
async def transition_stage(
    ticket_id: str,
    request: StageTransitionRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TicketState).where(TicketState.ticket_id == ticket_id)
    )
    ticket_state = result.scalar_one_or_none()

    if not ticket_state:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    pipeline = TicketPipeline(ticket_state)
    old_stage = ticket_state.current_stage

    if request.stage == TicketStage.BLOCKED and request.blocked_reason:
        success = await pipeline.block(request.blocked_reason)
    elif ticket_state.current_stage == TicketStage.BLOCKED:
        success = await pipeline.unblock(request.stage)
    else:
        success = await pipeline.transition_to(request.stage)

    if success:
        ticket_state.updated_at = ticket_state.updated_at
        await db.commit()

        await event_bus.publish_ticket_event(
            event_type=EventType.TICKET_STAGE_CHANGED,
            ticket_id=ticket_id,
            payload={
                "old_stage": old_stage.value,
                "new_stage": request.stage.value,
                "blocked_reason": request.blocked_reason,
            },
        )

    return StageTransitionResponse(
        ticket_id=ticket_id,
        old_stage=old_stage,
        new_stage=ticket_state.current_stage,
        success=success,
        message="Stage transition successful"
        if success
        else "Invalid stage transition",
    )


@router.get("/{ticket_id}/state")
async def get_ticket_state(ticket_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TicketState).where(TicketState.ticket_id == ticket_id)
    )
    ticket_state = result.scalar_one_or_none()

    if not ticket_state:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    return {
        "ticket_id": ticket_state.ticket_id,
        "jira_key": ticket_state.jira_key,
        "current_stage": ticket_state.current_stage.value,
        "assigned_agent": ticket_state.assigned_agent,
        "blocked_reason": ticket_state.blocked_reason,
        "context_window": ticket_state.context_window,
        "artifacts": ticket_state.artifacts,
        "handoff_history": ticket_state.handoff_history,
        "updated_at": ticket_state.updated_at.isoformat()
        if ticket_state.updated_at
        else None,
    }


@router.get("/events/{ticket_id}/stream")
async def stream_ticket_events(ticket_id: str, last_event_id: str | None = None):
    async def event_generator():
        async for event in event_bus.subscribe_ticket(ticket_id, last_event_id):
            yield {
                "event": event.type.value,
                "data": event.to_dict(),
            }

    return EventSourceResponse(event_generator())
