export type AgentRole = 'orchestrator' | 'backend' | 'frontend' | 'qa' | 'architect';

export type AgentState = 'idle' | 'thinking' | 'working' | 'waiting' | 'success' | 'error';

export type EventType =
  | 'pipeline_started'
  | 'pipeline_completed'
  | 'pipeline_error'
  | 'agent_state_change'
  | 'agent_log'
  | 'task_assigned'
  | 'task_completed'
  | 'pr_created'
  | 'budget_exceeded'
  | 'llm_credit_exhausted'
  | 'llm_rate_limited';

export const DEFAULT_AGENTS: Agent[] = [
  { id: "orchestrator", name: "Orchestrator", role: "orchestrator", state: "idle" },
  { id: "backend_agent", name: "Backend Agent", role: "backend", state: "idle" },
  { id: "frontend_agent", name: "Frontend Agent", role: "frontend", state: "idle" },
  { id: "qa_agent", name: "QA Agent", role: "qa", state: "idle" },
];

export const AGENT_ID_TO_ROLE: Record<string, AgentRole> = {
  "orchestrator": "orchestrator",
  "backend_agent": "backend",
  "frontend_agent": "frontend",
  "qa_agent": "qa",
};

export interface Agent {
  id: string;
  name: string;
  role: AgentRole;
  state: AgentState;
  task?: string;
  progress?: number;
}

export interface AgentEvent {
  type: EventType;
  session_id: string;
  timestamp: string;
  payload: AgentStateChangePayload | AgentLogPayload | TaskPayload | PipelinePayload | ErrorPayload;
}

export interface AgentStateChangePayload {
  agent_id: string;
  previous_state: AgentState;
  new_state: AgentState;
  task?: string;
  progress?: number;
}

export interface AgentLogPayload {
  agent_id: string;
  message: string;
  level: 'info' | 'warn' | 'error';
}

export interface TaskPayload {
  agent_id: string;
  task: string;
}

export interface PipelinePayload {
  ticket_id: string;
  pr_url?: string;
}

export interface ErrorPayload {
  error: string;
}

export interface LlmCreditExhaustedPayload {
  error: string;
  agent_type?: string;
  timestamp: string;
}

export interface LlmRateLimitedPayload {
  error: string;
  agent_type?: string;
  retry_count: number;
  timestamp: string;
}

export interface SessionState {
  session_id: string;
  ticket_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  agents: Agent[];
  logs: AgentLog[];
  metrics: SessionMetrics;
}

export interface AgentLog {
  id: string;
  agent_id: string;
  message: string;
  level: 'info' | 'warn' | 'error';
  timestamp: string;
}

export interface SessionMetrics {
  tokens_used: number;
  duration_seconds: number;
  files_created: number;
  tests_passed: boolean | null;
}
