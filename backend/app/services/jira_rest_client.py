from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from typing import Any

import app.config

logger = logging.getLogger(__name__)


class JiraRestClient:
    def __init__(
        self,
        jira_url: str | None = None,
        jira_email: str | None = None,
        jira_api_token: str | None = None,
    ):
        self.jira_url = jira_url or os.getenv("JIRA_URL")
        self.jira_email = jira_email or os.getenv("JIRA_EMAIL")
        self.jira_api_token = jira_api_token or os.getenv("JIRA_API_TOKEN")
        self._base_url = f"{self.jira_url}/rest/api/3"

    @property
    def auth_header(self) -> str:
        auth = base64.b64encode(
            f"{self.jira_email}:{self.jira_api_token}".encode()
        ).decode()
        return f"Basic {auth}"

    async def _request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        import urllib.request

        url = f"{self._base_url}/{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", self.auth_header)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")

        if data:
            req.data = json.dumps(data).encode()

        loop = asyncio.get_running_loop()

        def _fetch():
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())

        return await loop.run_in_executor(None, _fetch)

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        logger.info(f"Jira REST: Getting issue {issue_key}")
        return await self._request("GET", f"issue/{issue_key}")

    async def search_issues(
        self, jql: str, max_results: int = 50
    ) -> list[dict[str, Any]]:
        logger.info(f"Jira REST: Searching issues with jql: {jql}")
        fields = "key,summary,status,issuetype,priority,assignee,reporter,labels,components,created,updated"
        jql_encoded = jira_url_encode(jql)
        fields_encoded = jira_url_encode(fields)
        data = await self._request(
            "GET",
            f"search/jql?jql={jql_encoded}&maxResults={max_results}&fields={fields_encoded}",
        )
        return data.get("issues", [])

    async def get_comments(self, issue_key: str) -> list[dict[str, Any]]:
        logger.info(f"Jira REST: Getting comments for {issue_key}")
        data = await self._request("GET", f"issue/{issue_key}/comment")
        return data.get("comments", [])

    async def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        logger.info(f"Jira REST: Adding comment to {issue_key}")
        return await self._request(
            "POST",
            f"issue/{issue_key}/comment",
            data={
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}],
                        }
                    ],
                }
            },
        )

    async def transition_issue(
        self, issue_key: str, transition_id: str
    ) -> dict[str, Any]:
        logger.info(f"Jira REST: Transitioning {issue_key} to {transition_id}")
        return await self._request(
            "POST",
            f"issue/{issue_key}/transitions",
            data={"transition": {"id": transition_id}},
        )

    async def update_issue(
        self, issue_key: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        logger.info(
            f"Jira REST: Updating {issue_key} with fields: {list(fields.keys())}"
        )
        return await self._request("PUT", f"issue/{issue_key}", data={"fields": fields})


def jira_url_encode(jql: str) -> str:
    import urllib.parse

    return urllib.parse.quote(jql)


_jira_client: JiraRestClient | None = None


async def get_jira_client() -> JiraRestClient:
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraRestClient()
    return _jira_client


async def close_jira_client() -> None:
    global _jira_client
    _jira_client = None
