import { useEffect, useCallback, useRef } from "react";
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

    const onPipelineStarted = (data: {
      session_id: string;
      ticket_id: string;
    }) => {
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline started for ticket: ${data.ticket_id}`,
        level: "info",
        timestamp: new Date().toISOString(),
      });
      startAgentSequence(data.ticket_id);
    };

    const onPipelineCompleted = (data: {
      session_id: string;
      ticket_id: string;
    }) => {
      clearAnimations();
      DEFAULT_AGENTS.forEach((agent) => {
        updateAgent({ ...agent, state: "success", progress: 1 });
      });
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline completed for ticket: ${data.ticket_id}`,
        level: "info",
        timestamp: new Date().toISOString(),
      });
    };

    const onPipelineError = (data: {
      session_id: string;
      ticket_id: string;
      error: string;
    }) => {
      clearAnimations();
      DEFAULT_AGENTS.forEach((agent) => {
        updateAgent({ ...agent, state: "error" });
      });
      addLog({
        id: `${Date.now()}-${Math.random()}`,
        agent_id: "system",
        message: `Pipeline error: ${data.error}`,
        level: "error",
        timestamp: new Date().toISOString(),
      });
    };

    socket.on("pipeline_started", onPipelineStarted);
    socket.on("pipeline_completed", onPipelineCompleted);
    socket.on("pipeline_error", onPipelineError);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("pipeline_started", onPipelineStarted);
      socket.off("pipeline_completed", onPipelineCompleted);
      socket.off("pipeline_error", onPipelineError);
    };
  }, [clearAnimations, startAgentSequence, setStatus, addLog, updateAgent]);

  useEffect(() => {
    if (!sessionId) return;

    joinSession(sessionId);

    const onAgentEvent = (event: AgentEvent) => {
      const payload = event.payload as AgentStateChangePayload | AgentLogPayload;

      if (event.type === "agent_state_change" && "agent_id" in payload) {
        const statePayload = payload as AgentStateChangePayload;
        const existingAgent = DEFAULT_AGENTS.find(
          (a) => a.id === statePayload.agent_id
        );
        if (existingAgent) {
          updateAgent({
            ...existingAgent,
            state: statePayload.new_state,
            task: statePayload.task || existingAgent.task,
            progress: statePayload.progress ?? existingAgent.progress,
          });
        }
      }

      if (event.type === "agent_log" && "message" in payload) {
        const logPayload = payload as AgentLogPayload;
        addLog({
          id: `${Date.now()}-${Math.random()}`,
          agent_id: logPayload.agent_id,
          message: logPayload.message,
          level: logPayload.level,
          timestamp: event.timestamp,
        });
      }

      onEvent?.(event);
    };

    socket.on("agent_event", onAgentEvent);

    return () => {
      leaveSession(sessionId);
      socket.off("agent_event", onAgentEvent);
    };
  }, [sessionId, onEvent, updateAgent, addLog]);

  const agents = useSessionStore((state) => Object.values(state.agentStates));
  const logs = useSessionStore((state) => state.logs);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  return {
    isConnected,
    agents,
    logs,
    resetAgents,
  };
}
