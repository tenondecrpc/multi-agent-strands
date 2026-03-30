from unittest.mock import patch, MagicMock

from app.agents.backend_agent import create_backend_agent, BACKEND_AGENT_SYSTEM_PROMPT
from app.agents.frontend_agent import (
    create_frontend_agent,
    FRONTEND_AGENT_SYSTEM_PROMPT,
)
from app.agents.qa_agent import create_qa_agent, QA_AGENT_SYSTEM_PROMPT
from app.agents.orchestrator import (
    ORCHESTRATOR_SYSTEM_PROMPT,
)


class TestBackendAgent:
    def test_backend_agent_system_prompt_contains_fastapi(self):
        assert "FastAPI" in BACKEND_AGENT_SYSTEM_PROMPT
        assert "Pydantic" in BACKEND_AGENT_SYSTEM_PROMPT
        assert "SQLAlchemy" in BACKEND_AGENT_SYSTEM_PROMPT

    @patch("app.agents.backend_agent.OpenAIModel")
    def test_create_backend_agent_with_model(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        agent = create_backend_agent(model=mock_model)

        assert agent is not None
        assert agent._system_prompt == BACKEND_AGENT_SYSTEM_PROMPT
        mock_model_class.assert_not_called()


class TestFrontendAgent:
    def test_frontend_agent_system_prompt_contains_react(self):
        assert "React" in FRONTEND_AGENT_SYSTEM_PROMPT
        assert "Vite" in FRONTEND_AGENT_SYSTEM_PROMPT
        assert "TypeScript" in FRONTEND_AGENT_SYSTEM_PROMPT

    @patch("app.agents.frontend_agent.OpenAIModel")
    def test_create_frontend_agent_with_model(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        agent = create_frontend_agent(model=mock_model)

        assert agent is not None
        assert agent._system_prompt == FRONTEND_AGENT_SYSTEM_PROMPT


class TestQAAgent:
    def test_qa_agent_system_prompt_contains_pytest(self):
        assert "pytest" in QA_AGENT_SYSTEM_PROMPT
        assert "Vitest" in QA_AGENT_SYSTEM_PROMPT

    @patch("app.agents.qa_agent.OpenAIModel")
    def test_create_qa_agent_with_model(self, mock_model_class):
        mock_model = MagicMock()
        mock_model_class.return_value = mock_model

        agent = create_qa_agent(model=mock_model)

        assert agent is not None
        assert agent._system_prompt == QA_AGENT_SYSTEM_PROMPT


class TestOrchestratorAgent:
    def test_orchestrator_system_prompt_contains_jira(self):
        assert "Jira" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "backend_agent" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "frontend_agent" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "qa_agent" in ORCHESTRATOR_SYSTEM_PROMPT
        assert "GitHub" in ORCHESTRATOR_SYSTEM_PROMPT
