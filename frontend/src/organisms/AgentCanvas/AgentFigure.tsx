import { motion } from "framer-motion";
import type { Agent, AgentRole, AgentState } from "@/types/agent";
import juliaIdle from "@/assets/free-office-pixel-art/Julia-Idle.png";
import juliaWorking from "@/assets/free-office-pixel-art/Julia_PC.png";
import juliaCoffee from "@/assets/free-office-pixel-art/Julia_Drinking_Coffee.png";

interface AgentFigureProps {
  agent: Agent;
}

const ROLE_COLORS: Record<AgentRole, string> = {
  orchestrator: '#818cf8',
  backend: '#2dd4bf',
  frontend: '#f472b6',
  qa: '#fbbf24',
};

const PixelAnimations = () => (
  <style>{`
    @keyframes play-sprite-idle {
      100% { background-position: -128px; }
    }
    @keyframes play-sprite-working {
      100% { background-position: -384px; }
    }
    @keyframes play-sprite-coffee {
      100% { background-position: -96px; }
    }
    .pixelSprite {
      image-rendering: pixelated;
      background-repeat: no-repeat;
    }
    .sprite-idle {
      width: 32px;
      height: 32px;
      background-image: url('${juliaIdle}');
      animation: play-sprite-idle 0.8s steps(4) infinite;
    }
    .sprite-working {
      width: 64px;
      height: 64px;
      background-image: url('${juliaWorking}');
      animation: play-sprite-working 0.8s steps(6) infinite;
    }
    .sprite-coffee {
      width: 32px;
      height: 32px;
      background-image: url('${juliaCoffee}');
      animation: play-sprite-coffee 0.9s steps(3) infinite;
    }
  `}</style>
);

function AgentSprite({ role, state }: { role: AgentRole; state: AgentState }) {
  let spriteClass = 'sprite-idle';
  let is64 = false;

  if (state === 'working' || state === 'communicating' || state === 'success') {
    spriteClass = 'sprite-working';
    is64 = true;
  } else if (state === 'waiting') {
    spriteClass = 'sprite-coffee';
  }

  const scale = is64 ? 1 : 2;
  const size = is64 ? 64 : 32;
  const xOffset = -(size * scale) / 2;
  const yOffset = -(size * scale) / 2;

  return (
    <motion.g className={`agent-sprite agent-${role}`} initial={false}>
      <circle cx={0} cy={20} r={14} fill={ROLE_COLORS[role]} opacity={0.3} filter="blur(4px)" />

      <foreignObject x={xOffset} y={yOffset} width={size * scale} height={size * scale} style={{ pointerEvents: 'none' }}>
        <div 
          className={`pixelSprite ${spriteClass}`} 
          style={{ 
            transform: `scale(${scale})`, 
            transformOrigin: 'top left',
            opacity: state === 'error' || state === 'blocked' ? 0.7 : 1
          }} 
        />
      </foreignObject>

      {state === 'success' && (
        <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
          <circle cx="20" cy="20" r="10" fill="#22c55e" />
          <path d="M 15 20 L 19 24 L 25 16" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </motion.g>
      )}
      {state === 'error' && (
        <motion.g initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
          <circle cx="20" cy="20" r="10" fill="#ef4444" />
          <line x1="16" y1="16" x2="24" y2="24" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          <line x1="24" y1="16" x2="16" y2="24" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
        </motion.g>
      )}
      {state === 'thinking' && (
        <motion.g 
          initial={{ opacity: 0, y: 5 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.3, repeat: Infinity, repeatType: 'reverse' }}
        >
          <circle cx="16" cy="-20" r="2.5" fill="var(--color-muted-foreground)" />
          <circle cx="24" cy="-26" r="3.5" fill="var(--color-muted-foreground)" />
          <circle cx="34" cy="-30" r="5" fill="var(--color-muted-foreground)" />
        </motion.g>
      )}
      {state === 'communicating' && (
        <motion.g
          initial={{ opacity: 0.5 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2, repeat: Infinity, repeatType: 'reverse' }}
        >
          <circle cx="20" cy="-22" r="3" fill="var(--color-primary)" />
          <circle cx="28" cy="-26" r="4" fill="var(--color-primary)" />
          <circle cx="38" cy="-28" r="5" fill="var(--color-primary)" />
        </motion.g>
      )}
      {state === 'blocked' && (
        <g>
          <rect x="-18" y="-36" width="36" height="10" rx="2" fill="var(--color-destructive)" />
          <text x="0" y="-28" textAnchor="middle" fontSize="8" fill="white" fontWeight="bold">BLOCKED</text>
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
      <text textAnchor="middle" dy="-40" fontSize="10" fontWeight="bold" fill="var(--color-primary)">
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
    >
      <PixelAnimations />

      {isBlocked && (
        <motion.circle
          cx="0"
          cy="0"
          r="36"
          fill="none"
          stroke="var(--color-destructive)"
          strokeWidth="1.5"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: [0.8, 1.2], opacity: [0.6, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}

      <AgentSprite role={agent.role} state={agent.state} />

      {agent.state === 'working' && agent.progress != null && <ProgressRing progress={agent.progress} />}

      <motion.text
        className="agent-name"
        x="0"
        textAnchor="middle"
        y={48}
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
          x="0"
          textAnchor="middle"
          y={62}
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
        x="0"
        textAnchor="middle"
        y={74}
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
