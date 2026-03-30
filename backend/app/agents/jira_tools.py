from __future__ import annotations

import json
import logging
from typing import Any

from strands import tool

from app.services.jira_service import JiraService

logger = logging.getLogger(__name__)

jira_service = JiraService()


@tool(description="Get full details of a Jira issue by its key (e.g., PROJ-123)")
async def jira_get_issue(issue_key: str) -> str:
    logger.info(f"[JIRA_TOOL] Getting issue: {issue_key}")
    try:
        data = await jira_service.get_issue(issue_key)
        return json.dumps(data, indent=2)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error getting issue {issue_key}: {e}")
        return json.dumps({"error": str(e)})


@tool(description="Search for Jira issues using JQL query")
async def jira_search_issues(jql: str, max_results: int = 50) -> str:
    logger.info(f"[JIRA_TOOL] Searching: {jql}")
    try:
        issues = await jira_service.search_issues(jql, max_results)
        return json.dumps(issues, indent=2, default=str)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error searching: {e}")
        return json.dumps({"error": str(e)})


@tool(description="Add a comment to a Jira issue")
async def jira_add_comment(issue_key: str, comment: str) -> str:
    logger.info(f"[JIRA_TOOL] Adding comment to {issue_key}")
    try:
        result = await jira_service.add_comment(issue_key, comment)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error adding comment: {e}")
        return json.dumps({"error": str(e)})


@tool(description="Get comments for a Jira issue")
async def jira_get_comments(issue_key: str) -> str:
    logger.info(f"[JIRA_TOOL] Getting comments for {issue_key}")
    try:
        comments = await jira_service.get_issue_comments(issue_key)
        return json.dumps(comments, indent=2, default=str)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error getting comments: {e}")
        return json.dumps({"error": str(e)})


@tool(description="Transition a Jira issue to a new status")
async def jira_transition_issue(issue_key: str, transition_id: str) -> str:
    logger.info(f"[JIRA_TOOL] Transitioning {issue_key} to {transition_id}")
    try:
        result = await jira_service.transition_issue(issue_key, transition_id)
        return json.dumps(result)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error transitioning issue: {e}")
        return json.dumps({"error": str(e)})


@tool(description="Get enriched ticket data including comments")
async def jira_enrich_ticket(issue_key: str) -> str:
    logger.info(f"[JIRA_TOOL] Enriching ticket: {issue_key}")
    try:
        data = await jira_service.enrich_ticket_data(issue_key)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        logger.error(f"[JIRA_TOOL] Error enriching ticket: {e}")
        return json.dumps({"error": str(e)})


def get_jira_tools() -> list:
    return [
        jira_get_issue,
        jira_search_issues,
        jira_add_comment,
        jira_get_comments,
        jira_transition_issue,
        jira_enrich_ticket,
    ]
