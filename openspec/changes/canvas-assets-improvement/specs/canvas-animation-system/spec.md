## ADDED Requirements

### Requirement: Smooth Subtree Animation Orchestration
The UI SHALL use the Framer Motion library to orchestrate smooth layout transitions for agents scaling, translating, or entering/exiting the canvas according to the active pipeline topology.

#### Scenario: Orchestrator spawns Backend
- **WHEN** a new session initially moves out of the `pending` phase and spins up the Backend agent
- **THEN** the transition SHALL animate smoothly via Framer Motion's `layout` and `animate` lifecycle hooks rather than snapping abruptly

### Requirement: Complex Sequence Coordination
The canvas SHALL orchestrate coordinated visual sequences for system-wide behaviors (e.g., pipeline success, multi-agent failure or rate-limit warnings) via a dedicated animation controller using Framer Motion capabilities.

#### Scenario: Rate Limit Exhaustion effect
- **WHEN** the system emits an `llm_rate_limited` event and enters an immediate backoff/retry loop
- **THEN** the animation controller SHALL trigger a coordinated "warning" or "shudder" effect synchronized across all currently active agents on the canvas

### Requirement: Idleness Micro-Animations (Desirable)
The dashboard SHOULD render unique, CSS/Framer Motion or path-based idleness micro-animations native to the SVG character to provide continuous visual heartbeat (e.g. slight floating, sketching, reading).

#### Scenario: Agent remains idle or waiting
- **WHEN** an agent is not processing a task, or explicitly waiting in parallel operation
- **THEN** the character's SVG path or transform SHOULD loop a subtle, role-appropriate micro-animation indefinitely
