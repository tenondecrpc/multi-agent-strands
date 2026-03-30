from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.models.ticket_state import TicketStage, VALID_TRANSITIONS, TicketState
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


@dataclass
class ProcessingResult:
    ticket_id: str
    status: ProcessingStatus
    summary: str
    artifacts: dict[str, Any] = field(default_factory=dict)
    next_actions: list[str] = field(default_factory=list)
    handoff_to: str | None = None
    error: str | None = None


class TicketPipeline:
    def __init__(self, ticket_state: TicketState):
        self.ticket_state = ticket_state

    def validate_transition(self, new_stage: TicketStage) -> bool:
        if self.ticket_state.current_stage == TicketStage.BLOCKED:
            return True
        return new_stage in VALID_TRANSITIONS.get(
            self.ticket_state.current_stage, set()
        )

    async def transition_to(
        self, new_stage: TicketStage, blocked_reason: str | None = None
    ) -> bool:
        if not self.validate_transition(new_stage):
            logger.warning(
                f"Invalid transition from {self.ticket_state.current_stage} to {new_stage} "
                f"for ticket {self.ticket_state.ticket_id}"
            )
            return False

        old_stage = self.ticket_state.current_stage
        self.ticket_state.current_stage = new_stage

        if new_stage == TicketStage.BLOCKED:
            self.ticket_state.blocked_reason = blocked_reason
        elif old_stage == TicketStage.BLOCKED:
            self.ticket_state.blocked_reason = None

        self.ticket_state.updated_at = datetime.utcnow()

        logger.info(
            f"Ticket {self.ticket_state.ticket_id} transitioned from {old_stage} to {new_stage}"
        )
        return True

    async def block(self, reason: str) -> bool:
        return await self.transition_to(TicketStage.BLOCKED, blocked_reason=reason)

    async def unblock(self, target_stage: TicketStage) -> bool:
        if self.ticket_state.current_stage != TicketStage.BLOCKED:
            return False
        return await self.transition_to(target_stage)

    def get_previous_stage(self) -> TicketStage | None:
        transition_map = {
            TicketStage.TRIAGED: TicketStage.NEW,
            TicketStage.IN_ANALYSIS: TicketStage.TRIAGED,
            TicketStage.IN_DEVELOPMENT: TicketStage.IN_ANALYSIS,
            TicketStage.IN_REVIEW: TicketStage.IN_DEVELOPMENT,
            TicketStage.IN_TESTING: TicketStage.IN_REVIEW,
            TicketStage.DONE: TicketStage.IN_TESTING,
        }
        return transition_map.get(self.ticket_state.current_stage)

    async def process_validate(self) -> tuple[bool, str]:
        if not self.ticket_state.ticket_id:
            return False, "Ticket ID is required"
        return True, "Validation passed"

    async def process_enrich(self, jira_data: dict[str, Any]) -> tuple[bool, str]:
        self.ticket_state.jira_key = jira_data.get("key", self.ticket_state.jira_key)
        self.ticket_state.context_window["jira_data"] = jira_data
        return True, "Enrichment completed"

    async def process_triage(self, triage_result: dict[str, Any]) -> tuple[bool, str]:
        suggested_agent = triage_result.get("suggested_agent", "backend")
        self.ticket_state.assigned_agent = suggested_agent

        if suggested_agent == "backend":
            await self.transition_to(TicketStage.IN_DEVELOPMENT)
        elif suggested_agent == "frontend":
            await self.transition_to(TicketStage.IN_DEVELOPMENT)
        elif suggested_agent == "qa":
            await self.transition_to(TicketStage.IN_TESTING)
        else:
            await self.transition_to(TicketStage.TRIAGED)

        return True, f"Triage completed, assigned to {suggested_agent}"

    async def execute_pipeline(self) -> ProcessingResult:
        ticket_id = self.ticket_state.ticket_id

        valid, msg = await self.process_validate()
        if not valid:
            return ProcessingResult(
                ticket_id=ticket_id,
                status=ProcessingStatus.FAILURE,
                summary=msg,
            )

        if self.ticket_state.current_stage == TicketStage.NEW:
            await self.transition_to(TicketStage.TRIAGED)

        return ProcessingResult(
            ticket_id=ticket_id,
            status=ProcessingStatus.SUCCESS,
            summary="Pipeline executed successfully",
            artifacts=self.ticket_state.artifacts,
            next_actions=["analyze", "develop", "review", "test"],
            handoff_to=self.ticket_state.assigned_agent,
        )
