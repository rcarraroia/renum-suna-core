import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { useWebSocketChannels } from './useWebSocketChannels';

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

interface ErrorStatistics {
  total_errors: number;
  errors_by_type: Record<string, number>;
  errors_by_severity: Record<string, number>;
  recovery_rate: number;
  most_common_errors: Array<{
    error_type: string;
    count: number;
    percentage: number;
  }>;
}

interface UseExecutionErrorsOptions {
  executionId?: string;
  teamId?: string;
  userId?: string;
  autoSubscribe?: boolean;
  includeResolved?: boolean;
  maxErrors?: number;
}

interface UseExecutionErrorsReturn {
  errors: ExecutionError[];
  errorsByExecution: Record<string, ExecutionError[]>;
  criticalErrors: ExecutionError[];
  recoverableErrors: ExecutionError[];
  statistics: ErrorStatistics | null;
  isLoading: boolean;
  error: string | null;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  retryExecution: (executionId: string) => Promise<boolean>;
  dismissError: (errorId: string) => Promise<boolean>;
  resolveError: (errorId: string) => Promise<boolean>;
  refreshErrors: () => Promise<void>;
  getErrorHistory: (executionId: string) => Promise<ExecutionError[]>;
  clearError: () => void;
}

export const useExecutionErrors = (
  options: UseExecutionErrorsOptions = {}
): UseExecutionErrorsReturn => {
  const {
    executionId,
    teamId,
    userId,
    autoSubscribe = true,
    includeResolved = false,
    maxErrors = 50
  } = options;

  const { isConnected } = useWebSocket();
  const { subscribeToChannel, unsubscribeFromChannel } = useWebSocketChannels();

  const [errors, setErrors] = useState<ExecutionError[]>([]);
  const [statistics, setStatistics] = useState<ErrorStatistics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscribedChannels, setSubscribedChannels] = useState<Set<string>>(new Set());

  // Filtrar erros por categoria
  const errorsByExecution = errors.reduce((acc, error) => {
    if (!acc[error.execution_id]) {
      acc[error.execution_id] = [];
    }
    acc[error.execution_id].push(error);
    return acc;
  }, {} as Record<string, ExecutionError[]>);

  const criticalErrors = errors.filter(e => 
    e.severity === 'critical' && (!e.resolved || includeResolved)
  );

  const recoverableErrors = errors.filter(e => 
    e.recoverable && e.retry_count < e.max_retries && (!e.resolved || includeResolved)
  );

  // Manipular atualizações de erro via WebSocket
  const handleErrorUpdate = useCallback((data: any) => {
    if (data.type === 'execution_error') {
      setErrors(prev => {
        const existingIndex = prev.findIndex(e => e.id === data.error.id);
        
        if (existingIndex >= 0) {
          // Atualizar erro existente
          const updated = [...prev];
          updated[existingIndex] = data.error;
          return updated;
        } else {
          // Adicionar novo erro
          const newErrors = [data.error, ...prev];
          return newErrors.slice(0, maxErrors);
        }
      });
    } else if (data.type === 'execution_retry_scheduled') {
      setErrors(prev => 
        prev.map(error => 
          error.execution_id === data.execution_id
            ? { ...error, retry_count: data.retry_count }
            : error
        )
      );
    } else if (data.type === 'execution_failed_final') {
      setErrors(prev => 
        prev.map(error => 
          error.execution_id === data.execution_id
            ? { ...error, resolved: true }
            : error
        )
      );
    } else if (data.type === 'error_resolved') {
      setErrors(prev => 
        prev.map(error => 
          error.id === data.error_id
            ? { ...error, resolved: true }
            : error
        )
      );
    }
  }, [maxErrors]);

  // Inscrever-se em canal
  const subscribe = useCallback((channel: string) => {
    if (!isConnected || subscribedChannels.has(channel)) return;

    subscribeToChannel(channel, handleErrorUpdate);
    setSubscribedChannels(prev => new Set([...prev, channel]));
  }, [isConnected, subscribedChannels, subscribeToChannel, handleErrorUpdate]);

  // Desinscrever-se de canal
  const unsubscribe = useCallback((channel: string) => {
    if (!subscribedChannels.has(channel)) return;

    unsubscribeFromChannel(channel);
    setSubscribedChannels(prev => {
      const newSet = new Set(prev);
      newSet.delete(channel);
      return newSet;
    });
  }, [subscribedChannels, unsubscribeFromChannel]);

  // Carregar erros da API
  const refreshErrors = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (executionId) params.append('execution_id', executionId);
      if (teamId) params.append('team_id', teamId);
      if (userId) params.append('user_id', userId);
      if (!includeResolved) params.append('resolved', 'false');
      params.append('limit', maxErrors.toString());

      const response = await fetch(`/api/v1/execution-errors?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Erro ao carregar erros: ${response.statusText}`);
      }

      const data = await response.json();
      setErrors(data.errors || []);
      
      // Carregar estatísticas se não há filtros específicos
      if (!executionId && !userId) {
        await loadStatistics();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      console.error('Erro ao carregar erros de execução:', err);
    } finally {
      setIsLoading(false);
    }
  }, [executionId, teamId, userId, includeResolved, maxErrors]);

  // Carregar estatísticas
  const loadStatistics = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (teamId) params.append('team_id', teamId);

      const response = await fetch(`/api/v1/execution-errors/statistics?${params.toString()}`);
      
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (err) {
      console.error('Erro ao carregar estatísticas:', err);
    }
  }, [teamId]);

  // Tentar execução novamente
  const retryExecution = useCallback(async (executionId: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/v1/executions/${executionId}/retry`, {
        method: 'POST'
      });

      if (response.ok) {
        // Atualizar erros relacionados
        setErrors(prev => 
          prev.map(error => 
            error.execution_id === executionId
              ? { ...error, retry_count: error.retry_count + 1 }
              : error
          )
        );
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Erro ao tentar execução novamente:', err);
      return false;
    }
  }, []);

  // Descartar erro
  const dismissError = useCallback(async (errorId: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/v1/execution-errors/${errorId}/dismiss`, {
        method: 'PATCH'
      });

      if (response.ok) {
        setErrors(prev => prev.filter(e => e.id !== errorId));
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Erro ao descartar erro:', err);
      return false;
    }
  }, []);

  // Resolver erro
  const resolveError = useCallback(async (errorId: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/v1/execution-errors/${errorId}/resolve`, {
        method: 'PATCH'
      });

      if (response.ok) {
        setErrors(prev => 
          prev.map(error => 
            error.id === errorId
              ? { ...error, resolved: true }
              : error
          )
        );
        return true;
      }
      
      return false;
    } catch (err) {
      console.error('Erro ao resolver erro:', err);
      return false;
    }
  }, []);

  // Obter histórico de erros
  const getErrorHistory = useCallback(async (executionId: string): Promise<ExecutionError[]> => {
    try {
      const response = await fetch(`/api/v1/executions/${executionId}/error-history`);
      
      if (response.ok) {
        const data = await response.json();
        return data.errors || [];
      }
      
      return [];
    } catch (err) {
      console.error('Erro ao carregar histórico de erros:', err);
      return [];
    }
  }, []);

  // Limpar erro
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-inscrição
  useEffect(() => {
    if (!autoSubscribe || !isConnected) return;

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

    channels.forEach(channel => subscribe(channel));

    return () => {
      channels.forEach(channel => unsubscribe(channel));
    };
  }, [autoSubscribe, isConnected, executionId, teamId, userId, subscribe, unsubscribe]);

  // Carregar dados iniciais
  useEffect(() => {
    if (executionId || teamId || userId) {
      refreshErrors();
    }
  }, [executionId, teamId, userId, refreshErrors]);

  // Reinscrever-se após reconexão
  useEffect(() => {
    if (isConnected && subscribedChannels.size > 0) {
      subscribedChannels.forEach(channel => {
        subscribeToChannel(channel, handleErrorUpdate);
      });
    }
  }, [isConnected, subscribedChannels, subscribeToChannel, handleErrorUpdate]);

  return {
    errors,
    errorsByExecution,
    criticalErrors,
    recoverableErrors,
    statistics,
    isLoading,
    error,
    subscribe,
    unsubscribe,
    retryExecution,
    dismissError,
    resolveError,
    refreshErrors,
    getErrorHistory,
    clearError
  };
};