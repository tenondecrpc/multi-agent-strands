## MODIFIED Requirements

### Requirement: Organism Components
Organism components SHALL compose molecules and atoms into complex UI sections with distinct functionality (AgentCanvas, TaskPanel, LogPanel, MetricsBar, AgentInfoOverlay). The legacy duplicate components (e.g., `components/AgentCanvas.tsx`) SHALL be removed in favor of these distinct organisms.

#### Scenario: Organism complexity
- **WHEN** an organism component is created (e.g., AgentCanvas)
- **THEN** it SHALL compose multiple molecules and/or atoms and represent a distinct UI section

## REMOVED Requirements

### Requirement: Legacy Components Structure Migration
**Reason**: Older duplicate components like `components/AgentCanvas.tsx` are being actively removed or refactored into the strict atomic design tiers.
**Migration**: Ensure all complex UI flows utilize `organisms/` directly and refactor existing dependents from the legacy `components/` path.
