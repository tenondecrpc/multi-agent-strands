## Why

The system needs a standardized way to interact with Jira to fetch ticket details, update statuses, and post comments during the automated software development lifecycle. By using the Model Context Protocol (MCP) with `mcp-atlassian`, the orchestrator agent can natively use Jira functions as direct tools without requiring complex custom API integration logic, reducing overhead and improving reliability.

## What Changes

- Add the `mcp-atlassian` server as a sub-process in the FastAPI backend environment.
- Pass Jira MCP tools (`jira_get_issue`, `jira_update_issue`, `jira_add_comment`, etc.) to the Orchestrator Agent's toolset.
- Implement an endpoint/polling logic to retrieve "Ready for Dev" Jira tickets to trigger the multi-agent pipeline.
- Implement status updates and comment logging within the agent pipeline so it can post progress and PR links back to Jira.
- Add Jira-specific environment variables to the project configuration.

## Capabilities

### New Capabilities
- `jira-mcp-integration`: Ability to read tickets, post comments, update status, and search issues via the MCP Atlassian server.

### Modified Capabilities
- (None)

## Impact

- **Dependencies:** Requires adding/configuring `mcp-atlassian` and configuring MCP clients in the FastAPI backend.
- **Environment:** Requires `JIRA_URL`, `JIRA_API_TOKEN`, and `JIRA_EMAIL` in the `.env` file and Docker environment.
- **Agents:** The Orchestrator Agent will be updated to depend on these new tools.
