import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { useWebSocketChannels } from './useWebSocketChannels';

interface ExecutionUpdate {
  execution_id: string;
  team_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step?: string;
  total_steps?: number;
  completed_steps?: number;
  current_agent?: string;
  total_agents?: number;
  completed_agents?: number;
  error_message?: string;
  result?: any;
  updated_at: string;
}

interface ExecutionSummary {
  id: string;
  team_id: string;
  team_name: string;
  status: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  created_by: string;
  error_message?: string;
  result?: any;
}

interface UseRealTimeExecutionsOptions {
  teamId?: string;
  userId?: string;
  autoSubscribe?: boolean;
  includeCompleted?: boolean;
  maxExecutions?: number;
}

interface UseRealTimeExecutionsReturn {
  executions: ExecutionSummary[];
  activeExecutions: ExecutionSummary[];
  completedExecutions: ExecutionSummary[];
  failedExecutions: ExecutionSummary[];
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  subscribe: (teamId: string) => void;
  unsubscribe: (teamId: string) => void;
  subscribeToExecution: (executionId: string) => void;
  unsubscribeFromExecution: (executionId: string) => void;
  refreshExecutions: () => Promise<void>;
  clearError: () => void;
}

export const useRealTimeExecutions = (
  options: UseRealTimeExecutionsOptions = {}
): UseRealTimeExecutionsReturn => {
  const {
    teamId,
    userId,
    autoSubscribe = true,
    includeCompleted = true,
    maxExecutions = 50
  } = options;

  const { isConnected } = useWebSocket();
  const { subscribeToChannel, unsubscribeFromChannel } = useWebSocketChannels();

  const [executions, setExecutions] = useState<ExecutionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subscribedTeams, setSubscribedTeams] = useState<Set<string>>(new Set());
  const [subscribedExecutions, setSubscribedExecutions] = useState<Set<string>>(new Set());

  // Filtrar execuções por status
  const activeExecutions = executions.filter(e => 
    ['pending', 'running'].includes(e.status)
  );
  
  const completedExecutions = executions.filter(e => 
    e.status === 'completed'
  );
  
  const failedExecutions = executions.filter(e => 
    ['failed', 'cancelled'].includes(e.status)
  );

  // Manipular atualizações de execução
  const handleExecutionUpdate = useCallback((data: ExecutionUpdate) => {
    setExecutions(prev => {
      const existingIndex = prev.findIndex(e => e.id === data.execution_id);
      
      const updatedExecution: ExecutionSummary = {
        id: data.execution_id,
        team_id: data.team_id,
        team_name: '', // Será preenchido pela API
        status: data.status,
        progress: data.progress,
        started_at: data.updated_at,
        completed_at: data.status === 'completed' ? data.updated_at : undefined,
        created_by: '', // Será preenchido pela API
        error_message: data.error_message,
        result: data.result
      };

      if (existingIndex >= 0) {
        // Atualizar execução existente
        const newExecutions = [...prev];
        newExecutions[existingIndex] = {
          ...newExecutions[existingIndex],
          ...updatedExecution
        };
        return newExecutions;
      } else {
        // Adicionar nova execução
        const newExecutions = [updatedExecution, ...prev];
        // Limitar o número máximo de execuções
        return newExecutions.slice(0, maxExecutions);
      }
    });
  }, [maxExecutions]);

  // Inscrever-se em canal de equipe
  const subscribe = useCallback((teamId: string) => {
    if (!isConnected || subscribedTeams.has(teamId)) return;

    const channelName = `team_${teamId}`;
    
    const handleTeamUpdate = (data: any) => {
      if (data.type === 'execution_update' && data.execution) {
        handleExecutionUpdate(data.execution);
      }
    };

    subscribeToChannel(channelName, handleTeamUpdate);
    setSubscribedTeams(prev => new Set([...prev, teamId]));
  }, [isConnected, subscribedTeams, subscribeToChannel, handleExecutionUpdate]);

  // Desinscrever-se de canal de equipe
  const unsubscribe = useCallback((teamId: string) => {
    if (!subscribedTeams.has(teamId)) return;

    const channelName = `team_${teamId}`;
    unsubscribeFromChannel(channelName);
    setSubscribedTeams(prev => {
      const newSet = new Set(prev);
      newSet.delete(teamId);
      return newSet;
    });
  }, [subscribedTeams, unsubscribeFromChannel]);

  // Inscrever-se em execução específica
  const subscribeToExecution = useCallback((executionId: string) => {
    if (!isConnected || subscribedExecutions.has(executionId)) return;

    const channelName = `execution_${executionId}`;
    
    const handleExecutionUpdate = (data: any) => {
      if (data.type === 'execution_update' && data.execution) {
        handleExecutionUpdate(data.execution);
      }
    };

    subscribeToChannel(channelName, handleExecutionUpdate);
    setSubscribedExecutions(prev => new Set([...prev, executionId]));
  }, [isConnected, subscribedExecutions, subscribeToChannel, handleExecutionUpdate]);

  // Desinscrever-se de execução específica
  const unsubscribeFromExecution = useCallback((executionId: string) => {
    if (!subscribedExecutions.has(executionId)) return;

    const channelName = `execution_${executionId}`;
    unsubscribeFromChannel(channelName);
    setSubscribedExecutions(prev => {
      const newSet = new Set(prev);
      newSet.delete(executionId);
      return newSet;
    });
  }, [subscribedExecutions, unsubscribeFromChannel]);

  // Carregar execuções da API
  const refreshExecutions = useCallback(async () => {
    if (!teamId && !userId) return;

    try {
      setIsLoading(true);
      setError(null);

      let url = '/api/v1/executions?';
      const params = new URLSearchParams();
      
      if (teamId) params.append('team_id', teamId);
      if (userId) params.append('user_id', userId);
      if (!includeCompleted) params.append('status', 'active');
      params.append('limit', maxExecutions.toString());

      const response = await fetch(`${url}${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Erro ao carregar execuções: ${response.statusText}`);
      }

      const data = await response.json();
      setExecutions(data.executions || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      console.error('Erro ao carregar execuções:', err);
    } finally {
      setIsLoading(false);
    }
  }, [teamId, userId, includeCompleted, maxExecutions]);

  // Limpar erro
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-inscrição quando conectado
  useEffect(() => {
    if (autoSubscribe && teamId && isConnected) {
      subscribe(teamId);
    }

    return () => {
      if (teamId) {
        unsubscribe(teamId);
      }
    };
  }, [autoSubscribe, teamId, isConnected, subscribe, unsubscribe]);

  // Carregar execuções iniciais
  useEffect(() => {
    if (teamId || userId) {
      refreshExecutions();
    }
  }, [teamId, userId, refreshExecutions]);

  // Reinscrever-se após reconexão
  useEffect(() => {
    if (isConnected) {
      // Reinscrever-se em todas as equipes
      subscribedTeams.forEach(teamId => {
        const channelName = `team_${teamId}`;
        const handleTeamUpdate = (data: any) => {
          if (data.type === 'execution_update' && data.execution) {
            handleExecutionUpdate(data.execution);
          }
        };
        subscribeToChannel(channelName, handleTeamUpdate);
      });

      // Reinscrever-se em todas as execuções
      subscribedExecutions.forEach(executionId => {
        const channelName = `execution_${executionId}`;
        const handleExecutionUpdate = (data: any) => {
          if (data.type === 'execution_update' && data.execution) {
            handleExecutionUpdate(data.execution);
          }
        };
        subscribeToChannel(channelName, handleExecutionUpdate);
      });
    }
  }, [isConnected, subscribedTeams, subscribedExecutions, subscribeToChannel, handleExecutionUpdate]);

  return {
    executions,
    activeExecutions,
    completedExecutions,
    failedExecutions,
    isLoading,
    error,
    totalCount: executions.length,
    subscribe,
    unsubscribe,
    subscribeToExecution,
    unsubscribeFromExecution,
    refreshExecutions,
    clearError
  };
};