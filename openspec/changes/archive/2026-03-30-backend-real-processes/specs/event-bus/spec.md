## ADDED Requirements

### Requirement: Event Type Definition
The system SHALL define EventType enum including TICKET_RECEIVED, TICKET_UPDATED, TICKET_STAGE_CHANGED, AGENT_STARTED, AGENT_COMPLETED, AGENT_FAILED, AGENT_HANDOFF, ARTIFACT_CREATED, and COMMENT_ADDED.

#### Scenario: Event type usage
- **WHEN** an event is created
- **THEN** it SHALL have a valid EventType value

### Requirement: Event Structure
Events SHALL contain id, type, ticket_id, optional agent_id, payload dict, and timestamp.

#### Scenario: Event creation
- **WHEN** an event is published
- **THEN** it SHALL contain all specified fields with proper types

### Requirement: Event Subscription
Subscribers SHALL be able to subscribe to specific EventTypes and receive notifications when those events occur.

#### Scenario: Subscribe to event type
- **WHEN** subscribe is called with an EventType and handler
- **THEN** the handler SHALL be called when events of that type are published

### Requirement: Event Publication
The event bus SHALL deliver events to all subscribed handlers asynchronously.

#### Scenario: Publish event
- **WHEN** publish is called with an event
- **THEN** all handlers subscribed to event.type SHALL be called
- **AND** handlers SHALL be called asynchronously

### Requirement: Ticket Event Subscriptions
The system SHALL support SSE subscriptions to ticket-specific events with optional last_event_id for replay.

#### Scenario: SSE subscription
- **WHEN** subscribe_ticket is called with ticket_id and last_event_id
- **THEN** it SHALL yield events from that point onwards
- **AND** new events SHALL be streamed as they occur

### Requirement: Event Retention
The event bus SHALL retain recent events for replay with a configurable retention limit (default 1000).

#### Scenario: Event replay
- **WHEN** a subscriber provides last_event_id
- **THEN** events after that ID SHALL be delivered first
- **WHEN** retention limit is exceeded
- **THEN** oldest events SHALL be discarded (FIFO)
