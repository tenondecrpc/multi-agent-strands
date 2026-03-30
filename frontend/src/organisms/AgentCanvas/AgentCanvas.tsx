import { useMemo } from "react";
import { AgentFigure } from "@/components/AgentFigure";
import type { Agent } from "@/types/agent";
import { cn } from "@/lib/utils";

interface AgentCanvasProps {
  agents: Agent[];
  ticketId?: string;
  className?: string;
}

interface Point {
  x: number;
  y: number;
}

const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 500;
const AGENT_SPACING_X = 180;
const AGENT_SPACING_Y = 160;

const AGENT_POSITIONS: Record<string, Point> = {
  architect: { x: CANVAS_WIDTH / 2, y: 80 },
  backend: { x: CANVAS_WIDTH / 2 - AGENT_SPACING_X, y: 80 + AGENT_SPACING_Y },
  frontend: { x: CANVAS_WIDTH / 2 + AGENT_SPACING_X, y: 80 + AGENT_SPACING_Y },
  qa: { x: CANVAS_WIDTH / 2, y: 80 + AGENT_SPACING_Y * 2 },
};

const CONNECTIONS: [string, string][] = [
  ["architect", "backend"],
  ["architect", "frontend"],
  ["backend", "qa"],
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
    <line
      x1={from.x}
      y1={from.y}
      x2={to.x}
      y2={to.y}
      stroke={active ? "#4A90D9" : "#ccc"}
      strokeWidth={active ? 2 : 1}
      strokeDasharray={active ? "8 4" : "none"}
      className={active ? "animate-dash" : ""}
    />
  );
}

export const AgentCanvas = ({ agents, ticketId, className }: AgentCanvasProps) => {
  const agentMap = useMemo(() => {
    const map: Record<string, Agent> = {};
    agents.forEach((agent) => {
      map[agent.role] = agent;
    });
    return map;
  }, [agents]);

  const getAgentPosition = (role: string): Point => {
    return AGENT_POSITIONS[role] || { x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 };
  };

  const isConnectionActive = (from: string, to: string): boolean => {
    const fromAgent = agentMap[from];
    const toAgent = agentMap[to];
    if (!fromAgent || !toAgent) return false;
    return fromAgent.state === "working" || toAgent.state === "working";
  };

  return (
    <div className={cn("agent-canvas", className)}>
      <svg
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        viewBox={`0 0 ${CANVAS_WIDTH} ${CANVAS_HEIGHT}`}
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon points="0 0, 10 3.5, 0 7" fill="#4A90D9" />
          </marker>
        </defs>

        {CONNECTIONS.map(([from, to]) => (
          <AgentConnection
            key={`${from}-${to}`}
            from={getAgentPosition(from)}
            to={getAgentPosition(to)}
            active={isConnectionActive(from, to)}
          />
        ))}

        {Object.entries(AGENT_POSITIONS).map(([role, pos]) => {
          const agent = agentMap[role];
          if (!agent) return null;
          return (
            <g key={role} transform={`translate(${pos.x}, ${pos.y})`}>
              <AgentFigure agent={agent} />
            </g>
          );
        })}

        {ticketId && (
          <text
            x={CANVAS_WIDTH / 2}
            y={25}
            textAnchor="middle"
            fontSize="16"
            fontWeight="bold"
          >
            Ticket: {ticketId}
          </text>
        )}
      </svg>
    </div>
  );
};
