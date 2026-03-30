## 1. Setup and Initialization

- [x] 1.1 Verify and configure `MINIMAX_API_KEY` and MiniMax base URL in the environment.
- [x] 1.2 Initialize the basic file structure for agent definitions within the `backend/app/agents` directory.

## 2. Tools Integration

- [x] 2.1 Set up and export `strands_tools` (`file_read`, `file_write`, `editor`, `shell`, `python_repl`, `current_time`) for use by the agents.
- [x] 2.2 Configure the GitHub MCP server integration using the `mcp.client` wrapper and expose it as a tool.

## 3. Agent Definitions

- [x] 3.1 Implement the `create_backend_agent(model)` function using the Strands SDK and `OpenAIModel` provider with MiniMax M2.7.
- [x] 3.2 Implement the `create_frontend_agent(model)` function using the Strands SDK and `OpenAIModel` provider with MiniMax M2.7.
- [x] 3.3 Implement the `create_qa_agent(model)` function using the Strands SDK and `OpenAIModel` provider with MiniMax M2.7.
- [x] 3.4 Implement the main Orchestrator Agent, assigning the backend, frontend, qa agents, and GitHub MCP client as its tools.

## 4. Pipeline Orchestration

- [x] 4.1 Create the `launch_agent_pipeline(ticket_id: str)` function to execute the Orchestrator.
- [x] 4.2 Integrate database persistence to create, update, and close `agent_sessions` and `agent_events`.
- [x] 4.3 Implement Socket.IO event emissions (`pipeline_started`, `pipeline_completed`, `pipeline_error`) inside the pipeline execution.
- [x] 4.4 Add session guardrails (e.g., token tracker, timeout, and max tool calls) to prevent infinite loops.

## 5. Testing and Verification

- [x] 5.1 Write tests for individual agent definitions to ensure prompts and tools load correctly.
- [x] 5.2 Write integration tests for `launch_agent_pipeline` using a mock ticket ID, database, and LLM responses.
- [x] 5.3 Implement Socket.IO server with `/pipeline` namespace for real-time event emission.
- [x] 5.4 Verify Socket.IO connection via command-line client test.
