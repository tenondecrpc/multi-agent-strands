## Context

The multi-agent system uses Jira as the source of truth for software development tasks. To integrate seamlessly, we want agents to natively use Jira functionality via MCP tools instead of building custom API clients. The plan specifies using `mcp-atlassian` for this purpose.

## Goals / Non-Goals

**Goals:**
- Provide agents with the ability to read, update, and search Jira issues.
- Connect the `mcp-atlassian` sub-process server in the backend.
- Expose the relevant MCP tools to the Orchestrator agent.
- Add configuration parameters to support Atlassian connection.

**Non-Goals:**
- Implement webhook listeners in this phase (polling is used for MVP as per PLAN.md).
- Build a custom Jira API client (we rely entirely on MCP).

## Decisions

- **Use `mcp-atlassian` CLI via `uvx`**: This is the recommended and fastest way to launch the Atlassian MCP server. The `MCPClient` wrapper from `strands` will launch it using `stdio_client`.
- **Environment Variables**: Add `JIRA_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL` for Atlassian authentication, and `JIRA_POLL_INTERVAL_MINUTES` to configure the polling frequency (defaulting to 5 minutes).
- **Strands Tool Adapter**: To natively integrate with the Strands Agents SDK, dynamically discovered MCP tools will be wrapped in a custom `MCPStrandsTool` class that extends `strands.tools.Tool`. This ensures the Orchestrator agent can seamlessly parse and execute Jira tools using the native Strands framework.
- **Orchestrator Role**: The Orchestrator Agent will be the primary consumer of Jira tools since its role is to parse tickets, manage statuses, and coordinate the development flow.

## Risks / Trade-offs

- **Risk**: Rate limiting or slow responses from Atlassian API.
  - **Mitigation**: Adjust polling intervals to be reasonable and add timeout configurations to the MCP client wrapper.
- **Risk**: Authentication failures.
  - **Mitigation**: Validate Jira tokens at startup and log errors clearly to ensure prompt resolution.