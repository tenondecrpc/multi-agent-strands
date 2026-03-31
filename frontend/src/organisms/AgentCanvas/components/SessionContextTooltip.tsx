import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Agent, AgentRole } from "@/types/agent";

export interface SessionContextTooltipProps {
  agent: Agent;
  visible: boolean;
  position: { x: number; y: number };
  handoffHistory?: HandoffEntry[];
  className?: string;
}

export interface HandoffEntry {
  from: AgentRole;
  to: AgentRole;
  timestamp: string;
  summary?: string;
}

const stateDescriptions: Record<Agent["state"], string> = {
  idle: "Agent is idle, waiting for tasks",
  thinking: "Agent is processing and analyzing",
  working: "Agent is actively working on a task",
  waiting: "Agent is waiting for external input",
  success: "Agent completed its task successfully",
  error: "Agent encountered an error",
  communicating: "Agent is communicating with another agent",
  blocked: "Agent is blocked and needs attention",
};

const roleDescriptions: Record<AgentRole, string> = {
  orchestrator: "Coordinates the overall workflow and delegates tasks",
  backend: "Implements backend services and APIs",
  frontend: "Builds user interfaces and frontend components",
  qa: "Tests and validates code quality and functionality",
};

export const SessionContextTooltip = ({
  agent,
  visible,
  position,
  handoffHistory = [],
  className,
}: SessionContextTooltipProps) => {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className={cn(
            "absolute z-50 w-64 rounded-lg border bg-popover text-popover-foreground shadow-lg p-3 text-xs",
            className
          )}
          style={{ left: position.x, top: position.y }}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15 }}
        >
          <div className="space-y-2">
            <div>
              <div className="font-semibold text-sm">{agent.name}</div>
              <div className="text-muted-foreground capitalize">{roleDescriptions[agent.role]}</div>
            </div>

            <div className="pt-1 border-t border-border">
              <div className="text-muted-foreground mb-1">Current State</div>
              <div className="capitalize font-medium">{stateDescriptions[agent.state]}</div>
            </div>

            {agent.state === "blocked" && agent.task && (
              <div className="pt-1 border-t border-border">
                <div className="text-destructive font-medium mb-1">Blocked Reason</div>
                <div className="text-muted-foreground">{agent.task}</div>
              </div>
            )}

            {handoffHistory.length > 0 && (
              <div className="pt-1 border-t border-border">
                <div className="text-muted-foreground mb-1">Recent Handoffs</div>
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {handoffHistory.slice(-3).map((entry, index) => (
                    <div key={index} className="flex items-center gap-1 text-muted-foreground">
                      <span className="capitalize">{entry.from}</span>
                      <span>→</span>
                      <span className="capitalize">{entry.to}</span>
                      {entry.summary && (
                        <span className="truncate text-[10px] ml-1">({entry.summary})</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {(agent.current_file || agent.current_branch) && (
              <div className="pt-1 border-t border-border">
                <div className="text-muted-foreground mb-1">Context</div>
                {agent.current_file && (
                  <div className="font-mono text-[10px] truncate">{agent.current_file}</div>
                )}
                {agent.current_branch && (
                  <div className="font-mono text-[10px] text-muted-foreground">{agent.current_branch}</div>
                )}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
