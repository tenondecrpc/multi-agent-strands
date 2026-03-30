# 11. Operational Runbook

## 11.1 Common Operations

### Start the system (local)

```bash
# 1. Verify Docker is running
docker --version

# 2. Start all services
docker compose up -d

# 3. Check service status
docker compose ps

# 4. View real-time logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# 5. Verify Jira API connection
docker compose exec backend curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_URL/rest/api/3/myself" | head -c 200
```

### Stop the system

```bash
# Stop all services (preserves data)
docker compose stop

# Stop and remove volumes (DELETES DATA)
docker compose down -v
```

### Restart a specific service

```bash
docker compose restart backend
docker compose restart frontend
docker compose restart db
```

---

## 11.2 Health Verification

### Healthchecks

```bash
# Backend API
curl -f http://localhost:8000/health

# Frontend
curl -f http://localhost:5173

# PostgreSQL
docker compose exec db pg_isready -U agent -d multi_agent

# WebSocket (Socket.IO)
curl -f http://localhost:8000/socket.io/?EIO=4&transport=polling
```

### Pipeline Health Checklist

| Component | Verification | Command |
|---|---|---|
| **PostgreSQL** | Active connection | `docker compose exec db psql -U agent -d multi_agent -c "SELECT 1"` |
| **MiniMax API** | API responds | `curl -s -o /dev/null -w "%{http_code}" https://api.minimax.io/v1/models` |
| **Jira API** | API responds | `curl -s -o /dev/null -w "%{http_code}" https://your-domain.atlassian.net/rest/api/3/myself` |
| **GitHub MCP** | Valid token | `gh auth status` |
| **strands_tools** | Tools load | `python -c "from strands_tools import file_read, file_write; print('OK')"` |

---

## 11.3 Incident Handling

### Failed Pipeline — Blocked Ticket

**Symptom**: Jira ticket is in "Blocked" status or PR was not created.

**Diagnosis**:
```bash
# 1. Check backend logs
docker compose logs backend --tail=100 | grep -i error

# 2. Verify workspace exists
ls -la workspaces/

# 3. Check session state in DB
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT id, ticket_id, status, error FROM agent_sessions ORDER BY created_at DESC LIMIT 5;"
```

**Resolution**:
```bash
# 1. Clean ticket workspace
rm -rf workspaces/<ticket-id>/

# 2. Reset state in Jira (manual or via UI)

# 3. Re-launch pipeline manually
curl -X POST http://localhost:8000/trigger/<ticket-id>
```

### Jira/GitHub Authentication Error

**Symptom**: `AuthenticationError` in logs.

**Diagnosis**:
```bash
# Verify environment variables
docker compose exec backend env | grep -E "(JIRA|GITHUB)"

# Test Jira token
docker compose exec backend curl -s -u "$JIRA_EMAIL:$JIRA_API_TOKEN" \
  "$JIRA_URL/rest/api/2/myself" | head -c 200

# Test GitHub token
gh auth status
```

**Resolution**:
```bash
# Update secrets in .env
# Restart backend
docker compose restart backend
```

### Budget exceeded (tokens/iterations)

**Symptom**: `BudgetExceededError` in logs, ticket in "Blocked".

**Diagnosis**:
```bash
# Check token consumption
docker compose logs backend | grep -i "budget\|tokens"

# Check last budget event
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT * FROM agent_events WHERE event_type = 'budget_exceeded' ORDER BY created_at DESC LIMIT 3;"
```

**Resolution**:
```bash
# Increase limits in config (temporarily)
# Or clear session and retry
docker compose exec db psql -U agent -d multi_agent -c \
  "DELETE FROM agent_events WHERE session_id = '<session-id>';"
```

### MiniMax API Not Responding

**Symptom**: `ConnectionError` or timeout on LLM calls.

**Diagnosis**:
```bash
# Test connectivity
curl -v https://api.minimax.io/v1/models \
  -H "Authorization: Bearer $MINIMAX_API_KEY" 2>&1 | head -20

# Check rate limits
curl -s https://api.minimax.io/v1/usage \
  -H "Authorization: Bearer $MINIMAX_API_KEY"
```

**Resolution**:
```bash
# Wait and retry (automatic backoff if implemented)
# If problem persists, check MiniMax status
# Alternative: use OpenRouter as fallback
```

### Model reaches 70% usage (dynamic switch)

**Symptom**: ~70% of current model's token quota reached.

**Configured models**:
- **Primary**: `MiniMax-M2.7` via api.minimax.io
- **Fallback**: `MiniMax-M2.7` via OpenRouter

**Resolution (manual switch to fallback)**:
```bash
# Change MINIMAX_API_URL in .env to OpenRouter
sed -i 's|MINIMAX_API_URL=.*|MINIMAX_API_URL=https://openrouter.ai/api/v1|' .env
docker compose restart backend
```

---

## 11.4 Recovery Procedures

### Disaster Recovery — PostgreSQL Loss

```bash
# 1. Verify volume persists
docker compose inspect db | grep -A5 "Mounts"

# 2. If there is a backup, restore
docker compose exec db psql -U agent -d multi_agent < backup.sql

# 3. If no backup and there are workspaces:
#    Agents can regenerate code from the PR
#    Only events/historic are lost
```

### Corrupt Workspace Recovery

```bash
# 1. Identify problematic workspaces
ls -la workspaces/

# 2. Regenerate from PR
#    - The PR contains all generated code

# 3. Clean workspace
rm -rf workspaces/<ticket-id>/
```

---

## 11.5 Debugging Commands

```bash
# View all events from a session
docker compose exec db psql -U agent -d multi_agent -c \
  "SELECT agent_id, event_type, created_at FROM agent_events \
   WHERE session_id = '<session-id>' ORDER BY created_at;"

# View logs from a specific agent
docker compose logs -f backend 2>&1 | grep "backend_agent"

# View resource consumption
docker stats

# View environment variables loaded in backend
docker compose exec backend env | sort

# Access shell in container
docker compose exec backend /bin/bash

# Verify dependency versions
docker compose exec backend pip list | grep -E "(strands|fastapi|socketio)"

# Test MCP manually
docker compose exec backend python -c "
from mcp import stdio_client, StdioServerParameters
print('MCP client imported OK')
"
```

---

## 11.6 Contacts and Escalation

| Level | Responsible | When to Escalate |
|---|---|---|
| **L1** | DevOps on-call | Failed pipeline, connection errors |
| **L2** | Backend Lead | Agent bugs, memory leaks, performance |
| **L3** | Architect | Agent design, flow changes, major incidents |
