import type { Agent } from '../types/agent';

interface TaskPanelProps {
  ticketId?: string;
  agents: Agent[];
}

const STATE_COLORS: Record<string, string> = {
  idle: '#888',
  thinking: '#f0ad4e',
  working: '#4A90D9',
  waiting: '#17a2b8',
  success: '#28a745',
  error: '#dc3545',
};

const STATE_ICONS: Record<string, string> = {
  idle: '○',
  thinking: '◐',
  working: '◉',
  waiting: '⧖',
  success: '✓',
  error: '✗',
};

export const TaskPanel: React.FC<TaskPanelProps> = ({ ticketId, agents }) => {
  return (
    <div className="task-panel">
      <div className="task-panel-header">
        <h3>Tasks</h3>
        {ticketId && <span className="ticket-badge">{ticketId}</span>}
      </div>
      <div className="task-list">
        {agents.map((agent) => (
          <div key={agent.id} className="task-item">
            <span className="task-icon" style={{ color: STATE_COLORS[agent.state] }}>
              {STATE_ICONS[agent.state]}
            </span>
            <span className="task-name">{agent.name}</span>
            {agent.task && <span className="task-desc">{agent.task}</span>}
          </div>
        ))}
      </div>
    </div>
  );
};
