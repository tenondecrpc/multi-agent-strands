## Why

To handle software development tasks automatically triggered by Jira tickets, we need a multi-agent system powered by the Strands SDK. This system will decompose tickets, generate code, run tests, and create Pull Requests. By leveraging specialized agents, we can significantly accelerate the development lifecycle and ensure consistent quality, while maintaining strict human oversight through PR reviews before merging to production.

## What Changes

- Implementation of the connection with MiniMax M2.7 using the `OpenAIModel` provider in Strands SDK.
- Setup of `strands_tools` (such as `file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`) for file and code operations.
- Integration of GitHub MCP client to allow the orchestrator to create branches and Pull Requests.
- Creation of the Orchestrator (Architect) Agent which coordinates tasks, updates Jira, and delegates to sub-agents.
- Creation of the Backend Developer Agent tailored for FastAPI, Pydantic, and SQLAlchemy.
- Creation of the Frontend Developer Agent tailored for React, Vite, and TypeScript.
- Creation of the QA Agent to automatically write and execute tests (pytest, vitest/testing-library).
- Implementation of the `launch_agent_pipeline` function to start the session, emit Socket.IO events, coordinate the orchestrator, and save the final result in the database.

## Capabilities

### New Capabilities

- `development-agents`: Orchestrates a team of specialized software development agents (Architect, Backend, Frontend, QA) using the Strands SDK and MiniMax M2.7 model to automatically process tickets, write code, run tests, and create PRs.

### Modified Capabilities

## Impact

- **Backend/Agents:** Introduces new agent definitions and the main execution pipeline.
- **Tools:** Integrates `strands_tools` and GitHub MCP server.
- **Database:** Interacts with the `agent_sessions` and `agent_events` tables to track pipeline status.
- **Frontend/Observability:** Will trigger new real-time Socket.IO events (`pipeline_started`, `pipeline_completed`, `pipeline_error`) that the frontend dashboard will consume.
