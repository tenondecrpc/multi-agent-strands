from __future__ import annotations

import logging
from typing import Any

from strands import Agent

from app.mcp import get_jira_tools
from app.utils import JiraStatus

logger = logging.getLogger(__name__)

JIRA_TOOLS_SYSTEM_PROMPT = f"""You are the Orchestrator Agent responsible for managing the software development workflow.

Your responsibilities include:
- Parsing Jira tickets to understand requirements
- Updating ticket statuses as work progresses
- Adding comments to Jira tickets to keep stakeholders informed
- Coordinating the development pipeline

When working with Jira tickets:
- Use `jira_get_issue` to fetch full ticket details
- Use `jira_update_issue` to change ticket status or fields
- Use `jira_add_comment` to communicate updates on tickets
- Search for tickets with "{JiraStatus.TO_DO}" status to initiate workflows

Always maintain accurate ticket status in Jira to keep the team informed."""


async def create_orchestrator_agent() -> Agent:
    tools = await get_jira_tools()
    return Agent(
        system_prompt=JIRA_TOOLS_SYSTEM_PROMPT,
        tools=tools,
    )


async def launch_agent_pipeline(ticket_id: str) -> dict[str, Any]:
    logger.info(f"Launching agent pipeline for ticket: {ticket_id}")
    agent = await create_orchestrator_agent()
    result = await agent.run(
        f"Process Jira ticket {ticket_id}. Get the issue details, understand the requirements, and update the ticket status as work progresses."
    )
    logger.info(f"Pipeline completed for ticket: {ticket_id}")
    return {"ticket_id": ticket_id, "status": "processed", "result": result}
