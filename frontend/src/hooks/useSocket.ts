import { useEffect, useCallback, useRef, useMemo } from "react";
import { shallow } from "zustand/shallow";
import {
  socket,
  connectSocket,
  joinSession,
  leaveSession,
} from "@/lib/socket";
import { useSessionStore } from "@/lib/stores/sessionStore";
import { useConnectionStore } from "@/lib/stores/connectionStore";
import type {
  AgentEvent,
  Agent,
  AgentState,
  AgentStateChangePayload,
  AgentLogPayload,
} from "@/types/agent";

interface UseSocketOptions {
  sessionId: string | null;
  onEvent?: (event: AgentEvent) => void;
}

const AGENT_SEQUENCE: { id: string; delay: number }[] = [
  { id: "architect", delay: 0 },
  { id: "backend_agent", delay: 2000 },
  { id: "frontend_agent", delay: 4000 },
  { id: "qa_agent", delay: 6000 },
];

const DEFAULT_AGENTS: Agent[] = [
  { id: "architect", name: "Architect", role: "architect", state: "idle" },
  { id: "backend_agent", name: "Backend Agent", role: "backend", state: "idle" },
  { id: "frontend_agent", name: "Frontend Agent", role: "frontend", state: "idle" },
  { id: "qa_agent", name: "QA Agent", role: "qa", state: "idle" },
];

export function useSocket({ sessionId, onEvent }: UseSocketOptions) {
  const setAgentStates = useSessionStore((state) => state.setAgentStates);
  const updateAgent = useSessionStore((state) => state.updateAgent);
  const addLog = useSessionStore((state) => state.addLog);
  const setLogs = useSessionStore((state) => state.setLogs);
  const setStatus = useConnectionStore((state) => state.setStatus);

  const animationTimeouts = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearAnimations = useCallback(() => {
    animationTimeouts.current.forEach(clearTimeout);
    animationTimeouts.current = [];
  }, []);

  const startAgentSequence = useCallback(
    (ticketId: string) => {
      clearAnimations();

      AGENT_SEQUENCE.forEach(({ id, delay }) => {
        const timeout = setTimeout(() => {
          updateAgent({
            id,
            name: DEFAULT_AGENTS.find((a) => a.id === id)?.name || id,
            role: id as Agent["role"],
            state: "working" as AgentState,
            task: `Processing ${ticketId}`,
            progress: 0.5,
          });
        }, delay);
        animationTimeouts.current.push(timeout);
      });

      const finalTimeout = setTimeout(() => {
        DEFAULT_AGENTS.forEach((agent) => {
          updateAgent({
            ...agent,
            state: "success" as AgentState,
            task: undefined,
            progress: 1,
          });
        });
      }, 10000);
      animationTimeouts.current.push(finalTimeout);
    },
    [clearAnimations, updateAgent]
  );

  const resetAgents = useCallback(() => {
    clearAnimations();
    setAgentStates(
      DEFAULT_AGENTS.reduce((acc, agent) => {
        acc[agent.id] = agent;
        return acc;
      }, {} as Record<string, Agent>)
    );
    setLogs([]);
  }, [clearAnimations, setAgentStates, setLogs]);

  useEffect(() => {
    connectSocket();

    const onConnect = () => setStatus("connected");
    const onDisconnect = () => setStatus("disconnected");

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return;

    joinSession(sessionId);

    const onPipelineStarted = (data: { session_id: string; ticket_id: string }) => {
      console.log('[Socket] pipeline_started received:', data);
      if (data.ticket_id) {
        updateAgent({
          id: "orchestrator",
          name: "Orchestrator",
          role: "orchestrator",
          state: "working",
          task: `Processing ${data.ticket_id}`,
          progress: 0.1,
        });
      }
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline started for ticket: ${data.ticket_id}`,
        level: "info",
        timestamp: new Date().toISOString(),
      });
    };

    const onPipelineCompleted = (data: { session_id: string; ticket_id: string; result: any }) => {
      console.log('[Socket] pipeline_completed received:', data);
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline completed for ticket: ${data.ticket_id}`,
        level: "success",
        timestamp: new Date().toISOString(),
      });
    };

    const onPipelineError = (data: { session_id: string; ticket_id: string; error: string }) => {
      console.log('[Socket] pipeline_error received:', data);
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline error: ${data.error}`,
        level: "error",
        timestamp: new Date().toISOString(),
      });
    };

    const onAgentEvent = (event: any) => {
      console.log('[Socket] Received agent_event:', event);
      const payload = event.payload || {};

      if (event.type === "agent_state_change") {
        const agentId = payload.agent_id || event.agent_id;
        if (!agentId) return;

        const existingAgent = DEFAULT_AGENTS.find((a) => a.id === agentId);
        if (existingAgent) {
          updateAgent({
            ...existingAgent,
            state: payload.new_state || payload.state,
            task: payload.task || existingAgent.task,
            progress: payload.progress ?? existingAgent.progress,
          });
        } else {
          updateAgent({
            id: agentId,
            name: agentId.charAt(0).toUpperCase() + agentId.slice(1),
            role: agentId as Agent["role"],
            state: payload.new_state || payload.state || "working",
            task: payload.task,
            progress: payload.progress ?? 0.5,
          });
        }
      }

      if (event.type === "agent_log") {
        addLog({
          id: `${Date.now()}-${Math.random()}`,
          agent_id: payload.agent_id || event.agent_id,
          message: payload.message,
          level: payload.level || "info",
          timestamp: event.timestamp || new Date().toISOString(),
        });
      }

      if (event.type === "llm_credit_exhausted") {
        addLog({
          id: `${Date.now()}-${Math.random()}`,
          agent_id: "system",
          message: `LLM credit exhausted: ${payload.error || 'Unknown error'}`,
          level: "error",
          timestamp: event.timestamp || new Date().toISOString(),
        });
      }

      if (event.type === "llm_rate_limited") {
        addLog({
          id: `${Date.now()}-${Math.random()}`,
          agent_id: "system",
          message: `LLM rate limited (retry ${payload.retry_count || 0}): ${payload.error || 'Unknown error'}`,
          level: "warning",
          timestamp: event.timestamp || new Date().toISOString(),
        });
      }

      onEvent?.(event);
    };

    socket.on("pipeline_started", onPipelineStarted);
    socket.on("pipeline_completed", onPipelineCompleted);
    socket.on("pipeline_error", onPipelineError);
    socket.on("agent_event", onAgentEvent);

    return () => {
      leaveSession(sessionId);
      socket.off("pipeline_started", onPipelineStarted);
      socket.off("pipeline_completed", onPipelineCompleted);
      socket.off("pipeline_error", onPipelineError);
      socket.off("agent_event", onAgentEvent);
    };
  }, [sessionId, onEvent, updateAgent, addLog]);

  const agentStates = useSessionStore((state) => state.agentStates, shallow);
  const logs = useSessionStore((state) => state.logs, shallow);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  const agents = useMemo(() => Object.values(agentStates), [agentStates]);
  const agentList = agents.length > 0 ? agents : [];
  const logList = logs.length > 0 ? logs : [];

  return {
    isConnected,
    agents: agentList,
    logs: logList,
    resetAgents,
  };
}
