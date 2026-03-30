import { useEffect, useState, useCallback, useRef } from 'react';
import { socket, connectSocket, joinSession, leaveSession } from '../services/socket';
import type { AgentEvent, SessionState, Agent, AgentLog, AgentState, AgentStateChangePayload, AgentLogPayload } from '../types/agent';

interface UseSocketOptions {
  sessionId: string | null;
  onEvent?: (event: AgentEvent) => void;
}

const AGENT_SEQUENCE: { id: string; delay: number }[] = [
  { id: 'architect', delay: 0 },
  { id: 'backend_agent', delay: 2000 },
  { id: 'frontend_agent', delay: 4000 },
  { id: 'qa_agent', delay: 6000 },
];

export function useSocket({ sessionId, onEvent }: UseSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [agents, setAgents] = useState<Agent[]>([
    { id: 'architect', name: 'Architect', role: 'architect', state: 'idle' },
    { id: 'backend_agent', name: 'Backend Agent', role: 'backend', state: 'idle' },
    { id: 'frontend_agent', name: 'Frontend Agent', role: 'frontend', state: 'idle' },
    { id: 'qa_agent', name: 'QA Agent', role: 'qa', state: 'idle' },
  ]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [error, setError] = useState<string | null>(null);
  const animationTimeouts = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearAnimations = useCallback(() => {
    animationTimeouts.current.forEach(clearTimeout);
    animationTimeouts.current = [];
  }, []);

  const startAgentSequence = useCallback((ticketId: string) => {
    clearAnimations();

    AGENT_SEQUENCE.forEach(({ id, delay }) => {
      const timeout = setTimeout(() => {
        setAgents((prev) =>
          prev.map((agent) =>
            agent.id === id
              ? { ...agent, state: 'working' as AgentState, task: `Processing ${ticketId}`, progress: 0.5 }
              : agent
          )
        );
      }, delay);
      animationTimeouts.current.push(timeout);
    });

    const finalTimeout = setTimeout(() => {
      setAgents((prev) =>
        prev.map((agent) => ({ ...agent, state: 'success' as AgentState, task: undefined, progress: 1 }))
      );
    }, 10000);
    animationTimeouts.current.push(finalTimeout);
  }, [clearAnimations]);

  const resetAgents = useCallback(() => {
    clearAnimations();
    setAgents([
      { id: 'architect', name: 'Architect', role: 'architect', state: 'idle' },
      { id: 'backend_agent', name: 'Backend Agent', role: 'backend', state: 'idle' },
      { id: 'frontend_agent', name: 'Frontend Agent', role: 'frontend', state: 'idle' },
      { id: 'qa_agent', name: 'QA Agent', role: 'qa', state: 'idle' },
    ]);
    setLogs([]);
    setSessionState(null);
  }, [clearAnimations]);

  useEffect(() => {
    connectSocket();

    const onConnect = () => setIsConnected(true);
    const onDisconnect = () => setIsConnected(false);
    const onConnectError = () => setError('Connection failed');

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('connect_error', onConnectError);

    const onPipelineStarted = (data: { session_id: string; ticket_id: string }) => {
      setLogs((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          agent_id: 'system',
          message: `Pipeline started for ticket: ${data.ticket_id}`,
          level: 'info',
          timestamp: new Date().toISOString(),
        },
      ]);
      startAgentSequence(data.ticket_id);
    };

    const onPipelineCompleted = (data: { session_id: string; ticket_id: string }) => {
      clearAnimations();
      setAgents((prev) =>
        prev.map((agent) => ({ ...agent, state: 'success', progress: 1 }))
      );
      setLogs((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          agent_id: 'system',
          message: `Pipeline completed for ticket: ${data.ticket_id}`,
          level: 'info',
          timestamp: new Date().toISOString(),
        },
      ]);
    };

    const onPipelineError = (data: { session_id: string; ticket_id: string; error: string }) => {
      clearAnimations();
      setAgents((prev) =>
        prev.map((agent) => ({ ...agent, state: 'error' }))
      );
      setLogs((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          agent_id: 'system',
          message: `Pipeline error: ${data.error}`,
          level: 'error',
          timestamp: new Date().toISOString(),
        },
      ]);
    };

    socket.on('pipeline_started', onPipelineStarted);
    socket.on('pipeline_completed', onPipelineCompleted);
    socket.on('pipeline_error', onPipelineError);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('connect_error', onConnectError);
      socket.off('pipeline_started', onPipelineStarted);
      socket.off('pipeline_completed', onPipelineCompleted);
      socket.off('pipeline_error', onPipelineError);
    };
  }, [clearAnimations, startAgentSequence]);

  useEffect(() => {
    if (!sessionId) return;

    joinSession(sessionId);

    const onAgentEvent = (event: AgentEvent) => {
      const payload = event.payload as AgentStateChangePayload | AgentLogPayload;

      if (event.type === 'agent_state_change' && 'agent_id' in payload) {
        const statePayload = payload as AgentStateChangePayload;
        setAgents((prev) =>
          prev.map((agent) =>
            agent.id === statePayload.agent_id
              ? {
                  ...agent,
                  state: statePayload.new_state,
                  task: statePayload.task || agent.task,
                  progress: statePayload.progress ?? agent.progress,
                }
              : agent
          )
        );
      }

      if (event.type === 'agent_log' && 'message' in payload) {
        const logPayload = payload as AgentLogPayload;
        setLogs((prev) => [
          ...prev,
          {
            id: `${Date.now()}-${Math.random()}`,
            agent_id: logPayload.agent_id,
            message: logPayload.message,
            level: logPayload.level,
            timestamp: event.timestamp,
          },
        ]);
      }

      onEvent?.(event);
    };

    const onStateSync = (state: SessionState) => {
      setSessionState(state);
      if (state.agents) {
        setAgents(state.agents);
      }
    };

    socket.on('agent_event', onAgentEvent);
    socket.on('state_sync', onStateSync);

    return () => {
      leaveSession(sessionId);
      socket.off('agent_event', onAgentEvent);
      socket.off('state_sync', onStateSync);
    };
  }, [sessionId, onEvent]);

  return {
    isConnected,
    sessionState,
    agents,
    logs,
    error,
    resetAgents,
  };
}
