import { io, Socket } from 'socket.io-client';
import type { AgentEvent, LlmCreditExhaustedPayload, LlmRateLimitedPayload, SessionState } from '../types/agent';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000';
const NAMESPACE = '/pipeline';

console.log('[Socket] Initializing with URL:', `${SOCKET_URL}${NAMESPACE}`);

interface ServerToClientEvents {
  pipeline_started: (data: { session_id: string; ticket_id: string }) => void;
  pipeline_completed: (data: { session_id: string; ticket_id: string; result: unknown }) => void;
  pipeline_error: (data: { session_id: string; ticket_id: string; error: string }) => void;
  agent_event: (event: AgentEvent) => void;
  state_sync: (state: SessionState) => void;
  llm_credit_exhausted: (data: LlmCreditExhaustedPayload & { session_id: string; ticket_id: string }) => void;
  llm_rate_limited: (data: LlmRateLimitedPayload & { session_id: string; ticket_id: string }) => void;
}

interface ClientToServerEvents {
  join_session: (data: { session_id: string }) => void;
  leave_session: (data: { session_id: string }) => void;
}

export const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io(`${SOCKET_URL}${NAMESPACE}`, {
  autoConnect: false,
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000,
});

socket.on('connect', () => {
  console.log('[Socket] Connected! SID:', socket.id);
});

socket.on('disconnect', (reason) => {
  console.log('[Socket] Disconnected:', reason);
});

socket.on('connect_error', (error) => {
  console.error('[Socket] Connection error:', error.message);
});

socket.on('error', (error) => {
  console.error('[Socket] Error:', error);
});

export function connectSocket(): void {
  console.log('[Socket] connectSocket() called, connected:', socket.connected);
  if (!socket.connected) {
    console.log('[Socket] Calling socket.connect()...');
    socket.connect();
  }
}

export function disconnectSocket(): void {
  if (socket.connected) {
    socket.disconnect();
  }
}

export function joinSession(sessionId: string): void {
  console.log('[Socket] joinSession:', sessionId);
  socket.emit('join_session', { session_id: sessionId });
}

export function leaveSession(sessionId: string): void {
  console.log('[Socket] leaveSession:', sessionId);
  socket.emit('leave_session', { session_id: sessionId });
}

export function onLlmCreditExhausted(
  callback: (data: { session_id: string; ticket_id: string; error: string; agent_type?: string; timestamp: string }) => void,
): void {
  socket.on('llm_credit_exhausted', callback);
}

export function offLlmCreditExhausted(
  callback?: (data: { session_id: string; ticket_id: string; error: string; agent_type?: string; timestamp: string }) => void,
): void {
  socket.off('llm_credit_exhausted', callback);
}

export function onLlmRateLimited(
  callback: (data: { session_id: string; ticket_id: string; error: string; agent_type?: string; retry_count: number; timestamp: string }) => void,
): void {
  socket.on('llm_rate_limited', callback);
}

export function offLlmRateLimited(
  callback?: (data: { session_id: string; ticket_id: string; error: string; agent_type?: string; retry_count: number; timestamp: string }) => void,
): void {
  socket.off('llm_rate_limited', callback);
}
