from __future__ import annotations

import os
from typing import Any

from strands import Agent
from strands.models import OpenAIModel

from app.agents.tools import strands_tools

FRONTEND_AGENT_SYSTEM_PROMPT = """You are the Frontend Developer Agent specialized in React, Vite, and TypeScript.

Your responsibilities include:
- Implementing UI components with React and TypeScript
- Creating pages and routing with React Router
- Integrating with backend APIs
- Writing frontend tests with Vitest and React Testing Library
- Ensuring responsive and accessible design

When implementing features:
1. First read existing code to understand the project structure
2. Use file_write to create new components or editor to modify existing ones
3. Use shell to run the development server and tests
4. Always verify your implementation works before reporting completion

Workspace root: /Users/tenonde/Projects/personal/multi-agent-strands"""


def create_frontend_agent(model: OpenAIModel | None = None) -> Agent:
    if model is None:
        client = OpenAIModelProvider.get_client()
        model_name = os.getenv("OPENAI_MODEL", "minimax/minimax-m2.7")
        model = OpenAIModel(client=client, model_config={"model": model_name})
    return Agent(
        system_prompt=FRONTEND_AGENT_SYSTEM_PROMPT,
        tools=strands_tools,
        model=model,
    )


class OpenAIModelProvider:
    _client: Any = None

    @classmethod
    def get_client(cls) -> Any:
        if cls._client is None:
            from openai import OpenAI

            cls._client = OpenAI(
                api_key=os.getenv("MINIMAX_API_KEY"),
                base_url=os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1"),
            )
        return cls._client
