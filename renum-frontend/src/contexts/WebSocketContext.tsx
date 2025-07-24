/**
 * Contexto para o serviço WebSocket
 */

import React, { createContext, useContext, ReactNode, useMemo } from 'react';
import { useWebSocket, UseWebSocketOptions } from '../hooks/useWebSocket';
import {
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketConnectionStatus,
} from '../types/websocket';

/**
 * Tipo do contexto WebSocket
 */
interface WebSocketContextType {
  status: WebSocketConnectionStatus;
  lastMessage: WebSocketMessage | null;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  reconnect: () => void;
  subscribe: (channel: string, onMessage?: (message: WebSocketMessage) => void) => () => void;
  unsubscribe: (channel: string, handler?: (message: WebSocketMessage) => void) => void;
  publish: (channel: string, message: any, requestId?: string) => void;
  sendCommand: (command: string, params?: any) => void;
  on: (type: WebSocketMessageType | string, handler: (message: WebSocketMessage) => void) => () => void;
  getBufferedMessages: () => void;
  clearBufferedMessages: () => void;
  resetCircuitBreaker: () => void;
  isConnected: boolean;
}

/**
 * Propriedades do provedor WebSocket
 */
interface WebSocketProviderProps {
  children: ReactNode;
  options: UseWebSocketOptions;
}

// Cria o contexto
const WebSocketContext = createContext<WebSocketContextType | null>(null);

/**
 * Provedor do contexto WebSocket
 */
export function WebSocketProvider({ children, options }: WebSocketProviderProps) {
  const {
    status,
    lastMessage,
    error,
    connect,
    disconnect,
    reconnect,
    subscribe: subscribeToChannel,
    unsubscribe: unsubscribeFromChannel,
    publish: publishToChannel,
    sendCommand,
    on,
    getBufferedMessages,
    clearBufferedMessages,
    resetCircuitBreaker,
    isConnected,
  } = useWebSocket(options);

  // Simplifica a API de assinatura
  const subscribe = (channel: string, onMessage?: (message: WebSocketMessage) => void) => {
    return subscribeToChannel({ channel, onMessage });
  };

  // Simplifica a API de publicação
  const publish = (channel: string, message: any, requestId?: string) => {
    publishToChannel(channel, message, requestId);
  };

  // Memoriza o valor do contexto
  const value = useMemo(
    () => ({
      status,
      lastMessage,
      error,
      connect,
      disconnect,
      reconnect,
      subscribe,
      unsubscribe: unsubscribeFromChannel,
      publish,
      sendCommand,
      on,
      getBufferedMessages,
      clearBufferedMessages,
      resetCircuitBreaker,
      isConnected,
    }),
    [
      status,
      lastMessage,
      error,
      connect,
      disconnect,
      reconnect,
      subscribeToChannel,
      unsubscribeFromChannel,
      publishToChannel,
      sendCommand,
      on,
      getBufferedMessages,
      clearBufferedMessages,
      resetCircuitBreaker,
      isConnected,
    ]
  );

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}

/**
 * Hook para usar o contexto WebSocket
 * @returns Contexto WebSocket
 * @throws Error se usado fora de um WebSocketProvider
 */
export function useWebSocketContext(): WebSocketContextType {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
}