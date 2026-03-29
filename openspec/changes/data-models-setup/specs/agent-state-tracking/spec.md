## ADDED Requirements

### Requirement: AgentSession Model
The system SHALL store the high-level state of a Jira ticket's pipeline in an `AgentSession` table.

#### Scenario: Session creation
- **WHEN** a new pipeline is started for a ticket
- **THEN** a record is created with a unique UUID, the `ticket_id`, and status set to 'started'.

### Requirement: AgentEvent Model
The system SHALL store individual state changes and logs of agents in an `AgentEvent` table.

#### Scenario: Event logging
- **WHEN** an agent performs an action or changes state
- **THEN** a record is created linking to the `AgentSession` UUID, containing the `agent_id`, `event_type`, and a JSON `payload`.
