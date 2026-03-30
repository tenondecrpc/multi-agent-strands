import { useSession, useSessionLogs } from "@/lib/query/hooks";
import { useConnectionStore } from "@/lib/stores/connectionStore";

export function useSessionData(sessionId: string) {
  const { data: session, isLoading } = useSession(sessionId);
  const { data: logsData } = useSessionLogs(sessionId);
  const isConnected = useConnectionStore((state) => state.status === "connected");

  return {
    session,
    logs: logsData?.logs || session?.logs || [],
    isLoading,
    isConnected,
  };
}
