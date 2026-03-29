## ADDED Requirements

### Requirement: Jira Ticket Polling via Direct API (✅ Completado)
The system SHALL support polling Jira for tickets in status "To Do" to automatically trigger workflows. The polling interval SHALL be configurable via the `JIRA_POLL_INTERVAL_MINUTES` environment variable, defaulting to 5 minutes.

#### Scenario: Trigger pipeline from poll
- **WHEN** the polling mechanism executes a search and finds a "To Do" ticket
- **THEN** it triggers the automated development pipeline for that ticket ID

#### Scenario: Configurable polling interval
- **WHEN** the system starts with `JIRA_POLL_INTERVAL_MINUTES` set to a specific integer
- **THEN** the polling mechanism uses that interval to check for new tickets

### Future Enhancement

- **Jira Webhook**: Replace polling with Jira webhook for real-time ticket detection (future work)

### Implementation Notes

- **Polling**: Uses direct Jira REST API (`/rest/api/3/search/jql`) via `urllib` for reliable polling
- **Jira Statuses**: `JiraStatus` enum defines `TO_DO = "To Do"`, `IN_PROGRESS = "In Progress"`, `DONE = "Done"`
- **MCP**: Not used for Jira. MCP (`mcp-atlassian`) is considered for future integrations with other tools.
