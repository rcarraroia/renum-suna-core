/**
 * Hook para usar o serviço WebSocket
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketService, createWebSocketService } from '../services/websocket-service';
import {
  WebSocketMessage,
  WebSocketMessageType,
  WebSocketConnectionStatus,
  WebSocketConnectionOptions,
  WebSocketSubscriptionOptions,
} from '../types/websocket';

/**
 * Opções do hook useWebSocket
 */
export interface UseWebSocketOptions extends Omit<WebSocketConnectionOptions, 'onOpen' | 'onClose' | 'onError' | 'onMessage'> {
  autoConnect?: boolean;
}

/**
 * Hook para usar o serviço WebSocket
 * @param options Opções de conexão
 * @returns Objeto com o serviço WebSocket e funções auxiliares
 */
export function useWebSocket(options: UseWebSocketOptions) {
  const [status, setStatus] = useState<WebSocketConnectionStatus>(WebSocketConnectionStatus.DISCONNECTED);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const serviceRef = useRef<WebSocketService | null>(null);

  // Inicializa o serviço WebSocket
  useEffect(() => {
    const service = createWebSocketService({
      ...options,
      onOpen: (event) => {
        setStatus(WebSocketConnectionStatus.CONNECTED);
        setError(null);
      },
      onClose: (event) => {
        setStatus(WebSocketConnectionStatus.DISCONNECTED);
        if (event.code !== 1000) {
          setError(new Error(`WebSocket closed: ${event.code} ${event.reason}`));
        }
      },
      onError: (event) => {
        setStatus(WebSocketConnectionStatus.ERROR);
        setError(new Error('WebSocket error'));
      },
      onMessage: (message) => {
        setLastMessage(message);
      },
    });

    serviceRef.current = service;

    // Conecta automaticamente se necessário
    if (options.autoConnect !== false) {
      service.connect();
    }

    // Limpa o serviço ao desmontar
    return () => {
      service.disconnect();
    };
  }, [options.url, options.token]); // Recria o serviço apenas se a URL ou o token mudarem

  // Função para conectar
  const connect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.connect();
    }
  }, []);

  // Função para desconectar
  const disconnect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.disconnect();
    }
  }, []);

  // Função para reconectar
  const reconnect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.reconnect();
    }
  }, []);

  // Função para assinar um canal
  const subscribe = useCallback((options: WebSocketSubscriptionOptions) => {
    if (serviceRef.current) {
      return serviceRef.current.subscribe(options);
    }
    return () => {};
  }, []);

  // Função para cancelar a assinatura de um canal
  const unsubscribe = useCallback((channel: string, handler?: (message: WebSocketMessage) => void) => {
    if (serviceRef.current) {
      serviceRef.current.unsubscribe(channel, handler);
    }
  }, []);

  // Função para publicar uma mensagem
  const publish = useCallback((channel: string, message: any, requestId?: string) => {
    if (serviceRef.current) {
      serviceRef.current.publish({ channel, message, requestId });
    }
  }, []);

  // Função para enviar um comando
  const sendCommand = useCallback((command: string, params?: any) => {
    if (serviceRef.current) {
      serviceRef.current.sendCommand(command, params);
    }
  }, []);

  // Função para registrar um handler para um tipo de mensagem específico
  const on = useCallback((type: WebSocketMessageType | string, handler: (message: WebSocketMessage) => void) => {
    if (serviceRef.current) {
      return serviceRef.current.on(type, handler);
    }
    return () => {};
  }, []);

  // Função para obter mensagens em buffer
  const getBufferedMessages = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.getBufferedMessages();
    }
  }, []);

  // Função para limpar mensagens em buffer
  const clearBufferedMessages = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.clearBufferedMessages();
    }
  }, []);

  // Função para resetar o circuit breaker
  const resetCircuitBreaker = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.resetCircuitBreaker();
    }
  }, []);

  return {
    service: serviceRef.current,
    status,
    lastMessage,
    error,
    connect,
    disconnect,
    reconnect,
    subscribe,
    unsubscribe,
    publish,
    sendCommand,
    on,
    getBufferedMessages,
    clearBufferedMessages,
    resetCircuitBreaker,
    isConnected: status === WebSocketConnectionStatus.CONNECTED,
  };
}