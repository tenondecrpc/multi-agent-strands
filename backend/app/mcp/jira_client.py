from __future__ import annotations

import asyncio
import os
from typing import Any

import app.config  # noqa: F401 - ensures .env is loaded

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class JiraMCPClient:
    def __init__(
        self,
        jira_url: str | None = None,
        jira_email: str | None = None,
        jira_api_token: str | None = None,
    ):
        self.jira_url = jira_url or os.getenv("JIRA_URL")
        self.jira_email = jira_email or os.getenv("JIRA_EMAIL")
        self.jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self._session: ClientSession | None = None

    def _get_server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command="uvx",
            args=["mcp-atlassian"],
            env={
                "JIRA_URL": self.jira_url or "",
                "JIRA_EMAIL": self.jira_email or "",
                "JIRA_API_TOKEN": self.jira_api_token or "",
            },
        )

    async def initialize(self) -> None:
        if not all([self.jira_url, self.jira_email, self.jira_api_token]):
            raise ValueError("JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set")
        server_params = self._get_server_params()
        self._streams = stdio_client(server_params)
        self._read, self._write = await self._streams.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.initialize()

    async def list_tools(self) -> list[dict[str, Any]]:
        if not self._session:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        tools_response = await self._session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools_response.tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        if not self._session:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        result = await self._session.call_tool(tool_name, arguments)
        return result

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        if hasattr(self, "_streams") and self._streams:
            await self._streams.__aexit__(None, None, None)
            self._streams = None


_jira_client: JiraMCPClient | None = None
_jira_client_lock: asyncio.Lock | None = None


async def get_jira_client() -> JiraMCPClient:
    global _jira_client, _jira_client_lock
    if _jira_client is None:
        if _jira_client_lock is None:
            _jira_client_lock = asyncio.Lock()
        async with _jira_client_lock:
            if _jira_client is None:
                _jira_client = JiraMCPClient()
                await _jira_client.initialize()
    return _jira_client


async def close_jira_client() -> None:
    global _jira_client
    if _jira_client is not None:
        await _jira_client.close()
        _jira_client = None
