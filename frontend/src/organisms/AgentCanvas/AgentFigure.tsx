import { motion } from "framer-motion";
import type { Agent, AgentRole, AgentState } from "@/types/agent";
import boss from "@/assets/free-office-pixel-art/boss.png";
import worker1 from "@/assets/free-office-pixel-art/worker1.png";
import worker2 from "@/assets/free-office-pixel-art/worker2.png";
import worker4 from "@/assets/free-office-pixel-art/worker4.png";

interface AgentFigureProps {
  agent: Agent;
}

const ROLE_COLORS: Record<AgentRole, string> = {
  orchestrator: '#818cf8',
  backend: '#2dd4bf',
  frontend: '#f472b6',
  qa: '#fbbf24',
};

const CHARACTER_MAP: Record<AgentRole, string> = {
  orchestrator: boss,
  backend: worker1,
  frontend: worker2,
  qa: worker4,
};

function AgentCharacter({ role, state }: { role: AgentRole; state: AgentState }) {
  const isWorking = state === 'working' || state === 'communicating';
  const imgUrl = CHARACTER_MAP[role] || worker1;

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
            backgroundRepeat: 'no-repeat',
            transform: 'scale(2)',
            transformOrigin: 'top left',
            imageRendering: 'pixelated',
            opacity: state === 'error' || state === 'blocked' ? 0.7 : 1
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

function ProgressRing({ progress }: { progress: number }) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - progress);

  return (
    <motion.g
      className="progress-ring"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      transform="translate(32, 32)"
    >
      <circle cx="0" cy="0" r={radius} fill="none" stroke="var(--color-border)" strokeWidth="2" />
      <motion.circle
        cx="0"
        cy="0"
        r={radius}
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth="2"
        strokeDasharray={circumference}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 0.5, ease: "easeInOut" }}
        transform="rotate(-90)"
      />
      <text textAnchor="middle" dy="46" fontSize="10" fontWeight="bold" fill="var(--color-primary)">
        {Math.round(progress * 100)}%
      </text>
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
        y={80}
        fontSize="12"
        fontWeight="bold"
        fill="var(--color-foreground)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{
          textShadow: '0 1px 4px var(--color-background), 0 0 8px var(--color-background)',
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
          y={94}
          fontSize="9"
          fill="var(--color-muted-foreground)"
          fontWeight="500"
          style={{
            textShadow: '0 1px 2px var(--color-background)',
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
        y={106}
        fontSize="10"
        fontWeight="bold"
        fill={agent.state === 'error' ? 'var(--color-destructive)' : 'var(--color-muted-foreground)'}
        style={{
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          textShadow: '0 1px 2px var(--color-background)',
          paintOrder: 'stroke fill'
        }}
      >
        {agent.state}
      </text>
    </motion.g>
  );
};
