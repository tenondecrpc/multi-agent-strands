# 4. Jira Integration (MVP) ✅

Jira polling uses **direct REST API** for better reliability. MCP (`mcp-atlassian`) **is not currently used** — considered for future integrations with other tools.

## JiraStatus Enum

```python
# app/utils/jira_status.py
from enum import StrEnum

class JiraStatus(StrEnum):
    TO_DO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
```

## Polling: Direct REST API

Polling uses **direct REST API** for better reliability:

```python
# app/mcp/polling.py
import base64
import urllib.parse
import urllib.request

async def search_ready_for_dev_tickets():
    auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    jql = urllib.parse.quote(f"status = '{JiraStatus.TO_DO}' ORDER BY created ASC")
    url = f"{JIRA_URL}/rest/api/3/search/jql?jql={jql}&maxResults=10"
    # Uses urllib.request directly for polling
```

## Jira Tools Available to Agents

| MCP Tool | Use in Pipeline |
|---|---|
| `jira_search_issues` | Search tickets by JQL |
| `jira_get_issue` | Read full ticket details |
| `jira_update_issue` | Change status (In Progress, Done, Blocked) |
| `jira_add_comment` | Comment progress, errors, PR link |
| `jira_get_comments` | Read comments/additional context |
| `jira_add_issues_to_sprint` | Sprint organization |

**Note:** Jira tools are not implemented via MCP. Future integration via Jira webhook.

## MCP Servers (Future)

### GitHub MCP

To create branches and PRs, the official GitHub MCP server will be used:

```python
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

github_mcp = MCPClient(
    lambda: streamablehttp_client(
        url="https://api.githubcopilot.com/mcp/",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    ),
    prefix="github",
)
```

## Trigger: Polling (MVP) + Webhook (Future)

**MVP (current):** Polling searches for "To Do" tickets every N minutes using direct REST API.

**Future:** Jira webhook → API Gateway → FastAPI for real-time detection.

## Ticket Lifecycle

| Event | Action (via MCP tools) |
|---|---|
| Ticket detected (polling) | Direct API → `launch_agent_pipeline(ticket_id)` |
| Pipeline started | `jira_update_issue` → "In Progress" + `jira_add_comment` |
| PR created | `jira_add_comment` → PR link |
| Tests failed | `jira_add_comment` + `jira_update_issue` → "Blocked" |
| Review approved | `jira_update_issue` → "Done" |
