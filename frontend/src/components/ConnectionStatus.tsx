import { useEffect, useState } from 'react';
import { socket, connectSocket, disconnectSocket } from '../services/socket';

interface ConnectionStatusProps {
  onConnectedChange?: (connected: boolean) => void;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ onConnectedChange }) => {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [socketId, setSocketId] = useState<string | undefined>(socket.id);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[ConnectionStatus] Mounting, calling connectSocket()');
    connectSocket();

    const onConnect = () => {
      console.log('[ConnectionStatus] Socket connected!', socket.id);
      setIsConnected(true);
      setSocketId(socket.id);
      setError(null);
      onConnectedChange?.(true);
    };
    const onDisconnect = (reason: string) => {
      console.log('[ConnectionStatus] Socket disconnected:', reason);
      setIsConnected(false);
      setSocketId(undefined);
      onConnectedChange?.(false);
    };
    const onConnectError = (err: Error) => {
      console.error('[ConnectionStatus] Connection error:', err.message);
      setError(err.message);
    };

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    socket.on('connect_error', onConnectError);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      socket.off('connect_error', onConnectError);
      disconnectSocket();
    };
  }, [onConnectedChange]);

  return (
    <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot" />
      <span className="status-text">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
      {socketId && <span className="socket-id"> (SID: {socketId})</span>}
      {error && <span className="socket-error"> - {error}</span>}
    </div>
  );
};
