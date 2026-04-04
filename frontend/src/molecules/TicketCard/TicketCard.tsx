import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/atoms/Badge";
import { Avatar, AvatarFallback } from "@/atoms/Avatar";
import { Icon } from "@/atoms/Icon";
import { cn } from "@/lib/utils";

export interface TicketCardProps {
  ticketId: string;
  title: string;
  status: "pending" | "running" | "completed" | "failed";
  agentName?: string;
  onClick?: () => void;
  className?: string;
}

const statusConfig = {
  pending: { variant: "secondary" as const, icon: "clock" },
  running: { variant: "warning" as const, icon: "clock" },
  completed: { variant: "success" as const, icon: "check" },
  failed: { variant: "destructive" as const, icon: "error" },
};

export const TicketCard = ({
  ticketId,
  title,
  status,
  agentName,
  onClick,
  className,
}: TicketCardProps) => {
  const config = statusConfig[status];

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:bg-accent/30 hover:border-accent-foreground/20",
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <Badge variant={config.variant} className="flex items-center gap-1.5 capitalize px-2.5 py-0.5">
            <Icon name={config.icon} size="sm" className="h-3.5 w-3.5" />
            {status}
          </Badge>
          {agentName && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">{agentName}</span>
              <Avatar className="h-6 w-6 ring-1 ring-border">
                <AvatarFallback className="text-[10px] bg-background">{agentName.charAt(0)}</AvatarFallback>
              </Avatar>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          <CardTitle className="text-xl tracking-tight">{title}</CardTitle>
          <div className="flex items-center text-sm text-muted-foreground gap-1.5">
            <Icon name="hash" size="sm" className="h-3.5 w-3.5 opacity-70" />
            <p className="font-mono text-xs">{ticketId}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
