/**
 * Componente de progresso de reconexão WebSocket
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

interface ReconnectionProgressProps {
  className?: string;
}

/**
 * Componente de progresso de reconexão WebSocket
 */
const ReconnectionProgress: React.FC<ReconnectionProgressProps> = ({
  className = '',
}) => {
  const { status } = useWebSocketContext();
  const [visible, setVisible] = useState(false);
  const [progress, setProgress] = useState(0);
  const [intervalId, setIntervalId] = useState<NodeJS.Timeout | null>(null);

  // Monitora o status da conexão
  useEffect(() => {
    if (status === WebSocketConnectionStatus.RECONNECTING) {
      setVisible(true);
      setProgress(0);
      
      // Inicia o progresso simulado
      if (!intervalId) {
        const id = setInterval(() => {
          setProgress((prev) => {
            // Limita o progresso a 95% para indicar que ainda está tentando
            return Math.min(prev + 1, 95);
          });
        }, 100);
        
        setIntervalId(id);
      }
    } else {
      // Se conectado, completa o progresso rapidamente
      if (status === WebSocketConnectionStatus.CONNECTED && visible) {
        setProgress(100);
        
        // Esconde após um breve momento
        const timer = setTimeout(() => {
          setVisible(false);
        }, 500);
        
        return () => clearTimeout(timer);
      } else {
        setVisible(false);
      }
      
      // Limpa o intervalo
      if (intervalId) {
        clearInterval(intervalId);
        setIntervalId(null);
      }
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [status, intervalId, visible]);

  if (!visible) {
    return null;
  }

  return (
    <div className={`fixed top-0 left-0 right-0 z-50 ${className}`}>
      <div className="h-1 bg-blue-100 overflow-hidden">
        <div
          className="h-full bg-blue-500 transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      {status === WebSocketConnectionStatus.RECONNECTING && (
        <div className="bg-blue-500 text-white text-xs text-center py-1">
          Reconectando ao servidor...
        </div>
      )}
    </div>
  );
};

export default ReconnectionProgress;