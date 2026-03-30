## ADDED Requirements

### Requirement: Agent State Schema
The application SHALL provide a Zod schema for validating agent state objects.

#### Scenario: Validate agent state
- **WHEN** an agent state object is validated with AgentStateSchema
- **THEN** it SHALL validate fields: agent_id (string), state (enum: idle/thinking/working/waiting/success/error), task (optional string), progress (optional number)

### Requirement: Session Event Schema
The application SHALL provide a Zod schema for validating session event objects.

#### Scenario: Validate session event
- **WHEN** a session event object is validated with SessionEventSchema
- **THEN** it SHALL validate fields: type (string), session_id (string), timestamp (string), payload (record of unknown)

### Requirement: Session Metrics Schema
The application SHALL provide a Zod schema for validating session metrics objects.

#### Scenario: Validate session metrics
- **WHEN** a session metrics object is validated with SessionMetricsSchema
- **THEN** it SHALL validate fields: tokens_used (number), duration_seconds (number), files_generated (number), tests_passed (optional boolean)

### Requirement: API Response Validation
API response data SHALL be validated with Zod schemas before being used in components.

#### Scenario: API response validation
- **WHEN** an API response is received
- **THEN** it SHALL be parsed through the appropriate Zod schema and throw an error if validation fails

### Requirement: Form Input Validation
Form inputs SHALL be validated with Zod schemas before submission.

#### Scenario: Form validation
- **WHEN** a form is submitted
- **THEN** form data SHALL be validated against the appropriate Zod schema and display user-friendly error messages on failure
