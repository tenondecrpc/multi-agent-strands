# 7. Monitoring Dashboard (MVP) ✅

## 7.1 Architecture

```
PostgreSQL → Socket.IO (FastAPI) → React Dashboard
                                               ↓
                                          Canvas 2D (SVG)
                                          AgentFigures
                                          LogPanel
                                          MetricsPanel
```

## 7.2 Real-Time Communication (Socket.IO)

```python
import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

async def emit_event(session_id: str, event_type: str, payload: dict):
    """Emits event to all clients connected to the session room."""
    await sio.emit("agent_event", {
        "type": event_type,
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }, room=session_id)

@sio.event
async def join_session(sid, data):
    """Client joins a session room to receive events."""
    sio.enter_room(sid, data["session_id"])
    state = await get_session_state(data["session_id"])
    await sio.emit("state_sync", state, to=sid)
```

### Message Format

```json
{
  "type": "agent_state_change",
  "session_id": "abc-123",
  "timestamp": "2026-03-29T10:30:00Z",
  "payload": {
    "agent_id": "backend_agent",
    "previous_state": "idle",
    "new_state": "working",
    "task": "Creating user model and API endpoints",
    "progress": 0.3
  }
}
```

Event types: `agent_state_change`, `agent_log`, `task_assigned`, `task_completed`, `error`, `pipeline_started`, `pipeline_completed`, `pr_created`.

## 7.3 2D Figure System (SVG Sprites)

Each agent is represented as a simple SVG character with CSS animations per state.

### Visual States

| State | Visual | CSS Animation |
|---|---|---|
| `idle` | Neutral character, base color | `animate-bob` (soft vertical float 2px, 2s) |
| `thinking` | Thought bubble with "..." | `animate-pulse` (pulsing opacity, 1s) |
| `working` | Activity particles, active tool | `animate-work` (hand movement, 0.5s) |
| `waiting` | Hourglass or "?" above head | `animate-wait` (slow opacity, 3s) |
| `success` | Green check, happy expression | `animate-bounce` (bounce, 0.5s) |
| `error` | Red "!", worried expression | `animate-shake` (horizontal vibration, 0.3s) |

### Design by Role

| Agent | Primary Color | Distinctive Element |
|---|---|---|
| **Architect** | Navy blue `#1E3A5F` | Hat/helmet + blueprint |
| **Backend** | Emerald green `#0D7377` | Terminal/prompt + headphones |
| **Frontend** | Coral `#FF6B6B` | Color palette + round glasses |
| **QA** | Orange `#F0932B` | Giant magnifying glass + lab coat |

### React Component

```tsx
interface AgentFigureProps {
  agent: {
    id: string;
    name: string;
    role: "architect" | "backend" | "frontend" | "qa";
    state: "idle" | "thinking" | "working" | "waiting" | "success" | "error";
    task?: string;
    progress?: number;
  };
}

const ANIMATION_CLASS: Record<string, string> = {
  idle: "animate-bob",
  thinking: "animate-pulse",
  working: "animate-work",
  waiting: "animate-wait",
  success: "animate-bounce",
  error: "animate-shake",
};

const AgentFigure: React.FC<AgentFigureProps> = ({ agent }) => (
  <g className={`agent agent-${agent.role} ${ANIMATION_CLASS[agent.state]}`}>
    <AgentSprite role={agent.role} state={agent.state} />

    {agent.state === "thinking" && <ThoughtBubble />}
    {agent.state === "working" && agent.progress != null && (
      <ProgressRing progress={agent.progress} />
    )}
    {agent.state === "error" && <ErrorIndicator />}

    <text className="agent-name" textAnchor="middle" y={120}>
      {agent.name}
    </text>
    {agent.task && (
      <text className="agent-task" textAnchor="middle" y={136} fontSize={10}>
        {agent.task}
      </text>
    )}
  </g>
);
```

### Connections Between Agents

```tsx
const AgentConnection: React.FC<{ from: Point; to: Point; active: boolean }> = ({
  from, to, active,
}) => (
  <line
    x1={from.x} y1={from.y}
    x2={to.x} y2={to.y}
    stroke={active ? "#4A90D9" : "#ccc"}
    strokeWidth={active ? 2 : 1}
    strokeDasharray={active ? "8 4" : "none"}
    className={active ? "animate-dash" : ""}
  />
);
```

## 7.4 Dashboard Layout

```
┌──────────────┬──────────────────────────────┬──────────────┐
│              │                              │              │
│  Task List   │     Central Canvas (60%)     │   Log Panel  │
│   (20%)      │                              │    (20%)     │
│              │   ┌─────┐     ┌─────┐       │              │
│  PROJ-123    │   │Arch │────→│Back │       │  [backend]   │
│  ├─ Backend  │   └──┬──┘     └──┬──┘       │  Creating    │
│  ├─ Frontend │      │           │           │  user model  │
│  └─ QA       │      │       ┌───┴──┐       │              │
│              │      └──────→│Front │       │  [qa]        │
│  Status:     │              └───┬──┘       │  Waiting...  │
│  In Progress │                  │           │              │
│              │              ┌───┴──┐       │              │
│              │              │  QA  │       │              │
│              │              └──────┘       │              │
│              │                              │              │
└──────────────┴──────────────────────────────┴──────────────┘
│                    Metrics Bar                              │
│  Tokens: 12.4k  │  Time: 2m 30s  │  Files: 8  │  Tests: ✓ │
└─────────────────────────────────────────────────────────────┘
```

## 7.5 Dashboard Components

| Component | Responsibility |
|---|---|
| `AgentCanvas` | Central SVG canvas, renders figures and connections |
| `AgentFigure` | Individual sprite with state and animation |
| `TaskPanel` | Ticket task list, state of each |
| `LogPanel` | Real-time logs, filterable by agent |
| `MetricsBar` | Tokens used, time, files generated, test status |
| `ConnectionStatus` | Socket.IO connection status with auto-reconnect |
