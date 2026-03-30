## Why

The current frontend lacks maintainable architecture, has inconsistent component patterns, and uses outdated state management. A complete refactor to atomic design with modern React patterns will improve developer experience, code quality, and make the codebase sustainable for future development.

## What Changes

- Migrate to Atomic Design architecture (atoms, molecules, organisms, templates, pages)
- Replace inline CSS/styles with Tailwind CSS + shadcn/ui components
- Add React Query (TanStack Query) for server state management
- Add Zustand for client-side state with persistence middleware
- Add Zod for runtime validation of API responses and forms
- Replace fetch with Axios with interceptors, retries, and error handling
- Add React Router v6 with loader/action patterns
- Apply clean code practices: consistent naming, single responsibility, DRY principles
- Migrate Socket.IO integration to use new patterns

## Capabilities

### New Capabilities
- `atomic-component-architecture`: Component library organized into atomic design tiers with clear responsibilities and composition patterns
- `server-state-management`: TanStack Query integration for API data fetching, caching, background refetching, and optimistic updates
- `client-state-persistence`: Zustand-based state management with persistence middleware for session, connection, and UI state
- `runtime-validation`: Zod schemas for validating API responses and form inputs at runtime
- `http-client-orchestration`: Axios HTTP client with request/response interceptors, auth handling, and retry logic
- `routing-with-loaders`: React Router v6 with loader/action pattern for data fetching and mutations

### Modified Capabilities
- `base-architecture`: Update to reflect new frontend structure and dependencies (adds Tailwind, shadcn/ui, React Query, Zustand, Zod, Axios, React Router)

## Impact

- **Frontend**: Complete architecture restructure - new directory layout, component migration, hook patterns, state management
- **Dependencies**: New npm packages (Tailwind CSS, shadcn/ui components, @tanstack/react-query, zustand, zod, axios, react-router-dom)
- **Build Config**: Vite configuration updates for Tailwind CSS
- **API Layer**: Refactored HTTP client layer replacing current fetch implementation
