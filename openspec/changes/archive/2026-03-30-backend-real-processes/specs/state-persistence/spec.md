## ADDED Requirements

### Requirement: TicketState Model
The database SHALL contain a ticket_states table with ticket_id (unique), jira_key, current_stage, assigned_agent, context_window (JSON), artifacts (JSON), handoff_history (JSON), and updated_at timestamp.

#### Scenario: TicketState schema
- **WHEN** database schema is created
- **THEN** ticket_states table SHALL have all specified columns
- **AND** ticket_id SHALL be unique and indexed

### Requirement: AgentSession Model
The database SHALL contain an agent_sessions table with session_id (unique), ticket_id (indexed), agent_type, status, current_task, result (JSON, nullable), error (nullable), started_at, completed_at (nullable), and retry_count.

#### Scenario: AgentSession schema
- **WHEN** database schema is created
- **THEN** agent_sessions table SHALL have all specified columns
- **AND** session_id SHALL be unique and indexed

### Requirement: Ticket State Persistence
The system SHALL save ticket state to database on every stage transition.

#### Scenario: Persist ticket state
- **WHEN** ticket stage changes
- **THEN** TicketState record SHALL be created or updated
- **AND** updated_at SHALL be set to current time

### Requirement: Session State Persistence
The system SHALL save agent session state including results and errors to database.

#### Scenario: Persist session state
- **WHEN** agent execution completes or fails
- **THEN** session record SHALL be updated with result or error
- **AND** completed_at SHALL be set if session ended

### Requirement: State Retrieval
The system SHALL provide functions to retrieve current ticket state and agent session by ID.

#### Scenario: State retrieval
- **WHEN** get_ticket_state is called with ticket_id
- **THEN** it SHALL return the current TicketState record
- **WHEN** get_agent_session is called with session_id
- **THEN** it SHALL return the AgentSession record

### Requirement: Handoff History Tracking
The system SHALL maintain complete handoff history in ticket_state.handoff_history.

#### Scenario: Handoff history
- **WHEN** an agent hands off to another
- **THEN** handoff entry SHALL be appended to handoff_history
- **AND** history SHALL be persisted to database
