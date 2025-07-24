/**
 * Componente para monitorar execuções de equipes em tempo real
 */

import React, { useEffect } from 'react';
import { useExecutionMonitor } from '../../hooks/useExecutionMonitor';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { WebSocketStatus, ConnectionLostBanner } from '../websocket';

interface TeamExecutionMonitorProps {
  executionId: string;
  teamId: string;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
  className?: string;
}

/**
 * Componente para monitorar execuções de equipes em tempo real
 */
const TeamExecutionMonitor: React.FC<TeamExecutionMonitorProps> = ({
  executionId,
  teamId,
  onComplete,
  onError,
  className = '',
}) => {
  const {
    executionUpdate,
    logs,
    isRunning,
    isCompleted,
    isFailed,
    progress,
    result,
    error,
    stopExecution,
    loadMoreLogs,
  } = useExecutionMonitor(executionId, {
    autoSubscribe: true,
    onComplete,
    onError,
  });

  // Integração com o sistema de notificações
  const { notifications } = useWebSocketNotifications({
    autoMarkAsRead: true,
  });

  // Efeito para mostrar notificações de conclusão/erro
  useEffect(() => {
    if (isCompleted && result) {
      console.log('Execução concluída com sucesso:', result);
    } else if (isFailed && error) {
      console.error('Execução falhou:', error);
    }
  }, [isCompleted, isFailed, result, error]);

  // Define a cor do status
  const getStatusColor = () => {
    if (isCompleted) return 'text-green-600';
    if (isRunning) return 'text-blue-600';
    if (isFailed) return 'text-red-600';
    return 'text-yellow-600'; // queued
  };

  // Formata o status
  const getStatusText = () => {
    if (isCompleted) return 'Concluído';
    if (isRunning) return 'Em execução';
    if (isFailed) return 'Falhou';
    return 'Na fila';
  };

  return (
    <div className={`${className}`}>
      {/* Banner de conexão perdida */}
      <ConnectionLostBanner />

      {/* Status da conexão WebSocket */}
      <div className="mb-4 flex justify-end">
        <WebSocketStatus showStatusText={true} />
      </div>

      {/* Informações da execução */}
      <div className="bg-white shadow rounded-lg p-4 mb-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">Execução da Equipe</h2>
          <span className={`px-2 py-1 rounded-full text-sm font-medium ${getStatusColor()} bg-opacity-10`}>
            {getStatusText()}
          </span>
        </div>

        {/* Progresso */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium">Progresso</span>
            <span className="text-sm font-medium">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Etapa atual */}
        {executionUpdate?.current_step && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-100 rounded">
            <h3 className="text-sm font-medium text-blue-800 mb-1">Etapa atual:</h3>
            <p className="text-sm text-blue-700">{executionUpdate.current_step}</p>
          </div>
        )}

        {/* Ações */}
        <div className="flex space-x-2">
          {isRunning && (
            <button
              onClick={stopExecution}
              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm"
            >
              Parar execução
            </button>
          )}
        </div>
      </div>

      {/* Resultado ou erro */}
      {isCompleted && result && (
        <div className="bg-white shadow rounded-lg p-4 mb-4">
          <h3 className="font-medium text-green-800 mb-2">Resultado</h3>
          <pre className="text-sm bg-green-50 p-3 rounded overflow-auto max-h-60 border border-green-100">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}

      {isFailed && error && (
        <div className="bg-white shadow rounded-lg p-4 mb-4">
          <h3 className="font-medium text-red-800 mb-2">Erro</h3>
          <pre className="text-sm bg-red-50 p-3 rounded overflow-auto max-h-60 border border-red-100">
            {error}
          </pre>
        </div>
      )}

      {/* Logs */}
      {logs.length > 0 && (
        <div className="bg-white shadow rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium">Logs</h3>
            <button
              onClick={loadMoreLogs}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Carregar mais
            </button>
          </div>
          <div className="bg-gray-800 text-gray-200 p-3 rounded overflow-auto max-h-80">
            {logs.map((log, index) => (
              <div key={index} className="mb-1 text-sm font-mono">
                <span className="text-gray-400">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                <span className={`${log.level === 'ERROR' ? 'text-red-400' : 'text-green-400'}`}>
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

export default TeamExecutionMonitor;