from typing import Any

from app.mcp.jira_client import JiraMCPClient, get_jira_client


class JiraService:
    def __init__(self, client: JiraMCPClient | None = None):
        self._client = client

    async def get_client(self) -> JiraMCPClient:
        if self._client is None:
            self._client = await get_jira_client()
        return self._client

    async def get_issue(self, issue_key: str) -> dict[str, Any]:
        client = await self.get_client()
        result = await client.call_tool("get_issue", {"issueKey": issue_key})
        return self._parse_issue_result(result)

    async def search_issues(
        self, jql: str, max_results: int = 50
    ) -> list[dict[str, Any]]:
        client = await self.get_client()
        result = await client.call_tool(
            "search_issues", {"jql": jql, "maxResults": max_results}
        )
        return self._parse_search_result(result)

    async def get_issue_comments(self, issue_key: str) -> list[dict[str, Any]]:
        client = await self.get_client()
        result = await client.call_tool("get_comments", {"issueKey": issue_key})
        return self._parse_comments_result(result)

    async def add_comment(self, issue_key: str, comment: str) -> dict[str, Any]:
        client = await self.get_client()
        await client.call_tool(
            "add_comment", {"issueKey": issue_key, "comment": comment}
        )
        return {"success": True, "issue_key": issue_key}

    async def transition_issue(
        self, issue_key: str, transition_id: str
    ) -> dict[str, Any]:
        client = await self.get_client()
        await client.call_tool(
            "transition_issue", {"issueKey": issue_key, "transitionId": transition_id}
        )
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

    def _parse_issue_result(self, result: Any) -> dict[str, Any]:
        if hasattr(result, "content") and isinstance(result.content, list):
            for item in result.content:
                if hasattr(item, "text"):
                    try:
                        import json

                        return json.loads(item.text)
                    except (json.JSONDecodeError, TypeError):
                        pass
        return {}

    def _parse_search_result(self, result: Any) -> list[dict[str, Any]]:
        if hasattr(result, "content") and isinstance(result.content, list):
            for item in result.content:
                if hasattr(item, "text"):
                    try:
                        import json

                        data = json.loads(item.text)
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "issues" in data:
                            return data["issues"]
                    except (json.JSONDecodeError, TypeError):
                        pass
        return []

    def _parse_comments_result(self, result: Any) -> list[dict[str, Any]]:
        if hasattr(result, "content") and isinstance(result.content, list):
            for item in result.content:
                if hasattr(item, "text"):
                    try:
                        import json

                        data = json.loads(item.text)
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict) and "comments" in data:
                            return data["comments"]
                    except (json.JSONDecodeError, TypeError):
                        pass
        return []


jira_service = JiraService()
