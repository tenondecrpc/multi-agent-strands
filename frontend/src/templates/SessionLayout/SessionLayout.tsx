import type { ReactNode } from "react";
import { AgentCanvas } from "@/organisms/AgentCanvas";
import { TaskPanel } from "@/organisms/TaskPanel";
import { LogPanel } from "@/organisms/LogPanel";
import { MetricsBar } from "@/organisms/MetricsBar";
import { Badge } from "@/atoms/Badge";
import type { Agent, AgentLog, SessionMetrics } from "@/types/agent";
import { cn } from "@/lib/utils";

interface SessionLayoutProps {
  sessionId: string;
  ticketId?: string;
  agents: Agent[];
  logs: AgentLog[];
  metrics: SessionMetrics;
  isConnected: boolean;
  error?: string;
  children?: ReactNode;
  className?: string;
}

export const SessionLayout = ({
  sessionId,
  ticketId,
  agents,
  logs,
  metrics,
  isConnected,
  error,
  children,
  className,
}: SessionLayoutProps) => {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">Session {sessionId}</h2>
          {ticketId && (
            <Badge variant="secondary" className="font-mono">
              {ticketId}
            </Badge>
          )}
        </div>
        <MetricsBar metrics={metrics} isConnected={isConnected} />
      </div>
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">Session Failed</p>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <AgentCanvas agents={agents} ticketId={ticketId} />
        </div>
        <div className="space-y-4">
          <TaskPanel ticketId={ticketId} agents={agents} />
          <LogPanel logs={logs} />
        </div>
      </div>
      {children}
    </div>
  );
};
