import type { Agent, AgentRole, AgentState } from "@/types/agent";

interface AgentFigureProps {
  agent: Agent;
}

const ROLE_COLORS: Record<AgentRole, string> = {
  orchestrator: '#6b7280', // gray-500
  architect: '#818cf8', // indigo-400
  backend: '#2dd4bf',   // teal-400
  frontend: '#f472b6',  // pink-400
  qa: '#fbbf24',        // amber-400
};

const ANIMATION_CLASS: Record<AgentState, string> = {
  idle: 'animate-bob',
  thinking: 'animate-pulse',
  working: 'animate-work',
  waiting: 'animate-wait',
  success: 'animate-bounce',
  error: 'animate-shake',
};

function AgentSprite({ role, state }: { role: AgentRole; state: AgentState }) {
  const color = ROLE_COLORS[role];

  return (
    <g className={`agent-sprite agent-${role}`}>
      <circle cx="0" cy="-20" r="25" fill={color} />
      <circle cx="-8" cy="-25" r="4" fill="var(--color-foreground)" />
      <circle cx="8" cy="-25" r="4" fill="var(--color-foreground)" />
      {state === 'success' && (
        <path d="M -8 -15 Q 0 -5 8 -15" stroke="var(--color-foreground)" strokeWidth="3" fill="none" />
      )}
      {state === 'error' && (
        <>
          <line x1="-5" y1="-30" x2="5" y2="-20" stroke="var(--color-background)" strokeWidth="2" />
          <line x1="5" y1="-30" x2="-5" y2="-20" stroke="var(--color-background)" strokeWidth="2" />
        </>
      )}
      {state === 'thinking' && (
        <g className="thought-bubble">
          <circle cx="30" cy="-45" r="5" fill="var(--color-muted)" />
          <circle cx="40" cy="-55" r="8" fill="var(--color-muted)" />
          <circle cx="55" cy="-60" r="12" fill="var(--color-muted)" />
        </g>
      )}
      {role === 'architect' && (
        <path d="M -15 -45 L 0 -55 L 15 -45 Z" fill={color} />
      )}
      {role === 'backend' && (
        <rect x="-20" y="-45" width="40" height="10" rx="2" fill={color} />
      )}
      {role === 'frontend' && (
        <circle cx="0" cy="-48" r="8" fill="none" stroke={color} strokeWidth="2" />
      )}
      {role === 'qa' && (
        <g transform="translate(15, -50)">
          <circle cx="0" cy="0" r="8" fill="none" stroke={color} strokeWidth="2" />
          <line x1="6" y1="6" x2="14" y2="14" stroke={color} strokeWidth="2" />
        </g>
      )}
    </g>
  );
}

function ProgressRing({ progress }: { progress: number }) {
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - progress);

  return (
    <g className="progress-ring" transform="translate(0, 20)">
      <circle cx="0" cy="0" r={radius} fill="none" stroke="var(--color-border)" strokeWidth="4" />
      <circle
        cx="0"
        cy="0"
        r={radius}
        fill="none"
        stroke="var(--color-primary)"
        strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90)"
      />
      <text textAnchor="middle" dy="4" fontSize="12" fill="var(--color-foreground)">
        {Math.round(progress * 100)}%
      </text>
    </g>
  );
}

export const AgentFigure: React.FC<AgentFigureProps> = ({ agent }) => {
  return (
    <g
      className={`agent-figure agent-${agent.role} ${ANIMATION_CLASS[agent.state]}`}
      transform="translate(0, 0)"
    >
      <AgentSprite role={agent.role} state={agent.state} />

      {agent.state === 'working' && agent.progress != null && <ProgressRing progress={agent.progress} />}

      <text className="agent-name" textAnchor="middle" y={50} fontSize="14" fontWeight="bold" fill="var(--color-foreground)">
        {agent.name}
      </text>
      {agent.task && (
        <text className="agent-task" textAnchor="middle" y={68} fontSize="10" fill="var(--color-muted-foreground)">
          {agent.task}
        </text>
      )}
      <text
        className="agent-state"
        textAnchor="middle"
        y={85}
        fontSize="9"
        fill={agent.state === 'error' ? 'var(--color-destructive)' : 'var(--color-muted-foreground)'}
      >
        {agent.state}
      </text>
    </g>
  );
};
