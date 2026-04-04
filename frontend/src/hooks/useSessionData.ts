import { useEffect } from "react";
import { useSession, useSessionLogs } from "@/lib/query/hooks";
import { useConnectionStore } from "@/lib/stores/connectionStore";
import { useSessionStore } from "@/lib/stores/sessionStore";
import type { Agent } from "@/types/agent";

export function useSessionData(sessionId: string) {
  const { data: session, isLoading } = useSession(sessionId);
  const { data: logsData } = useSessionLogs(sessionId);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  const socketAgentStates = useSessionStore((state) => state.agentStates);
  const setAgentStates = useSessionStore((state) => state.setAgentStates);
  const hasSocketData = Object.keys(socketAgentStates).length > 0;

  useEffect(() => {
    if (!hasSocketData && session?.agents?.length) {
      const mapped: Record<string, Agent> = {};
      for (const agent of session.agents) {
        mapped[agent.id] = agent;
      }
      setAgentStates(mapped);
    }
  }, [session?.agents, hasSocketData, setAgentStates]);

  const agents = hasSocketData
    ? Object.values(socketAgentStates)
    : (session?.agents || []);

  const logs = (logsData?.logs || session?.logs || []);

  return {
    session,
    agents,
    logs,
    isLoading,
    isConnected,
  };
}
