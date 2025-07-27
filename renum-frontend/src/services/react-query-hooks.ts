/**
 * React Query hooks para o Renum API Client
 * 
 * Este módulo fornece hooks React Query para interagir com a API do Renum Backend.
 * Inclui funções para gerenciar equipes, membros de equipe e execuções de equipe.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions, QueryKey } from '@tanstack/react-query';
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
  teams: ['teams'] as const,
  team: (id: string) => ['team', id] as const,
  executions: ['executions'] as const,
  teamExecutions: (teamId: string) => ['executions', teamId] as const,
  execution: (id: string) => ['execution', id] as const,
  executionStatus: (id: string) => ['execution', id, 'status'] as const,
  executionResult: (id: string) => ['execution', id, 'result'] as const,
  executionLogs: (id: string) => ['execution', id, 'logs'] as const,
  apiKeys: ['apiKeys'] as const
};

/**
 * Hook para listar equipes
 */
export function useTeams(options: ListTeamsOptions = {}, queryOptions: Omit<UseQueryOptions<PaginatedTeamResponse>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: [queryKeys.teams, options],
    queryFn: () => apiClient.listTeams(options),
    staleTime: 1000 * 60 * 5, // 5 minutos
    ...queryOptions
  });
}

/**
 * Hook para obter uma equipe por ID
 */
export function useTeam(teamId: string, queryOptions: Omit<UseQueryOptions<TeamResponse>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.team(teamId),
    queryFn: () => apiClient.getTeam(teamId),
    staleTime: 1000 * 60 * 5, // 5 minutos
    enabled: !!teamId,
    ...queryOptions
  });
}

/**
 * Hook para criar uma equipe
 */
export function useCreateTeam(options: UseMutationOptions<TeamResponse, Error, TeamCreate> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (teamData: TeamCreate) => apiClient.createTeam(teamData),
    onSuccess: (data: TeamResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams });
      queryClient.setQueryData(queryKeys.team(data.team_id), data);
    },
    ...options
  });
}

/**
 * Hook para atualizar uma equipe
 */
export function useUpdateTeam(options: UseMutationOptions<TeamResponse, Error, { teamId: string; data: TeamUpdate }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ teamId, data }: { teamId: string; data: TeamUpdate }) => apiClient.updateTeam(teamId, data),
    onSuccess: (data: TeamResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams });
      queryClient.setQueryData(queryKeys.team(data.team_id), data);
    },
    ...options
  });
}

/**
 * Hook para excluir uma equipe
 */
export function useDeleteTeam(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (teamId: string) => apiClient.deleteTeam(teamId),
    onSuccess: (_: { success: boolean }, teamId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teams });
      queryClient.removeQueries({ queryKey: queryKeys.team(teamId) });
    },
    ...options
  });
}

/**
 * Hook para adicionar um membro à equipe
 */
export function useAddTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; memberData: { agent_id: string; role?: string; execution_order?: number } }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ teamId, memberData }: { teamId: string; memberData: { agent_id: string; role?: string; execution_order?: number } }) => apiClient.addTeamMember(teamId, memberData),
    onSuccess: (data: TeamResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team(data.team_id) });
    },
    ...options
  });
}

/**
 * Hook para atualizar um membro da equipe
 */
export function useUpdateTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; agentId: string; memberData: { role?: string; execution_order?: number } }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ teamId, agentId, memberData }: { teamId: string; agentId: string; memberData: { role?: string; execution_order?: number } }) => apiClient.updateTeamMember(teamId, agentId, memberData),
    onSuccess: (data: TeamResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team(data.team_id) });
    },
    ...options
  });
}

/**
 * Hook para remover um membro da equipe
 */
export function useRemoveTeamMember(options: UseMutationOptions<TeamResponse, Error, { teamId: string; agentId: string }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ teamId, agentId }: { teamId: string; agentId: string }) => apiClient.removeTeamMember(teamId, agentId),
    onSuccess: (data: TeamResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team(data.team_id) });
    },
    ...options
  });
}

/**
 * Hook para listar execuções
 */
export function useExecutions(options: ListExecutionsOptions = {}, queryOptions: Omit<UseQueryOptions<TeamExecutionResponse[]>, 'queryKey' | 'queryFn'> = {}) {
  const queryKey = options.teamId 
    ? queryKeys.teamExecutions(options.teamId)
    : queryKeys.executions;
    
  return useQuery({
    queryKey: [queryKey, options],
    queryFn: () => apiClient.listExecutions(options),
    staleTime: 1000 * 60, // 1 minuto
    ...queryOptions
  });
}

/**
 * Hook para obter status da execução
 */
export function useExecutionStatus(executionId: string, queryOptions: Omit<UseQueryOptions<TeamExecutionStatus>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.executionStatus(executionId),
    queryFn: () => apiClient.getExecutionStatus(executionId),
    staleTime: 1000 * 5, // 5 segundos
    refetchInterval: (query) => {
      // Refetch frequentemente se estiver em andamento
      const data = query.state.data as TeamExecutionStatus | undefined;
      if (data && ['pending', 'running'].includes(data.status)) {
        return 2000; // 2 segundos
      }
      return false; // Não refetch se completo
    },
    enabled: !!executionId,
    ...queryOptions
  });
}

/**
 * Hook para obter resultado da execução
 */
export function useExecutionResult(executionId: string, queryOptions: Omit<UseQueryOptions<TeamExecutionResult>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.executionResult(executionId),
    queryFn: () => apiClient.getExecutionResult(executionId),
    staleTime: 1000 * 60 * 5, // 5 minutos
    enabled: !!executionId,
    ...queryOptions
  });
}

/**
 * Hook para obter logs de execução
 */
export function useExecutionLogs(executionId: string, options: GetExecutionLogsOptions = {}, queryOptions: Omit<UseQueryOptions<ExecutionLogEntry[]>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: [queryKeys.executionLogs(executionId), options],
    queryFn: () => apiClient.getExecutionLogs(executionId, options),
    staleTime: 1000 * 10, // 10 segundos
    refetchInterval: 5000, // 5 segundos
    enabled: !!executionId,
    ...queryOptions
  });
}

/**
 * Hook para executar uma equipe
 */
export function useExecuteTeam(options: UseMutationOptions<TeamExecutionResponse, Error, { teamId: string; executionData: Omit<TeamExecutionCreate, 'team_id'> }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ teamId, executionData }: { teamId: string; executionData: Omit<TeamExecutionCreate, 'team_id'> }) => apiClient.executeTeam(teamId, executionData),
    onSuccess: (data: TeamExecutionResponse) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.teamExecutions(data.team_id) });
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
  });
}

/**
 * Hook para parar uma execução
 */
export function useStopExecution(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (executionId: string) => apiClient.stopExecution(executionId),
    onSuccess: (_: { success: boolean }, executionId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.executionStatus(executionId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.executions });
    },
    ...options
  });
}

/**
 * Hook para listar chaves API
 */
export function useApiKeys(queryOptions: Omit<UseQueryOptions<UserApiKeyResponse[]>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.apiKeys,
    queryFn: () => apiClient.listApiKeys(),
    staleTime: 1000 * 60 * 5, // 5 minutos
    ...queryOptions
  });
}

/**
 * Hook para criar uma chave API
 */
export function useCreateApiKey(options: UseMutationOptions<UserApiKeyResponse, Error, UserApiKeyCreate> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (keyData: UserApiKeyCreate) => apiClient.createApiKey(keyData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys });
    },
    ...options
  });
}

/**
 * Hook para excluir uma chave API
 */
export function useDeleteApiKey(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (serviceName: string) => apiClient.deleteApiKey(serviceName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.apiKeys });
    },
    ...options
  });
}