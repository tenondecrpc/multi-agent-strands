## ADDED Requirements

### Requirement: SVG Character Illustrations
The system SHALL display each agent role (Orchestrator, Backend, Frontend, QA) using distinct vector (SVG) character illustrations rather than simple geometric shapes.

#### Scenario: Visual distinctness
- **WHEN** the multi-agent canvas renders the active session participants
- **THEN** it SHALL display a unique SVG illustration corresponding to each active agent `role` mapped from `AGENT_ID_TO_ROLE`

### Requirement: State-Aware Visual Variations
The SVG character illustrations SHALL contain distinct visual variations or layers (e.g., props, poses, facial expressions) representing the agent's current state (`idle`, `thinking`, `working`, `waiting`, `success`, `error`, `communicating`, `blocked`).

#### Scenario: Agent enters blocked state
- **WHEN** an agent transitions to the `blocked` state in the `AgentState` transition log
- **THEN** the corresponding SVG illustration SHALL visually swap to a variation indicating distress, halted work, or confusion

### Requirement: Orchestrator Canvas Presence
The canvas SHALL define and render a distinct position and SVG character for the Orchestrator agent to represent the system's central coordination point.

#### Scenario: Orchestrator placement
- **WHEN** the `AgentCanvas` component computes rendering positions for agents in the workflow
- **THEN** it SHALL position the Orchestrator centrally, distinctly from the executing roles (Backend, Frontend, QA)
