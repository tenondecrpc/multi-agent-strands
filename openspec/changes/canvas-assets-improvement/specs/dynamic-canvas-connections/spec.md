## ADDED Requirements

### Requirement: Dynamic Event-Driven Connections
The canvas SHALL draw connection lines between agents dynamically based on `agent_state_change` and `task_assigned` events, representing the actual flow of work and handoffs.

#### Scenario: Dynamic connection drawing
- **WHEN** an agent (Agent A) completes a task and passes output or control to another agent (Agent B)
- **THEN** the canvas SHALL establish a visible connection line between Agent A's node and Agent B's node to reflect the handoff relationship, rather than relying on a static fixed topology matrix

### Requirement: Animated Connection Pulses (Desirable)
The system SHOULD visibly animate data or control flow along a dynamically drawn connection line when an active handoff or explicit communication event occurs between two agents.

#### Scenario: Agent handoff pulse
- **WHEN** Agent A hands a compiled artifact to Agent B for review (triggering an event linking the two)
- **THEN** the connection line between A and B SHOULD display a visual "pulse" or moving dashed effect flowing from A to B

### Requirement: Temporary 'Communicating' Visual State
The dashboard SHALL temporarily override an agent's visual state to `communicating` during the payload transmission/handling phase of a multi-agent handoff event.

#### Scenario: Cross-agent task assignment
- **WHEN** the Orchestrator dispatches a payload to the Backend agent via `task_assigned`
- **THEN** both the Orchestrator and the Backend agent SHALL display their `communicating` visual state variations during the immediate handoff window
