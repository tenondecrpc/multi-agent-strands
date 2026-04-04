import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/atoms/Badge";
import type { AgentLog } from "@/types/agent";
import { cn } from "@/lib/utils";
import { AgentLogsTimeline } from "./AgentLogsTimeline";

interface LogPanelProps {
  logs: AgentLog[];
  className?: string;
}

export const LogPanel = ({ logs = [], className }: LogPanelProps) => {
  return (
    <Card className={cn("log-panel bg-zinc-950 font-mono text-sm border-zinc-800 flex flex-col", className)}>
      <CardHeader className="pb-2 border-b border-zinc-900 bg-zinc-900/50 shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-zinc-200">Terminal Logs</CardTitle>
          <Badge variant="secondary" className="bg-zinc-800 text-zinc-300">{logs.length}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0 flex-1 min-h-0 flex flex-col">
        <div className="log-list flex-1 overflow-y-auto">
          <AgentLogsTimeline logs={logs} />
        </div>
      </CardContent>
    </Card>
  );
};
