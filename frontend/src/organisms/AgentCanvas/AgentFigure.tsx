import { motion } from "framer-motion";
import type { Agent, AgentRole, AgentState } from "@/types/agent";
import juliaIdle from "@/assets/free-office-pixel-art/Julia-Idle.png";

interface AgentFigureProps {
  agent: Agent;
}

const ROLE_COLORS: Record<AgentRole, string> = {
  orchestrator: '#818cf8',
  backend: '#2dd4bf',
  frontend: '#f472b6',
  qa: '#fbbf24',
};

// We use hue-rotate to change the character's clothing color per role
const ROLE_HUE: Record<AgentRole, string> = {
  orchestrator: 'hue-rotate(220deg)', // Blue/Purple
  backend: 'hue-rotate(150deg)',      // Teal/Green
  frontend: 'hue-rotate(300deg)',     // Pink/Magenta
  qa: 'hue-rotate(45deg)',            // Yellow/Orange
};

function AgentCharacter({ role, state }: { role: AgentRole; state: AgentState }) {
  const isWorking = state === 'working' || state === 'communicating';
  const imgUrl = juliaIdle;

  return (
    <motion.g 
      className={`agent-character agent-${role}`} 
      initial={false}
      animate={{
        y: isWorking ? [0, -4, 0] : 0,
      }}
      transition={{
        duration: isWorking ? 0.3 : 1,
        repeat: isWorking ? Infinity : 0,
        ease: "easeInOut"
      }}
    >
      <circle cx={32} cy={64} r={14} fill={ROLE_COLORS[role]} opacity={0.3} filter="blur(4px)" />

      <foreignObject x={0} y={0} width={64} height={64} style={{ pointerEvents: 'none' }}>
        <div style={{
            width: '32px', height: '32px', 
            backgroundImage: `url(${imgUrl})`,
            backgroundPosition: 'left top',
            backgroundSize: '128px 32px',
            backgroundRepeat: 'no-repeat',
            transform: 'scale(2)',
            transformOrigin: 'top left',
            imageRendering: 'pixelated',
            filter: `${ROLE_HUE[role]} ${state === 'error' || state === 'blocked' ? 'grayscale(0.7)' : ''}`
          }} 
        />
      </foreignObject>

      {state === 'success' && (
        <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }} transform="translate(32, -10)">
          <circle cx="16" cy="16" r="10" fill="#22c55e" />
          <path d="M 11 16 L 15 20 L 21 12" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </motion.g>
      )}
      {state === 'error' && (
        <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }} transform="translate(32, -10)">
          <circle cx="16" cy="16" r="10" fill="#ef4444" />
          <line x1="12" y1="12" x2="20" y2="20" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          <line x1="20" y1="12" x2="12" y2="20" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
        </motion.g>
      )}
      {state === 'thinking' && (
        <motion.g 
          initial={{ opacity: 0, y: 5 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.3, repeat: Infinity, repeatType: 'reverse' }}
          transform="translate(32, -5)"
        >
          <circle cx="0" cy="0" r="2.5" fill="var(--color-muted-foreground)" />
          <circle cx="8" cy="-6" r="3.5" fill="var(--color-muted-foreground)" />
          <circle cx="18" cy="-10" r="5" fill="var(--color-muted-foreground)" />
        </motion.g>
      )}
      {state === 'communicating' && (
        <motion.g
          initial={{ opacity: 0.5 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, repeat: Infinity, repeatType: 'reverse' }}
          transform="translate(32, -5)"
        >
          <circle cx="4" cy="-2" r="3" fill="var(--color-primary)" />
          <circle cx="12" cy="-6" r="4" fill="var(--color-primary)" />
          <circle cx="22" cy="-8" r="5" fill="var(--color-primary)" />
        </motion.g>
      )}
      {state === 'blocked' && (
        <g transform="translate(32, -15)">
          <rect x="-18" y="-10" width="36" height="10" rx="2" fill="var(--color-destructive)" />
          <text x="0" y="-2" textAnchor="middle" fontSize="8" fill="white" fontWeight="bold">BLOCKED</text>
        </g>
      )}
    </motion.g>
  );
}

export const AgentFigure: React.FC<AgentFigureProps> = ({ agent }) => {
  const isRateLimited = agent.state === 'error' && agent.task?.toLowerCase().includes('rate limit');
  const isBlocked = agent.state === 'blocked';

  return (
    <motion.g
      className={`agent-figure agent-${agent.role}`}
      initial={false}
      animate={{
        filter: agent.state === 'error' ? 'grayscale(40%)' : 'grayscale(0%)',
        x: isRateLimited ? [0, -4, 4, -4, 4, -2, 2, 0] : undefined,
      }}
      transition={{
        duration: 0.3,
        x: isRateLimited ? { duration: 0.6, repeat: 2, ease: "easeInOut" } : undefined,
      }}
      transform="translate(-32, -48)"
    >
      {isBlocked && (
        <motion.circle
          cx="32"
          cy="32"
          r="36"
          fill="none"
          stroke="var(--color-destructive)"
          strokeWidth="1.5"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: [0.8, 1.2], opacity: [0.6, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      <AgentCharacter role={agent.role} state={agent.state} />

      {/* Progress ring removed as per request */}

      <motion.text
        className="agent-name"
        x="32"
        textAnchor="middle"
        y={76}
        fontSize="12"
        fontWeight="bold"
        fill="var(--color-foreground)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{
          textShadow: '0 1px 4px rgba(0,0,0,0.8), 0 0 8px rgba(0,0,0,0.8)',
          paintOrder: 'stroke fill'
        }}
      >
        {agent.name}
      </motion.text>

      {agent.task && (
        <text
          className="agent-task"
          x="32"
          textAnchor="middle"
          y={88}
          fontSize="9"
          fill="#d1d5db"
          fontWeight="500"
          style={{
            textShadow: '0 1px 3px rgba(0,0,0,0.9)',
            paintOrder: 'stroke fill'
          }}
        >
          {agent.task.length > 35 ? agent.task.substring(0, 35) + '...' : agent.task}
        </text>
      )}

      <text
        className="agent-state"
        x="32"
        textAnchor="middle"
        y={agent.task ? 100 : 90}
        fontSize="10"
        fontWeight="bold"
        fill={agent.state === 'error' ? '#ef4444' : (agent.state === 'success' ? '#22c55e' : '#9ca3af')}
        style={{
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          textShadow: '0 1px 3px rgba(0,0,0,0.9)',
          paintOrder: 'stroke fill'
        }}
      >
        {agent.state}
      </text>
    </motion.g>
  );
};
