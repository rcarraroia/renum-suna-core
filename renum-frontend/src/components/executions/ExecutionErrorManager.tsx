import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWebSocketChannels } from '../../hooks/useWebSocketChannels';
import { ExecutionErrorDisplay } from './ExecutionErrorDisplay';

interface ExecutionError {
  id: string;
  execution_id: string;
  team_id: string;
  error_type: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, any>;
  recoverable: boolean;
  retry_count: number;
  max_retries: number;
  agent_id?: string;
  step_name?: string;
  timestamp: string;
  stack_trace?: string;
  resolved: boolean;
}

interface ExecutionErrorManagerProps {
  executionId?: string;
  teamId?: string;
  userId?: string;
  showResolved?: boolean;
  maxErrors?: number;
  onRetryExecution?: (executionId: string) => Promise<void>;
  className?: string;
}

export const ExecutionErrorManager: React.FC<ExecutionErrorManagerProps> = ({
  executionId,
  teamId,
  userId,
  showResolved = false,
  maxErrors = 20,
  onRetryExecution,
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  const { subscribeToChannel, unsubscribeFromChannel } = useWebSocketChannels();
  
  const [errors, setErrors] = useState<ExecutionError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
  const [retryingExecutions, setRetryingExecutions] = useState<Set<string>>(new Set());

  // Carregar erros iniciais
  useEffect(() => {
    loadErrors();
  }, [executionId, teamId, userId, showResolved]);

  // Inscrever-se em atualizações via WebSocket
  useEffect(() => {
    if (!isConnected) return;

    const channels: string[] = [];
    
    if (executionId) {
      channels.push(`execution_${executionId}`);
    }
    
    if (teamId) {
      channels.push(`team_${teamId}`);
    }
    
    if (userId) {
      channels.push(`user_${userId}`);
    }

    const handleErrorUpdate = (data: any) => {
      if (data.type === 'execution_error') {
        addOrUpdateError(data.error);
      } else if (data.type === 'execution_retry_scheduled') {
        handleRetryScheduled(data);
      } else if (data.type === 'execution_failed_final') {
        handleFinalFailure(data);
      }
    };

    channels.forEach(channel => {
      subscribeToChannel(channel, handleErrorUpdate);
    });

    return () => {
      channels.forEach(channel => {
        unsubscribeFromChannel(channel);
      });
    };
  }, [isConnected, executionId, teamId, userId, subscribeToChannel, unsubscribeFromChannel]);

  const loadErrors = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (executionId) params.append('execution_id', executionId);
      if (teamId) params.append('team_id', teamId);
      if (userId) params.append('user_id', userId);
      if (!showResolved) params.append('resolved', 'false');
      params.append('limit', maxErrors.toString());

      const response = await fetch(`/api/v1/execution-errors?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Erro ao carregar erros: ${response.statusText}`);
      }

      const data = await response.json();
      setErrors(data.errors || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      console.error('Erro ao carregar erros de execução:', err);
    } finally {
      setLoading(false);
    }
  };

  const addOrUpdateError = (newError: ExecutionError) => {
    setErrors(prev => {
      const existingIndex = prev.findIndex(e => e.id === newError.id);
      
      if (existingIndex >= 0) {
        // Atualizar erro existente
        const updated = [...prev];
        updated[existingIndex] = newError;
        return updated;
      } else {
        // Adicionar novo erro
        const newErrors = [newError, ...prev];
        return newErrors.slice(0, maxErrors);
      }
    });
  };

  const handleRetryScheduled = (data: any) => {
    // Atualizar status de retry
    setErrors(prev => 
      prev.map(error => 
        error.execution_id === data.execution_id
          ? { ...error, retry_count: data.retry_count }
          : error
      )
    );
  };

  const handleFinalFailure = (data: any) => {
    // Marcar como falha final
    setErrors(prev => 
      prev.map(error => 
        error.execution_id === data.execution_id
          ? { ...error, resolved: true }
          : error
      )
    );
  };

  const handleRetry = async (error: ExecutionError) => {
    if (!onRetryExecution) return;

    try {
      setRetryingExecutions(prev => new Set([...prev, error.execution_id]));
      await onRetryExecution(error.execution_id);
    } catch (err) {
      console.error('Erro ao tentar novamente:', err);
      // Aqui você poderia mostrar uma notificação de erro
    } finally {
      setRetryingExecutions(prev => {
        const newSet = new Set(prev);
        newSet.delete(error.execution_id);
        return newSet;
      });
    }
  };

  const handleDismissError = async (errorId: string) => {
    try {
      const response = await fetch(`/api/v1/execution-errors/${errorId}/dismiss`, {
        method: 'PATCH'
      });

      if (response.ok) {
        setErrors(prev => prev.filter(e => e.id !== errorId));
      }
    } catch (err) {
      console.error('Erro ao descartar erro:', err);
    }
  };

  const getFilteredErrors = () => {
    let filtered = errors;

    if (!showResolved) {
      filtered = filtered.filter(e => !e.resolved);
    }

    if (filter !== 'all') {
      filtered = filtered.filter(e => e.severity === filter);
    }

    return filtered;
  };

  const getErrorCountBySeverity = (severity: string) => {
    return errors.filter(e => e.severity === severity && (!e.resolved || showResolved)).length;
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando erros...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800 font-medium">Erro ao carregar</span>
          </div>
          <button
            onClick={loadErrors}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Tentar novamente
          </button>
        </div>
        <p className="text-red-700 mt-1">{error}</p>
      </div>
    );
  }

  const filteredErrors = getFilteredErrors();

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Erros de Execução
            {filteredErrors.length > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                {filteredErrors.length}
              </span>
            )}
          </h3>
          
          <div className="flex items-center space-x-4">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Conectado' : 'Desconectado'}
            </span>
            
            <button
              onClick={loadErrors}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-red-600">{getErrorCountBySeverity('critical')}</div>
            <div className="text-xs text-gray-600">Críticos</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-orange-600">{getErrorCountBySeverity('high')}</div>
            <div className="text-xs text-gray-600">Altos</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-yellow-600">{getErrorCountBySeverity('medium')}</div>
            <div className="text-xs text-gray-600">Médios</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-blue-600">{getErrorCountBySeverity('low')}</div>
            <div className="text-xs text-gray-600">Baixos</div>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="px-6 py-3 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">Filtrar por severidade:</span>
          <div className="flex space-x-2">
            {[
              { key: 'all', label: 'Todos', count: filteredErrors.length },
              { key: 'critical', label: 'Críticos', count: getErrorCountBySeverity('critical') },
              { key: 'high', label: 'Altos', count: getErrorCountBySeverity('high') },
              { key: 'medium', label: 'Médios', count: getErrorCountBySeverity('medium') },
              { key: 'low', label: 'Baixos', count: getErrorCountBySeverity('low') }
            ].map((filterOption) => (
              <button
                key={filterOption.key}
                onClick={() => setFilter(filterOption.key as any)}
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  filter === filterOption.key
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {filterOption.label}
                {filterOption.count > 0 && (
                  <span className="ml-1">({filterOption.count})</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Lista de erros */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {filteredErrors.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhum erro encontrado
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {filter === 'all' 
                ? 'Não há erros de execução no momento.'
                : `Não há erros de severidade ${filter}.`
              }
            </p>
          </div>
        ) : (
          filteredErrors.map((executionError) => (
            <div key={executionError.id} className="p-6">
              <ExecutionErrorDisplay
                error={executionError}
                executionId={executionError.execution_id}
                onRetry={executionError.recoverable && !retryingExecutions.has(executionError.execution_id) 
                  ? () => handleRetry(executionError) 
                  : undefined
                }
                onDismiss={() => handleDismissError(executionError.id)}
                showStackTrace={true}
              />
              
              {retryingExecutions.has(executionError.execution_id) && (
                <div className="mt-3 bg-blue-50 border border-blue-200 rounded p-3">
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                    <span className="text-sm text-blue-800">
                      Tentando executar novamente...
                    </span>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};