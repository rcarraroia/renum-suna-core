/**
 * Componente para exibir o status da conexão WebSocket
 */

import React from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

/**
 * Propriedades do componente WebSocketStatus
 */
interface WebSocketStatusProps {
  showReconnectButton?: boolean;
  showStatusText?: boolean;
  className?: string;
}

/**
 * Componente para exibir o status da conexão WebSocket
 */
const WebSocketStatus: React.FC<WebSocketStatusProps> = ({
  showReconnectButton = true,
  showStatusText = true,
  className = '',
}) => {
  const { status, reconnect, isConnected } = useWebSocketContext();

  // Define a cor do indicador de status
  const getStatusColor = () => {
    switch (status) {
      case WebSocketConnectionStatus.CONNECTED:
        return 'bg-green-500';
      case WebSocketConnectionStatus.CONNECTING:
      case WebSocketConnectionStatus.RECONNECTING:
        return 'bg-yellow-500';
      case WebSocketConnectionStatus.DISCONNECTED:
      case WebSocketConnectionStatus.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  // Define o texto de status
  const getStatusText = () => {
    switch (status) {
      case WebSocketConnectionStatus.CONNECTED:
        return 'Conectado';
      case WebSocketConnectionStatus.CONNECTING:
        return 'Conectando...';
      case WebSocketConnectionStatus.RECONNECTING:
        return 'Reconectando...';
      case WebSocketConnectionStatus.DISCONNECTED:
        return 'Desconectado';
      case WebSocketConnectionStatus.ERROR:
        return 'Erro';
      default:
        return 'Desconhecido';
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      {/* Indicador de status */}
      <div
        className={`h-3 w-3 rounded-full ${getStatusColor()} mr-2`}
        title={getStatusText()}
      />

      {/* Texto de status */}
      {showStatusText && (
        <span className="text-sm mr-2">{getStatusText()}</span>
      )}

      {/* Botão de reconexão */}
      {showReconnectButton && !isConnected && (
        <button
          onClick={reconnect}
          className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          title="Reconectar"
        >
          Reconectar
        </button>
      )}
    </div>
  );
};

export default WebSocketStatus;