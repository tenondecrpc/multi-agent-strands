## Context

The frontend currently lacks structured architecture. Components are not organized by responsibility, state management is scattered across useState/useEffect hooks, API calls are inconsistent, and styling is not DRY. This makes the codebase difficult to maintain and extend.

## Goals / Non-Goals

**Goals:**
- Establish atomic design structure for UI component organization
- Implement clear separation between server state (React Query) and client state (Zustand)
- Provide type-safe API layer with Zod validation
- Create reusable, accessible UI components via shadcn/ui
- Enable persistent UI preferences and session state

**Non-Goals:**
- Rewriting business logic that works correctly
- Changing the visual design significantly (only structural refactoring)
- Adding new features beyond infrastructure improvements
- SSR/Next.js migration (React Router setup is SSR-ready, but not activated)

## Decisions

### Atomic Design Structure

**Decision**: Organize components into atoms, molecules, organisms, templates, pages following Brad Frost's atomic design methodology.

**Rationale**: Creates clear composition hierarchy, improves reusability, makes component responsibilities explicit, and aligns with industry-proven patterns.

**Alternatives**: Feature-based folders (couples UI to features), flat structure (scales poorly).

### Tailwind CSS + shadcn/ui over CSS Modules/Motion

**Decision**: Use Tailwind CSS for styling with shadcn/ui component library.

**Rationale**: shadcn/ui provides accessible, customizable components that live in the project (not npm dependency), Tailwind enables rapid styling without context switching, both are headless (no unwanted styling).

**Alternatives**: CSS Modules (no reusability across components), styled-components (runtime overhead), Material UI (opinionated, hard to customize).

### TanStack Query over SWR or Redux

**Decision**: Use TanStack Query (React Query) for server state.

**Rationale**: Built-in caching, background refetching, optimistic updates, DevTools. SWR is simpler but less powerful for complex cases. Redux is overkill for server state and requires too much boilerplate.

**Alternatives**: SWR (simpler but less extensible), Redux Toolkit Query (couples to Redux).

### Zustand over Context API or Redux

**Decision**: Use Zustand for client state management.

**Rationale**: Minimal boilerplate, TypeScript-first, easy persistence middleware, no providers wrapping the app. Context API causes re-renders, Redux is too verbose.

**Alternatives**: Context API (re-render issues), Redux Toolkit (verbose, requires providers).

### Axios over fetch

**Decision**: Use Axios for HTTP client.

**Rationale**: Interceptors for auth/logging, automatic JSON transformation, request/response typing, retry handling. fetch is built-in but requires more boilerplate for these features.

**Alternatives**: fetch (more boilerplate for interceptors/retry), tRPC (couples frontend/backend too tightly).

### Zod over TypeScript only or Joi

**Decision**: Use Zod for runtime validation.

**Rationale**: TypeScript types are compile-time only. Zod validates at runtime, infers TypeScript types from schemas, excellent DX. Joi is older, less TypeScript-friendly.

**Alternatives**: TypeScript only (no runtime safety), Joi (less TypeScript integration).

## Risks / Trade-offs

[Tailwind learning curve] → Provide base component examples and cn() utility for common patterns

[shadcn/ui requires manual installation] → Document exact CLI commands, add to onboarding

[React Query over-fetching] → Configure staleTime/gcTime appropriately, use queryKey factories

[Zustand persistence security] → Only persist non-sensitive data, exclude tokens

[Axios bundle size] → Tree-shaking is effective; if critical, fallback to fetch for simple GETs

## Migration Plan

1. Install dependencies: Tailwind, shadcn/ui, React Query, Zustand, Zod, Axios, React Router
2. Configure Vite for Tailwind CSS
3. Initialize shadcn/ui with desired components
4. Create `lib/` directory structure: api/, schemas/, stores/, query/
5. Set up Axios instance with interceptors
6. Configure React Query client with defaults
7. Create base Zustand stores (session, connection, UI)
8. Define Zod schemas for API responses
9. Create atomic component directories
10. Migrate existing components to new structure
11. Add React Router routes
12. Wire up Socket.IO with new patterns
13. Verify all components render correctly

Rollback: Revert to previous component files from git.

## Open Questions

- Should we migrate all existing components at once or incrementally page-by-page?
- Do we keep Socket.IO in a separate hook or integrate it with React Query?
- Should we enable React Router's SSR features in the future?
