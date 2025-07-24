/**
 * Componente para monitorar execuções em tempo real
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketExecutionUpdate } from '../../types/websocket';

/**
 * Propriedades do componente ExecutionMonitor
 */
interface ExecutionMonitorProps {
  executionId: string;
  onUpdate?: (update: WebSocketExecutionUpdate) => void;
  showProgress?: boolean;
  showStatus?: boolean;
  className?: string;
}

/**
 * Componente para monitorar execuções em tempo real
 */
const ExecutionMonitor: React.FC<ExecutionMonitorProps> = ({
  executionId,
  onUpdate,
  showProgress = true,
  showStatus = true,
  className = '',
}) => {
  const { subscribe, unsubscribe, sendCommand } = useWebSocketContext();
  const [executionUpdate, setExecutionUpdate] = useState<WebSocketExecutionUpdate | null>(null);
  const [logs, setLogs] = useState<any[]>([]);

  // Inscreve-se para receber atualizações de execução
  useEffect(() => {
    const channel = `ws:execution:${executionId}`;
    
    const unsubscribeFunc = subscribe(channel, (message) => {
      if (message.type === WebSocketMessageType.EXECUTION_UPDATE && message.data) {
        const update = message.data as WebSocketExecutionUpdate;
        setExecutionUpdate(update);
        
        if (onUpdate) {
          onUpdate(update);
        }
      }
    });

    // Solicita logs iniciais
    sendCommand('get_logs', { limit: 100, offset: 0 });

    return () => {
      unsubscribe(channel);
    };
  }, [executionId, subscribe, unsubscribe, sendCommand, onUpdate]);

  // Define a cor do status
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      case 'queued':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  // Formata o status
  const formatStatus = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'Concluído';
      case 'running':
        return 'Em execução';
      case 'failed':
        return 'Falhou';
      case 'queued':
        return 'Na fila';
      default:
        return status || 'Desconhecido';
    }
  };

  // Solicita mais logs
  const loadMoreLogs = () => {
    sendCommand('get_logs', { limit: 100, offset: logs.length });
  };

  // Para a execução
  const stopExecution = () => {
    sendCommand('stop_execution');
  };

  if (!executionUpdate) {
    return (
      <div className={`flex items-center justify-center p-4 ${className}`}>
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2">Aguardando atualizações...</span>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {/* Status e progresso */}
      <div className="mb-4">
        {showStatus && (
          <div className="flex items-center mb-2">
            <span className="font-medium mr-2">Status:</span>
            <span className={`${getStatusColor(executionUpdate.status)}`}>
              {formatStatus(executionUpdate.status)}
            </span>
          </div>
        )}

        {showProgress && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">Progresso</span>
              <span className="text-sm font-medium">{Math.round(executionUpdate.progress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full"
                style={{ width: `${executionUpdate.progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Etapa atual */}
        {executionUpdate.current_step && (
          <div className="mt-2 text-sm text-gray-600">
            {executionUpdate.current_step}
          </div>
        )}
      </div>

      {/* Ações */}
      <div className="flex space-x-2 mb-4">
        {executionUpdate.status === 'running' && (
          <button
            onClick={stopExecution}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm"
          >
            Parar execução
          </button>
        )}
        <button
          onClick={loadMoreLogs}
          className="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors text-sm"
        >
          Carregar mais logs
        </button>
      </div>

      {/* Resultado ou erro */}
      {executionUpdate.status === 'completed' && executionUpdate.result && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
          <h3 className="font-medium text-green-800 mb-2">Resultado</h3>
          <pre className="text-sm bg-white p-2 rounded overflow-auto max-h-60">
            {typeof executionUpdate.result === 'string'
              ? executionUpdate.result
              : JSON.stringify(executionUpdate.result, null, 2)}
          </pre>
        </div>
      )}

      {executionUpdate.status === 'failed' && executionUpdate.error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded">
          <h3 className="font-medium text-red-800 mb-2">Erro</h3>
          <pre className="text-sm bg-white p-2 rounded overflow-auto max-h-60">
            {executionUpdate.error}
          </pre>
        </div>
      )}

      {/* Logs */}
      {logs.length > 0 && (
        <div className="mt-4">
          <h3 className="font-medium mb-2">Logs</h3>
          <div className="bg-gray-800 text-gray-200 p-4 rounded overflow-auto max-h-80">
            {logs.map((log, index) => (
              <div key={index} className="mb-1 text-sm font-mono">
                <span className="text-gray-400">[{log.timestamp}]</span>{' '}
                <span className={log.level === 'ERROR' ? 'text-red-400' : 'text-green-400'}>
                  {log.level}
                </span>
                : {log.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionMonitor;