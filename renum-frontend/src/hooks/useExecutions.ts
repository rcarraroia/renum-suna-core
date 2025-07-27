// Hooks personalizados para execuções de equipes

import { useState, useEffect, useCallback } from 'react';
import { useExecutionContext } from '../contexts/ExecutionContext';
import { TeamExecution, TeamExecutionCreate, TeamExecutionStatus, TeamExecutionResult, ExecutionLogEntry } from '../services/api-types';
import { ApiError } from '../services/api-error';
// import { useExecutionWebSocket } from '../services/team-execution-hooks'; // Comentado temporariamente

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