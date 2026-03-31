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
        model_name = os.getenv("LLM_MODEL_ID", "qwen/qwen3.6-plus-preview:free")
        model = OpenAIModel(
            model_id=model_name,
            client_args={
                "api_key": os.getenv("LLM_API_KEY"),
                "base_url": os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1"),
                "timeout": 300.0,
                "max_retries": 3,
            },
        )
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
            from openai import AsyncOpenAI

            cls._client = AsyncOpenAI(
                api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_API_URL", "https://api.minimax.chat/v1"),
            )
        return cls._client
