# 8. UX/UI Improvements and Frontend Refactoring ✅

> **Status**: Planned — Next priority before MVP completion

## Objective

Refactor the frontend to improve developer experience, maintainability, and visual quality using modern React patterns and a component-driven architecture.

## Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| **Component Architecture** | Atomic Design | Organize UI into atoms, molecules, organisms, templates, pages |
| **Styling** | Tailwind CSS + shadcn/ui | Utility-first CSS with accessible, customizable components |
| **HTTP Client** | Axios | API requests with interceptors, retries, and error handling |
| **Routing** | React Router v6 | SPA routing with loaders, actions, and cache (future SSR-ready) |
| **Data Fetching/Cache** | TanStack Query (React Query) | Server state fetching, caching, background refetching, optimistic updates |
| **Validation** | Zod | Runtime type validation for forms and API responses |
| **State Persistence** | Zustand | Lightweight state management with middleware for persistence |

## Atomic Design Structure

```
frontend/src/
├── atoms/                 # Basic UI primitives
│   ├── Button/
│   ├── Input/
│   ├── Badge/
│   └── Icon/
├── molecules/             # Composed UI elements
│   ├── SearchBar/
│   ├── TicketCard/
│   └── AgentAvatar/
├── organisms/             # Complex UI sections
│   ├── AgentCanvas/
│   ├── TaskPanel/
│   └── LogPanel/
├── templates/              # Page layouts
│   ├── DashboardLayout/
│   └── SessionLayout/
├── pages/                 # Route pages
│   ├── Dashboard/
│   └── SessionDetail/
└── lib/
    ├── api/               # Axios instance and interceptors
    ├── schemas/            # Zod validation schemas
    ├── stores/             # Zustand stores
    └── query/              # React Query hooks and client
```

## Implementation Priorities

1. **Apply Clean Code practices** — Consistent patterns across all components and hooks
2. **Setup Tailwind + shadcn/ui** — Configure theme, add necessary components
3. **Migrate Socket.IO integration** — Keep real-time, refactor connection handling
4. **Create atomic components** — Button, Input, Badge, Avatar, Card
5. **Build organism components** — AgentCanvas, TaskPanel, LogPanel, MetricsBar
6. **Add React Router** — Define routes with loader/action pattern
7. **Setup React Query** — Configure QueryClient with default options, create useQuery/useMutation hooks
8. **Integrate Axios + React Query** — Use Axios for HTTP, React Query for caching and state sync
9. **Implement Zustand stores** — Session state, connection status, UI preferences
10. **Add Zod schemas** — Validate API responses and form inputs

## Clean Code Best Practices

### Component Guidelines

```typescript
// ✅ Good: Small, focused components with single responsibility
const AgentAvatar: React.FC<AgentAvatarProps> = ({ agent, size = "md" }) => (
  <Avatar size={size}>
    <AvatarImage src={agent.avatarUrl} />
    <AvatarFallback>{agent.name.charAt(0)}</AvatarFallback>
  </Avatar>
);

// ❌ Bad: Large component handling multiple concerns
const Dashboard: React.FC = () => {
  const [agents, setAgents] = useState([]);
  const [logs, setLogs] = useState([]);
  const [theme, setTheme] = useState("dark");
  // ... 500 lines later
};
```

### Hooks Patterns

```typescript
// ✅ Good: Custom hooks encapsulate logic, return meaningful values
export const useAgentState = (agentId: string) => {
  const { data: agent } = useQuery({
    queryKey: ["agent", agentId],
    queryFn: () => api.get(`/agents/${agentId}`),
  });

  const isWorking = agent?.state === "working";
  const isComplete = agent?.state === "success" || agent?.state === "error";

  return { agent, isWorking, isComplete };
};

// ✅ Good: Composable hooks following SRP
const useAgentWorking = (agentId: string) => {
  const { agent } = useAgentState(agentId);
  return agent?.state === "working";
};
```

### Naming Conventions

| Pattern | Convention | Example |
|---|---|---|
| Components | PascalCase | `AgentCard.tsx` |
| Hooks | camelCase with `use` prefix | `useAgentState.ts` |
| Utilities | camelCase | `formatDate.ts` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| Types/Interfaces | PascalCase | `AgentState` |
| Files (components) | Match component name | `AgentCard/` |

### File Structure per Component

```
AgentCard/
├── AgentCard.tsx          # Main component
├── AgentCard.test.tsx     # Tests
├── AgentCard.types.ts     # Type definitions
└── index.ts               # Re-export
```

### Error Handling

```typescript
// ✅ Good: Try-catch with user-friendly errors
const useTriggerPipeline = () => {
  return useMutation({
    mutationFn: triggerPipeline,
    onError: (error) => {
      toast.error(error.message || "Failed to trigger pipeline");
    },
  });
};

// ✅ Good: Zod validation with descriptive errors
const validateSession = (data: unknown) => {
  const result = SessionSchema.safeParse(data);
  if (!result.success) {
    throw new Error(`Invalid session: ${result.error.issues[0].message}`);
  }
  return result.data;
};
```

### DRY Principles

```typescript
// ✅ Good: Shared components reduce duplication
const LoadingSpinner = ({ size = "md" }) => (
  <Spinner className={cn("h-4 w-4", sizeClasses[size])} />
);

// ✅ Good: Composable styles with cn utility
const cardClasses = cn(
  "rounded-lg border bg-card text-card-foreground shadow-sm",
  className
);

// ❌ Bad: Repeated inline styles
<div className="flex items-center justify-between p-4 border-b rounded-t-lg" />
<div className="flex items-center justify-between p-4 border-b" />
```

### Performance Considerations

```typescript
// ✅ Good: Memoize expensive computations
const sortedAgents = useMemo(
  () => agents.sort((a, b) => a.name.localeCompare(b.name)),
  [agents]
);

// ✅ Good: React.memo for pure components
const AgentAvatar = React.memo<AgentAvatarProps>(({ agent }) => (
  <Avatar>
    <AvatarImage src={agent.avatarUrl} />
    <AvatarFallback>{agent.name.charAt(0)}</AvatarFallback>
  </Avatar>
));

// ✅ Good: Query keys as constants for consistency
const QUERY_KEYS = {
  sessions: ["sessions"] as const,
  session: (id: string) => ["session", id] as const,
  sessionEvents: (id: string) => ["session", id, "events"] as const,
} as const;
```

### Import Organization

```typescript
// Order: 1. React 2. External libraries 3. Internal modules 4. Types 5. Assets
import React, { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AgentState } from "./AgentCard.types";
import type { Agent } from "@/types";
```

## shadcn/ui Components to Install

```bash
npx shadcn@latest add button input badge avatar card separator scroll-area tooltip
```

## Zustand Store Structure

```typescript
// stores/sessionStore.ts
interface SessionState {
  sessionId: string | null;
  agentStates: Record<string, AgentState>;
  logs: LogEntry[];
  metrics: SessionMetrics;
}

interface UIState {
  theme: "light" | "dark";
  sidebarOpen: boolean;
  logFilter: string | null;
}

// stores/connectionStore.ts
interface ConnectionState {
  status: "connected" | "disconnected" | "reconnecting";
  lastPing: Date | null;
}
```

## Zod Schema Examples

```typescript
// schemas/session.ts
import { z } from "zod";

export const AgentStateSchema = z.object({
  agent_id: z.string(),
  state: z.enum(["idle", "thinking", "working", "waiting", "success", "error"]),
  task: z.string().optional(),
  progress: z.number().optional(),
});

export const SessionEventSchema = z.object({
  type: z.string(),
  session_id: z.string(),
  timestamp: z.string(),
  payload: z.record(z.unknown()),
});

export const SessionMetricsSchema = z.object({
  tokens_used: z.number(),
  duration_seconds: z.number(),
  files_generated: z.number(),
  tests_passed: z.boolean().optional(),
});
```

## Axios Configuration

```typescript
// lib/api/client.ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) await refreshToken();
    if (error.config && !error.config._retry) {
      error.config._retry = true;
      return api.request(error.config);
    }
    throw error;
  }
);
```

## React Query Configuration

```typescript
// lib/query/client.ts
import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,           // 1 minute before data is considered stale
      gcTime: 1000 * 60 * 5,          // 5 minutes before unused data is garbage collected
      refetchOnWindowFocus: false,    // Don't refetch when window regains focus
      retry: 1,                       // Retry failed requests once
    },
  },
});
```

## React Query + Axios Integration

```typescript
// lib/query/hooks.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { SessionMetricsSchema } from "../schemas/session";

// Query hooks for server data
export const useSession = (sessionId: string) =>
  useQuery({
    queryKey: ["session", sessionId],
    queryFn: async () => {
      const { data } = await api.get(`/sessions/${sessionId}`);
      return SessionMetricsSchema.parse(data);
    },
    enabled: !!sessionId,
  });

export const useSessionEvents = (sessionId: string) =>
  useQuery({
    queryKey: ["session", sessionId, "events"],
    queryFn: async () => {
      const { data } = await api.get(`/sessions/${sessionId}/events`);
      return data;
    },
    refetchInterval: 2000,  // Poll every 2s for real-time updates (Socket.IO handles primary updates)
  });

// Mutation hooks for actions
export const useTriggerPipeline = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (ticketId: string) => api.post(`/trigger/${ticketId}`),
    onSuccess: (_, ticketId) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
};
```
