from __future__ import annotations

import json
from typing import Any

from strands import tool

from app.mcp.github_client import get_github_client


def create_mcp_tool_adapter(mcp_tool_def: dict[str, Any]):
    name = mcp_tool_def["name"]
    description = mcp_tool_def.get("description", "")
    input_schema = mcp_tool_def.get("input_schema", {})

    async def invoke_impl(**kwargs: Any) -> str:
        client = await get_github_client()
        result = await client.call_tool(name, kwargs)
        if hasattr(result, "content"):
            return json.dumps(result.content, default=str)
        return json.dumps(result, default=str)

    invoke_impl.__name__ = name
    invoke_impl.__doc__ = description

    return tool(
        description=description,
        inputSchema=input_schema,
        name=name,
    )(invoke_impl)


async def get_github_tools() -> list:
    client = await get_github_client()
    tool_defs = await client.list_tools()
    return [create_mcp_tool_adapter(tool_def) for tool_def in tool_defs]
