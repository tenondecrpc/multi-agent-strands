import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/atoms/Badge";
import { StatusBadge } from "@/molecules/StatusBadge";
import type { Agent } from "@/types/agent";
import { cn } from "@/lib/utils";

interface TaskPanelProps {
  ticketId?: string;
  agents: Agent[];
  className?: string;
}

const STATE_COLORS: Record<string, string> = {
  idle: "var(--color-muted-foreground)",
  thinking: "var(--color-primary)",
  working: "var(--color-primary)",
  waiting: "var(--color-muted)",
  success: "var(--color-primary)",
  error: "var(--color-destructive)",
};

const STATE_ICONS: Record<string, string> = {
  idle: "○",
  thinking: "◐",
  working: "◉",
  waiting: "⧖",
  success: "✓",
  error: "✗",
};

export const TaskPanel = ({ ticketId, agents, className }: TaskPanelProps) => {
  return (
    <Card className={cn("task-panel", className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>Tasks</CardTitle>
          {ticketId && (
            <Badge variant="secondary" className="font-mono text-xs">
              {ticketId}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="task-list space-y-2">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="task-item flex items-center gap-3 rounded-md border p-2 bg-muted/20"
            >
              <span
                className="task-icon text-lg"
                style={{ color: STATE_COLORS[agent.state] }}
              >
                {STATE_ICONS[agent.state]}
              </span>
              <div className="flex flex-1 items-center justify-between">
                <span className="task-name font-medium">{agent.name}</span>
                <StatusBadge status={agent.state} />
              </div>
              {agent.task && (
                <p className="task-desc w-full text-sm text-muted-foreground">
                  {agent.task}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
