import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/atoms/Badge";
import { Icon } from "@/atoms/Icon";
import { useScrollToBottom } from "@/hooks/useScrollToBottom";
import type { AgentLog } from "@/types/agent";
import { cn } from "@/lib/utils";

interface LogPanelProps {
  logs: AgentLog[];
  className?: string;
}

const LOG_COLORS: Record<string, string> = {
  info: "text-blue-400",
  warn: "text-amber-400",
  error: "text-red-400",
};

export const LogPanel = ({ logs = [], className }: LogPanelProps) => {
  const logsEndRef = useScrollToBottom<HTMLDivElement>([logs]);

  return (
    <Card className={cn("log-panel bg-zinc-950 font-mono text-sm border-zinc-800 flex flex-col", className)}>
      <CardHeader className="pb-2 border-b border-zinc-900 bg-zinc-900/50 shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-zinc-200">Terminal Logs</CardTitle>
          <Badge variant="secondary" className="bg-zinc-800 text-zinc-300">{logs.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0 flex-1 min-h-0 flex flex-col">
        <div className="log-list flex-1 space-y-1 overflow-y-auto px-4 pb-4 pt-4">
          {logs.length === 0 ? (
            <div className="log-empty py-8 text-center text-zinc-600">
              No logs yet. Waiting for stream...
            </div>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "log-entry flex items-start gap-2 rounded-sm px-2 py-1 leading-snug break-words",
                  log.level === "error" && "bg-red-950/40"
                )}
              >
                <Icon
                  name={
                    log.level === "error"
                      ? "error"
                      : log.level === "warn"
                      ? "warning"
                      : "info"
                  }
                  size="sm"
                  className={cn("mt-0.5 shrink-0", LOG_COLORS[log.level])}
                />
                <span className="log-time shrink-0 text-zinc-500">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="log-agent shrink-0 text-zinc-400 font-bold">
                  [{log.agent_id}]
                </span>
                <span
                  className={cn("log-message flex-1", LOG_COLORS[log.level] || "text-zinc-300")}
                >
                  {log.message}
                </span>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </CardContent>
    </Card>
  );
};
