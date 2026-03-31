from __future__ import annotations

import os
from typing import Any

from strands import Agent
from strands.models import OpenAIModel

from app.agents.tools import strands_tools

BACKEND_AGENT_SYSTEM_PROMPT = """You are the Backend Developer Agent specialized in FastAPI, Pydantic, and SQLAlchemy.

Your responsibilities include:
- Implementing RESTful API endpoints with FastAPI
- Creating Pydantic models for request/response validation
- Designing and implementing database models with SQLAlchemy
- Writing backend tests with pytest
- Ensuring code follows best practices and is well-documented

When implementing features:
1. First read existing code to understand the project structure
2. Use file_write to create new files or editor to modify existing ones
3. Use shell to run tests and linting
4. Always verify your implementation works before reporting completion

Workspace root: /Users/tenonde/Projects/personal/multi-agent-strands/backend"""


def create_backend_agent(model: OpenAIModel | None = None) -> Agent:
    if model is None:
        client = OpenAIModelProvider.get_client()
        model_name = os.getenv("LLM_MODEL_ID", "minimax/minimax-m2.7")
        model = OpenAIModel(client=client, model_id=model_name)
    return Agent(
        system_prompt=BACKEND_AGENT_SYSTEM_PROMPT,
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
                api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_API_URL", "https://api.minimax.chat/v1"),
            )
        return cls._client
