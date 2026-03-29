## 1. Setup & Configuration

- [x] 1.1 Add Jira environment variables (`JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL`, `JIRA_POLL_INTERVAL_MINUTES`) to the backend configuration and `.env.example`.
- [x] 1.2 Ensure backend dependencies support starting the MCP sub-process (e.g., updating `requirements.txt` or `docker-compose.yml` to support `uvx`).

## 2. MCP Client Integration

- [x] 2.1 Create the Jira MCP client wrapper in the backend using `StdioServerParameters` to run `uvx mcp-atlassian`.
- [x] 2.2 Create a custom `MCPStrandsTool` class that extends `strands.tools.Tool` to adapt MCP tool definitions to the Strands framework.
- [x] 2.3 Parse and export the Jira tools (`jira_get_issue`, `jira_update_issue`, `jira_add_comment`, etc.) dynamically instantiating `MCPStrandsTool` for agent use.

## 3. Orchestrator Agent Update

- [x] 3.1 Update the Orchestrator Agent definition to include the Jira MCP tools in its `tools` list.
- [x] 3.2 Update the Orchestrator Agent system prompt with explicit instructions on interacting with Jira tickets.

## 4. Polling & Trigger Mechanism

- [x] 4.1 Implement a simple polling loop or trigger function in the FastAPI backend that searches Jira for "Ready for Dev" tickets.
- [x] 4.2 Connect the polling trigger to the `launch_agent_pipeline` function.

## 5. Testing & Verification

- [x] 5.1 Write tests verifying the initialization logic of the Atlassian MCP client.
- [x] 5.2 Verify end-to-end trigger logic locally.