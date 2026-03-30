import { useEffect, useState } from 'react';
import { socket, connectSocket, disconnectSocket } from '../services/socket';

interface ConnectionStatusProps {
  onConnectedChange?: (connected: boolean) => void;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ onConnectedChange }) => {
  const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    connectSocket();

    const onConnect = () => {
      setIsConnected(true);
      onConnectedChange?.(true);
    };
    const onDisconnect = () => {
      setIsConnected(false);
      onConnectedChange?.(false);
    };

    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);

    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      disconnectSocket();
    };
  }, [onConnectedChange]);

  return (
    <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
      <span className="status-dot" />
      <span className="status-text">{isConnected ? 'Connected' : 'Disconnected'}</span>
    </div>
  );
};
