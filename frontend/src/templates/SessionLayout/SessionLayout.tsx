import type { ReactNode } from "react";
import { AgentCanvas } from "@/organisms/AgentCanvas";
import { TaskPanel } from "@/organisms/TaskPanel";
import { LogPanel } from "@/organisms/LogPanel";
import { MetricsBar } from "@/organisms/MetricsBar";
import { Badge } from "@/atoms/Badge";
import { Button } from "@/atoms/Button";
import { Icon } from "@/atoms/Icon";
import { useUIStore } from "@/lib/stores/uiStore";
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
  const { theme, toggleTheme } = useUIStore();

  return (
    <div className={cn("flex min-h-screen flex-col space-y-4 p-6 bg-background text-foreground", className)}>
      <div className="flex shrink-0 items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold">Session {sessionId}</h2>
          {ticketId && (
            <Badge variant="secondary" className="font-mono">
              {ticketId}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-4">
          <MetricsBar metrics={metrics} isConnected={isConnected} />
          <Button variant="ghost" size="icon" onClick={toggleTheme} className="rounded-full">
            <Icon name={theme === "dark" ? "sun" : "moon"} />
          </Button>
        </div>
      </div>
      {error && (
        <div className="shrink-0 rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">Session Failed</p>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}
      <div className="grid flex-1 min-h-0 grid-cols-3 gap-4">
        <div className="col-span-2 relative h-full">
          <AgentCanvas agents={agents} ticketId={ticketId} className="absolute inset-0" />
        </div>
        <div className="flex h-full flex-col gap-4">
          <TaskPanel ticketId={ticketId} agents={agents} className="shrink-0 max-h-[50%] overflow-y-auto" />
          <LogPanel logs={logs} className="flex-1 min-h-0" />
        </div>
      </div>
      {children}
    </div>
  );
};
