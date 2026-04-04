import asyncio
import logging
import os
from datetime import datetime

from app.services.jira_service import JiraService

logger = logging.getLogger(__name__)

JIRA_POLL_INTERVAL = int(os.getenv("JIRA_POLL_INTERVAL_MINUTES", "5")) * 60

_processed_tickets: set[str] = set()


async def check_and_process_new_tickets():
    global _processed_tickets
    jira_service = JiraService()

    from app.database import async_session_maker
    from app.models.agent_session_model import AgentSession, AgentSessionStatus
    from sqlalchemy import select

    try:
        jql = 'status = "To Do" ORDER BY created DESC'
        logger.info(f"[JIRA Polling] Searching for: {jql}")
        issues = await jira_service.search_issues(jql, max_results=5)
        logger.info(f"[JIRA Polling] Found {len(issues)} issues")

        if issues:
            async with async_session_maker() as db:
                for issue in issues:
                    if not issue:
                        continue
                    ticket_id = issue.get("key")

                    if not ticket_id:
                        continue

                    result = await db.execute(
                        select(AgentSession)
                        .where(AgentSession.ticket_id == ticket_id)
                        .order_by(AgentSession.started_at.desc())
                        .limit(1)
                    )
                    existing_session = result.scalar_one_or_none()

                    if existing_session:
                        logger.info(
                            f"[JIRA Polling] Skipping {ticket_id} - session already exists ({existing_session.status.value}): {existing_session.id}"
                        )
                        continue

                    if ticket_id in _processed_tickets:
                        logger.debug(
                            f"[JIRA Polling] Skipping {ticket_id} - currently being processed"
                        )
                        continue

                    logger.info(
                        f"[JIRA Polling] Processing NEW ticket: {ticket_id}"
                    )
                    _processed_tickets.add(ticket_id)
                    from app.api.tickets import process_ticket_background

                    try:
                        await process_ticket_background(ticket_id)
                    except Exception as e:
                        logger.error(
                            f"[JIRA Polling] Error processing {ticket_id}: {e}"
                        )
                    finally:
                        _processed_tickets.discard(ticket_id)
        else:
            logger.info("[JIRA Polling] No tickets found")
    except Exception as e:
        logger.error(f"[JIRA Polling] Error checking tickets: {e}", exc_info=True)


async def poll_jira_tickets():
    logger.info(f"[JIRA Polling] Starting polling every {JIRA_POLL_INTERVAL}s")
    while True:
        try:
            await check_and_process_new_tickets()
        except Exception as e:
            logger.error(f"[JIRA Polling] Error in polling loop: {e}", exc_info=True)
        await asyncio.sleep(JIRA_POLL_INTERVAL)


def start_jira_polling():
    asyncio.create_task(poll_jira_tickets())
    logger.info(f"[JIRA Polling] Polling task scheduled every {JIRA_POLL_INTERVAL}s")
