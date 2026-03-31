## ADDED Requirements

### Requirement: Agent Information Density Overlay
The canvas SHALL display detailed, real-time information cards or overlays adjacent to each agent on the canvas to represent their current executing subtask.

#### Scenario: Display current active file and branch
- **WHEN** an agent is modifying a repository file or running a git operation in a specific branch
- **THEN** the overlay card next to the agent SHALL indicate the active file (e.g. `user_service.py`) and branch name (e.g. `feat/PROJ-123`)

### Requirement: Current Progress and Token Consumption Metrics
The agent info cards SHALL track and display LLM resource token utilization and elapsed task time for that specific agent.

#### Scenario: Update token count during task execution
- **WHEN** the agent performs LLM inference operations reported via the agent log stream
- **THEN** its associated info card SHALL update to show total tokens consumed and total seconds elapsed working on its current task

### Requirement: Full Session Tooltip
The system SHALL provide extended session context (handoff path, past sub-tasks, error summaries) via a hover tooltip over an agent or their info card.

#### Scenario: Inspecting blocked agent
- **WHEN** the user hovers the cursor over a `blocked` agent's character or associated info card
- **THEN** a tooltip overlay SHALL appear displaying the immediate error payload or reason blocking the task and the preceding step that led to it
