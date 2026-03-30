# 12. Future / Desired

> The following functionalities **are not part of the MVP** but are planned for future iterations.

## 12.1 Jira Webhook Integration

Replace polling with **Jira webhooks** for real-time ticket detection:

- Jira webhook → API Gateway (Cloudflare/Railway) → FastAPI endpoint
- Eliminates polling interval delay
- More efficient in API calls
- Requires: publicly exposed endpoint or tunnel (ngrok/cloudflared)

## 12.2 Production Remediation Agents

Use agents to **diagnose and automatically resolve production errors**:

- CloudWatch Alarm → EventBridge → Lambda → Strands Orchestrator
- Diagnostic Agent: analyzes logs, metrics, error traces
- Remediation Agent: executes corrective actions (scale instance, rollback, restart service)
- Validation Agent: verifies fix worked
- Requires: IAM roles with execution permissions, strict guardrails, predefined runbooks

## 12.3 DevOps Agent

Agent that generates and maintains IaC (CDK/CloudFormation), Dockerfiles, and CI/CD pipelines.

## 12.4 Documentation Agent

Generates and maintains README, API docs, and contribution guides from generated code.

## 12.5 Review Learning

Store human code review feedback so agents improve over time (fine-tuning or RAG over PR comments).

## 12.6 Advanced Dashboard

- Sprite sheets with pixel art and advanced animations
- Light/dark themes
- Configurable agent skins
- Historical metrics and analytics
- **Reference for pixel art agent visualization**: [Pixel Agents](https://github.com/pablodelucca/pixel-agents) — VS Code extension with pixel art office, Canvas 2D game loop, BFS pathfinding, character state machine, and modular asset system (sprites, furniture, floors). 5.7k stars. Agent-agnostic and platform-agnostic architecture designed to extend beyond Claude Code.

## 12.7 AgentCore with Full AWS (Alternative Architecture)

**Future alternative for teams already invested in AWS.**

| Criteria | Strands SDK (MVP) | Bedrock AgentCore (Future) |
|---|---|---|
| External LLM (MiniMax) | **Yes** — `OpenAIModel` provider | No — Bedrock models only |
| Flow control | Total, it's your Python code | Managed, less flexibility |
| Infra cost | Only ECS + LLM API | AgentCore Runtime + LLM |
| Multi-agent patterns | Agents-as-tools, GraphBuilder, Swarm | Limited to Bedrock agents |
| Learning curve | Moderate, good docs | Low but less flexible |
| Demo-friendliness | **High** — you can show the code | More "black box" |
| Vendor lock-in | **Low** — cloud-agnostic | High — AWS only |

**When to consider migrating to AgentCore:**
- Team already has deep AWS experience
- Native Bedrock integration needed (Claude, etc.)
- Management simplicity prioritized over control
- AgentCore Runtime cost is acceptable

**Note:** The current architecture (Strands + Docker + PostgreSQL) is designed to be cloud-agnostic. If migrating to Bedrock in the future, Strands supports both without significant architectural changes.

### DynamoDB as PostgreSQL Alternative (AWS)

For AWS deployment, PostgreSQL can be replaced with DynamoDB:

| Table | PK | SK | Use |
|---|---|---|---|
| `AgentSessions` | `session_id` | `#metadata` | Pipeline state |
| `AgentEvents` | `session_id` | `timestamp#event_id` | Dashboard events |
| GSI: `TicketIndex` | `ticket_id` | `created_at` | Search by ticket |

The data access layer is abstracted with a **repository pattern** so the PostgreSQL → DynamoDB switch is transparent.

```
DynamoDB Streams → Lambda → Socket.IO (FastAPI) → React Dashboard
```
