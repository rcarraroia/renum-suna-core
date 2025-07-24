/**
 * React Query hooks para o Renum API Client
 * 
 * Este módulo fornece hooks React Query para interagir com a API do Renum Backend.
 * Inclui funções para gerenciar equipes, membros de equipe e execuções de equipe.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from 'react-query';
import RenumApiClient from './api-client';
import {
  TeamCreate,
  TeamUpdate,
  TeamResponse,
  PaginatedTeamResponse,
  ListTeamsOptions,
  TeamExecutionCreate,
  TeamExecutionResponse,
  TeamExecutionStatus,
  TeamExecutionResult,
  ExecutionLogEntry,
  GetExecutionLogsOptions,
  ListExecutionsOptions,
  UserApiKeyCreate,
  UserApiKeyResponse
} from './api-types';

// Re-exporta os hooks de agentes
export * from './agent-hooks';

// Instância do cliente API
const apiClient = new RenumApiClient();

// Chaves de consulta
export const queryKeys = {
  teams: 'teams',
  team: (id: string) => ['team', id],
  executions: 'executions',
  teamExecutions: (teamId: string) => ['executions', teamId],
  execution: (id: string) => ['execution', id],
  executionStatus: (id: string) => ['execution', id, 'status'],
  executionResult: (id: string) => ['execution', id, 'result'],
  executionLogs: (id: string) => ['execution', id, 'logs'],
  apiKeys: 'apiKeys'
};

/**
 * Hook para listar equipes
 */
export function useTeams(options: ListTeamsOptions = {}, queryOptions: UseQueryOptions<PaginatedTeamResponse> = {}) {
  return useQuery<PaginatedTeamResponse>(
    [queryKeys.teams, options],
    () => apiClient.listTeams(options),
    {
      staleTime: 1000 * 60 * 5, // 5 minutos
      ...queryOptions
    }
  );
}

/**
 * Hook para obter uma equipe por ID
 */
export function useTeam(teamId: string, queryOptions: UseQueryOptions<TeamResponse> = {}) {
  return useQuery<TeamResponse>(
    queryKeys.team(teamId),
    () => apiClient.getTeam(teamId),
    {
      staleTime: 1000 * 60 * 5, // 5 minutos
      enabled: !!teamId,
      ...queryOptions
    }
  );
}

/**
 * Hook para criar uma equipe
 */
export function useCreateTeam(options: UseMutationOptions<TeamResponse, Error, TeamCreate> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamResponse, Error, TeamCreate>(
    (teamData) => apiClient.createTeam(teamData),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.teams);
        queryClient.setQueryData(queryKeys.team(data.team_id), data);
      },
      ...options
    }
  );
}

/**
 * Hook para atualizar uma equipe
 */
export function useUpdateTeam(options: UseMutationOptions<TeamResponse, Error, { teamId: string; data: TeamUpdate }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamResponse, Error, { teamId: string; data: TeamUpdate }>(
    ({ teamId, data }) => apiClient.updateTeam(teamId, data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.teams);
        queryClient.setQueryData(queryKeys.team(data.team_id), data);
      },
      ...options
    }
  );
}

/**
 * Hook para excluir uma equipe
 */
export function useDeleteTeam(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<{ success: boolean }, Error, string>(
    (teamId) => apiClient.deleteTeam(teamId),
    {
      onSuccess: (_, teamId) => {
        queryClient.invalidateQueries(queryKeys.teams);
        queryClient.removeQueries(queryKeys.team(teamId));
      },
      ...options
    }
  );
}

/**
 * Hook para adicionar um membro à equipe
 */
export function useAddTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; memberData: { agent_id: string; role?: string; execution_order?: number } }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamResponse, Error, { teamId: string; memberData: { agent_id: string; role?: string; execution_order?: number } }>(
    ({ teamId, memberData }) => apiClient.addTeamMember(teamId, memberData),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.team(data.team_id));
      },
      ...options
    }
  );
}

/**
 * Hook para atualizar um membro da equipe
 */
export function useUpdateTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; agentId: string; memberData: { role?: string; execution_order?: number } }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamResponse, Error, { teamId: string; agentId: string; memberData: { role?: string; execution_order?: number } }>(
    ({ teamId, agentId, memberData }) => apiClient.updateTeamMember(teamId, agentId, memberData),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.team(data.team_id));
      },
      ...options
    }
  );
}

/**
 * Hook para remover um membro da equipe
 */
export function useRemoveTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; agentId: string }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamResponse, Error, { teamId: string; agentId: string }>(
    ({ teamId, agentId }) => apiClient.removeTeamMember(teamId, agentId),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.team(data.team_id));
      },
      ...options
    }
  );
}

/**
 * Hook para listar execuções
 */
export function useExecutions(options: ListExecutionsOptions = {}, queryOptions: UseQueryOptions<TeamExecutionResponse[]> = {}) {
  const queryKey = options.teamId 
    ? queryKeys.teamExecutions(options.teamId)
    : queryKeys.executions;
    
  return useQuery<TeamExecutionResponse[]>(
    [queryKey, options],
    () => apiClient.listExecutions(options),
    {
      staleTime: 1000 * 60, // 1 minuto
      ...queryOptions
    }
  );
}

/**
 * Hook para obter status da execução
 */
export function useExecutionStatus(executionId: string, queryOptions: UseQueryOptions<TeamExecutionStatus> = {}) {
  return useQuery<TeamExecutionStatus>(
    queryKeys.executionStatus(executionId),
    () => apiClient.getExecutionStatus(executionId),
    {
      staleTime: 1000 * 5, // 5 segundos
      refetchInterval: (data) => {
        // Refetch frequentemente se estiver em andamento
        if (data && ['pending', 'running'].includes(data.status)) {
          return 2000; // 2 segundos
        }
        return false; // Não refetch se completo
      },
      enabled: !!executionId,
      ...queryOptions
    }
  );
}

/**
 * Hook para obter resultado da execução
 */
export function useExecutionResult(executionId: string, queryOptions: UseQueryOptions<TeamExecutionResult> = {}) {
  return useQuery<TeamExecutionResult>(
    queryKeys.executionResult(executionId),
    () => apiClient.getExecutionResult(executionId),
    {
      staleTime: 1000 * 60 * 5, // 5 minutos
      enabled: !!executionId,
      ...queryOptions
    }
  );
}

/**
 * Hook para obter logs de execução
 */
export function useExecutionLogs(executionId: string, options: GetExecutionLogsOptions = {}, queryOptions: UseQueryOptions<ExecutionLogEntry[]> = {}) {
  return useQuery<ExecutionLogEntry[]>(
    [queryKeys.executionLogs(executionId), options],
    () => apiClient.getExecutionLogs(executionId, options),
    {
      staleTime: 1000 * 10, // 10 segundos
      refetchInterval: 5000, // 5 segundos
      enabled: !!executionId,
      ...queryOptions
    }
  );
}

/**
 * Hook para executar uma equipe
 */
export function useExecuteTeam(options: UseMutationOptions<TeamExecutionResponse, Error, { teamId: string; executionData: Omit<TeamExecutionCreate, 'team_id'> }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<TeamExecutionResponse, Error, { teamId: string; executionData: Omit<TeamExecutionCreate, 'team_id'> }>(
    ({ teamId, executionData }) => apiClient.executeTeam(teamId, executionData),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.teamExecutions(data.team_id));
        queryClient.setQueryData(queryKeys.executionStatus(data.execution_id), {
          execution_id: data.execution_id,
          team_id: data.team_id,
          status: data.status,
          agent_statuses: {},
          progress: 0,
          total_steps: 0,
          active_agents: [],
          completed_agents: [],
          failed_agents: [],
          last_updated: new Date().toISOString()
        });
      },
      ...options
    }
  );
}

/**
 * Hook para parar uma execução
 */
export function useStopExecution(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<{ success: boolean }, Error, string>(
    (executionId) => apiClient.stopExecution(executionId),
    {
      onSuccess: (_, executionId) => {
        queryClient.invalidateQueries(queryKeys.executionStatus(executionId));
        queryClient.invalidateQueries(queryKeys.executions);
      },
      ...options
    }
  );
}

/**
 * Hook para listar chaves API
 */
export function useApiKeys(queryOptions: UseQueryOptions<UserApiKeyResponse[]> = {}) {
  return useQuery<UserApiKeyResponse[]>(
    queryKeys.apiKeys,
    () => apiClient.listApiKeys(),
    {
      staleTime: 1000 * 60 * 5, // 5 minutos
      ...queryOptions
    }
  );
}

/**
 * Hook para criar uma chave API
 */
export function useCreateApiKey(options: UseMutationOptions<UserApiKeyResponse, Error, UserApiKeyCreate> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<UserApiKeyResponse, Error, UserApiKeyCreate>(
    (keyData) => apiClient.createApiKey(keyData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.apiKeys);
      },
      ...options
    }
  );
}

/**
 * Hook para excluir uma chave API
 */
export function useDeleteApiKey(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation<{ success: boolean }, Error, string>(
    (serviceName) => apiClient.deleteApiKey(serviceName),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(queryKeys.apiKeys);
      },
      ...options
    }
  );
}