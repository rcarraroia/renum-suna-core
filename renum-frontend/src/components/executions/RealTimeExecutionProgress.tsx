import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useExecutionMonitor } from '../../hooks/useExecutionMonitor';
import { ExecutionProgress } from './ExecutionProgress';

interface ExecutionUpdate {
  execution_id: string;
  status: 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
  current_step?: string;
  total_steps?: number;
  completed_steps?: number;
  error_message?: string;
  result?: any;
  updated_at: string;
}

interface RealTimeExecutionProgressProps {
  executionId: string;
  teamId?: string;
  onStatusChange?: (status: string) => void;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const RealTimeExecutionProgress: React.FC<RealTimeExecutionProgressProps> = ({
  executionId,
  teamId,
  onStatusChange,
  onComplete,
  onError,
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  const { 
    executionData, 
    isMonitoring, 
    startMonitoring, 
    stopMonitoring,
    error: monitorError 
  } = useExecutionMonitor(executionId);

  const [executionState, setExecutionState] = useState<ExecutionUpdate | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [connectionLost, setConnectionLost] = useState(false);

  // Iniciar monitoramento quando o componente monta
  useEffect(() => {
    if (executionId && isConnected) {
      startMonitoring();
      setConnectionLost(false);
    }

    return () => {
      stopMonitoring();
    };
  }, [executionId, isConnected, startMonitoring, stopMonitoring]);

  // Atualizar estado quando receber dados
  useEffect(() => {
    if (executionData) {
      setExecutionState(executionData);
      setLastUpdate(new Date());
      
      // Chamar callbacks apropriados
      if (onStatusChange) {
        onStatusChange(executionData.status);
      }
      
      if (executionData.status === 'completed' && onComplete) {
        onComplete(executionData.result);
      }
      
      if (executionData.status === 'failed' && onError && executionData.error_message) {
        onError(executionData.error_message);
      }
    }
  }, [executionData, onStatusChange, onComplete, onError]);

  // Detectar perda de conexão
  useEffect(() => {
    if (!isConnected && isMonitoring) {
      setConnectionLost(true);
    } else if (isConnected && connectionLost) {
      setConnectionLost(false);
      // Reiniciar monitoramento após reconexão
      startMonitoring();
    }
  }, [isConnected, isMonitoring, connectionLost, startMonitoring]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      case 'paused':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        );
      case 'completed':
        return (
          <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      case 'paused':
        return (
          <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const formatDuration = (startTime: string, endTime?: string) => {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (monitorError) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-red-800 font-medium">Erro no monitoramento</span>
        </div>
        <p className="text-red-700 mt-1">{monitorError}</p>
      </div>
    );
  }

  if (!executionState) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-600 mr-3"></div>
          <span className="text-gray-600">Carregando dados da execução...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header com status */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {getStatusIcon(executionState.status)}
            <span className={`ml-2 font-medium ${getStatusColor(executionState.status)}`}>
              {executionState.status.charAt(0).toUpperCase() + executionState.status.slice(1)}
            </span>
          </div>
          
          <div className="flex items-center text-sm text-gray-500">
            {connectionLost && (
              <span className="text-red-500 mr-3 flex items-center">
                <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
                Conexão perdida
              </span>
            )}
            
            {lastUpdate && (
              <span>
                Atualizado: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Conteúdo principal */}
      <div className="p-4">
        {/* Barra de progresso */}
        <ExecutionProgress
          progress={executionState.progress}
          status={executionState.status}
          currentStep={executionState.current_step}
          totalSteps={executionState.total_steps}
          completedSteps={executionState.completed_steps}
        />

        {/* Informações detalhadas */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Progresso</h4>
            <div className="text-sm text-gray-600">
              {executionState.completed_steps && executionState.total_steps ? (
                <p>{executionState.completed_steps} de {executionState.total_steps} etapas concluídas</p>
              ) : (
                <p>{executionState.progress}% concluído</p>
              )}
              
              {executionState.current_step && (
                <p className="mt-1">
                  <span className="font-medium">Etapa atual:</span> {executionState.current_step}
                </p>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Tempo</h4>
            <div className="text-sm text-gray-600">
              <p>
                <span className="font-medium">Duração:</span>{' '}
                {formatDuration(executionState.updated_at)}
              </p>
              <p className="mt-1">
                <span className="font-medium">Última atualização:</span>{' '}
                {new Date(executionState.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Mensagem de erro */}
        {executionState.status === 'failed' && executionState.error_message && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-red-800 mb-1">Erro na execução</h4>
            <p className="text-sm text-red-700">{executionState.error_message}</p>
          </div>
        )}

        {/* Resultado da execução */}
        {executionState.status === 'completed' && executionState.result && (
          <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-3">
            <h4 className="text-sm font-medium text-green-800 mb-1">Resultado</h4>
            <pre className="text-sm text-green-700 whitespace-pre-wrap">
              {typeof executionState.result === 'string' 
                ? executionState.result 
                : JSON.stringify(executionState.result, null, 2)
              }
            </pre>
          </div>
        )}
      </div>

      {/* Footer com indicador de conexão */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Execução ID: {executionId}</span>
          
          <div className="flex items-center">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};