// Execution Context for Team Orchestration

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import RenumApiClient from '../services/api-client';

// Criar instância do cliente API
const apiClient = new RenumApiClient();
import { 
  TeamExecution, 
  TeamExecutionCreate, 
  TeamExecutionStatus, 
  TeamExecutionResult,
  ExecutionLogEntry
} from '../services/api-types';
import { ApiError } from '../services/api-error';

interface ExecutionContextType {
  executions: TeamExecution[];
  loading: boolean;
  error: ApiError | null;
  selectedExecution: TeamExecution | null;
  executionStatus: TeamExecutionStatus | null;
  executionResult: TeamExecutionResult | null;
  executionLogs: ExecutionLogEntry[];
  fetchExecutions: (teamId?: string) => Promise<void>;
  executeTeam: (teamId: string, data: TeamExecutionCreate) => Promise<TeamExecution | null>;
  fetchExecutionStatus: (executionId: string) => Promise<TeamExecutionStatus | null>;
  fetchExecutionResult: (executionId: string) => Promise<TeamExecutionResult | null>;
  fetchExecutionLogs: (executionId: string) => Promise<ExecutionLogEntry[]>;
  stopExecution: (executionId: string) => Promise<boolean>;
  selectExecution: (execution: TeamExecution | null) => void;
}

const ExecutionContext = createContext<ExecutionContextType | undefined>(undefined);

export function useExecutionContext() {
  const context = useContext(ExecutionContext);
  if (context === undefined) {
    throw new Error('useExecutionContext must be used within an ExecutionProvider');
  }
  return context;
}

interface ExecutionProviderProps {
  children: ReactNode;
}

export function ExecutionProvider({ children }: ExecutionProviderProps) {
  const [executions, setExecutions] = useState<TeamExecution[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<TeamExecution | null>(null);
  const [executionStatus, setExecutionStatus] = useState<TeamExecutionStatus | null>(null);
  const [executionResult, setExecutionResult] = useState<TeamExecutionResult | null>(null);
  const [executionLogs, setExecutionLogs] = useState<ExecutionLogEntry[]>([]);

  const fetchExecutions = useCallback(async (teamId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.listExecutions(1, 50, teamId);
      setExecutions(data);
      setLoading(false);
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
    }
  }, []);

  const executeTeam = useCallback(async (teamId: string, data: TeamExecutionCreate) => {
    setLoading(true);
    setError(null);
    try {
      const execution = await apiClient.executeTeam(teamId, data);
      setExecutions(prev => [execution, ...prev]);
      setSelectedExecution(execution);
      setLoading(false);
      return execution;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
      return null;
    }
  }, []);

  const fetchExecutionStatus = useCallback(async (executionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const status = await apiClient.getExecutionStatus(executionId);
      setExecutionStatus(status);
      setLoading(false);
      return status;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
      return null;
    }
  }, []);

  const fetchExecutionResult = useCallback(async (executionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiClient.getExecutionResult(executionId);
      setExecutionResult(result);
      setLoading(false);
      return result;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
      return null;
    }
  }, []);

  const fetchExecutionLogs = useCallback(async (executionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const logs = await apiClient.getExecutionLogs(executionId);
      setExecutionLogs(logs);
      setLoading(false);
      return logs;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
      return [];
    }
  }, []);

  const stopExecution = useCallback(async (executionId: string) => {
    setLoading(true);
    setError(null);
    try {
      await apiClient.stopExecution(executionId);
      
      // Atualiza o status da execução na lista
      setExecutions(prev => 
        prev.map(exec => 
          exec.execution_id === executionId 
            ? { ...exec, status: 'cancelled' } 
            : exec
        )
      );
      
      // Atualiza a execução selecionada se for a mesma
      if (selectedExecution && selectedExecution.execution_id === executionId) {
        setSelectedExecution(prev => prev ? { ...prev, status: 'cancelled' } : null);
      }
      
      setLoading(false);
      return true;
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError(500, 'Unknown error');
      setError(apiError);
      setLoading(false);
      return false;
    }
  }, [selectedExecution]);

  const selectExecution = useCallback((execution: TeamExecution | null) => {
    setSelectedExecution(execution);
    if (execution) {
      fetchExecutionStatus(execution.execution_id);
      fetchExecutionLogs(execution.execution_id);
      if (execution.status === 'completed') {
        fetchExecutionResult(execution.execution_id);
      }
    } else {
      setExecutionStatus(null);
      setExecutionResult(null);
      setExecutionLogs([]);
    }
  }, [fetchExecutionStatus, fetchExecutionLogs, fetchExecutionResult]);

  const value = {
    executions,
    loading,
    error,
    selectedExecution,
    executionStatus,
    executionResult,
    executionLogs,
    fetchExecutions,
    executeTeam,
    fetchExecutionStatus,
    fetchExecutionResult,
    fetchExecutionLogs,
    stopExecution,
    selectExecution
  };

  return <ExecutionContext.Provider value={value}>{children}</ExecutionContext.Provider>;
}