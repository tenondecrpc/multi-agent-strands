# AGENTS.md - Development Guidelines for Multi-Agent Strands Project

This document provides guidelines for agents working on this codebase.

## Project Overview

This is a multi-agent software development system that automates Jira ticket handling. It consists of:
- **Frontend**: React + Vite + TypeScript
- **Backend**: FastAPI (Python 3.12+) with Strands Agents SDK
- **Database**: PostgreSQL with SQLAlchemy + asyncpg

## 1. Build, Lint, and Test Commands

### Backend (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt
# or with uv
uv pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run a single test
pytest tests/test_file.py::test_function_name
pytest -k "test_function_name"

# Run tests with coverage
pytest --cov=. --cov-report=html

# Lint with ruff
ruff check .
ruff check --fix .

# Format code
ruff format .

# Type checking with mypy
mypy .
```

### Frontend (React + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run a single test
npm test -- --testPathPattern="test_name"
# or with Vitest
npx vitest run test_file_name

# Run tests in watch mode
npm test -- --watch

# Lint
npm run lint

# Format code
npm run format

# Type checking
npx tsc --noEmit
```

### Docker

```bash
# Start all services
docker compose up -d

# Start with logs
docker compose up

# Stop all services
docker compose down

# Rebuild services
docker compose build --no-cache

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 2. Code Style Guidelines

### General Principles

- **No comments** unless explicitly requested by the user
- Use meaningful variable and function names
- Keep functions small and focused (single responsibility)
- Follow DRY (Don't Repeat Yourself) principle
- Write tests for all new functionality

### Python (Backend)

#### Imports

```python
# Standard library first
import os
import sys
from typing import Optional, List
from datetime import datetime

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Local application imports
from app.models import User
from app.schemas import UserCreate
from app.services.user import UserService
```

#### Naming Conventions

- **Variables/functions**: `snake_case` (e.g., `get_user_by_id`, `user_data`)
- **Classes**: `PascalCase` (e.g., `UserService`, `TicketResponse`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)
- **Private methods**: prefix with underscore (e.g., `_internal_method`)
- **Async functions**: prefix with `async_` or use `aio` where appropriate

#### Type Annotations

```python
# Always use type annotations for function signatures
def process_ticket(ticket_id: str, user_id: int) -> dict[str, Any]:
    ...

# Use Optional for nullable types
def get_optional_value(value: Optional[str] = None) -> str:
    ...

# Use Union for multiple types
def parse_input(value: str | int) -> str:
    ...

# Generic types
def process_items(items: list[dict[str, Any]]) -> list[User]:
    ...
```

#### Error Handling

```python
# Use custom exception classes
class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")

# Handle exceptions with specific except blocks
try:
    result = await service.get_ticket(ticket_id)
except TicketNotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

#### Database (SQLAlchemy)

```python
# Use async sessions
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

# Use async context manager for sessions
async def get_db():
    async with async_session_maker() as session:
        yield session
```

#### Pydantic Models

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8)

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### TypeScript/React (Frontend)

#### Imports

```typescript
// React imports first
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

// Third-party imports
import { useQuery, useMutation } from '@tanstack/react-query';
import { AxiosError } from 'axios';

// Local imports
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
```

#### Naming Conventions

- **Components**: `PascalCase` (e.g., `UserProfile.tsx`, `TicketCard.tsx`)
- **Hooks**: `camelCase` with `use` prefix (e.g., `useUserData`, `useTickets`)
- **Utils/Helpers**: `camelCase` (e.g., `formatDate.ts`, `validateEmail.ts`)
- **Constants**: `UPPER_SNAKE_CASE` or `camelCase` depending on usage
- **Types/Interfaces**: `PascalCase` (e.g., `UserType`, `TicketProps`)

#### Type Annotations

```typescript
// Interface definitions
interface User {
  id: number;
  email: string;
  name: string;
  createdAt: Date;
}

// Type with generics
interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

// Function type annotations
const fetchUser = async (id: string): Promise<User> => {
  const response = await api.get(`/users/${id}`);
  return response.data;
};
```

#### Component Structure

```typescript
// Functional component with TypeScript
interface TicketCardProps {
  ticket: Ticket;
  onSelect: (id: string) => void;
}

export const TicketCard = ({ ticket, onSelect }: TicketCardProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = () => {
    setIsLoading(true);
    onSelect(ticket.id);
  };

  return (
    <div className="ticket-card">
      <h3>{ticket.title}</h3>
      <Button onClick={handleClick} disabled={isLoading}>
        {isLoading ? 'Loading...' : 'View'}
      </Button>
    </div>
  );
};
```

#### Error Handling

```typescript
// Try-catch with proper typing
try {
  const data = await fetchTicket(ticketId);
  setTicket(data);
} catch (error) {
  if (error instanceof AxiosError) {
    setError(error.response?.data?.message || 'Failed to fetch ticket');
  } else {
    setError('An unexpected error occurred');
  }
}

// Use error boundaries for component errors
```

### Git Conventions

- **Branch naming**: `feature/ticket-description` or `fix/bug-description`
- **Commit messages**: Use imperative mood (e.g., "Add user authentication" not "Added user authentication")
- **PR titles**: Clear description of changes

---

## 3. Project Structure

```
multi-agent-strands/
├── frontend/                 # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── types/            # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                  # FastAPI + Strands
│   ├── app/
│   │   ├── api/              # API routes/endpoints
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── agents/            # Strands agent definitions
│   │   ├── tools/            # Custom tools
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── docker-compose.yml
└── AGENTS.md
```

---

## 4. Database Schema

PostgreSQL database with the following tables (to be defined):
- `users` - System users
- `tickets` - Jira ticket tracking
- `agents` - Agent state and history
- `workspaces` - Agent workspace references
- `audit_log` - Operation logs

---

## 5. Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://agent:agent_local@db:5432/multi_agent

# LLM
MINIMAX_API_KEY=your_api_key

# Jira (MCP)
JIRA_URL=your_jira_url
JIRA_API_TOKEN=your_api_token
JIRA_EMAIL=your_email

# GitHub (MCP)
GITHUB_TOKEN=your_github_token

# Frontend
VITE_SOCKET_URL=http://localhost:8000
```

---

## 6. Testing Guidelines

### Backend Tests

- Use `pytest` with `pytest-asyncio` for async tests
- Place tests in `tests/` directory mirroring the `app/` structure
- Use fixtures for common test data
- Mock external services (LLM, MCP, database)

```python
@pytest.fixture
async def mock_db():
    # Create mock database session
    ...

@pytest.mark.asyncio
async def test_get_ticket(mock_db):
    service = TicketService(mock_db)
    ticket = await service.get_ticket("PROJ-123")
    assert ticket.title == "Test Ticket"
```

### Frontend Tests

- Use Vitest or Jest with React Testing Library
- Test component rendering and user interactions
- Mock API calls with MSW or similar

```typescript
import { render, screen, fireEvent } from '@testing-library/react';

test('renders ticket card', () => {
  render(<TicketCard ticket={mockTicket} onSelect={fn} />);
  expect(screen.getByText('Test Ticket')).toBeInTheDocument();
});
```

---

## 7. Strands Agents Configuration

Agents use the Strands SDK with the following tools:
- `file_read` - Read files from workspace
- `file_write` - Write files to workspace
- `editor` - Edit files in workspace
- `shell` - Execute shell commands
- `python_repl` - Execute Python code
- `current_time` - Get current time

MCP integrations:
- `mcp-atlassian` - Jira integration
- `github-mcp-server` - GitHub integration

---

## 8. Key Conventions

1. **Always verify changes** - Run tests and lint before considering work complete
2. **Type safety** - Use TypeScript types and Python type hints everywhere
3. **Error handling** - Never let exceptions propagate unhandled
4. **Logging** - Use structured logging for debugging
5. **Security** - Never expose secrets; use environment variables
6. **Human review** - All code changes require human approval before merge
7. **Use official CLIs for scaffolding** - Always prefer official CLIs over manual file creation when initializing projects or adding scaffolds (see Section 10)

---

## 9. OpenSpec Commands (SDD - Specification Driven Development)

This project uses OpenSpec for specification-driven development. The following commands are available:

### List of Commands

| Command | Alias | Description |
|---------|-------|-------------|
| `/opsx:propose` | - | Propose a new change with all artifacts generated in one step |
| `/opsx:apply` | `/opsx:implement` | Implement tasks from an OpenSpec change |
| `/opsx:explore` | - | Enter explore mode - think through ideas and investigate problems |
| `/opsx:archive` | - | Archive a completed change after implementation is complete |

### Runbooks

For operational procedures and incident handling, see [MULTI_AGENT_DEV_SYSTEM.md](./MULTI_AGENT_DEV_SYSTEM.md#10-runbook-operacional).

### OpenSpec CLI Commands

You can also use the `openspec` CLI directly:

```bash
# List all changes
openspec list
openspec list --json

# Check status of a specific change
openspec status --change "<name>"
openspec status --change "<name>" --json

# Create a new change
openspec new change "<name>"

# Get instructions for an artifact
openspec instructions <artifact-id> --change "<name>" --json

# Get instructions for apply phase
openspec instructions apply --change "<name>" --json

# Show help
openspec --help
```

### Workflow

1. **Explore**: Use `/opsx:explore` to think through ideas before committing
2. **Propose**: Use `/opsx:propose` to create a new change with proposal, design, and tasks
3. **Implement**: Use `/opsx:apply` to implement tasks from the change
4. **Archive**: Use `/opsx:archive` to finalize and archive completed changes

---

## 10. Project Scaffolding with Official CLIs

**RULE: Always use official CLIs for project scaffolding and initialization.** Manual file creation is only acceptable when no official CLI exists or when extending an existing project.

### Why CLIs?

| Aspect | CLI | Manual |
|--------|-----|--------|
| Speed | Seconds | Minutes |
| Consistency | Always the same | Human errors |
| Versions | Always up to date | Can become outdated |
| Boilerplate | Proven templates | May forget something |

### Frontend (React + Vite + TypeScript)

```bash
# Use npm create vite for new projects
npm create vite@latest my-app -- --template react-ts

# Do NOT do this manually:
# mkdir -p src/components src/hooks src/pages
# touch src/App.tsx vite.config.ts
```

### Backend (Python/FastAPI)

```bash
# Use pip/uv to install and create structure
uv pip install fastapi uvicorn sqlalchemy pydantic

# For more complex structures, use cookiecutters or official templates
# https://github.com/tiangolo/full-stack-fastapi-postgresql
```

### Node.js Libraries

```bash
# Use npm init to initialize
npm init -y

# For TypeScript libraries
npx tsdx create mylib
```

### Docker

```bash
# Use docker init when available
docker init

# Do NOT create docker-compose.yml manually if docker init exists
```

### When NOT to use CLIs

1. **Extending existing projects** - Add individual files to an already created project
2. **Specific configuration files** - Custom `docker-compose.yml`, `.env.example`
3. **Business code** - Never generate business logic with CLIs
4. **When CLI does not support the exact template** - If you need a very specific structure

### Recommended Workflow

1. Create base project with official CLI
2. Customize configuration according to project needs
3. Add additional structure manually if necessary

---

## 11. Agent Communication Standards

This section applies to all AI agents working on this project, including but not limited to **Claude Code** and **OpenCode**.

### Language Requirements

- **All communication must be in English** - This includes:
  - Code comments and documentation (when explicitly allowed)
  - Pull request descriptions and commit messages
  - Issue comments and discussions
  - Chat messages and terminal output
  - Any other form of communication related to the project

### Code Comment Policy

- **No code comments unless explicitly requested by the user**
  - Code should be self-documenting through meaningful variable and function names
  - Only add comments when the user specifically requests them
  - When comments are needed, keep them concise and relevant

### Rationale

These standards ensure:
- Consistent developer experience across all AI assistants
- Clean, maintainable code that relies on naming rather than comments
- Clear communication that all team members can understand

---

This file should be updated as the project evolves and new conventions are established.
