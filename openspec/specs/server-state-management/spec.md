## ADDED Requirements

### Requirement: React Query Client Configuration
The application SHALL provide a configured QueryClient with sensible defaults for stale time, garbage collection, and retry behavior.

#### Scenario: QueryClient initialization
- **WHEN** the application starts
- **THEN** a QueryClient SHALL be created with defaultOptions including staleTime of 60 seconds, gcTime of 5 minutes, refetchOnWindowFocus disabled, and retry of 1

### Requirement: Query Key Factory
The application SHALL provide a QUERY_KEYS constant object for consistent query key management across the application.

#### Scenario: Query key usage
- **WHEN** a useQuery hook is called
- **THEN** it SHALL use query keys from the QUERY_KEYS factory to ensure consistency

### Requirement: useQuery Hook for Sessions
The application SHALL provide a useSession query hook that fetches session data by ID with React Query caching.

#### Scenario: Fetch session data
- **WHEN** useSession(sessionId) is called with a valid sessionId
- **THEN** it SHALL fetch from GET /sessions/{sessionId}, cache the result, and return typed session data

### Requirement: useQuery Hook for Session Events
The application SHALL provide a useSessionEvents query hook that polls for session event updates.

#### Scenario: Poll session events
- **WHEN** useSessionEvents(sessionId) is called
- **THEN** it SHALL fetch from GET /sessions/{sessionId}/events with refetchInterval of 2000ms

### Requirement: useMutation Hook for Pipeline Trigger
The application SHALL provide a useTriggerPipeline mutation hook that invalidates session queries on success.

#### Scenario: Trigger pipeline mutation
- **WHEN** useTriggerPipeline mutation is invoked with a ticketId
- **THEN** it SHALL POST to /trigger/{ticketId} and invalidate sessions query on success

### Requirement: Optimistic Update Support
Mutation hooks SHALL support optimistic updates via onMutate and rollback via onError.

#### Scenario: Optimistic mutation
- **WHEN** a mutation with optimistic update is triggered
- **THEN** the UI SHALL update immediately and rollback if the server returns an error
