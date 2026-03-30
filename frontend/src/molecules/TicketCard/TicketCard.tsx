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
        "cursor-pointer transition-colors hover:bg-accent/50",
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <Badge variant={config.variant} className="flex items-center gap-1">
            <Icon name={config.icon} size="sm" />
            {status}
          </Badge>
          {agentName && (
            <div className="flex items-center gap-2">
              <Avatar size="sm">
                <AvatarFallback>{agentName.charAt(0)}</AvatarFallback>
              </Avatar>
              <span className="text-sm text-muted-foreground">{agentName}</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <CardTitle className="text-base">{title}</CardTitle>
        <p className="mt-1 text-sm text-muted-foreground">{ticketId}</p>
      </CardContent>
    </Card>
  );
};
