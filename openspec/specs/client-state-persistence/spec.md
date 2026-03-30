## ADDED Requirements

### Requirement: Session State Store
The application SHALL provide a Zustand store for session state including sessionId, agentStates, logs, and metrics.

#### Scenario: Session store structure
- **WHEN** the sessionStore is accessed
- **THEN** it SHALL contain sessionId (string | null), agentStates (Record<string, AgentState>), logs (LogEntry[]), and metrics (SessionMetrics)

### Requirement: Connection State Store
The application SHALL provide a Zustand store for WebSocket connection status.

#### Scenario: Connection store structure
- **WHEN** the connectionStore is accessed
- **THEN** it SHALL contain status ("connected" | "disconnected" | "reconnecting") and lastPing (Date | null)

### Requirement: UI Preferences Store
The application SHALL provide a Zustand store for UI preferences including theme and sidebar state.

#### Scenario: UI store structure
- **WHEN** the uiStore is accessed
- **THEN** it SHALL contain theme ("light" | "dark"), sidebarOpen (boolean), and logFilter (string | null)

### Requirement: Persistence Middleware
Session and UI stores SHALL use Zustand persistence middleware to persist state to localStorage.

#### Scenario: State persistence
- **WHEN** the user changes theme or opens/closes sidebar
- **THEN** the state SHALL be persisted to localStorage and restored on page reload

### Requirement: Sensitive Data Exclusion
Auth tokens and sensitive data SHALL NOT be stored in Zustand persistence.

#### Scenario: Token exclusion
- **WHEN** the connectionStore or any store is configured with persist
- **THEN** it SHALL explicitly exclude tokens and sensitive fields from persistence
