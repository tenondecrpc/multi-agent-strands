import { useEffect, useCallback, useRef, useMemo } from "react";
// // import type { Agent } from "@/types/agent"; // shallow not used // shallow not used
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
  //  // AgentState, // not used // not used
  AgentLog,
} from "@/types/agent";

interface UseSocketOptions {
  sessionId: string | null;
  onEvent?: (event: AgentEvent) => void;
}

// AGENT_SEQUENCE removed as it is unused

const DEFAULT_AGENTS: Agent[] = [
  { id: "orchestrator", name: "Orchestrator", role: "orchestrator", state: "idle" },
  { id: "backend_agent", name: "Backend Agent", role: "backend", state: "idle" },
  { id: "frontend_agent", name: "Frontend Agent", role: "frontend", state: "idle" },
  { id: "qa_agent", name: "QA Agent", role: "qa", state: "idle" },
];

const AGENT_ID_TO_ROLE: Record<string, Agent["role"]> = {
  orchestrator: "orchestrator",
  backend_agent: "backend",
  frontend_agent: "frontend",
  qa_agent: "qa",
};

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

// startAgentSequence removed as unused

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
        level: "info",
        timestamp: new Date().toISOString(),
      });
      const resultPayload = data.result;
      const resultText = typeof resultPayload === 'string'
        ? resultPayload
        : resultPayload?.result || resultPayload?.output || JSON.stringify(resultPayload);
      
      if (resultText && resultText !== '{}' && resultText !== '{"status":"completed"}') {
        addLog({
          id: `result-${Date.now()}-${Math.random()}`,
          agent_id: "orchestrator",
          message: `{'result': '${String(resultText).replace(/\n/g, '\\n').replace(/'/g, "\\'")}'}`,
          level: "info",
          timestamp: new Date().toISOString(),
        });
      }
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
        const mappedRole = AGENT_ID_TO_ROLE[agentId] || (agentId as Agent["role"]);
        console.log('[Socket] agent_state_change - existingAgent:', existingAgent, 'mappedRole:', mappedRole);
        
        if (existingAgent) {
          updateAgent({
            ...existingAgent,
            role: mappedRole,
            state: payload.new_state || payload.state,
            task: payload.task || existingAgent.task,
            progress: payload.progress ?? existingAgent.progress,
          });
        } else {
          updateAgent({
            id: agentId,
            name: agentId.charAt(0).toUpperCase() + agentId.slice(1),
            role: mappedRole,
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
          level: "warn",
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

  const agentStates = useSessionStore((state) => state.agentStates);
  const logs = useSessionStore((state) => state.logs);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  const agents = useMemo(() => Object.values(agentStates) as Agent[], [agentStates]);
  const agentList = agents.length > 0 ? agents : [] as Agent[];
  const logList = logs.length > 0 ? logs : [] as AgentLog[];

  return {
    isConnected,
    agents: agentList,
    logs: logList,
    resetAgents,
  };
}
