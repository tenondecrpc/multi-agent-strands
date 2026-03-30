import { useState, useEffect } from 'react';
import { AgentCanvas } from './AgentCanvas';
import { TaskPanel } from './TaskPanel';
import { LogPanel } from './LogPanel';
import { MetricsBar } from './MetricsBar';
import { ConnectionStatus } from './ConnectionStatus';
import { useSocket } from '../hooks/useSocket';
import type { SessionMetrics } from '../types/agent';

export const Dashboard: React.FC = () => {
  const [ticket] = useState<string | undefined>();
  const [metrics, setMetrics] = useState<SessionMetrics>({
    tokens_used: 0,
    duration_seconds: 0,
    files_created: 0,
    tests_passed: null,
  });
  const [startTime] = useState(() => Date.now());

  const { isConnected, agents, logs, resetAgents } = useSocket({
    sessionId: null,
    onEvent: () => {},
  });

  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setMetrics((prev) => ({ ...prev, duration_seconds: elapsed }));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Multi-Agent Pipeline Dashboard</h1>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          {ticket && <span>Ticket: {ticket}</span>}
          <button onClick={resetAgents} style={{ padding: '4px 12px', cursor: 'pointer' }}>
            Reset
          </button>
          <ConnectionStatus />
        </div>
      </header>

      <div className="dashboard-content">
        <aside className="dashboard-sidebar">
          <TaskPanel ticketId={ticket} agents={agents} />
        </aside>

        <main className="dashboard-main">
          <AgentCanvas agents={agents} ticketId={ticket} />
        </main>

        <aside className="dashboard-logs">
          <LogPanel logs={logs} />
        </aside>
      </div>

      <footer className="dashboard-footer">
        <MetricsBar metrics={metrics} isConnected={isConnected} />
      </footer>
    </div>
  );
};
