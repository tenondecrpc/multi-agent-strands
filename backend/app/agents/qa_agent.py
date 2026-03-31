from __future__ import annotations

import os
from typing import Any

from strands import Agent
from strands.models import OpenAIModel

from app.agents.tools import strands_tools

QA_AGENT_SYSTEM_PROMPT = """You are the QA Agent specialized in writing and executing tests.

Your responsibilities include:
- Writing backend tests with pytest
- Writing frontend tests with Vitest and React Testing Library
- Running test suites and verifying results
- Reporting test failures with detailed error logs
- Ensuring code quality and test coverage

When testing:
1. First understand what needs to be tested by reading the relevant code
2. Use shell to run test suites (e.g., pytest, npm test)
3. Analyze test results and report failures
4. If tests fail, return detailed error logs to the Orchestrator for fixes

Workspace root: /Users/tenonde/Projects/personal/multi-agent-strands"""


def create_qa_agent(model: OpenAIModel | None = None) -> Agent:
    if model is None:
        client = OpenAIModelProvider.get_client()
        model_name = os.getenv("LLM_MODEL_ID", "minimax/minimax-m2.7")
        model = OpenAIModel(client=client, model_id=model_name)
    return Agent(
        system_prompt=QA_AGENT_SYSTEM_PROMPT,
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
