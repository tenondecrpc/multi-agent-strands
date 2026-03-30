import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.agents.pipeline import (
    TokenTracker,
    ToolCallTracker,
    PipelineGuardrails,
    launch_agent_pipeline,
)
from app.models.agent_session import SessionStatus


class TestTokenTracker:
    def test_init_with_default_max_tokens(self):
        tracker = TokenTracker()
        assert tracker.max_tokens == 100000
        assert tracker.tokens_used == 0

    def test_init_with_custom_max_tokens(self):
        tracker = TokenTracker(max_tokens=50000)
        assert tracker.max_tokens == 50000

    def test_add_usage(self):
        tracker = TokenTracker(max_tokens=1000)
        tracker.add_usage(100)
        assert tracker.tokens_used == 100

    def test_add_usage_raises_when_exceeded(self):
        tracker = TokenTracker(max_tokens=100)
        tracker.add_usage(50)
        tracker.add_usage(49)
        assert tracker.tokens_used == 99
        with pytest.raises(RuntimeError, match="Token budget exceeded"):
            tracker.add_usage(2)


class TestToolCallTracker:
    def test_init_with_default_max_calls(self):
        tracker = ToolCallTracker()
        assert tracker.max_calls == 100
        assert tracker.call_count == 0

    def test_init_with_custom_max_calls(self):
        tracker = ToolCallTracker(max_calls=50)
        assert tracker.max_calls == 50

    def test_increment(self):
        tracker = ToolCallTracker(max_calls=10)
        tracker.increment()
        assert tracker.call_count == 1

    def test_increment_raises_when_exceeded(self):
        tracker = ToolCallTracker(max_calls=2)
        tracker.increment()
        tracker.increment()
        with pytest.raises(RuntimeError, match="Max tool calls exceeded"):
            tracker.increment()


class TestPipelineGuardrails:
    def test_init_with_defaults(self):
        guardrails = PipelineGuardrails()
        assert guardrails.token_tracker is not None
        assert guardrails.tool_call_tracker is not None
        assert guardrails.timeout_seconds == 600

    def test_init_with_custom_values(self):
        guardrails = PipelineGuardrails(
            token_tracker=TokenTracker(max_tokens=500),
            tool_call_tracker=ToolCallTracker(max_calls=10),
            timeout_seconds=300,
        )
        assert guardrails.token_tracker.max_tokens == 500
        assert guardrails.tool_call_tracker.max_calls == 10
        assert guardrails.timeout_seconds == 300

    def test_start_sets_start_time(self):
        guardrails = PipelineGuardrails()
        assert guardrails.start_time is None
        guardrails.start()
        assert guardrails.start_time is not None


class TestLaunchAgentPipeline:
    @pytest.mark.asyncio
    async def test_launch_agent_pipeline_creates_session(self):
        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.status = SessionStatus.RUNNING

        with (
            patch(
                "app.agents.pipeline.create_session", new_callable=AsyncMock
            ) as mock_create_session,
            patch(
                "app.agents.pipeline.create_orchestrator_agent", new_callable=AsyncMock
            ) as mock_create_agent,
            patch("app.agents.pipeline.update_session_status", new_callable=AsyncMock),
            patch("app.agents.pipeline.create_event", new_callable=AsyncMock),
            patch("app.agents.pipeline.emit_pipeline_started", new_callable=AsyncMock),
            patch(
                "app.agents.pipeline.emit_pipeline_completed", new_callable=AsyncMock
            ),
        ):
            mock_create_session.return_value = mock_session

            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value="test result")
            mock_create_agent.return_value = mock_agent

            result = await launch_agent_pipeline("TEST-1")

            assert result["ticket_id"] == "TEST-1"
            assert result["status"] == "completed"
            mock_create_session.assert_called_once_with("TEST-1")

    @pytest.mark.asyncio
    async def test_launch_agent_pipeline_handles_error(self):
        import asyncio

        mock_session = MagicMock()
        mock_session.id = uuid4()
        mock_session.status = SessionStatus.RUNNING

        with (
            patch(
                "app.agents.pipeline.create_session", new_callable=AsyncMock
            ) as mock_create_session,
            patch(
                "app.agents.pipeline.create_orchestrator_agent", new_callable=AsyncMock
            ) as mock_create_agent,
            patch("app.agents.pipeline.PipelineGuardrails") as mock_guardrails_class,
            patch("app.agents.pipeline.update_session_status", new_callable=AsyncMock),
            patch("app.agents.pipeline.create_event", new_callable=AsyncMock),
            patch("app.agents.pipeline.emit_pipeline_started", new_callable=AsyncMock),
            patch("app.agents.pipeline.emit_pipeline_error", new_callable=AsyncMock),
        ):
            mock_create_session.return_value = mock_session

            mock_guardrails = MagicMock()
            mock_guardrails.start_time = None
            mock_guardrails.timeout_seconds = 0.001
            mock_guardrails_class.return_value = mock_guardrails

            async def slow_run(*args, **kwargs):
                await asyncio.sleep(1)
                return "result"

            mock_agent = MagicMock()
            mock_agent.run = slow_run
            mock_create_agent.return_value = mock_agent

            result = await launch_agent_pipeline("TEST-1")

            assert result["ticket_id"] == "TEST-1"
            assert result["status"] in ["timeout", "error"]
