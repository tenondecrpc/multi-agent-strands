import { useParams } from "react-router-dom";
import { SessionLayout } from "@/templates/SessionLayout";
import { Spinner } from "@/atoms/Spinner";
import { useSessionData } from "@/hooks/useSessionData";

export const SessionDetail = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { session, logs, isLoading, isConnected } = useSessionData(sessionId || "");

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-muted-foreground">Session not found</p>
      </div>
    );
  }

  return (
    <SessionLayout
      sessionId={session.session_id}
      ticketId={session.ticket_id}
      agents={session.agents}
      logs={logs}
      metrics={session.metrics}
      isConnected={isConnected}
    />
  );
};
