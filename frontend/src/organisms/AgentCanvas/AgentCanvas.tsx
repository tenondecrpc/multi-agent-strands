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
import trash from "@/assets/free-office-pixel-art/Trash.png";
import stampingTable from "@/assets/free-office-pixel-art/stamping-table.png";

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

const CANVAS_WIDTH = 900;
const CANVAS_HEIGHT = 500;
const VIEWBOX_PADDING = 40;

// Compact office layout centered around a collaborative area
const AGENT_POSITIONS: Record<string, Point> = {
  orchestrator: { x: 320, y: 160 },
  backend: { x: 560, y: 160 },
  frontend: { x: 560, y: 320 },
  qa: { x: 320, y: 320 },
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
    return AGENT_POSITIONS[role] || { x: 440, y: 240 };
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
    <div className={cn("agent-canvas rounded-lg border bg-[#8c674e] text-card-foreground shadow-sm w-full h-full flex items-center justify-center relative p-2 overflow-hidden", className)}>
      <svg
        width="100%"
        height="100%"
        viewBox={`${-VIEWBOX_PADDING} ${-VIEWBOX_PADDING} ${CANVAS_WIDTH + VIEWBOX_PADDING * 2} ${CANVAS_HEIGHT + VIEWBOX_PADDING * 2}`}
        preserveAspectRatio="xMidYMid meet"
        style={{
          boxShadow: 'inset 0 0 100px rgba(0,0,0,0.5)' // Gives a bit of depth to the room
        }}
      >
        <defs>
          <pattern id="floor-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#75523d" strokeWidth="2" />
          </pattern>
        </defs>

        {/* Floor */}
        <rect x={-VIEWBOX_PADDING} y={-VIEWBOX_PADDING} width="100%" height="100%" fill="#8c674e" />
        <rect x={-VIEWBOX_PADDING} y={-VIEWBOX_PADDING} width="100%" height="100%" fill="url(#floor-grid)" />

        {/* --- OFFICE ZONES (Carpet areas) --- */}
        {/* Main Work Carpet */}
        <rect x={240} y={80} width={480} height={360} fill="#704e38" rx={12} opacity={0.6} />

        {/* --- OFFICE PROPS --- */}
        {/* Top edge (Breakroom / Files) */}
        <image href={cabinet} x={240} y={16} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={cabinet} x={304} y={16} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={plant} x={368} y={32} width={48} height={48} style={{ imageRendering: "pixelated" }} />
        
        <image href={trash} x={576} y={48} width={32} height={32} style={{ imageRendering: "pixelated" }} />
        <image href={waterCooler} x={608} y={16} width={48} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={desk} x={656} y={16} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={coffeeMaker} x={672} y={0} width={32} height={32} style={{ imageRendering: "pixelated" }} />

        {/* Partitions and desks associated with agents */}
        {/* Orchestrator Area (Top Left) */}
        <image href={partitions1} x={240} y={120} width={200} height={100} style={{ imageRendering: "pixelated" }} />
        <image href={deskWithPc} x={320} y={160} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        
        {/* Backend Area (Top Right) */}
        <image href={partitions2} x={520} y={120} width={200} height={100} style={{ imageRendering: "pixelated" }} />
        <image href={deskWithPc} x={560} y={160} width={96} height={96} style={{ imageRendering: "pixelated" }} />

        {/* Frontend Area (Bottom Right) */}
        <image href={deskWithPc} x={560} y={320} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        <image href={plant} x={656} y={360} width={48} height={48} style={{ imageRendering: "pixelated" }} />
        
        {/* QA Area (Bottom Left) */}
        <image href={deskWithPc} x={320} y={320} width={96} height={96} style={{ imageRendering: "pixelated" }} />
        <image href={printer} x={256} y={340} width={64} height={64} style={{ imageRendering: "pixelated" }} />

        {/* Central collaborative table */}
        <image href={stampingTable} x={464} y={240} width={64} height={64} style={{ imageRendering: "pixelated" }} />
        <image href={trash} x={464} y={300} width={32} height={32} style={{ imageRendering: "pixelated" }} />

        {/* --- AGENTS --- */}
        {Object.entries(AGENT_POSITIONS).map(([role, pos]) => {
          const roleAgents = agentsByRole[role as AgentRole];
          if (!roleAgents || roleAgents.length === 0) return null;
          
          return roleAgents.map((agent, index) => {
            const isWorking = agent.state === 'working' || agent.state === 'communicating' || agent.state === 'thinking';
            
            // Standard desk position
            const deskX = pos.x;
            const deskY = pos.y + 20 + (index * 40);

            // Meeting position around the center table (center is roughly 496, 272)
            let meetX = 496;
            let meetY = 272;

            if (role === 'orchestrator') { meetX -= 120; meetY -= 80; }
            else if (role === 'backend') { meetX += 80; meetY -= 80; }
            else if (role === 'frontend') { meetX += 80; meetY += 80; }
            else if (role === 'qa') { meetX -= 120; meetY += 80; }

            meetX += index * 40;
            meetY += index * 40;

            const targetX = isWorking ? meetX : deskX;
            const targetY = isWorking ? meetY : deskY;

            return (
              <motion.g
                key={agent.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ 
                  opacity: 1, 
                  scale: 1,
                  x: targetX,
                  y: targetY
                }}
                transition={{ duration: 0.8, ease: "easeInOut" }}
                onMouseEnter={() => handleAgentHover(agent)}
                onMouseLeave={handleAgentLeave}
                className="cursor-pointer"
              >
                <AgentFigure agent={agent} />
              </motion.g>
            );
          });
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
