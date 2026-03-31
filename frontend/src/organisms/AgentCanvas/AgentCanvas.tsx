import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AgentFigure } from "./AgentFigure";
import { SessionContextTooltip } from "./components/SessionContextTooltip";
import type { Agent, AgentStateChangePayload, AgentRole } from "@/types/agent";
import type { HandoffEntry } from "./components/SessionContextTooltip";
import { cn } from "@/lib/utils";

// Pixel art imports
import cabinet from "@/assets/free-office-pixel-art/cabinet.png";
import coffeeMaker from "@/assets/free-office-pixel-art/coffee-maker.png";
import deskWithPc from "@/assets/free-office-pixel-art/desk-with-pc.png";
import desk from "@/assets/free-office-pixel-art/desk.png";
import plant from "@/assets/free-office-pixel-art/plant.png";
import waterCooler from "@/assets/free-office-pixel-art/water-cooler.png";
import printer from "@/assets/free-office-pixel-art/printer.png";
import partitions1 from "@/assets/free-office-pixel-art/office-partitions-1.png";
import partitions2 from "@/assets/free-office-pixel-art/office-partitions-2.png";
import sink from "@/assets/free-office-pixel-art/sink.png";
import trash from "@/assets/free-office-pixel-art/Trash.png";

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
const CANVAS_HEIGHT = 450;
const VIEWBOX_PADDING = 50;

// Hardcoded positions mapping roles to coordinates in the virtual office
const AGENT_POSITIONS: Record<string, Point> = {
  orchestrator: { x: CANVAS_WIDTH / 2 - 250, y: CANVAS_HEIGHT / 2 - 100 },
  backend: { x: CANVAS_WIDTH / 2 + 100, y: CANVAS_HEIGHT / 2 - 100 },
  frontend: { x: CANVAS_WIDTH / 2 + 100, y: CANVAS_HEIGHT / 2 + 100 },
  qa: { x: CANVAS_WIDTH / 2 - 250, y: CANVAS_HEIGHT / 2 + 100 },
};

export const AgentCanvas = ({ agents, className, handoffHistory = [] }: AgentCanvasProps) => {
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

  const getAgentPosition = (role: string): Point => {
    return AGENT_POSITIONS[role] || { x: CANVAS_WIDTH / 2, y: CANVAS_HEIGHT / 2 };
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
    <div className={cn("agent-canvas rounded-lg border bg-[#2b2b2b] text-card-foreground shadow-sm w-full h-full flex items-center justify-center relative p-2 overflow-hidden", className)}>
      <svg
        width="100%"
        height="100%"
        viewBox={`${-VIEWBOX_PADDING} ${-VIEWBOX_PADDING} ${CANVAS_WIDTH + VIEWBOX_PADDING * 2} ${CANVAS_HEIGHT + VIEWBOX_PADDING * 2}`}
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <pattern id="floor-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#333" strokeWidth="1" />
          </pattern>
        </defs>

        {/* Floor */}
        <rect x={-VIEWBOX_PADDING} y={-VIEWBOX_PADDING} width="100%" height="100%" fill="url(#floor-grid)" />

        {/* --- OFFICE PROPS --- */}
        {/* Top wall items */}
        <image href={cabinet} x={50} y={-20} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={cabinet} x={114} y={-20} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={plant} x={0} y={10} width={48} height={48} style={{ imageRendering: "pixelated" }} />
        <image href={waterCooler} x={CANVAS_WIDTH - 150} y={0} width={48} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={coffeeMaker} x={CANVAS_WIDTH - 80} y={15} width={32} height={32} style={{ imageRendering: "pixelated" }} />
        <image href={desk} x={CANVAS_WIDTH - 100} y={40} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={trash} x={CANVAS_WIDTH - 200} y={40} width={32} height={32} style={{ imageRendering: "pixelated" }} />
        <image href={sink} x={CANVAS_WIDTH - 300} y={20} width={64} height={64} style={{ imageRendering: "pixelated" }} />

        {/* Partitions and desks associated with agents */}
        {/* Orchestrator Area */}
        <image href={partitions1} x={CANVAS_WIDTH / 2 - 320} y={CANVAS_HEIGHT / 2 - 120} width={200} height={100} style={{ imageRendering: "pixelated" }} />
        <image href={deskWithPc} x={CANVAS_WIDTH / 2 - 250} y={CANVAS_HEIGHT / 2 - 80} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        
        {/* Backend Area */}
        <image href={partitions2} x={CANVAS_WIDTH / 2 + 50} y={CANVAS_HEIGHT / 2 - 120} width={200} height={100} style={{ imageRendering: "pixelated" }} />
        <image href={deskWithPc} x={CANVAS_WIDTH / 2 + 100} y={CANVAS_HEIGHT / 2 - 80} width={96} height={96} style={{ imageRendering: "pixelated" }} />

        {/* Frontend Area */}
        <image href={deskWithPc} x={CANVAS_WIDTH / 2 + 100} y={CANVAS_HEIGHT / 2 + 120} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        
        {/* QA Area */}
        <image href={deskWithPc} x={CANVAS_WIDTH / 2 - 250} y={CANVAS_HEIGHT / 2 + 120} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        <image href={printer} x={CANVAS_WIDTH / 2 - 350} y={CANVAS_HEIGHT / 2 + 120} width={64} height={64} style={{ imageRendering: "pixelated" }} />

        {/* Central plant and area (instead of text) */}
        <image href={plant} x={CANVAS_WIDTH / 2 - 24} y={CANVAS_HEIGHT / 2} width={48} height={48} style={{ imageRendering: "pixelated" }} />

        {/* --- AGENTS --- */}
        {Object.entries(AGENT_POSITIONS).map(([role, pos]) => {
          const roleAgents = agentsByRole[role as AgentRole];
          if (!roleAgents || roleAgents.length === 0) return null;
          // We can render multiple agents of the same role slightly offset, 
          // but for now, we'll assume one primary agent per role, or stack them using index.
          return roleAgents.map((agent, index) => (
            <motion.g
              key={agent.id}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              transform={`translate(${pos.x + index * 40}, ${pos.y + 10 + index * 20})`}
              onMouseEnter={() => handleAgentHover(agent)}
              onMouseLeave={handleAgentLeave}
              className="cursor-pointer"
            >
              <AgentFigure agent={agent} />
            </motion.g>
          ));
        })}
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
