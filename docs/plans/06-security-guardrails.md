# 6. Security and Guardrails

## Security
- API keys in `.env` (git-ignored). In production, inject as cloud provider secrets
- Agents execute code in **isolated directories** (`/app/workspaces/<ticket-id>/`)
- Branch protection rules prevent merge without review
- MCP servers run as backend subprocesses, not exposed externally

## Anti-Loop Guardrails and Billing Control

> **CRITICAL for PoC and production.** Agents can enter infinite loops that consume tokens non-stop. These guardrails are mandatory.

### Per-Agent Limits

```python
from strands import Agent

agent = Agent(
    model=minimax,
    system_prompt="...",
    tools=[...],
)
```

### Limit Configuration

| Guardrail | Default Value | Description |
|---|---|---|
| **Agent timeout** | 5 min | Agent is cancelled if exceeded |
| **Max iterations (tool calls)** | 20 | Max tool calls per agent invocation |
| **Max orchestrator iterations** | 50 | Orchestrator has more margin because it coordinates |
| **Token budget per session** | 100k tokens | Tracked and cut if exceeded |
| **Max files per agent** | 15 | Prevents an agent from creating infinite files |
| **Max file size** | 500 lines | If an agent generates more, it's cut and reports error |

### Token Tracker Implementation

```python
import time
from dataclasses import dataclass, field

@dataclass
class SessionBudget:
    max_tokens: int = 100_000
    max_duration_seconds: int = 600
    max_tool_calls_per_agent: int = 20

    tokens_used: int = 0
    start_time: float = field(default_factory=time.time)
    tool_calls: dict[str, int] = field(default_factory=dict)

    def track_tokens(self, agent_id: str, tokens: int):
        self.tokens_used += tokens
        if self.tokens_used > self.max_tokens:
            raise BudgetExceededError(
                f"Session token budget exceeded: {self.tokens_used}/{self.max_tokens}"
            )

    def track_tool_call(self, agent_id: str):
        self.tool_calls[agent_id] = self.tool_calls.get(agent_id, 0) + 1
        if self.tool_calls[agent_id] > self.max_tool_calls_per_agent:
            raise BudgetExceededError(
                f"Agent {agent_id} exceeded max tool calls: "
                f"{self.tool_calls[agent_id]}/{self.max_tool_calls_per_agent}"
            )

    def check_timeout(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.max_duration_seconds:
            raise BudgetExceededError(
                f"Session timeout: {elapsed:.0f}s / {self.max_duration_seconds}s"
            )

class BudgetExceededError(Exception):
    pass
```

### What Happens When a Limit is Exceeded

1. The agent stops immediately
2. Partial state is saved to DB
3. `budget_exceeded` event is emitted to dashboard
4. Comment posted to Jira: "Agent pipeline paused — budget exceeded. Manual intervention required."
5. Ticket is transitioned to "Blocked"

## Error Handling
- Retry with exponential backoff on MiniMax API calls
- Circuit breaker if MiniMax is down (notifies and pauses)
- Per-agent timeout (configurable, default 5 min)
- If an agent fails 2 times, the orchestrator marks the ticket as "Blocked" in Jira

## Costs
- **MiniMax M2.7**: check current pricing at https://platform.minimax.io/subscribe/token-plan
- **Infra**: PostgreSQL + Docker containers — fixed and predictable cost
- **No serverless services** that scale unexpectedly
- Token budget guardrails are the main protection against surprise billing

## Observability
- Logs in stdout (structured JSON) + PostgreSQL (`agent_events` table) + Socket.IO dashboard
- In production, add log collector (Loki, ELK, or cloud provider's native solution)
