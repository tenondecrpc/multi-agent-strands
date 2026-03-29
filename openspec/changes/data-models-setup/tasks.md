## 1. Setup Data Persistence

- [ ] 1.1 In `backend/app/`, create `database.py` with SQLAlchemy 2.0 async engine and `get_db` session dependency.
- [ ] 1.2 In `backend/app/`, create `models/__init__.py` and define the SQLAlchemy Declarative `Base`.
- [ ] 1.3 Configure `alembic` in the `backend` directory (`alembic init -t async migrations`).
- [ ] 1.4 Update `alembic.ini` and `migrations/env.py` to use `DATABASE_URL` and support async migrations.

## 2. Implement Core Models

- [ ] 2.1 In `backend/app/models/agent_session.py`, implement the `AgentSession` model (UUID primary key, ticket_id, status, timestamps).
- [ ] 2.2 In `backend/app/models/agent_event.py`, implement the `AgentEvent` model (UUID primary key, session_id foreign key, agent_id, event_type, payload JSON).
- [ ] 2.3 Add relationship mappings between `AgentSession` and `AgentEvent` models.
- [ ] 2.4 Import both models in `backend/app/models/__init__.py` so Alembic can discover them.

## 3. Generate Migrations

- [ ] 3.1 Run `alembic revision --autogenerate -m "Initial schema: agent sessions and events"`.
- [ ] 3.2 Review the generated migration file to ensure columns and indexes (like `ticket_id`) are correct.
- [ ] 3.3 Test the migration by running `alembic upgrade head` locally.
