/**
 * Hook para monitorar execuções em tempo real
 */

import { useState, useEffect, useCallback } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketExecutionUpdate } from '../types/websocket';

/**
 * Opções do hook useExecutionMonitor
 */
interface UseExecutionMonitorOptions {
  autoSubscribe?: boolean;
  onUpdate?: (update: WebSocketExecutionUpdate) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

/**
 * Hook para monitorar execuções em tempo real
 * @param executionId ID da execução
 * @param options Opções
 * @returns Objeto com dados da execução e funções auxiliares
 */
export function useExecutionMonitor(
  executionId: string,
  options: UseExecutionMonitorOptions = {}
) {
  const {
    autoSubscribe = true,
    onUpdate,
    onComplete,
    onError,
  } = options;

  const { subscribe, unsubscribe, sendCommand } = useWebSocketContext();
  const [executionUpdate, setExecutionUpdate] = useState<WebSocketExecutionUpdate | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [isSubscribed, setIsSubscribed] = useState(false);

  // Inscreve-se para receber atualizações de execução
  const subscribeToExecution = useCallback(() => {
    if (isSubscribed || !executionId) return;

    const channel = `ws:execution:${executionId}`;
    
    subscribe(channel, (message) => {
      if (message.type === WebSocketMessageType.EXECUTION_UPDATE && message.data) {
        const update = message.data as WebSocketExecutionUpdate;
        setExecutionUpdate(update);
        
        if (onUpdate) {
          onUpdate(update);
        }

        // Verifica se a execução foi concluída
        if (update.status === 'completed' && onComplete) {
          onComplete(update.result);
        }

        // Verifica se a execução falhou
        if (update.status === 'failed' && onError && update.error) {
          onError(update.error);
        }
      } else if (message.type === 'logs_response' && message.data) {
        setLogs((prev) => [...prev, ...message.data]);
      }
    });

    // Solicita logs iniciais
    sendCommand('get_logs', { execution_id: executionId, limit: 100, offset: 0 });

    setIsSubscribed(true);

    return () => {
      unsubscribe(channel);
      setIsSubscribed(false);
    };
  }, [executionId, subscribe, unsubscribe, sendCommand, onUpdate, onComplete, onError, isSubscribed]);

  // Cancela a inscrição
  const unsubscribeFromExecution = useCallback(() => {
    if (!isSubscribed || !executionId) return;

    const channel = `ws:execution:${executionId}`;
    unsubscribe(channel);
    setIsSubscribed(false);
  }, [executionId, unsubscribe, isSubscribed]);

  // Auto-inscrição
  useEffect(() => {
    if (autoSubscribe && executionId && !isSubscribed) {
      const unsubscribeFunc = subscribeToExecution();
      return unsubscribeFunc;
    }
    return undefined;
  }, [autoSubscribe, executionId, isSubscribed, subscribeToExecution]);

  // Solicita mais logs
  const loadMoreLogs = useCallback(() => {
    sendCommand('get_logs', { execution_id: executionId, limit: 100, offset: logs.length });
  }, [executionId, logs.length, sendCommand]);

  // Para a execução
  const stopExecution = useCallback(() => {
    sendCommand('stop_execution', { execution_id: executionId });
  }, [executionId, sendCommand]);

  return {
    executionUpdate,
    logs,
    isSubscribed,
    subscribeToExecution,
    unsubscribeFromExecution,
    loadMoreLogs,
    stopExecution,
    isRunning: executionUpdate?.status === 'running',
    isCompleted: executionUpdate?.status === 'completed',
    isFailed: executionUpdate?.status === 'failed',
    isQueued: executionUpdate?.status === 'queued',
    progress: executionUpdate?.progress || 0,
    result: executionUpdate?.result,
    error: executionUpdate?.error,
  };
}