# 1. Overview

Multi-agent system that activates automatically when a Jira ticket is created or updated. Specialized software development agents (Architect, Backend, Frontend, QA) analyze the ticket, generate code, run tests, and create a Pull Request. **A human always reviews and approves before merging to production.**

## Main Flow

```
Jira Ticket (polling detects "To Do")
       ↓
Strands SDK Orchestrator Agent
  ├── Jira API (direct polling)
  ├── GitHub MCP (future: create branch, PR)
  ↓ decomposes the ticket
  ┌────┼────┬────────┐
  ↓    ↓    ↓        ↓
Arch  Back  Front    QA
Agent Agent Agent  Agent
  │    (strands_tools: file_read, file_write, editor, shell)
  └────┼────┴────────┘
       ↓ generated code
  Git Branch + Pull Request (via GitHub API)
       ↓
  CI/CD Pipeline
       ↓ automated tests
  Human Review & Approve
       ↓
  Runbook: Validation and Documentation
       ↓
  Merge → Deploy to Prod
```

## Principles

- **Human-in-the-loop**: Generated code NEVER goes directly to production. Always passes through PR + human review.
- **Cost-effective**: MiniMax M2.7 as main LLM via OpenAI-compatible API.
- **Cloud-agnostic**: Docker + PostgreSQL locally and in production. No dependency on specific cloud services.
- **API-first**: Jira integrates via direct REST API; MCP for future tools.
- **Billing guardrails**: Timeouts, iteration limits, and token budgets per agent to avoid infinite loops.
- **Strands tools**: Agents use `strands_tools` (file_read, file_write, editor, shell) to operate on code.
- **Observable**: Real-time 2D Canvas dashboard via Socket.IO.
