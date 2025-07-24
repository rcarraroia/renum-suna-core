/**
 * Indicador de status de conexão para o cabeçalho
 */

import React from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketConnectionStatus } from '../../types/websocket';

interface HeaderConnectionIndicatorProps {
  showText?: boolean;
  className?: string;
}

/**
 * Indicador de status de conexão para o cabeçalho
 */
const HeaderConnectionIndicator: React.FC<HeaderConnectionIndicatorProps> = ({
  showText = false,
  className = '',
}) => {
  const { status, reconnect } = useWebSocketContext();

  // Define a cor do indicador
  const getIndicatorColor = () => {
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

  // Define o texto do status
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

  // Define o ícone do status
  const getStatusIcon = () => {
    switch (status) {
      case WebSocketConnectionStatus.CONNECTED:
        return (
          <svg className="h-4 w-4 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5.05 3.636a1 1 0 010 1.414 7 7 0 000 9.9 1 1 0 11-1.414 1.414 9 9 0 010-12.728 1 1 0 011.414 0zm9.9 0a1 1 0 011.414 0 9 9 0 010 12.728 1 1 0 11-1.414-1.414 7 7 0 000-9.9 1 1 0 010-1.414zM7.879 6.464a1 1 0 010 1.414 3 3 0 000 4.243 1 1 0 11-1.414 1.414 5 5 0 010-7.07 1 1 0 011.414 0zm4.242 0a1 1 0 011.414 0 5 5 0 010 7.072 1 1 0 01-1.414-1.414 3 3 0 000-4.244 1 1 0 010-1.414zM10 9a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
          </svg>
        );
      case WebSocketConnectionStatus.CONNECTING:
      case WebSocketConnectionStatus.RECONNECTING:
        return (
          <svg className="h-4 w-4 text-yellow-500 animate-spin" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
          </svg>
        );
      case WebSocketConnectionStatus.DISCONNECTED:
      case WebSocketConnectionStatus.ERROR:
        return (
          <svg className="h-4 w-4 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd" />
            <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
          </svg>
        );
      default:
        return (
          <svg className="h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <div className={`flex items-center ${className}`}>
      <div className="flex items-center">
        <div className={`h-2 w-2 rounded-full ${getIndicatorColor()} mr-2`} />
        {getStatusIcon()}
        {showText && (
          <span className="ml-2 text-sm">{getStatusText()}</span>
        )}
      </div>
      
      {(status === WebSocketConnectionStatus.DISCONNECTED || status === WebSocketConnectionStatus.ERROR) && (
        <button
          onClick={reconnect}
          className="ml-2 text-xs text-blue-600 hover:text-blue-800"
          title="Reconectar"
        >
          Reconectar
        </button>
      )}
    </div>
  );
};

export default HeaderConnectionIndicator;