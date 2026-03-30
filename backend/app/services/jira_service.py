from __future__ import annotations

import logging
from typing import Any

from app.services.jira_rest_client import JiraRestClient, get_jira_client

logger = logging.getLogger(__name__)


class JiraService:
    def __init__(self, client: JiraRestClient | None = None):
        self._client = client

    async def get_client(self) -> JiraRestClient:
        if self._client is None:
            self._client = await get_jira_client()
        return self._client

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        client = await self.get_client()
        data = await client.get_issue(issue_key)
        return self._transform_issue(data)

    async def search_issues(
        self, jql: str, max_results: int = 50
    ) -> list[dict[str, Any]]:
        client = await self.get_client()
        issues = await client.search_issues(jql, max_results)
        return [self._transform_issue(i) for i in issues]

    async def get_issue_comments(self, issue_key: str) -> list[dict[str, Any]]:
        client = await self.get_client()
        comments = await client.get_comments(issue_key)
        return [self._transform_comment(c) for c in comments]

    async def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        client = await self.get_client()
        await client.add_comment(issue_key, comment)
        return {"success": True, "issue_key": issue_key}

    async def transition_issue(
        self, issue_key: str, transition_id: str
    ) -> dict[str, Any]:
        client = await self.get_client()
        await client.transition_issue(issue_key, transition_id)
        return {"success": True, "issue_key": issue_key, "transition_id": transition_id}

    async def enrich_ticket_data(self, issue_key: str) -> dict[str, Any]:
        issue_data = await self.get_issue(issue_key)
        comments = await self.get_issue_comments(issue_key)

        return {
            "key": issue_key,
            "summary": issue_data.get("summary", ""),
            "description": issue_data.get("description", ""),
            "status": issue_data.get("status", ""),
            "issue_type": issue_data.get("issue_type", ""),
            "priority": issue_data.get("priority", ""),
            "assignee": issue_data.get("assignee", ""),
            "reporter": issue_data.get("reporter", ""),
            "labels": issue_data.get("labels", []),
            "components": issue_data.get("components", []),
            "comments": comments,
            "created": issue_data.get("created", ""),
            "updated": issue_data.get("updated", ""),
        }

    def _transform_issue(self, data: dict[str, Any]) -> dict[str, Any]:
        fields = data.get("fields") or {}
        return {
            "key": data.get("key", ""),
            "summary": fields.get("summary", ""),
            "description": self._extract_text(fields.get("description")),
            "status": (fields.get("status") or {}).get("name", ""),
            "issue_type": (fields.get("issuetype") or {}).get("name", ""),
            "priority": (fields.get("priority") or {}).get("name", ""),
            "assignee": (fields.get("assignee") or {}).get("displayName", ""),
            "reporter": (fields.get("reporter") or {}).get("displayName", ""),
            "labels": fields.get("labels", []),
            "components": [c.get("name", "") for c in fields.get("components", [])],
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
        }

    def _transform_comment(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data.get("id", ""),
            "author": data.get("author", {}).get("displayName", ""),
            "body": self._extract_text(data.get("body")),
            "created": data.get("created", ""),
        }

    def _extract_text(self, content: Any) -> str:
        if not content:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            return self._extract_text_from_doc(content)
        if isinstance(content, list):
            return " ".join(self._extract_text(c) for c in content)
        return str(content)

    def _extract_text_from_doc(self, doc: dict[str, Any]) -> str:
        if doc.get("type") == "text":
            return doc.get("text", "")
        content = doc.get("content", [])
        if isinstance(content, list):
            return " ".join(self._extract_text_from_doc(c) for c in content)
        return ""


jira_service = JiraService()
