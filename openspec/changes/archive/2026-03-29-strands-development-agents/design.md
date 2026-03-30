## Context

The system utilizes the Strands SDK to automate software development tasks triggered by Jira tickets. It leverages specialized agents (Architect, Backend Developer, Frontend Developer, and QA) powered by MiniMax M2.7 to build, test, and prepare code. The generated code is strictly subject to human review via Pull Requests.

## Goals / Non-Goals

**Goals:**
- Connect the Strands SDK to MiniMax M2.7 via the `OpenAIModel` provider.
- Integrate `strands_tools` (like `file_read`, `file_write`, `editor`, `shell`) for accurate file manipulations.
- Integrate the GitHub MCP server to allow the orchestrator to manage Git branches and create Pull Requests.
- Define a robust agent architecture with clear responsibilities.
- Implement the `launch_agent_pipeline` function to manage the agent lifecycle, database state, and real-time events.

**Non-Goals:**
- Direct deployment to production. (A human-in-the-loop review process is mandatory).
- Complex DevOps or production error remediation agents (these belong to future scope).

## Decisions

- **Model Integration:** We chose the native `OpenAIModel` provided by Strands because MiniMax M2.7 exposes an OpenAI-compatible endpoint. This eliminates the need for writing a custom model provider.
- **Strands Tools Usage:** Agents will interact with the filesystem directly via tools (`file_write`, `editor`) instead of outputting raw markdown code blocks. This is faster and prevents formatting errors.
- **Agent Orchestration:** We use the Agent-as-a-Tool pattern where the Orchestrator (Architect) is given the Backend, Frontend, and QA agents as tools. This provides dynamic coordination (e.g., repeating QA after a fix) compared to a strict sequential GraphBuilder pipeline.
- **Human-in-the-loop (Safety):** The system relies on GitHub PRs and branch protection rules to ensure no AI-generated code merges to main without human review.

## Risks / Trade-offs

- [Risk] Agents falling into infinite loops and consuming excessive API tokens. -> Mitigation: Implement strict token tracking, max iteration limits (e.g., 20 calls per agent), and time limits (5 mins) to pause the pipeline and mark the ticket as blocked.
- [Risk] Unreliable API endpoints (MiniMax or Jira downtime). -> Mitigation: Implement retry logic with exponential backoff and circuit breakers. Use a fallback model (e.g., MiniMax via OpenRouter) if the primary endpoint fails.

## Socket.IO Real-Time Events

The pipeline emits real-time events via Socket.IO to notify frontend clients of pipeline progress.

### Architecture

```
┌─────────────────┐     Socket.IO      ┌─────────────────┐
│   Frontend      │◄──────────────────►│   FastAPI       │
│   (React)       │   /pipeline        │   + python-socketio│
└─────────────────┘                     └────────┬────────┘
                                                 │
                                        ┌────────▼────────┐
                                        │   Pipeline      │
                                        │   (events.py)   │
                                        └─────────────────┘
```

### Server Configuration

Located in `backend/app/events.py`:
- `socketio.AsyncServer` with ASGI mode
- CORS: `*` (all origins)
- Namespace: `/pipeline`
- `PipelineNamespace` class handles connect/disconnect

### Emitted Events

| Event | Payload | Description |
|-------|---------|-------------|
| `pipeline_started` | `{session_id, ticket_id}` | Pipeline initiated for a ticket |
| `pipeline_completed` | `{session_id, ticket_id, result}` | Pipeline finished successfully |
| `pipeline_error` | `{session_id, ticket_id, error}` | Pipeline failed with error |

### Dependencies (Verified Compatible)

```
python-socketio==5.10.0
python-engineio==4.3.1
aiohttp==3.9.5
```

### Testing Socket.IO via Command Line

```bash
# Terminal 1: Start the server
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2: Connect client and listen for events
python -c "
import socketio
sio = socketio.AsyncClient()
@sio.on('pipeline_started')
def on_started(data): print(f'STARTED: {data}')
@sio.on('pipeline_completed') 
def on_completed(data): print(f'COMPLETED: {data}')
@sio.on('pipeline_error')
def on_error(data): print(f'ERROR: {data}')
async def test():
    await sio.connect('http://localhost:8000', namespaces=['/pipeline'], transports=['polling'])
    print('Connected to /pipeline! Waiting for events...')
    await sio.wait()
import asyncio; asyncio.run(test())
"
```

Expected output when connected:
```
Connected to /pipeline! Waiting for events...
```

The client will print events as they are emitted by the pipeline.
