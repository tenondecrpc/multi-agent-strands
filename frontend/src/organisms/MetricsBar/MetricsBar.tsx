import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Icon } from "@/atoms/Icon";
import type { SessionMetrics } from "@/types/agent";
import { cn } from "@/lib/utils";

interface MetricsBarProps {
  metrics: SessionMetrics;
  isConnected: boolean;
  className?: string;
}

export const MetricsBar = ({
  metrics,
  isConnected,
  className,
}: MetricsBarProps) => {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  };

  return (
    <Card className={cn("metrics-bar", className)}>
      <CardContent className="flex items-center justify-between p-4">
        <div className="metric flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Tokens</span>
          <span className="font-mono font-medium">
            {formatTokens(metrics.tokens_used)}
          </span>
        </div>
        <div className="metric flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Time</span>
          <span className="font-mono font-medium">
            {formatDuration(metrics.duration_seconds)}
          </span>
        </div>
        <div className="metric flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Files</span>
          <span className="font-mono font-medium">
            {metrics.files_created}
          </span>
        </div>
        <div className="metric flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Tests</span>
          <span className="font-mono font-medium">
            {metrics.tests_passed === null ? (
              <span className="tests-pending text-muted-foreground">—</span>
            ) : metrics.tests_passed ? (
              <Icon name="check" size="sm" className="text-green-500" />
            ) : (
              <Icon name="error" size="sm" className="text-destructive" />
            )}
          </span>
        </div>
        <div className="metric connection-status flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Status</span>
          <Badge variant={isConnected ? "success" : "secondary"}>
            {isConnected ? "● Connected" : "○ Disconnected"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};
