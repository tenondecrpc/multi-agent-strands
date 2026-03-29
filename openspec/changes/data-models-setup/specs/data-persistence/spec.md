## ADDED Requirements

### Requirement: Database Setup
The system SHALL provide an async SQLAlchemy connection to a PostgreSQL database.

#### Scenario: Async engine configuration
- **WHEN** the backend initializes
- **THEN** it connects to the database using `asyncpg` and the `DATABASE_URL` environment variable.

### Requirement: Migrations
The system SHALL use Alembic to manage database schema changes.

#### Scenario: Initial migration execution
- **WHEN** `alembic upgrade head` is executed
- **THEN** the `agent_sessions` and `agent_events` tables are created in the database.
