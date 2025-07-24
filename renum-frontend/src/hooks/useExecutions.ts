// Hooks personalizados para execuções de equipes

import { useState, useEffect, useCallback } from 'react';
import { useExecutionContext } from '../contexts/ExecutionContext';
import { TeamExecution, TeamExecutionCreate, TeamExecutionStatus, TeamExecutionResult, ExecutionLogEntry } from '../services/api-types';
import { ApiError } from '../services/api-error';
import { useExecutionWebSocket } from '../services/team-execution-hooks';

// Hook para gerenciar a execução de uma equipe
export function useTeamExecution() {
  const { executeTeam, loading, error } = useExecutionContext();
  const [success, setSuccess] = useState<boolean>(false);

  const runTeamExecution = useCallback(async (teamId: string, initialPrompt: string) => {
    setSuccess(false);
    const data: TeamExecutionCreate = {
      team_id: teamId,
      initial_prompt: initialPrompt
    };
    
    const result = await executeTeam(teamId, data);
    if (result) {
      setSuccess(true);
      return result;
    }
    return null;
  }, [executeTeam]);

  return { runTeamExecution, success, loading, error };
}

// Hook para monitorar o status de uma execução
export function useExecutionMonitor(executionId: string | null) {
  const { fetchExecutionStatus, stopExecution, loading, error } = useExecutionContext();
  const [status, setStatus] = useState<TeamExecutionStatus | null>(null);
  const [polling, setPolling] = useState<NodeJS.Timeout | null>(null);

  // Configuração do WebSocket para atualizações em tempo real
  const { connected, status: wsStatus, error: wsError } = useExecutionWebSocket(executionId);

  // Atualiza o status quando recebemos atualizações do WebSocket
  useEffect(() => {
    if (wsStatus) {
      setStatus(wsStatus);
    }
  }, [wsStatus]);

  // Função para buscar o status manualmente
  const fetchStatus = useCallback(async () => {
    if (!executionId) return null;
    
    const result = await fetchExecutionStatus(executionId);
    if (result) {
      setStatus(result);
    }
    return result;
  }, [executionId, fetchExecutionStatus]);

  // Inicia polling para atualizações de status quando não há WebSocket
  useEffect(() => {
    if (!executionId || connected) {
      // Se não temos ID de execução ou o WebSocket está conectado, não precisamos de polling
      if (polling) {
        clearInterval(polling);
        setPolling(null);
      }
      return;
    }

    // Busca o status inicial
    fetchStatus();
    
    // Configura polling a cada 5 segundos
    const interval = setInterval(fetchStatus, 5000);
    setPolling(interval);
    
    return () => {
      if (polling) {
        clearInterval(polling);
      }
    };
  }, [executionId, connected, fetchStatus]);

  // Para o polling quando a execução termina
  useEffect(() => {
    if (status && ['completed', 'failed', 'cancelled'].includes(status.status) && polling) {
      clearInterval(polling);
      setPolling(null);
    }
  }, [status, polling]);

  // Função para parar a execução
  const handleStopExecution = useCallback(async () => {
    if (!executionId) return false;
    return stopExecution(executionId);
  }, [executionId, stopExecution]);

  return { 
    status, 
    fetchStatus, 
    stopExecution: handleStopExecution, 
    loading, 
    error,
    wsConnected: connected,
    wsError
  };
}

// Hook para obter o resultado de uma execução
export function useExecutionResult(executionId: string | null) {
  const { fetchExecutionResult, loading, error } = useExecutionContext();
  const [result, setResult] = useState<TeamExecutionResult | null>(null);

  const getResult = useCallback(async () => {
    if (!executionId) return null;
    
    const data = await fetchExecutionResult(executionId);
    if (data) {
      setResult(data);
    }
    return data;
  }, [executionId, fetchExecutionResult]);

  useEffect(() => {
    if (executionId) {
      getResult();
    } else {
      setResult(null);
    }
  }, [executionId, getResult]);

  return { result, loading, error, refetch: getResult };
}

// Hook para obter logs de uma execução
export function useExecutionLogs(executionId: string | null) {
  const { fetchExecutionLogs, loading, error } = useExecutionContext();
  const [logs, setLogs] = useState<ExecutionLogEntry[]>([]);

  const getLogs = useCallback(async (limit: number = 100, offset: number = 0, logTypes?: string[], agentId?: string) => {
    if (!executionId) return [];
    
    const data = await fetchExecutionLogs(executionId);
    if (data) {
      setLogs(data);
    }
    return data;
  }, [executionId, fetchExecutionLogs]);

  useEffect(() => {
    if (executionId) {
      getLogs();
    } else {
      setLogs([]);
    }
  }, [executionId, getLogs]);

  return { logs, loading, error, refetch: getLogs };
}

// Hook para listar execuções
export function useExecutionsList(teamId?: string) {
  const { fetchExecutions, executions, loading, error } = useExecutionContext();

  useEffect(() => {
    fetchExecutions(teamId);
  }, [teamId, fetchExecutions]);

  return { 
    executions, 
    loading, 
    error, 
    refetch: () => fetchExecutions(teamId) 
  };
}