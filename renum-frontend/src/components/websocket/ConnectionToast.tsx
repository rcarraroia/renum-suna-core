/**
 * Componente de toast para notificações de estado da conexão WebSocket
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

interface ConnectionToastProps {
  autoHideDelay?: number;
  className?: string;
}

/**
 * Componente de toast para notificações de estado da conexão WebSocket
 */
const ConnectionToast: React.FC<ConnectionToastProps> = ({
  autoHideDelay = 5000,
  className = '',
}) => {
  const { status } = useWebSocketContext();
  const [visible, setVisible] = useState(false);
  const [lastStatus, setLastStatus] = useState<WebSocketConnectionStatus | null>(null);

  // Mostra o toast quando o status muda
  useEffect(() => {
    // Não mostra o toast na primeira renderização
    if (lastStatus === null) {
      setLastStatus(status);
      return;
    }

    // Mostra o toast apenas para mudanças de status relevantes
    if (
      (status === WebSocketConnectionStatus.CONNECTED && lastStatus !== WebSocketConnectionStatus.CONNECTED) ||
      (status === WebSocketConnectionStatus.DISCONNECTED && lastStatus === WebSocketConnectionStatus.CONNECTED) ||
      (status === WebSocketConnectionStatus.ERROR && lastStatus !== WebSocketConnectionStatus.ERROR)
    ) {
      setVisible(true);
      
      // Esconde o toast após um tempo
      const timer = setTimeout(() => {
        setVisible(false);
      }, autoHideDelay);
      
      return () => clearTimeout(timer);
    }
    
    setLastStatus(status);
  }, [status, lastStatus, autoHideDelay]);

  // Define a cor e o texto com base no status
  const getToastConfig = () => {
    switch (status) {
      case WebSocketConnectionStatus.CONNECTED:
        return {
          bgColor: 'bg-green-500',
          textColor: 'text-white',
          text: 'Conexão estabelecida',
          icon: (
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ),
        };
      case WebSocketConnectionStatus.DISCONNECTED:
        return {
          bgColor: 'bg-red-500',
          textColor: 'text-white',
          text: 'Conexão perdida',
          icon: (
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          ),
        };
      case WebSocketConnectionStatus.ERROR:
        return {
          bgColor: 'bg-red-500',
          textColor: 'text-white',
          text: 'Erro de conexão',
          icon: (
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ),
        };
      case WebSocketConnectionStatus.RECONNECTING:
        return {
          bgColor: 'bg-yellow-500',
          textColor: 'text-white',
          text: 'Reconectando...',
          icon: (
            <svg className="h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          ),
        };
      default:
        return {
          bgColor: 'bg-gray-500',
          textColor: 'text-white',
          text: 'Status desconhecido',
          icon: (
            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          ),
        };
    }
  };

  const { bgColor, textColor, text, icon } = getToastConfig();

  if (!visible) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-4 left-4 z-50 ${bgColor} ${textColor} rounded-lg shadow-lg p-4 flex items-center space-x-2 transition-all duration-300 ${className}`}
    >
      {icon}
      <span>{text}</span>
      <button
        onClick={() => setVisible(false)}
        className="ml-2 text-white opacity-70 hover:opacity-100"
      >
        <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  );
};

export default ConnectionToast;