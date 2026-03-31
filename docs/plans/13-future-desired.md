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

## 12.8 Remote Repository Operations

Allow agents to **operate on any GitHub repository** — not just the repo where the agent system lives. This decouples the agent infrastructure from the target codebases, enabling a single deployment to serve multiple projects.

### Problem

Currently agents can only read/write files within their own repository. In real-world scenarios, the code that needs to be modified lives in separate repositories (e.g., a backend API repo, a frontend SPA repo, or a monorepo with multiple services).

### Proposed Solution

#### Environment Configuration

Repositories are declared via environment variables or a YAML config file:

```bash
# Environment variables
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_ORG=my-org

# Target repositories (comma-separated or config file)
AGENT_TARGET_REPOS=my-org/backend-api,my-org/frontend-app,my-org/shared-libs
AGENT_REPOS_CONFIG_PATH=./config/repositories.yaml
```

```yaml
# config/repositories.yaml
repositories:
  - name: backend-api
    owner: my-org
    default_branch: main
    clone_depth: 1
    cache_ttl: 3600  # seconds
    languages: [python]

  - name: frontend-app
    owner: my-org
    default_branch: develop
    cache_ttl: 1800
    languages: [typescript, javascript]

  - name: infrastructure
    owner: my-org
    default_branch: main
    read_only: true  # agents can reference but not modify
    languages: [hcl, yaml]
```

#### Core Capabilities

| Capability | Description |
|---|---|
| **Clone & Checkout** | Shallow clone target repos into an isolated workspace per ticket |
| **Branch Management** | Create feature branches following repo-specific naming conventions |
| **Cached Workspaces** | Reuse cached clones with `git fetch` to avoid full re-clones |
| **Cross-Repo References** | Agents can read code from repo A while modifying repo B (e.g., check API contract in backend before updating frontend) |
| **Pull Request Creation** | Create PRs directly on the target repo via GitHub API/MCP |
| **Multi-Repo PRs** | A single Jira ticket can produce PRs across multiple repos |
| **Dependency Awareness** | Detect shared dependencies between repos (e.g., shared types, API contracts) |

#### Architecture

```
Jira Ticket
     ↓
Orchestrator Agent
     ↓ identifies affected repos
┌────────────────────────────────┐
│     RepoManager Service        │
│  ┌───────┐ ┌───────┐ ┌──────┐ │
│  │Cache  │ │Clone  │ │Branch│ │
│  │Layer  │ │Worker │ │Mgr   │ │
│  └───┬───┘ └───┬───┘ └──┬───┘ │
│      └─────────┼────────┘     │
│           Workspace FS         │
│   /workspaces/{ticket_id}/     │
│     ├── backend-api/           │
│     ├── frontend-app/          │
│     └── shared-libs/           │
└────────────────────────────────┘
     ↓
Specialized Agents operate on isolated workspaces
     ↓
PRs created on each affected repo
```

#### RepoManager Service

```python
class RepoManager:
    async def prepare_workspace(self, ticket_id: str, repos: list[str]) -> WorkspacePath:
        """Clone or restore cached repos into an isolated workspace."""

    async def create_branch(self, repo: str, ticket_id: str, base_branch: str | None = None) -> str:
        """Create a feature branch on the target repo."""

    async def create_pull_request(self, repo: str, branch: str, title: str, body: str) -> PRResult:
        """Create a PR on the remote repo via GitHub API."""

    async def sync_cache(self, repo: str) -> None:
        """Fetch latest changes into the cached clone."""

    async def cleanup_workspace(self, ticket_id: str) -> None:
        """Remove the isolated workspace after PR creation."""
```

#### Cache Strategy

- **Layer 1 — Bare clone cache**: Persistent bare clones per repo, updated via `git fetch` on a schedule or before each ticket.
- **Layer 2 — Worktree per ticket**: `git worktree add` from the bare clone for each ticket workspace. Fast, disk-efficient, fully isolated.
- **TTL-based invalidation**: Configurable per repo. High-churn repos get shorter TTL.
- **Disk budget**: Configurable max cache size with LRU eviction.

#### New Environment Variables

```bash
# Remote repo operations
AGENT_WORKSPACE_ROOT=/var/agent-workspaces
AGENT_CACHE_ROOT=/var/agent-cache
AGENT_CACHE_MAX_SIZE_GB=10
AGENT_DEFAULT_CACHE_TTL=3600
AGENT_PR_DRAFT_MODE=true          # create PRs as drafts by default
AGENT_PR_AUTO_REVIEWERS=true      # assign reviewers from CODEOWNERS
AGENT_CLONE_DEPTH=1               # default shallow clone depth
AGENT_MULTI_REPO_STRATEGY=parallel  # parallel | sequential
```

#### Integration with Existing Pipeline

The ticket pipeline gains a new early stage:

```
NEW → REPO_SETUP → TRIAGED → IN_ANALYSIS → IN_DEVELOPMENT → ...
```

During `REPO_SETUP`, the orchestrator:
1. Identifies which repos are affected (from ticket labels, description, or AI analysis)
2. Prepares isolated workspaces via `RepoManager`
3. Creates feature branches on each target repo
4. Passes workspace paths to specialized agents

#### Security Considerations

- GitHub token scoped to only the declared repos (use fine-grained PATs)
- `read_only` flag prevents agents from modifying infrastructure or sensitive repos
- Branch protection rules on target repos remain enforced
- All PRs require human review (existing human-in-the-loop principle)
- Workspace cleanup after ticket completion to avoid stale code accumulation
