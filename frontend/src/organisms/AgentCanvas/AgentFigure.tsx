import { motion } from "framer-motion";
import type { Agent, AgentRole, AgentState } from "@/types/agent";
import orchestratorAvatar from "@/assets/avatars/orchestrator.svg";
import backendAvatar from "@/assets/avatars/backend.svg";
import frontendAvatar from "@/assets/avatars/frontend.svg";
import qaAvatar from "@/assets/avatars/qa.svg";

interface AgentFigureProps {
  agent: Agent;
}

const ROLE_AVATARS: Record<AgentRole, string> = {
  orchestrator: orchestratorAvatar,
  backend: backendAvatar,
  frontend: frontendAvatar,
  qa: qaAvatar,
};

const ROLE_COLORS: Record<AgentRole, string> = {
  orchestrator: '#818cf8',
  backend: '#2dd4bf',
  frontend: '#f472b6',
  qa: '#fbbf24',
};

const ANIMATION_VARIANTS: Record<AgentState, { animate: { y?: number[]; x?: number[]; scale?: number[]; rotate?: number[]; opacity?: number[] } }> = {
  idle: { animate: { y: [0, -3, 0] } },
  thinking: { animate: { scale: [1, 1.02, 1] } },
  working: { animate: { rotate: [0, 1, -1, 0] } },
  waiting: { animate: { opacity: [1, 0.7, 1] } },
  success: { animate: { scale: [1, 1.1, 1] } },
  error: { animate: { x: [0, -3, 3, -3, 3, 0] } },
  communicating: { animate: { scale: [1, 1.05, 1] } },
  blocked: { animate: { x: [0, -2, 2, -2, 0] } },
};

function AgentSprite({ role, state }: { role: AgentRole; state: AgentState }) {
  const avatarUrl = ROLE_AVATARS[role];

  return (
    <motion.g
      className={`agent-sprite agent-${role}`}
      initial={false}
      animate={ANIMATION_VARIANTS[state]?.animate || {}}
      transition={{ duration: 0.5, repeat: state === 'idle' || state === 'thinking' ? Infinity : 0, repeatType: "reverse" }}
    >
      <image
        href={avatarUrl}
        x="-24"
        y="-24"
        width="48"
        height="48"
      />

      {state === 'success' && (
        <motion.g>
          <circle cx="18" cy="18" r="8" fill="#22c55e" />
          <path d="M 14 18 L 17 21 L 22 15" stroke="white" strokeWidth="2" fill="none" />
        </motion.g>
      )}
      {state === 'error' && (
        <motion.g>
          <circle cx="18" cy="18" r="8" fill="#ef4444" />
          <line x1="14" y1="14" x2="22" y2="22" stroke="white" strokeWidth="2" />
          <line x1="22" y1="14" x2="14" y2="22" stroke="white" strokeWidth="2" />
        </motion.g>
      )}
      {state === 'thinking' && (
        <g>
          <circle cx="20" cy="-16" r="2" fill="var(--color-muted)" />
          <circle cx="26" cy="-22" r="3" fill="var(--color-muted)" />
          <circle cx="34" cy="-26" r="4" fill="var(--color-muted)" />
        </g>
      )}
      {state === 'communicating' && (
        <g>
          <circle cx="20" cy="-12" r="2" fill="var(--color-primary)" />
          <circle cx="26" cy="-16" r="3" fill="var(--color-primary)" />
          <circle cx="34" cy="-18" r="4" fill="var(--color-primary)" />
        </g>
      )}
      {state === 'blocked' && (
        <g>
          <rect x="-18" y="-32" width="36" height="8" rx="2" fill="var(--color-destructive)" />
          <text x="0" y="-26" textAnchor="middle" fontSize="6" fill="white" fontWeight="bold">!</text>
        </g>
      )}
    </motion.g>
  );
}

function ProgressRing({ progress }: { progress: number }) {
  const radius = 26;
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
      <text textAnchor="middle" dy="4" fontSize="9" fill="var(--color-foreground)">
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
        filter: agent.state === 'error' ? 'brightness(0.8)' : 'brightness(1)',
        x: isRateLimited ? [0, -4, 4, -4, 4, -2, 2, 0] : undefined,
      }}
      transition={{
        duration: 0.3,
        x: isRateLimited ? { duration: 0.6, repeat: 2, ease: "easeInOut" } : undefined,
      }}
    >
      {isBlocked && (
        <motion.circle
          cx="0"
          cy="0"
          r="30"
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
        y={42}
        fontSize="11"
        fontWeight="600"
        fill="var(--color-foreground)"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{
          textShadow: '0 1px 3px rgba(0,0,0,0.8), 0 0 8px rgba(0,0,0,0.6)',
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
          y={56}
          fontSize="8"
          fill="var(--color-muted-foreground)"
          style={{
            textShadow: '0 1px 2px rgba(0,0,0,0.8)',
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
        y={68}
        fontSize="8"
        fill={agent.state === 'error' ? 'var(--color-destructive)' : 'var(--color-muted-foreground)'}
        style={{
          textTransform: 'capitalize',
          textShadow: '0 1px 2px rgba(0,0,0,0.8)',
          paintOrder: 'stroke fill'
        }}
      >
        {agent.state}
      </text>
    </motion.g>
  );
};
