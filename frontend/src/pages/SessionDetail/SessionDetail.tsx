import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { SessionLayout } from "@/templates/SessionLayout";
import { Spinner } from "@/atoms/Spinner";
import { useSessionStore } from "@/lib/stores/sessionStore";
import { useConnectionStore } from "@/lib/stores/connectionStore";
import { useSocket } from "@/hooks/useSocket";
import { api } from "@/lib/api/client";
import type { Agent } from "@/types/agent";

interface SessionResponse {
  session_id: string;
  ticket_id: string;
  status: string;
  started_at: string;
  agents: { id: string; name: string; role: string; state: string }[];
  logs: any[];
  metrics: any;
  error?: string | null;
}

export const SessionDetail = () => {
  const { ticketId } = useParams<{ ticketId: string }>();
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const isConnected = useConnectionStore((state) => state.status === "connected");
  const socketAgentStates = useSessionStore((state) => state.agentStates);
  const setAgentStates = useSessionStore((state) => state.setAgentStates);
  const socketLogs = useSessionStore((state) => state.logs);
  const setLogs = useSessionStore((state) => state.setLogs);

  // Establish socket connection to listen for new events
  useSocket({
    sessionId: session?.session_id ?? null,
    onEvent: undefined,
  });

  useEffect(() => {
    if (!ticketId) return;
    const fetchSession = async () => {
      try {
        const response = await api.get<{ session_id: string; ticket_id: string }>(
          `/sessions/ticket/${ticketId}/active`
        );
        const sessionId = response.data.session_id;
        const sessionResponse = await api.get<SessionResponse>(`/sessions/${sessionId}`);
        setSession(sessionResponse.data);
        
        // Initialize global store with fetched data so that websocket events append to it
        if (sessionResponse.data.logs && sessionResponse.data.logs.length > 0) {
          setLogs(sessionResponse.data.logs);
        }
        
        if (sessionResponse.data.agents && sessionResponse.data.agents.length > 0) {
          const initialAgents: Record<string, Agent> = {};
          sessionResponse.data.agents.forEach((a) => {
            initialAgents[a.id] = {
              id: a.id,
              name: a.name,
              role: a.role as Agent['role'],
              state: a.state as Agent['state'],
            };
          });
          setAgentStates(initialAgents);
        }
      } catch (error) {
        console.error("Failed to fetch session:", error);
        setSession(null);
      } finally {
        setLoading(false);
      }
    };
    fetchSession();
  }, [ticketId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">No active session for this ticket</p>
      </div>
    );
  }

  const hasSocketData = Object.keys(socketAgentStates).length > 0;
  const agents: Agent[] = hasSocketData
    ? Object.values(socketAgentStates)
    : session.agents.map((a) => ({
        id: a.id,
        name: a.name,
        role: a.role as any,
        state: a.state as any,
      }));

  // socketLogs has the most up-to-date state since we initialize it with session.logs
  const logs = socketLogs.length > 0 ? socketLogs : session.logs;

  return (
    <SessionLayout
      sessionId={session.session_id}
      ticketId={session.ticket_id}
      agents={agents}
      logs={logs}
      metrics={session.metrics}
      isConnected={isConnected}
      error={session.status === "FAILED" ? session.error || "Session failed with no error details" : undefined}
    />
  );
};
