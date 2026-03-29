## Why

The multi-agent software development system via Jira requires a functional baseline structure to begin operations. We need to implement the first task described in PLAN.md which includes scaffolding the MVP with Docker Compose, PostgreSQL, a FastAPI backend, and a React + Vite frontend. This initial scaffolding establishes the environment for the multi-agent orchestrator and the real-time dashboard.

## What Changes

- Initialize the base directory structure for the frontend and backend.
- Set up `docker-compose.yml` to run the database (PostgreSQL 16), backend (FastAPI), and frontend (Vite React).
- Create basic configuration files (`package.json`, `vite.config.ts`, `requirements.txt`, etc.) using official CLIs where possible.
- Set up initial environment variables for database, LLM, Jira, and GitHub integrations.

## Capabilities

### New Capabilities
- `base-architecture`: The foundational directory structure, build configurations, and multi-container runtime environment.

### Modified Capabilities
None.

## Impact

- Creates new directories (`frontend/`, `backend/`).
- Introduces `docker-compose.yml` at the project root.
- Sets up standard tooling for development (pytest, ruff, eslint, vitest) per the guidelines in AGENTS.md.
