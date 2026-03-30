from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import urllib.parse
import urllib.request
from typing import Any

from app.utils import JiraStatus

logger = logging.getLogger(__name__)

JIRA_POLL_INTERVAL_MINUTES = int(os.getenv("JIRA_POLL_INTERVAL_MINUTES", "5"))


async def search_ready_for_dev_tickets() -> list[dict[str, Any]]:
    logger.info(f"Searching for tickets with status '{JiraStatus.TO_DO}'...")

    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    jira_url = os.getenv("JIRA_URL")

    auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()

    jql = urllib.parse.quote(f"status = '{JiraStatus.TO_DO}' ORDER BY created ASC")
    url = f"{jira_url}/rest/api/3/search/jql?jql={jql}&maxResults=10&fields=key,summary,status"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")

    loop = asyncio.get_event_loop()

    def _fetch():
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())

    data = await loop.run_in_executor(None, _fetch)

    issues = data.get("issues", [])
    logger.info(f"Found {len(issues)} tickets with status '{JiraStatus.TO_DO}'")

    return issues


async def poll_jira_and_trigger() -> None:
    from app.agents.pipeline import launch_agent_pipeline

    logger.info(f"Jira polling started. Interval: {JIRA_POLL_INTERVAL_MINUTES} minutes")
    while True:
        try:
            tickets = await search_ready_for_dev_tickets()
            for ticket in tickets:
                ticket_id = ticket.get("key") or ticket.get("issueKey")
                if ticket_id:
                    logger.info(f"Triggering pipeline for ticket: {ticket_id}")
                    try:
                        await launch_agent_pipeline(ticket_id)
                    except Exception as e:
                        logger.error(
                            f"Error in launch_agent_pipeline: {type(e).__name__}: {e}"
                        )
                        import traceback

                        traceback.print_exc()
        except Exception as e:
            logger.error(f"Error in Jira polling: {type(e).__name__}: {e}")
        await asyncio.sleep(JIRA_POLL_INTERVAL_MINUTES * 60)


def start_jira_polling() -> asyncio.Task:
    return asyncio.create_task(poll_jira_and_trigger())
