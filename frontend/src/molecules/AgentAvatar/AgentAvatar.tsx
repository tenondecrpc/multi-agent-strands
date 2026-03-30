import { Avatar as UIAvatar, AvatarFallback as UIAvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export interface AgentAvatarProps {
  name: string;
  avatarUrl?: string;
  state?: "idle" | "thinking" | "working" | "waiting" | "success" | "error";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const stateColors = {
  idle: "bg-gray-400",
  thinking: "bg-yellow-400",
  working: "bg-blue-400",
  waiting: "bg-orange-400",
  success: "bg-green-400",
  error: "bg-red-400",
};

const stateIcons = {
  idle: "",
  thinking: "💭",
  working: "⚡",
  waiting: "⏳",
  success: "✅",
  error: "❌",
};

export const AgentAvatar = ({
  name,
  avatarUrl,
  state,
  size = "md",
  className,
}: AgentAvatarProps) => {
  return (
    <div className={cn("relative inline-block", className)}>
      <UIAvatar size={size}>
        {avatarUrl && (
          <img
            src={avatarUrl}
            alt={name}
            className="aspect-square h-full w-full object-cover"
          />
        )}
        <UIAvatarFallback className="flex items-center justify-center">
          {name.charAt(0).toUpperCase()}
        </UIAvatarFallback>
      </UIAvatar>
      {state && (
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 flex h-3 w-3 rounded-full border-2 border-background",
            stateColors[state]
          )}
          title={`${name}: ${state}`}
        >
          {stateIcons[state] && (
            <span className="absolute inset-0 flex items-center justify-center text-[6px]">
              {stateIcons[state]}
            </span>
          )}
        </span>
      )}
    </div>
  );
};
