## ADDED Requirements

### Requirement: Ticket Stage Enum
The system SHALL define a TicketStage enum with values NEW, TRIAGED, IN_ANALYSIS, IN_DEVELOPMENT, IN_REVIEW, IN_TESTING, DONE, and BLOCKED.

#### Scenario: Stage definition
- **WHEN** a ticket is created
- **THEN** its initial stage SHALL be NEW

### Requirement: Ticket Processing Pipeline
The system SHALL execute a processing pipeline that validates tickets, enriches data, triages by architect agent, and assigns to appropriate development agent.

#### Scenario: Full pipeline execution
- **WHEN** process_ticket is called with a ticket_id
- **THEN** the pipeline SHALL validate the ticket exists
- **AND** enrich ticket data from Jira
- **AND** triage via architect agent
- **AND** assign to appropriate agent based on ticket type

### Requirement: Stage Transition Validation
The system SHALL validate stage transitions to ensure only valid transitions occur (e.g., cannot go from NEW directly to IN_TESTING).

#### Scenario: Invalid transition rejection
- **WHEN** an invalid stage transition is attempted
- **THEN** the system SHALL reject the transition with an error

### Requirement: Ticket State Persistence
The system SHALL persist ticket processing state including current_stage, assigned_agent, context_window, artifacts, and handoff_history.

#### Scenario: State persistence
- **WHEN** a ticket stage changes
- **THEN** the ticket state SHALL be persisted to the database
- **AND** include timestamp of update

### Requirement: Processing Result Structure
The pipeline SHALL return a ProcessingResult with ticket_id, stage, success flag, summary, artifacts, next_actions, and optional handoff_to agent.

#### Scenario: Result structure
- **WHEN** pipeline execution completes
- **THEN** it SHALL return a result with all specified fields

### Requirement: Blocking and Unblocking Tickets
The system SHALL support BLOCKED stage with blocked_reason field and ability to unblock when reason is resolved.

#### Scenario: Blocking a ticket
- **WHEN** a ticket encounters a blocking issue
- **THEN** it SHALL transition to BLOCKED with blocked_reason
- **WHEN** blocked_reason is resolved
- **THEN** it SHALL transition back to previous stage
