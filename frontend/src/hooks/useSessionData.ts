import { useSession, useSessionLogs } from "@/lib/query/hooks";
import { useConnectionStore } from "@/lib/stores/connectionStore";
import { useSessionStore } from "@/lib/stores/sessionStore";

export function useSessionData(sessionId: string) {
  const { data: session, isLoading } = useSession(sessionId);
  const { data: logsData } = useSessionLogs(sessionId);
  const isConnected = useConnectionStore((state) => state.status === "connected");
  
  const socketAgentStates = useSessionStore((state) => state.agentStates);
  const hasSocketData = Object.keys(socketAgentStates).length > 0;
  
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
