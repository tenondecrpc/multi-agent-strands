from app.models.ticket_state import TicketState, TicketStage, VALID_TRANSITIONS


class TestTicketStage:
    def test_all_stages_defined(self):
        assert TicketStage.NEW.value == "NEW"
        assert TicketStage.TRIAGED.value == "TRIAGED"
        assert TicketStage.IN_ANALYSIS.value == "IN_ANALYSIS"
        assert TicketStage.IN_DEVELOPMENT.value == "IN_DEVELOPMENT"
        assert TicketStage.IN_REVIEW.value == "IN_REVIEW"
        assert TicketStage.IN_TESTING.value == "IN_TESTING"
        assert TicketStage.DONE.value == "DONE"
        assert TicketStage.BLOCKED.value == "BLOCKED"


class TestValidTransitions:
    def test_new_can_transition_to(self):
        assert TicketStage.TRIAGED in VALID_TRANSITIONS[TicketStage.NEW]
        assert TicketStage.BLOCKED in VALID_TRANSITIONS[TicketStage.NEW]
        assert TicketStage.IN_DEVELOPMENT not in VALID_TRANSITIONS[TicketStage.NEW]

    def test_triaged_can_transition_to(self):
        assert TicketStage.IN_ANALYSIS in VALID_TRANSITIONS[TicketStage.TRIAGED]
        assert TicketStage.IN_DEVELOPMENT in VALID_TRANSITIONS[TicketStage.TRIAGED]
        assert TicketStage.BLOCKED in VALID_TRANSITIONS[TicketStage.TRIAGED]

    def test_blocked_can_transition_to_any(self):
        blocked_transitions = VALID_TRANSITIONS[TicketStage.BLOCKED]
        assert TicketStage.NEW in blocked_transitions
        assert TicketStage.TRIAGED in blocked_transitions
        assert TicketStage.IN_ANALYSIS in blocked_transitions
        assert TicketStage.IN_DEVELOPMENT in blocked_transitions
        assert TicketStage.IN_REVIEW in blocked_transitions
        assert TicketStage.IN_TESTING in blocked_transitions

    def test_done_cannot_transition(self):
        assert len(VALID_TRANSITIONS[TicketStage.DONE]) == 0


class TestTicketState:
    def test_ticket_state_creation(self):
        ticket = TicketState(
            ticket_id="TEST-001",
            jira_key="PROJ-1",
            current_stage=TicketStage.NEW,
        )

        assert ticket.ticket_id == "TEST-001"
        assert ticket.jira_key == "PROJ-1"
        assert ticket.current_stage == TicketStage.NEW
        assert ticket.assigned_agent is None
        assert ticket.context_window == {}
        assert ticket.artifacts == {}
        assert ticket.handoff_history == []

    def test_can_transition_to_valid(self):
        ticket = TicketState(ticket_id="TEST-002", current_stage=TicketStage.NEW)

        assert ticket.can_transition_to(TicketStage.TRIAGED) is True
        assert ticket.can_transition_to(TicketStage.BLOCKED) is True

    def test_can_transition_to_invalid(self):
        ticket = TicketState(ticket_id="TEST-003", current_stage=TicketStage.NEW)

        assert ticket.can_transition_to(TicketStage.IN_DEVELOPMENT) is False
        assert ticket.can_transition_to(TicketStage.DONE) is False

    def test_can_transition_from_blocked(self):
        ticket = TicketState(ticket_id="TEST-004", current_stage=TicketStage.BLOCKED)

        assert ticket.can_transition_to(TicketStage.NEW) is True
        assert ticket.can_transition_to(TicketStage.IN_DEVELOPMENT) is True

    def test_can_transition_from_done(self):
        ticket = TicketState(ticket_id="TEST-005", current_stage=TicketStage.DONE)

        assert ticket.can_transition_to(TicketStage.NEW) is False
        assert ticket.can_transition_to(TicketStage.BLOCKED) is False


class TestTicketStateBlocked:
    def test_blocked_reason(self):
        ticket = TicketState(
            ticket_id="TEST-006",
            current_stage=TicketStage.NEW,
        )

        ticket.current_stage = TicketStage.BLOCKED
        ticket.blocked_reason = "Waiting for clarification"

        assert ticket.blocked_reason == "Waiting for clarification"

    def test_unblock_clears_reason(self):
        ticket = TicketState(
            ticket_id="TEST-007",
            current_stage=TicketStage.BLOCKED,
            blocked_reason="Some blocker",
        )

        assert ticket.blocked_reason == "Some blocker"


class TestTicketStateHandoffHistory:
    def test_handoff_history_default_empty(self):
        ticket = TicketState(ticket_id="TEST-008")

        assert ticket.handoff_history == []

    def test_handoff_history_can_be_updated(self):
        ticket = TicketState(ticket_id="TEST-009")

        ticket.handoff_history.append(
            {
                "from_agent": "backend",
                "to_agent": "qa",
                "summary": "Development complete",
            }
        )

        assert len(ticket.handoff_history) == 1
        assert ticket.handoff_history[0]["to_agent"] == "qa"
