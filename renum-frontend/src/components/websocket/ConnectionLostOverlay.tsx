/**
 * Overlay para quando a conexão WebSocket estiver perdida
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

interface ConnectionLostOverlayProps {
  showAfterMs?: number;
  className?: string;
  children?: React.ReactNode;
}

/**
 * Overlay para quando a conexão WebSocket estiver perdida
 */
const ConnectionLostOverlay: React.FC<ConnectionLostOverlayProps> = ({
  showAfterMs = 10000,
  className = '',
  children,
}) => {
  const { status, reconnect } = useWebSocketContext();
  const [visible, setVisible] = useState(false);
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);
  const [disconnectedTime, setDisconnectedTime] = useState<number | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Monitora o status da conexão
  useEffect(() => {
    if (status === WebSocketConnectionStatus.DISCONNECTED || status === WebSocketConnectionStatus.ERROR) {
      // Registra o momento da desconexão
      if (disconnectedTime === null) {
        setDisconnectedTime(Date.now());
      }
      
      // Inicia o timer para mostrar o overlay
      if (!timer) {
        const newTimer = setTimeout(() => {
          setVisible(true);
        }, showAfterMs);
        
        setTimer(newTimer);
      }
    } else {
      // Limpa o timer e esconde o overlay
      if (timer) {
        clearTimeout(timer);
        setTimer(null);
      }
      
      setVisible(false);
      setDisconnectedTime(null);
      setReconnectAttempts(0);
    }
    
    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [status, showAfterMs]);

  // Tenta reconectar
  const handleReconnect = () => {
    setReconnectAttempts((prev) => prev + 1);
    reconnect();
  };

  // Calcula o tempo de desconexão
  const getDisconnectedTimeText = () => {
    if (!disconnectedTime) return '';
    
    const seconds = Math.floor((Date.now() - disconnectedTime) / 1000);
    
    if (seconds < 60) {
      return `${seconds} segundos`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      return `${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours} ${hours === 1 ? 'hora' : 'horas'} e ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`;
    }
  };

  if (!visible) {
    return <>{children}</>;
  }

  return (
    <div className={`fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center ${className}`}>
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
        <div className="flex items-center justify-center mb-4 text-red-500">
          <svg className="h-12 w-12" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        
        <h2 className="text-xl font-bold text-center mb-2">Conexão perdida</h2>
        
        <p className="text-gray-600 text-center mb-4">
          A conexão com o servidor foi perdida há {getDisconnectedTimeText()}. 
          Tentando reconectar automaticamente...
        </p>
        
        {reconnectAttempts > 0 && (
          <p className="text-sm text-gray-500 text-center mb-4">
            Tentativas de reconexão: {reconnectAttempts}
          </p>
        )}
        
        <div className="flex justify-center">
          <button
            onClick={handleReconnect}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            Tentar reconectar agora
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConnectionLostOverlay;