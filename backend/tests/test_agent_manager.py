import pytest
from datetime import datetime
from app.services.agent_manager import (
    AgentContext,
    HandoffEntry,
    AGENT_CONFIGS,
)


class TestAgentConfig:
    def test_default_config(self):
        config = AGENT_CONFIGS.get("backend")
        assert config is not None
        assert config.name == "Backend Agent"
        assert config.max_iterations > 0
        assert config.timeout_seconds > 0

    def test_all_agent_types_defined(self):
        from app.models.agent_session_model import AgentType

        for agent_type in AgentType:
            assert agent_type in AGENT_CONFIGS


class TestAgentContext:
    def test_context_creation(self):
        context = AgentContext(
            session_id="test-session-1",
            ticket_id="TEST-123",
            agent_type="BACKEND",
        )

        assert context.session_id == "test-session-1"
        assert context.ticket_id == "TEST-123"
        assert context.agent_type == "BACKEND"
        assert context.current_task is None
        assert context.previous_results == []
        assert context.shared_state == {}
        assert context.handoff_log == []

    def test_add_handoff(self):
        context = AgentContext(
            session_id="test-session-2",
            ticket_id="TEST-456",
            agent_type="BACKEND",
        )

        context.add_handoff(
            from_agent="orchestrator",
            to_agent="backend",
            summary="Starting development",
        )

        assert len(context.handoff_log) == 1
        assert context.handoff_log[0].from_agent == "orchestrator"
        assert context.handoff_log[0].to_agent == "backend"
        assert context.handoff_log[0].summary == "Starting development"
        assert isinstance(context.handoff_log[0].timestamp, datetime)

    def test_to_dict(self):
        context = AgentContext(
            session_id="test-session-3",
            ticket_id="TEST-789",
            agent_type="QA",
        )

        context_dict = context.to_dict()

        assert context_dict["session_id"] == "test-session-3"
        assert context_dict["ticket_id"] == "TEST-789"
        assert context_dict["agent_type"] == "QA"
        assert "handoff_log" in context_dict


class TestHandoffEntry:
    def test_handoff_entry_creation(self):
        entry = HandoffEntry(
            from_agent="backend",
            to_agent="qa",
            summary="Code review passed",
        )

        assert entry.from_agent == "backend"
        assert entry.to_agent == "qa"
        assert entry.summary == "Code review passed"
        assert isinstance(entry.timestamp, datetime)


class TestAgentManager:
    def test_generate_session_id(self):
        from app.services.agent_manager import AgentManager
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())

        session_id = manager._generate_session_id("TEST-100", "BACKEND")

        assert "TEST-100" in session_id
        assert "backend" in session_id.lower()

    def test_start_session(self):
        from app.services.agent_manager import AgentManager
        from app.models.agent_session_model import AgentType
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())

        context = manager.start_session("TEST-200", AgentType.BACKEND)

        assert context.ticket_id == "TEST-200"
        assert context.agent_type == AgentType.BACKEND
        assert context.session_id in manager._sessions

    def test_get_session_found(self):
        from app.services.agent_manager import AgentManager
        from app.models.agent_session_model import AgentType
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())
        created = manager.start_session("TEST-300", AgentType.FRONTEND)

        retrieved = manager.get_session(created.session_id)

        assert retrieved.session_id == created.session_id

    def test_get_session_not_found(self):
        from app.services.agent_manager import AgentManager
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())

        with pytest.raises(KeyError):
            manager.get_session("non-existent-session")

    def test_cleanup_session(self):
        from app.services.agent_manager import AgentManager
        from app.models.agent_session_model import AgentType
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())
        context = manager.start_session("TEST-400", AgentType.QA)

        manager.cleanup_session(context.session_id)

        assert context.session_id not in manager._sessions

    def test_get_session_count(self):
        from app.services.agent_manager import AgentManager
        from app.models.agent_session_model import AgentType
        from app.core.event_bus import EventBus

        manager = AgentManager(EventBus())

        assert manager.get_session_count() == 0

        manager.start_session("TEST-500", AgentType.BACKEND)
        manager.start_session("TEST-501", AgentType.FRONTEND)

        assert manager.get_session_count() == 2
