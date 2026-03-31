import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AgentFigure } from "./AgentFigure";
import { SessionContextTooltip } from "./components/SessionContextTooltip";
import type { Agent, AgentStateChangePayload, AgentRole } from "@/types/agent";
import type { HandoffEntry } from "./components/SessionContextTooltip";
import { cn } from "@/lib/utils";

interface AgentCanvasProps {
  agents: Agent[];
  ticketId?: string;
  className?: string;
  recentEvents?: AgentStateChangePayload[];
  handoffHistory?: HandoffEntry[];
}

interface Point {
  x: number;
  y: number;
}

const CANVAS_WIDTH = 1100;
const CANVAS_HEIGHT = 300;
const VIEWBOX_PADDING = 50;

const AGENT_POSITIONS: Record<string, Point> = {
  orchestrator: { x: CANVAS_WIDTH / 2 - 300, y: CANVAS_HEIGHT / 2 },
  backend: { x: CANVAS_WIDTH / 2 - 100, y: CANVAS_HEIGHT / 2 },
  frontend: { x: CANVAS_WIDTH / 2 + 100, y: CANVAS_HEIGHT / 2 },
  qa: { x: CANVAS_WIDTH / 2 + 300, y: CANVAS_HEIGHT / 2 },
};

const DEFAULT_CONNECTIONS: [string, string][] = [
  ["orchestrator", "backend"],
  ["backend", "frontend"],
  ["frontend", "qa"],
];

function AgentConnection({
  from,
  to,
  active,
}: {
  from: Point;
  to: Point;
  active: boolean;
}) {
  return (
    <motion.line
      x1={from.x}
      y1={from.y}
      x2={to.x}
      y2={to.y}
      stroke={active ? "var(--color-primary)" : "var(--color-border)"}
      strokeWidth={active ? 2 : 1}
      strokeDasharray={active ? "6 4" : "none"}
      initial={false}
      animate={{
        stroke: active ? "var(--color-primary)" : "var(--color-border)",
        strokeWidth: active ? 2 : 1,
        strokeDashoffset: active ? [0, -20] : 0,
      }}
      transition={{
        duration: 0.3,
        strokeDashoffset: active ? { duration: 0.8, repeat: Infinity, ease: "linear" } : { duration: 0.3 },
      }}
    />
  );
}

function getActiveConnectionsFromEvents(
  events: AgentStateChangePayload[],
  agentMap: Record<string, Agent>
): Set<string> {
  const active = new Set<string>();
  const recentEvents = events.slice(-10);

  for (const event of recentEvents) {
    const agentRole = agentMap[event.agent_id]?.role;
    if (agentRole && (event.new_state === "working" || event.new_state === "communicating")) {
      for (const [from, to] of DEFAULT_CONNECTIONS) {
        if (from === agentRole || to === agentRole) {
          active.add(`${from}-${to}`);
        }
      }
    }
  }

  return active;
}

export const AgentCanvas = ({ agents, ticketId, className, recentEvents = [], handoffHistory = [] }: AgentCanvasProps) => {
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  const agentMap = useMemo(() => {
    const map: Record<string, Agent> = {};
    agents.forEach((agent) => {
      map[agent.id] = agent;
    });
    return map;
  }, [agents]);

  const agentsByRole = useMemo(() => {
    const byRole: Record<string, Agent[]> = {
      orchestrator: [],
      backend: [],
      frontend: [],
      qa: []
    };
    agents.forEach((agent) => {
      if (byRole[agent.role]) {
        byRole[agent.role].push(agent);
      }
    });
    return byRole;
  }, [agents]);

  const activeConnections = useMemo(
    () => getActiveConnectionsFromEvents(recentEvents, agentMap),
    [recentEvents, agentMap]
  );

  const getAgentPosition = (role: string): Point => {
    return AGENT_POSITIONS[role] || { x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 };
  };

  const isConnectionActive = (from: string, to: string): boolean => {
    const connectionKey = `${from}-${to}`;
    if (activeConnections.has(connectionKey)) return true;
    const fromAgents = agentsByRole[from as AgentRole];
    const toAgents = agentsByRole[to as AgentRole];
    if (!fromAgents || fromAgents.length === 0 || !toAgents || toAgents.length === 0) return false;
    const fromAgent = fromAgents[0];
    const toAgent = toAgents[0];
    return fromAgent.state === "working" || toAgent.state === "working" || fromAgent.state === "communicating" || toAgent.state === "communicating";
  };

  const handleAgentHover = (agent: Agent) => {
    setHoveredAgent(agent.id);
    const pos = getAgentPosition(agent.role);
    setTooltipPosition({
      x: pos.x + 50,
      y: pos.y,
    });
    setShowTooltip(true);
  };

  const handleAgentLeave = () => {
    setHoveredAgent(null);
    setShowTooltip(false);
  };

  const hoveredAgentData = hoveredAgent ? agentMap[hoveredAgent] : null;

  return (
    <div className={cn("agent-canvas rounded-lg border bg-card text-card-foreground shadow-sm w-full h-full flex items-center justify-center relative p-2", className)}>
      <svg
        width="100%"
        height="100%"
        viewBox={`${-VIEWBOX_PADDING} ${-VIEWBOX_PADDING} ${CANVAS_WIDTH + VIEWBOX_PADDING * 2} ${CANVAS_HEIGHT + VIEWBOX_PADDING * 2}`}
        preserveAspectRatio="xMidYMid meet"
      >
        {DEFAULT_CONNECTIONS.map(([from, to]) => {
          const fromAgents = agentsByRole[from as AgentRole];
          const toAgents = agentsByRole[to as AgentRole];
          if (!fromAgents || fromAgents.length === 0 || !toAgents || toAgents.length === 0) return null;
          return (
            <AgentConnection
              key={`${from}-${to}`}
              from={getAgentPosition(from)}
              to={getAgentPosition(to)}
              active={isConnectionActive(from, to)}
            />
          );
        })}

        {Object.entries(AGENT_POSITIONS).map(([role, pos]) => {
          const roleAgents = agentsByRole[role as AgentRole];
          if (!roleAgents || roleAgents.length === 0) return null;
          const agent = roleAgents[0];
          return (
            <motion.g
              key={role}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              transform={`translate(${pos.x}, ${pos.y})`}
              onMouseEnter={() => handleAgentHover(agent)}
              onMouseLeave={handleAgentLeave}
              className="cursor-pointer"
            >
              <AgentFigure agent={agent} />
            </motion.g>
          );
        })}

        {ticketId && (
          <>
            <text
              x={CANVAS_WIDTH / 2}
              y={40}
              textAnchor="middle"
              fontSize="12"
              fontWeight="600"
              fill="var(--color-muted-foreground)"
            >
              {ticketId}
            </text>
            <text
              x={CANVAS_WIDTH / 2}
              y={55}
              textAnchor="middle"
              fontSize="10"
              fill="var(--color-muted-foreground)"
              opacity="0.6"
            >
              Multi-Agent Collaboration
            </text>
          </>
        )}
      </svg>

      {hoveredAgentData && (
        <SessionContextTooltip
          agent={hoveredAgentData}
          visible={showTooltip}
          position={tooltipPosition}
          handoffHistory={handoffHistory}
        />
      )}
    </div>
  );
};
