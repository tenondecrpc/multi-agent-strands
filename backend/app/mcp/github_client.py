from __future__ import annotations

import os
from typing import Any

import app.config  # noqa: F401 - ensures .env is loaded

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class GitHubMCPClient:
    def __init__(
        self,
        github_token: str | None = None,
    ):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self._session: ClientSession | None = None

    def _get_server_params(self) -> StdioServerParameters:
        return StdioServerParameters(
            command="uvx",
            args=["github-mcp-server"],
            env={
                "GITHUB_TOKEN": self.github_token or "",
            },
        )

    async def initialize(self) -> None:
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN must be set")
        server_params = self._get_server_params()
        async with stdio_client(server_params) as (read, write):
            self._session = ClientSession(read, write)
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


_github_client: GitHubMCPClient | None = None


async def get_github_client() -> GitHubMCPClient:
    global _github_client
    if _github_client is None:
        _github_client = GitHubMCPClient()
        await _github_client.initialize()
    return _github_client


async def close_github_client() -> None:
    global _github_client
    if _github_client is not None:
        await _github_client.close()
        _github_client = None
