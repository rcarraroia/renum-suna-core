/**
 * Componente para exibir um banner de conexão perdida
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

/**
 * Propriedades do componente ConnectionLostBanner
 */
interface ConnectionLostBannerProps {
  className?: string;
  showAfterMs?: number;
}

/**
 * Componente para exibir um banner de conexão perdida
 */
const ConnectionLostBanner: React.FC<ConnectionLostBannerProps> = ({
  className = '',
  showAfterMs = 5000,
}) => {
  const { status, reconnect } = useWebSocketContext();
  const [visible, setVisible] = useState(false);
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);

  // Monitora o status da conexão
  useEffect(() => {
    if (status === WebSocketConnectionStatus.DISCONNECTED || status === WebSocketConnectionStatus.ERROR) {
      // Inicia o timer para mostrar o banner
      const newTimer = setTimeout(() => {
        setVisible(true);
      }, showAfterMs);
      
      setTimer(newTimer);
    } else {
      // Limpa o timer e esconde o banner
      if (timer) {
        clearTimeout(timer);
        setTimer(null);
      }
      
      setVisible(false);
    }
    
    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [status, showAfterMs]);

  if (!visible) {
    return null;
  }

  return (
    <div className={`fixed top-0 left-0 right-0 bg-red-500 text-white p-2 text-center z-50 ${className}`}>
      <div className="container mx-auto flex items-center justify-center">
        <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <span>Conexão perdida. Tentando reconectar...</span>
        <button
          onClick={reconnect}
          className="ml-4 px-3 py-1 bg-white text-red-500 rounded text-sm font-medium hover:bg-red-100 transition-colors"
        >
          Reconectar agora
        </button>
      </div>
    </div>
  );
};

export default ConnectionLostBanner;