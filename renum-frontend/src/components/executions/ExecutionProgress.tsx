/**
 * Componente para exibir o progresso de execução em tempo real
 */

import React, { useState, useEffect } from 'react';
import { useExecutionMonitor } from '../../hooks/useExecutionMonitor';

interface ExecutionProgressProps {
  executionId: string;
  teamId?: string;
  showDetails?: boolean;
  className?: string;
}

interface ExecutionStep {
  agent_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  step_order: number;
  result?: any;
  error?: string;
  started_at?: string;
  completed_at?: string;
}

/**
 * Componente para exibir o progresso de execução em tempo real
 */
const ExecutionProgress: React.FC<ExecutionProgressProps> = ({
  executionId,
  teamId,
  showDetails = true,
  className = '',
}) => {
  const {
    executionUpdate,
    isRunning,
    isCompleted,
    isFailed,
    isQueued,
    progress,
    result,
    error,
  } = useExecutionMonitor(executionId, {
    autoSubscribe: true,
  });

  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [currentStep, setCurrentStep] = useState<string | null>(null);

  // Atualiza os passos com base nas atualizações de execução
  useEffect(() => {
    if (executionUpdate?.current_step) {
      setCurrentStep(executionUpdate.current_step);
    }
  }, [executionUpdate]);

  // Define a cor do status
  const getStatusColor = () => {
    if (isCompleted) return 'text-green-600';
    if (isRunning) return 'text-blue-600';
    if (isFailed) return 'text-red-600';
    if (isQueued) return 'text-yellow-600';
    return 'text-gray-600';
  };

  // Define o texto do status
  const getStatusText = () => {
    if (isCompleted) return 'Concluído';
    if (isRunning) return 'Em execução';
    if (isFailed) return 'Falhou';
    if (isQueued) return 'Na fila';
    return 'Desconhecido';
  };

  // Define o ícone do status
  const getStatusIcon = () => {
    const iconClass = `h-5 w-5 ${getStatusColor()}`;
    
    if (isCompleted) {
      return (
        <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (isRunning) {
      return (
        <svg className={`${iconClass} animate-spin`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      );
    }
    
    if (isFailed) {
      return (
        <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      );
    }
    
    if (isQueued) {
      return (
        <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      );
    }
    
    return (
      <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
      </svg>
    );
  };

  // Formata a duração
  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diffInSeconds = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds}s`;
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      const seconds = diffInSeconds % 60;
      return `${minutes}m ${seconds}s`;
    } else {
      const hours = Math.floor(diffInSeconds / 3600);
      const minutes = Math.floor((diffInSeconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Execução {executionId.slice(0, 8)}...
            </h2>
            <p className={`text-sm ${getStatusColor()}`}>
              {getStatusText()}
            </p>
          </div>
        </div>
        
        {teamId && (
          <span className="text-sm text-gray-500">
            Equipe: {teamId}
          </span>
        )}
      </div>

      {/* Barra de progresso */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Progresso</span>
          <span className="text-sm font-medium text-gray-700">{Math.round(progress)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${
              isCompleted ? 'bg-green-500' : 
              isFailed ? 'bg-red-500' : 
              'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Etapa atual */}
      {currentStep && isRunning && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <svg className="h-4 w-4 text-blue-500 animate-pulse" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium text-blue-800">Etapa atual:</span>
          </div>
          <p className="text-sm text-blue-700 mt-1">{currentStep}</p>
        </div>
      )}

      {/* Resultado */}
      {isCompleted && result && showDetails && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="text-sm font-medium text-green-800 mb-2">Resultado</h3>
          <div className="text-sm text-green-700 bg-white p-3 rounded border max-h-40 overflow-auto">
            <pre className="whitespace-pre-wrap">
              {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Erro */}
      {isFailed && error && showDetails && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h3 className="text-sm font-medium text-red-800 mb-2">Erro</h3>
          <div className="text-sm text-red-700 bg-white p-3 rounded border max-h-40 overflow-auto">
            <pre className="whitespace-pre-wrap">{error}</pre>
          </div>
        </div>
      )}

      {/* Informações adicionais */}
      {showDetails && executionUpdate && (
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">ID da Execução:</span>
              <p className="text-gray-600 font-mono">{executionId}</p>
            </div>
            
            {executionUpdate.team_id && (
              <div>
                <span className="font-medium text-gray-700">ID da Equipe:</span>
                <p className="text-gray-600 font-mono">{executionUpdate.team_id}</p>
              </div>
            )}
            
            {executionUpdate.updated_at && (
              <div>
                <span className="font-medium text-gray-700">Última Atualização:</span>
                <p className="text-gray-600">
                  {new Date(executionUpdate.updated_at).toLocaleString()}
                </p>
              </div>
            )}
            
            <div>
              <span className="font-medium text-gray-700">Status:</span>
              <p className={`${getStatusColor()}`}>{executionUpdate.status}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionProgress;