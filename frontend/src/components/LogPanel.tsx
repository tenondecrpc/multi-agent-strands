import { useEffect, useRef } from 'react';
import type { AgentLog } from '../types/agent';

interface LogPanelProps {
  logs: AgentLog[];
}

const LOG_COLORS: Record<string, string> = {
  info: '#4A90D9',
  warn: '#f0ad4e',
  error: '#dc3545',
};

export const LogPanel: React.FC<LogPanelProps> = ({ logs }) => {
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="log-panel">
      <div className="log-panel-header">
        <h3>Logs</h3>
        <span className="log-count">{logs.length}</span>
      </div>
      <div className="log-list">
        {logs.length === 0 ? (
          <div className="log-empty">No logs yet</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className={`log-entry log-${log.level}`}>
              <span className="log-time">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="log-agent">[{log.agent_id}]</span>
              <span className="log-message" style={{ color: LOG_COLORS[log.level] }}>
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};
