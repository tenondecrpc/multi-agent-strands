import { useEffect, useState } from "react";
import { DashboardLayout } from "@/templates/DashboardLayout";
import { SearchBar } from "@/molecules/SearchBar";
import { TicketCard } from "@/molecules/TicketCard";
import { Button } from "@/atoms/Button";
import { Icon } from "@/atoms/Icon";
import type { SessionState } from "@/types/agent";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api/client";

interface DashboardProps {
  sessions?: SessionState[];
}

interface ApiSession {
  session_id: string;
  ticket_id: string;
  status: string;
  created_at: string;
  agents: { id: string; name: string; role: string; state: string }[];
}

export const Dashboard = ({ sessions: propSessions }: DashboardProps) => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ApiSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await api.get<{ sessions: ApiSession[] }>("/sessions");
        setSessions(response.data.sessions || []);
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, []);

  const displaySessions = propSessions ?? sessions;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <div className="flex items-center gap-4">
            <SearchBar placeholder="Search tickets..." />
            <Button>
              <Icon name="user" size="sm" />
              New Session
            </Button>
          </div>
        </div>
        {loading ? (
          <div className="col-span-full py-12 text-center text-muted-foreground">
            Loading sessions...
          </div>
        ) : displaySessions.length === 0 ? (
          <div className="col-span-full py-12 text-center text-muted-foreground">
            No active sessions. Start a new session to begin.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {displaySessions.map((session) => (
              <TicketCard
                key={session.session_id}
                ticketId={session.ticket_id}
                title={`Session ${session.session_id.slice(0, 8)}...`}
                status={session.status.toLowerCase() as SessionState["status"]}
                agentName={session.agents[0]?.name}
                onClick={() => navigate(`/session/${session.ticket_id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
