from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus import event_bus
from app.models.ticket_state import TicketStage, TicketState
from app.models.events import EventType
from app.services.ticket_pipeline import TicketPipeline, ProcessingResult


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_bus = event_bus

    async def get_ticket_state(self, ticket_id: str) -> TicketState | None:
        result = await self.db.execute(
            select(TicketState).where(TicketState.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def create_ticket_state(
        self,
        ticket_id: str,
        jira_key: str | None = None,
        initial_stage: TicketStage = TicketStage.NEW,
    ) -> TicketState:
        ticket_state = TicketState(
            ticket_id=ticket_id,
            jira_key=jira_key,
            current_stage=initial_stage,
        )
        self.db.add(ticket_state)
        await self.db.commit()
        await self.db.refresh(ticket_state)

        await self.event_bus.publish_ticket_event(
            event_type=EventType.TICKET_RECEIVED,
            ticket_id=ticket_id,
            payload={"jira_key": jira_key, "stage": initial_stage.value},
        )

        return ticket_state

    async def update_ticket_state(
        self,
        ticket_id: str,
        stage: TicketStage | None = None,
        assigned_agent: str | None = None,
        artifacts: dict[str, Any] | None = None,
    ) -> TicketState | None:
        ticket_state = await self.get_ticket_state(ticket_id)
        if not ticket_state:
            return None

        if stage is not None:
            pipeline = TicketPipeline(ticket_state)
            old_stage = ticket_state.current_stage
            if await pipeline.transition_to(stage):
                await self.event_bus.publish_ticket_event(
                    event_type=EventType.TICKET_STAGE_CHANGED,
                    ticket_id=ticket_id,
                    payload={
                        "old_stage": old_stage.value,
                        "new_stage": stage.value,
                    },
                )

        if assigned_agent is not None:
            ticket_state.assigned_agent = assigned_agent

        if artifacts is not None:
            ticket_state.artifacts.update(artifacts)

        await self.db.commit()
        await self.db.refresh(ticket_state)
        return ticket_state

    async def process_ticket(self, ticket_id: str) -> ProcessingResult:
        ticket_state = await self.get_ticket_state(ticket_id)
        if not ticket_state:
            ticket_state = await self.create_ticket_state(ticket_id)

        pipeline = TicketPipeline(ticket_state)
        result = await pipeline.execute_pipeline()

        ticket_state.assigned_agent = result.handoff_to
        ticket_state.artifacts.update(result.artifacts)

        await self.db.commit()
        await self.db.refresh(ticket_state)

        return result

    async def enrich_ticket(
        self, ticket_id: str, jira_data: dict[str, Any]
    ) -> TicketState | None:
        ticket_state = await self.get_ticket_state(ticket_id)
        if not ticket_state:
            return None

        ticket_state.jira_key = jira_data.get("key", ticket_state.jira_key)
        ticket_state.context_window["jira_data"] = jira_data

        await self.event_bus.publish_ticket_event(
            event_type=EventType.TICKET_UPDATED,
            ticket_id=ticket_id,
            payload={"enriched": True, "jira_key": ticket_state.jira_key},
        )

        await self.db.commit()
        await self.db.refresh(ticket_state)
        return ticket_state
