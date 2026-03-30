## 1. Dependencies Setup

- [x] 1.1 Add celery[redis], redis, sse-starlette, tenacity, structlog to requirements.txt
- [x] 1.2 Configure Celery app with Redis broker in backend/app/core/config.py
- [x] 1.3 Add structlog configuration for structured logging

## 2. State Persistence Models

- [x] 2.1 Create TicketStateModel in backend/app/models/ticket_state.py
- [x] 2.2 Create AgentSessionModel in backend/app/models/agent_session_model.py
- [x] 2.3 Create EventModel in backend/app/models/events.py
- [x] 2.4 Add database migration for new tables

## 3. Task Queue Implementation

- [x] 3.1 Define TaskStatus and TaskPriority enums
- [x] 3.2 Create Celery tasks for ticket processing in backend/app/core/task_queue.py
- [x] 3.3 Implement retry configuration with tenacity decorators
- [x] 3.4 Add task result handlers and error classification

## 4. Event Bus Implementation

- [x] 4.1 Define EventType enum with all event types
- [x] 4.2 Create EventBus class with subscribe/publish methods
- [x] 4.3 Implement SSE endpoint for ticket event subscriptions
- [x] 4.4 Add event retention with configurable limit

## 5. Agent Manager Implementation

- [x] 5.1 Create AgentConfig and AgentContext dataclasses
- [x] 5.2 Implement AgentManager class with session lifecycle
- [x] 5.3 Add streaming execution support via AsyncIterator
- [x] 5.4 Implement handoff mechanism with handoff_log

## 6. Ticket Processing Pipeline

- [x] 6.1 Define TicketStage enum with all stages
- [x] 6.2 Create TicketProcessing and ProcessingResult models
- [x] 6.3 Implement TicketPipeline class with stage transitions
- [x] 6.4 Add validation for stage transitions
- [x] 6.5 Implement blocking/unblocking with blocked_reason

## 7. API Endpoints

- [x] 7.1 Create POST /tickets/{ticket_id}/process endpoint
- [x] 7.2 Create POST /tickets/{ticket_id}/stage endpoint
- [x] 7.3 Create POST /sessions endpoint
- [x] 7.4 Create POST /sessions/{session_id}/execute streaming endpoint
- [x] 7.5 Create POST /sessions/{session_id}/handoff endpoint
- [x] 7.6 Create GET /events/{ticket_id} SSE endpoint

## 8. Integration & Services

- [x] 8.1 Update backend/app/services/ticket_service.py with pipeline integration
- [x] 8.2 Update backend/app/services/jira_service.py for ticket enrichment
- [x] 8.3 Integrate EventBus with ticket and agent operations
- [x] 8.4 Wire up AgentManager with existing agent implementations

## 9. Testing

- [x] 9.1 Write unit tests for task queue with mocked Celery
- [x] 9.2 Write unit tests for event bus subscribe/publish
- [x] 9.3 Write unit tests for ticket stage transitions
- [x] 9.4 Write integration tests for agent handoff flow
- [x] 9.5 Write tests for retry logic with error classification

## 10. Documentation

- [x] 10.1 Update AGENTS.md with new backend architecture
- [x] 10.2 Document API endpoints in OpenAPI/Swagger

## 11. Session Detail Integration

- [x] 11.1 Add logs and metrics to SessionResponse schema
- [x] 11.2 Create GET /sessions/{session_id}/logs endpoint
- [x] 11.3 Create GET /sessions/{session_id}/events endpoint
- [x] 11.4 Fix MetricsBar component with default metrics values
- [x] 11.5 Fix Dashboard TicketCard status case mismatch (FAILED vs failed)
