## Context

The multi-agent-strands project implements a Jira ticket automation system using:
- **Frontend**: React + Vite + TypeScript
- **Backend**: FastAPI with Strands Agents SDK
- **Database**: PostgreSQL with SQLAlchemy + asyncpg

The project needs a well-organized folder structure to support maintainability and parallel development.

## Goals / Non-Goals

**Goals:**
- Create intuitive directory structure following FastAPI and React best practices
- Separate concerns: API routes, models, schemas, services, agents, tools
- Enable easy discovery of code by functionality
- Support Docker-based development workflow

**Non-Goals:**
- Implement actual feature code (placeholder files only)
- Define detailed application architecture beyond folder organization
- Set up CI/CD pipelines

## Decisions

### 1. Backend Structure

Decision: Use layered architecture under `backend/app/`
- `api/` - API route definitions
- `models/` - SQLAlchemy database models
- `schemas/` - Pydantic request/response schemas
- `services/` - Business logic layer
- `agents/` - Strands agent definitions
- `tools/` - Custom tools for agents

Rationale: Layered architecture is well-established for FastAPI applications and separates concerns effectively.

### 2. Frontend Structure

Decision: Use feature-based organization under `frontend/src/`
- `components/` - Reusable UI components
- `hooks/` - Custom React hooks
- `pages/` - Page-level components
- `services/` - API service clients
- `types/` - TypeScript type definitions

Rationale: Feature-based structure scales better than grouping by file type as the app grows.

### 3. Docker Setup

Decision: Use `docker-compose.yml` for local development
- Services: `backend`, `frontend`, `db`
- Shared network for inter-service communication
- Volume mounts for hot-reload during development

Rationale: Ensures consistent development environment across team members.

### 4. OpenSpec Integration

Decision: Keep OpenSpec workflow artifacts in `openspec/` directory
- `changes/` - Individual change proposals and implementations
- `specs/` - Capability specifications
- `config.yaml` - OpenSpec configuration

Rationale: Keeps specification artifacts separate from application code.

## Risks / Trade-offs

[Risk] Over-engineering for small project → Mitigation: Start with minimal structure, add as needed
[Risk] Moving files later breaking imports → Mitigation: Use path aliases (e.g., `@/components`) in frontend

## Open Questions

None - folder structure is straightforward based on established conventions.
