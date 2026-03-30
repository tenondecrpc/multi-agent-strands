## ADDED Requirements

### Requirement: Axios Instance Configuration
The application SHALL provide a configured Axios instance with base URL from environment variable.

#### Scenario: Axios instance creation
- **WHEN** the api client is initialized
- **THEN** it SHALL use VITE_API_URL as baseURL and have a default timeout of 10000ms

### Requirement: Request Interceptor for Auth
The Axios instance SHALL include a request interceptor that adds Authorization header with Bearer token.

#### Scenario: Auth header injection
- **WHEN** an API request is made
- **THEN** the request interceptor SHALL add Authorization: Bearer {token} header if a token exists

### Requirement: Response Error Interceptor
The Axios instance SHALL include a response error interceptor that handles 401 errors and token refresh.

#### Scenario: Handle 401 error
- **WHEN** a response returns 401 Unauthorized
- **THEN** the error interceptor SHALL attempt to refresh the token before throwing

### Requirement: Request Retry Logic
Failed requests SHALL be retried once automatically if they fail due to network issues.

#### Scenario: Retry on network failure
- **WHEN** a request fails with a network error
- **THEN** it SHALL be retried once before throwing the error to the caller

### Requirement: API Method Helpers
The application SHALL provide typed helper functions for common API operations (GET, POST, PUT, DELETE).

#### Scenario: Typed API methods
- **WHEN** api.get(), api.post(), api.put(), or api.delete() is called
- **THEN** it SHALL be properly typed and return AxiosResponse with inferred type
