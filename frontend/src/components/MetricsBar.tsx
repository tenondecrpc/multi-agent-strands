import type { SessionMetrics } from '../types/agent';

interface MetricsBarProps {
  metrics: SessionMetrics;
  isConnected: boolean;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ metrics, isConnected }) => {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  };

  return (
    <div className="metrics-bar">
      <div className="metric">
        <span className="metric-label">Tokens</span>
        <span className="metric-value">{formatTokens(metrics.tokens_used)}</span>
      </div>
      <div className="metric">
        <span className="metric-label">Time</span>
        <span className="metric-value">{formatDuration(metrics.duration_seconds)}</span>
      </div>
      <div className="metric">
        <span className="metric-label">Files</span>
        <span className="metric-value">{metrics.files_created}</span>
      </div>
      <div className="metric">
        <span className="metric-label">Tests</span>
        <span className="metric-value">
          {metrics.tests_passed === null ? (
            <span className="tests-pending">—</span>
          ) : metrics.tests_passed ? (
            <span className="tests-passed">✓</span>
          ) : (
            <span className="tests-failed">✗</span>
          )}
        </span>
      </div>
      <div className="metric connection-status">
        <span className="metric-label">Status</span>
        <span className={`metric-value ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>
    </div>
  );
};
