#!/bin/bash
set -e

CONTAINER_NAME="${1:-multi-agent-strands-db-1}"
DB_NAME="${2:-multi_agent}"
DB_USER="${3:-agent}"

echo "=== Database Reset Script ==="
echo "DB Container: $CONTAINER_NAME"
echo "DB Name: $DB_NAME"
echo "DB User: $DB_USER"
echo ""

echo "[1/3] Dropping existing tables..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  DROP TABLE IF EXISTS agent_events CASCADE;
  DROP TABLE IF EXISTS agent_sessions CASCADE;
  DROP TYPE IF EXISTS eventtype CASCADE;
  DROP TYPE IF EXISTS sessionstatus CASCADE;
  DROP TABLE IF EXISTS alembic_version CASCADE;
"

echo "[2/3] Creating enums..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  DO \$\$ BEGIN
    CREATE TYPE sessionstatus AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');
  EXCEPTION
    WHEN duplicate_object THEN null;
  END \$\$;
"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  DO \$\$ BEGIN
    CREATE TYPE eventtype AS ENUM ('AGENT_STARTED', 'AGENT_COMPLETED', 'AGENT_FAILED', 'TOOL_CALL', 'STATE_CHANGE', 'LOG');
  EXCEPTION
    WHEN duplicate_object THEN null;
  END \$\$;
"

echo "[3/3] Creating tables..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  CREATE TABLE agent_sessions (
    id UUID NOT NULL,
    ticket_id VARCHAR(50) NOT NULL,
    status sessionstatus NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id)
  );
"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  CREATE INDEX ix_agent_sessions_ticket_id ON agent_sessions (ticket_id);
"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  CREATE TABLE agent_events (
    id UUID NOT NULL,
    session_id UUID NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    event_type eventtype NOT NULL,
    payload JSON,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
  );
"
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "
  CREATE INDEX ix_agent_events_session_id ON agent_events (session_id);
"

echo ""
echo "=== Done! ==="
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
