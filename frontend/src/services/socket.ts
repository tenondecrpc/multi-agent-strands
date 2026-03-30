import { io, Socket } from 'socket.io-client';
import type { AgentEvent, SessionState } from '../types/agent';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000';
const NAMESPACE = '/pipeline';

interface ServerToClientEvents {
  pipeline_started: (data: { session_id: string; ticket_id: string }) => void;
  pipeline_completed: (data: { session_id: string; ticket_id: string; result: unknown }) => void;
  pipeline_error: (data: { session_id: string; ticket_id: string; error: string }) => void;
  agent_event: (event: AgentEvent) => void;
  state_sync: (state: SessionState) => void;
}

interface ClientToServerEvents {
  join_session: (data: { session_id: string }) => void;
  leave_session: (data: { session_id: string }) => void;
}

export const socket: Socket<ServerToClientEvents, ClientToServerEvents> = io(`${SOCKET_URL}${NAMESPACE}`, {
  autoConnect: false,
  transports: ['websocket', 'polling'],
});

export function connectSocket(): void {
  if (!socket.connected) {
    socket.connect();
  }
}

export function disconnectSocket(): void {
  if (socket.connected) {
    socket.disconnect();
  }
}

export function joinSession(sessionId: string): void {
  socket.emit('join_session', { session_id: sessionId });
}

export function leaveSession(sessionId: string): void {
  socket.emit('leave_session', { session_id: sessionId });
}
