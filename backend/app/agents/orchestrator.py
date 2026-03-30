from __future__ import annotations

import logging
import os

import app.config  # noqa: F401 - ensures .env is loaded

from strands import Agent
from strands.models import OpenAIModel

from app.mcp import get_jira_tools, get_github_tools
from app.utils import JiraStatus

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """You are the Orchestrator Agent responsible for managing the software development workflow.

Your responsibilities include:
- Parsing Jira tickets to understand requirements
- Updating ticket statuses as work progresses
- Adding comments to Jira tickets to keep stakeholders informed
- Coordinating the development pipeline by delegating to specialized agents
- Creating GitHub branches and Pull Requests when development is complete

Available Development Agents:
- backend_agent: Use for implementing FastAPI endpoints, Pydantic models, and SQLAlchemy models
- frontend_agent: Use for implementing React components, pages, and TypeScript code
- qa_agent: Use for running tests and verifying implementation

When working with Jira tickets:
- Use jira_get_issue to fetch full ticket details
- Use jira_update_issue to change ticket status or fields
- Use jira_add_comment to communicate updates on tickets
- Search for tickets with "{to_do_status}" status to initiate workflows

When coordinating development:
1. Analyze the ticket requirements
2. Delegate backend tasks to backend_agent
3. Delegate frontend tasks to frontend_agent
4. Delegate testing to qa_agent
5. If tests fail, coordinate fixes with the appropriate agent
6. When all tasks are complete, use GitHub tools to create a branch and PR

GitHub Operations:
- Use github_create_branch to create a new branch
- Use github_commit_file to commit changes
- Use github_create_pull_request to open a PR

Always maintain accurate ticket status in Jira to keep the team informed.""".format(
    to_do_status=JiraStatus.TO_DO
)


def create_model() -> OpenAIModel:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("MINIMAX_API_KEY"),
        base_url=os.getenv("MINIMAX_API_URL", "https://api.minimax.chat/v1"),
    )
    model_name = os.getenv("OPENAI_MODEL", "minimax/minimax-m2.7")
    return OpenAIModel(client=client, model_config={"model": model_name})


async def create_orchestrator_agent() -> Agent:
    jira_tools = await get_jira_tools()
    github_tools = await get_github_tools()
    model = create_model()

    from app.agents.backend_agent import create_backend_agent
    from app.agents.frontend_agent import create_frontend_agent
    from app.agents.qa_agent import create_qa_agent

    backend_agent = create_backend_agent(model)
    frontend_agent = create_frontend_agent(model)
    qa_agent = create_qa_agent(model)

    backend_agent_tool = _agent_as_tool(
        backend_agent,
        "backend_agent",
        "Backend developer agent for FastAPI, Pydantic, and SQLAlchemy",
    )
    frontend_agent_tool = _agent_as_tool(
        frontend_agent,
        "frontend_agent",
        "Frontend developer agent for React, Vite, and TypeScript",
    )
    qa_agent_tool = _agent_as_tool(qa_agent, "qa_agent", "QA agent for running tests")

    all_tools = (
        jira_tools
        + github_tools
        + [backend_agent_tool, frontend_agent_tool, qa_agent_tool]
    )

    return Agent(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=all_tools,
        model=model,
    )


def _agent_as_tool(agent: Agent, name: str, description: str):
    from strands import tool

    @tool(description=description, name=name)
    async def agent_tool(task: str) -> str:
        result = await agent.run(task)
        return str(result)

    return agent_tool
