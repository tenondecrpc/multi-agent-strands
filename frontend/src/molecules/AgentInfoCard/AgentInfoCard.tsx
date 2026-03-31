import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Agent } from "@/types/agent";

export interface AgentInfoCardProps {
  agent: Agent;
  className?: string;
}

const stateBadgeStyles: Record<Agent["state"], string> = {
  idle: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
  thinking: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300",
  working: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  waiting: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  success: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  error: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  communicating: "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  blocked: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
};

export const AgentInfoCard = ({ agent, className }: AgentInfoCardProps) => {
  return (
    <motion.div
      className={cn(
        "absolute left-1/2 -translate-x-1/2 mt-2 w-48 rounded-lg border bg-card p-3 shadow-md text-xs",
        className
      )}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-card-foreground truncate">{agent.name}</span>
        <span
          className={cn(
            "px-1.5 py-0.5 rounded-full text-[10px] font-medium capitalize",
            stateBadgeStyles[agent.state]
          )}
        >
          {agent.state}
        </span>
      </div>

      <div className="space-y-1.5">
        {agent.current_file && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">File:</span>
            <span className="text-foreground truncate font-mono text-[10px]">{agent.current_file}</span>
          </div>
        )}
        {agent.current_branch && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Branch:</span>
            <span className="text-foreground font-mono text-[10px]">{agent.current_branch}</span>
          </div>
        )}
        {agent.tokens_used != null && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Tokens:</span>
            <span className="text-foreground font-mono text-[10px]">{agent.tokens_used.toLocaleString()}</span>
          </div>
        )}
        {agent.task && (
          <div className="flex items-start gap-2">
            <span className="text-muted-foreground shrink-0">Task:</span>
            <span className="text-foreground text-[10px] line-clamp-2">{agent.task}</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};
