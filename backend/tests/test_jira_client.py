import pytest
from unittest.mock import patch

from app.mcp.jira_client import JiraMCPClient


@pytest.fixture
def mock_env_vars():
    return {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_API_TOKEN": "test-token",
    }


class TestJiraMCPClient:
    def test_init_with_env_vars(self, mock_env_vars):
        with patch.dict("os.environ", mock_env_vars, clear=True):
            client = JiraMCPClient()
            assert client.jira_url == "https://test.atlassian.net"
            assert client.jira_email == "test@example.com"
            assert client.jira_api_token == "test-token"

    def test_init_with_explicit_params(self):
        client = JiraMCPClient(
            jira_url="https://custom.atlassian.net",
            jira_email="custom@example.com",
            jira_api_token="custom-token",
        )
        assert client.jira_url == "https://custom.atlassian.net"
        assert client.jira_email == "custom@example.com"
        assert client.jira_api_token == "custom-token"

    def test_init_prefers_explicit_over_env(self, mock_env_vars):
        with patch.dict("os.environ", mock_env_vars, clear=True):
            client = JiraMCPClient(jira_url="https://override.atlassian.net")
            assert client.jira_url == "https://override.atlassian.net"
            assert client.jira_email == "test@example.com"
            assert client.jira_api_token == "test-token"

    def test_get_server_params(self, mock_env_vars):
        with patch.dict("os.environ", mock_env_vars, clear=True):
            client = JiraMCPClient()
            params = client._get_server_params()
            assert params.command == "uvx"
            assert params.args == ["mcp-atlassian"]
            assert params.env["JIRA_URL"] == "https://test.atlassian.net"
            assert params.env["JIRA_EMAIL"] == "test@example.com"
            assert params.env["JIRA_API_TOKEN"] == "test-token"

    def test_initialize_raises_when_missing_credentials(self):
        with patch.dict("os.environ", {}, clear=True):
            client = JiraMCPClient()
            with pytest.raises(
                ValueError, match="JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN"
            ):
                import asyncio

                asyncio.run(client.initialize())

    @pytest.mark.asyncio
    async def test_list_tools_raises_when_not_initialized(self):
        client = JiraMCPClient(
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
            jira_api_token="test-token",
        )
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.list_tools()

    @pytest.mark.asyncio
    async def test_call_tool_raises_when_not_initialized(self):
        client = JiraMCPClient(
            jira_url="https://test.atlassian.net",
            jira_email="test@example.com",
            jira_api_token="test-token",
        )
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.call_tool("jira_get_issue", {"issueKey": "TEST-1"})
