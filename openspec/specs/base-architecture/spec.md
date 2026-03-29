# base-architecture Specification

## Purpose
TBD - created by archiving change scaffold-mvp. Update Purpose after archive.
## Requirements
### Requirement: Base Project Structure
The repository SHALL contain separate directories for frontend and backend, structured using their respective standard tools.

#### Scenario: Verify directories exist
- **WHEN** the project is cloned
- **THEN** a `frontend` and `backend` directory are present at the root

### Requirement: Docker Compose Orchestration
The system SHALL provide a `docker-compose.yml` file that orchestrates the backend, frontend, and database services.

#### Scenario: Starting services
- **WHEN** a user runs `docker-compose up`
- **THEN** the PostgreSQL database, FastAPI backend, and Vite frontend services start successfully and communicate over the internal network.

### Requirement: Backend Scaffolding
The backend SHALL use FastAPI and include configuration for testing (pytest) and linting (ruff).

#### Scenario: Backend tooling
- **WHEN** the backend is initialized
- **THEN** it includes `requirements.txt` with necessary dependencies (fastapi, uvicorn, sqlalchemy, pydantic, ruff, pytest).

### Requirement: Frontend Scaffolding
The frontend SHALL use Vite, React, and TypeScript with testing and linting configurations.

#### Scenario: Frontend tooling
- **WHEN** the frontend is initialized
- **THEN** it includes `package.json` with React, Vite, TypeScript, and related testing/linting tools.

