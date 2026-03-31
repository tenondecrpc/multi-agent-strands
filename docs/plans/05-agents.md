# 5. Development Agents (MVP) ✅

## 5.1 MiniMax M2.7 Connection

MiniMax exposes an OpenAI-compatible endpoint. Strands supports `OpenAIModel` natively.

```python
from strands.models.openai import OpenAIModel

minimax = OpenAIModel(
    client_args={
        "api_key": LLM_API_KEY,
        "base_url": LLM_API_URL,  # configurable: api.minimax.io or openrouter
    },
    model_id="MiniMax-M2.7",
)
```

## 5.2 Tools: strands_tools + MCP

Agents use a combination of **native strands_tools** (file/code operations) and **MCP clients** (only GitHub in the future).

```python
from strands import Agent
from strands.tools.mcp import MCPClient
from strands_tools import file_read, file_write, editor, shell, python_repl, current_time
from mcp import stdio_client, StdioServerParameters

# --- MCP Clients (future) ---
github_mcp = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN},
        )
    ),
    prefix="github",
)

# --- Tools by agent type ---
ORCHESTRATOR_TOOLS = [github_mcp]                    # MCP: creates PR (future)
DEV_TOOLS = [file_read, file_write, editor, shell]    # strands_tools: operates on code
QA_TOOLS = [file_read, file_write, shell, python_repl] # strands_tools: writes and runs tests
```

### Tools Map

| Tool | Source | Agents Using It |
|---|---|---|
| `file_read` | strands_tools | Backend, Frontend, QA |
| `file_write` | strands_tools | Backend, Frontend, QA |
| `editor` | strands_tools | Backend, Frontend (edit existing code) |
| `shell` | strands_tools | QA (run tests), Backend (migrations) |
| `python_repl` | strands_tools | QA (execute tests inline) |
| `current_time` | strands_tools | Orchestrator (timestamps in logs) |
| `github_create_branch` | MCP (github, future) | Orchestrator |
| `github_create_pull_request` | MCP (github, future) | Orchestrator |

## 5.3 Agent Definitions

Each agent has a clear role, limited system prompt, and specific tools. MCP clients are passed directly — Strands handles their lifecycle.

### Architect Agent (Orchestrator)

Receives Jira ticket (via direct API), analyzes requirements, decomposes into subtasks, and coordinates other agents (passed as tools).

```python
from strands import Agent

backend_agent = create_backend_agent(minimax)
frontend_agent = create_frontend_agent(minimax)
qa_agent = create_qa_agent(minimax)

orchestrator = Agent(
    model=minimax,
    system_prompt="""You are a software architect orchestrator.
You receive Jira ticket IDs and orchestrate their implementation.

Workflow:
1. Use Jira API to read ticket details (jira_get_issue equivalent)
2. Use Jira API to set status to "In Progress" (jira_update_issue equivalent)
3. Use Jira API to log that work has started (jira_add_comment equivalent)
4. Analyze requirements and determine which agents to call
5. Call backend_agent and/or frontend_agent with specific tasks
6. Call qa_agent to validate the generated code
7. Use shell to run: git checkout -b agent/<ticket-id> && git add . && git commit
8. Use github_create_pull_request to create the PR
9. Use Jira API to post the PR link (jira_add_comment equivalent)
10. If any agent fails twice, use Jira API to set "Blocked" and log error

Available agents:
- backend_agent: Server-side code, APIs, database models, business logic
- frontend_agent: UI components, pages, client-side logic
- qa_agent: Unit tests, integration tests, runs test suites
""",
    tools=[
        *ORCHESTRATOR_TOOLS,    # github_mcp (future)
        current_time,
        shell,                  # for git operations
        backend_agent,
        frontend_agent,
        qa_agent,
    ],
)
```

### Backend Developer Agent

```python
def create_backend_agent(model) -> Agent:
    return Agent(
        name="backend_agent",
        model=model,
        system_prompt="""You are a senior Python backend developer.
You work with FastAPI, Pydantic, SQLAlchemy, and follow clean architecture.

You have tools to read, write, and edit files directly. Use them — do NOT output
code blocks. Instead, use file_write to create files and editor to modify existing ones.

Conventions:
- Type hints on all functions
- Pydantic models for request/response validation
- Async endpoints with FastAPI
- Repository pattern for database access
""",
        tools=DEV_TOOLS,
    )
```

### Frontend Developer Agent

```python
def create_frontend_agent(model) -> Agent:
    return Agent(
        name="frontend_agent",
        model=model,
        system_prompt="""You are a senior React/TypeScript frontend developer.
You work with React, Vite, TypeScript, and follow component-based architecture.

You have tools to read, write, and edit files directly. Use them — do NOT output
code blocks. Instead, use file_write to create files and editor to modify existing ones.

Conventions:
- Functional components with TypeScript interfaces for props
- Custom hooks for API calls and state management
- CSS modules or Tailwind for styling
""",
        tools=DEV_TOOLS,
    )
```

### QA Agent

```python
def create_qa_agent(model) -> Agent:
    return Agent(
        name="qa_agent",
        model=model,
        system_prompt="""You are a QA engineer specialized in automated testing.
You write tests for Python (pytest) and React (vitest/testing-library).

Workflow:
1. Use file_read to read the code generated by backend/frontend agents
2. Use file_write to create test files
3. Use shell to run: pytest tests/ --tb=short (backend) or npm run test (frontend)
4. If tests fail, return failure details so the architect can request fixes
5. If tests pass, return a summary of coverage

You MUST run the tests, not just write them.
""",
        tools=QA_TOOLS,
    )
```

## 5.4 Alternative: Graph Builder for Sequential Flows

For tickets where the flow is always linear (Backend → Frontend → QA), you can use `GraphBuilder`:

```python
from strands import Agent, GraphBuilder

builder = GraphBuilder()
builder.add_node(backend_agent, "backend")
builder.add_node(frontend_agent, "frontend")
builder.add_node(qa_agent, "qa")
builder.add_edge("backend", "frontend")
builder.add_edge("frontend", "qa")
builder.set_entry_point("backend")

pipeline = builder.build()
result = pipeline(f"Implement Jira ticket: {ticket_context}")
```

## 5.5 Complete Pipeline

```python
import uuid

async def launch_agent_pipeline(ticket_id: str) -> str:
    """Launches the agent pipeline for a Jira ticket."""
    session_id = str(uuid.uuid4())

    # Save session to DB
    await save_session(session_id, ticket_id, status="started")

    # Emit event to dashboard
    await emit_event(session_id, "pipeline_started", {"ticket_id": ticket_id})

    try:
        # The orchestrator does EVERYTHING via tools (MCP + strands_tools):
        # - Reads ticket from Jira (jira_get_issue)
        # - Transitions it to "In Progress" (jira_update_issue)
        # - Delegates to dev agents (backend_agent, frontend_agent, qa_agent)
        # - Creates branch and PR (shell + github_create_pull_request)
        # - Comments on Jira with PR link (jira_add_comment)
        result = orchestrator(
            f"Implement Jira ticket {ticket_id}. "
            f"Read the ticket, implement the solution, run tests, "
            f"create a PR, and update Jira with the results. "
            f"Working directory: /app/workspaces/{ticket_id.lower()}"
        )

        await save_session(session_id, ticket_id, status="completed", result=str(result))

    except Exception as e:
        await save_session(session_id, ticket_id, status="error", error=str(e))
        await emit_event(session_id, "pipeline_error", {"error": str(e)})

    return session_id
```
