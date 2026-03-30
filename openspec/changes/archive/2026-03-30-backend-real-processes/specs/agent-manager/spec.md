## ADDED Requirements

### Requirement: Agent Configuration
The system SHALL define AgentConfig with name, model, system_prompt, tools list, max_iterations (default 10), and timeout_seconds (default 300).

#### Scenario: Agent config creation
- **WHEN** an agent is configured
- **THEN** it SHALL have name, model, tools, and timeout settings

### Requirement: Agent Session Creation
The AgentManager SHALL create sessions with unique session_id combining ticket_id, agent_type, and uuid4.

#### Scenario: Session creation
- **WHEN** start_session is called with ticket_id and agent_type
- **THEN** a unique session_id SHALL be generated
- **AND** session context SHALL be initialized with empty previous_results, shared_state, and handoff_log

### Requirement: Agent Streaming Execution
The AgentManager SHALL support streaming execution that yields tokens asynchronously via AsyncIterator.

#### Scenario: Streaming execution
- **WHEN** execute_agent is called
- **THEN** it SHALL return an AsyncIterator that yields output tokens
- **AND** update context.current_task with the task description

### Requirement: Agent Handoff
The AgentManager SHALL support handoff from one agent to another with a summary log entry.

#### Scenario: Handoff between agents
- **WHEN** handoff is called with session_id, from_agent, to_agent, and summary
- **THEN** handoff_log SHALL contain entry with all fields and timestamp
- **AND** agent_type for session SHALL be updated

### Requirement: Active Session Management
The AgentManager SHALL track active sessions and provide retrieval of session context.

#### Scenario: Session retrieval
- **WHEN** get_session is called with valid session_id
- **THEN** it SHALL return the AgentContext for that session
- **WHEN** get_session is called with invalid session_id
- **THEN** it SHALL raise KeyError

### Requirement: Session Cleanup
The system SHALL support cleanup of completed or failed sessions to prevent memory growth.

#### Scenario: Session cleanup
- **WHEN** cleanup_session is called
- **THEN** session SHALL be removed from active_sessions
- **AND** session record SHALL remain in database for auditing
