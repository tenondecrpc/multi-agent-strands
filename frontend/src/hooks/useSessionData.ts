import { useSession, useSessionLogs } from "@/lib/query/hooks";
import { useConnectionStore } from "@/lib/stores/connectionStore";

export function useSessionData(sessionId: string) {
  const { data: session, isLoading } = useSession(sessionId);
  const { data: logs } = useSessionLogs(sessionId);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  return {
    session,
    logs: logs || session?.logs || [],
    isLoading,
    isConnected,
  };
}
