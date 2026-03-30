import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.mcp.polling import (
    search_ready_for_dev_tickets,
)
from app.models.agent_session_model import AgentSessionStatus


class TestPollingLogic:
    def test_poll_interval_from_env(self):
        with patch.dict("os.environ", {"JIRA_POLL_INTERVAL_MINUTES": "10"}):
            import importlib
            import app.mcp.polling as polling_module

            importlib.reload(polling_module)
            assert polling_module.JIRA_POLL_INTERVAL_MINUTES == 10

    @pytest.mark.asyncio
    async def test_search_ready_for_dev_tickets_returns_issues(self):
        env_vars = {
            "JIRA_URL": "https://test.atlassian.net",
            "JIRA_EMAIL": "test@test.com",
            "JIRA_API_TOKEN": "test-token",
        }
        with patch.dict("os.environ", env_vars, clear=True):
            with patch("app.mcp.polling.urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b'{"issues": [{"key": "TEST-1", "fields": {"summary": "Test ticket"}}]}'
                mock_urlopen.return_value.__enter__ = MagicMock(
                    return_value=mock_response
                )
                mock_urlopen.return_value.__exit__ = MagicMock(return_value=None)

                tickets = await search_ready_for_dev_tickets()

        assert len(tickets) == 1
        assert tickets[0]["key"] == "TEST-1"


class TestOrchestratorPipeline:
    @pytest.mark.asyncio
    async def test_launch_agent_pipeline_returns_expected_structure(self):
        with (
            patch("app.agents.pipeline.create_session") as mock_create_session,
            patch(
                "app.agents.pipeline.create_orchestrator_agent",
                new_callable=AsyncMock,
            ) as mock_create_agent,
            patch(
                "app.agents.pipeline.update_session_status",
                new_callable=AsyncMock,
            ),
            patch("app.agents.pipeline.create_event", new_callable=AsyncMock),
            patch(
                "app.agents.pipeline.emit_pipeline_started",
                new_callable=AsyncMock,
            ),
            patch(
                "app.agents.pipeline.emit_pipeline_completed",
                new_callable=AsyncMock,
            ),
        ):
            mock_session = MagicMock()
            mock_session.id = uuid4()
            mock_session.status = AgentSessionStatus.RUNNING
            mock_create_session.return_value = mock_session

            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value="done")
            mock_create_agent.return_value = mock_agent

            from app.agents.pipeline import launch_agent_pipeline

            result = await launch_agent_pipeline("TEST-1")

            assert result["ticket_id"] == "TEST-1"
            assert result["status"] == "completed"
