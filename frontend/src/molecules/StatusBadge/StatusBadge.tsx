import { Badge } from "@/atoms/Badge";
import { cn } from "@/lib/utils";

export interface StatusBadgeProps {
  status: "idle" | "thinking" | "working" | "waiting" | "success" | "error" | "communicating" | "blocked";
  className?: string;
}

const statusConfig = {
  idle: { variant: "secondary" as const, label: "Idle" },
  thinking: { variant: "warning" as const, label: "Thinking" },
  working: { variant: "default" as const, label: "Working" },
  waiting: { variant: "secondary" as const, label: "Waiting" },
  success: { variant: "success" as const, label: "Success" },
  error: { variant: "destructive" as const, label: "Error" },
  communicating: { variant: "default" as const, label: "Communicating" },
  blocked: { variant: "destructive" as const, label: "Blocked" },
};

export const StatusBadge = ({ status, className }: StatusBadgeProps) => {
  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className={cn(className)}>
      {config.label}
    </Badge>
  );
};
