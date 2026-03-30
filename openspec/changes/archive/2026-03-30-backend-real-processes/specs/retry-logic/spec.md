## ADDED Requirements

### Requirement: Retry Configuration
The system SHALL provide RETRY_CONFIG with max_attempts (3), initial_wait (5s), max_wait (60s), and multiplier (2).

#### Scenario: Retry config structure
- **WHEN** retry logic is invoked
- **THEN** it SHALL use the configured values from RETRY_CONFIG

### Requirement: Retryable Error Classification
The system SHALL distinguish between RetryableError (temporary failures) and NonRetryableError (permanent failures).

#### Scenario: Error classification
- **WHEN** an error occurs during agent execution
- **THEN** it SHALL be classified as RetryableError or NonRetryableError
- **AND** retry logic SHALL only retry RetryableError

### Requirement: Automatic Retry with Backoff
Failed tasks SHALL automatically retry up to max_attempts with exponential backoff between retries.

#### Scenario: Automatic retry
- **WHEN** a task fails with RetryableError
- **THEN** it SHALL retry after calculated backoff period
- **AND** retry_count SHALL be incremented
- **WHEN** max_attempts is reached
- **THEN** task SHALL be marked as FAILED

### Requirement: AgentExecutionError Wrapper
Failed agent executions SHALL raise AgentExecutionError containing agent name, task description, and original error.

#### Scenario: Error wrapping
- **WHEN** agent execution fails after all retries
- **THEN** AgentExecutionError SHALL be raised with full context

### Requirement: Non-Retryable Error Handling
NonRetryableError SHALL fail immediately without retry attempts.

#### Scenario: Non-retryable error
- **WHEN** NonRetryableError is raised
- **THEN** it SHALL NOT be retried
- **AND** AgentExecutionError SHALL be raised immediately
