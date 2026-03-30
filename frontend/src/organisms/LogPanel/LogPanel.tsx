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
  info: "#4A90D9",
  warn: "#f0ad4e",
  error: "#dc3545",
};

export const LogPanel = ({ logs, className }: LogPanelProps) => {
  const logsEndRef = useScrollToBottom<HTMLDivElement>([logs]);

  return (
    <Card className={cn("log-panel", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Logs</CardTitle>
          <Badge variant="secondary">{logs.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="log-list max-h-[300px] space-y-1 overflow-y-auto px-4 pb-4">
          {logs.length === 0 ? (
            <div className="log-empty py-8 text-center text-muted-foreground">
              No logs yet
            </div>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "log-entry flex items-start gap-2 rounded-sm px-2 py-1 text-sm",
                  log.level === "error" && "bg-destructive/10"
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
                  className="mt-0.5 shrink-0"
                  style={{ color: LOG_COLORS[log.level] }}
                />
                <span className="log-time shrink-0 text-muted-foreground">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="log-agent shrink-0 font-mono text-xs text-muted-foreground">
                  [{log.agent_id}]
                </span>
                <span
                  className="log-message flex-1"
                  style={{ color: LOG_COLORS[log.level] }}
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
