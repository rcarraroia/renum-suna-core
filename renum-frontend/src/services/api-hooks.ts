/**
 * Hooks React Query para API do Renum
 * 
 * Este módulo fornece hooks React Query para interagir com a API do Renum Backend.
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import RenumApiClient from './api-client';
import { handleApiError } from './api-error';
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
  ListExecutionsOptions
} from './api-types';

// Chaves de consulta para React Query
export const queryKeys = {
  teams: 'teams',
  team: (id: string) => ['team', id],
  executions: 'executions',
  teamExecutions: (teamId: string) => ['executions', 'team', teamId],
  execution: (id: string) => ['execution', id],
  executionStatus: (id: string) => ['execution', id, 'status'],
  executionResult: (id: string) => ['execution', id, 'result'],
  executionLogs: (id: string) => ['execution', id, 'logs'],
  apiKeys: 'apiKeys'
};

/**
 * Hook para criar uma instância do cliente API
 */
import { LocalStorageManager } from '../utils/localStorage';

export function useApiClient() {
  // Aqui você pode adicionar lógica para obter o token de autenticação
  // de um contexto de autenticação ou localStorage
  const token = LocalStorageManager.getItem('auth_token');
  
  return new RenumApiClient({
    token: token || undefined
  });
}

/**
 * Hooks para gerenciamento de equipes
 */

/**
 * Hook para listar equipes
 */
export function useTeams(options: ListTeamsOptions = {}, queryOptions: Partial<UseQueryOptions<PaginatedTeamResponse, Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: [queryKeys.teams, options],
    queryFn: () => apiClient.listTeams(options),
    ...queryOptions
  });
}

/**
 * Hook para obter uma equipe por ID
 */
export function useTeam(teamId: string, queryOptions: Partial<UseQueryOptions<TeamResponse, Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: queryKeys.team(teamId),
    queryFn: () => apiClient.getTeam(teamId),
    enabled: !!teamId,
    ...queryOptions
  });
}

/**
 * Hook para criar uma equipe
 */
export function useCreateTeam(options: UseMutationOptions<TeamResponse, unknown, TeamCreate> = {}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (teamData: TeamCreate) => apiClient.createTeam(teamData),
    onSuccess: (data: TeamResponse) => {
      // Invalida a consulta de listagem para forçar uma atualização
      queryClient.invalidateQueries({ queryKey: [queryKeys.teams] });
      // Adiciona a nova equipe ao cache
      queryClient.setQueryData(queryKeys.team(data.team_id), data);
    },
    ...options
  });
}

/**
 * Hook para atualizar uma equipe
 */
export function useUpdateTeam(teamId: string, options: UseMutationOptions<TeamResponse, unknown, TeamUpdate> = {}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (teamData) => apiClient.updateTeam(teamId, teamData),
    onSuccess: (data) => {
      // Atualiza o cache
      queryClient.setQueryData(queryKeys.team(teamId), data);
      // Invalida a consulta de listagem para forçar uma atualização
      queryClient.invalidateQueries({ queryKey: [queryKeys.teams] });
    },
    
    ...options
  });
}

/**
 * Hook para excluir uma equipe
 */
export function useDeleteTeam(options: UseMutationOptions<{ success: boolean }, unknown, string> = {}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (teamId) => apiClient.deleteTeam(teamId),
    onSuccess: (_, teamId) => {
      // Remove do cache
      queryClient.removeQueries({ queryKey: queryKeys.team(teamId) });
      // Invalida a consulta de listagem para forçar uma atualização
      queryClient.invalidateQueries({ queryKey: [queryKeys.teams] });
    },
    
    ...options
  });
}

/**
 * Hooks para gerenciamento de membros da equipe
 */

/**
 * Hook para adicionar um membro à equipe
 */
export function useAddTeamMember(
  teamId: string, 
  options: UseMutationOptions<TeamResponse, unknown, { agent_id: string; role?: string; execution_order?: number }> = {}
) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (memberData) => apiClient.addTeamMember(teamId, memberData),
    onSuccess: (data) => {
      // Atualiza o cache
      queryClient.setQueryData(queryKeys.team(teamId), data);
    },
    
    ...options
  });
}

/**
 * Hook para remover um membro da equipe
 */
export function useRemoveTeamMember(
  teamId: string, 
  options: UseMutationOptions<TeamResponse, unknown, string> = {}
) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (agentId) => apiClient.removeTeamMember(teamId, agentId),
    onSuccess: (data) => {
      // Atualiza o cache
      queryClient.setQueryData(queryKeys.team(teamId), data);
    },
    
    ...options
  });
}

/**
 * Hooks para execução de equipes
 */

/**
 * Hook para listar execuções
 */
export function useExecutions(options: ListExecutionsOptions = {}, queryOptions: Partial<UseQueryOptions<TeamExecutionResponse[], Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: [queryKeys.executions, options],
    queryFn: () => apiClient.listExecutions(options),
    
    ...queryOptions
  });
}

/**
 * Hook para listar execuções de uma equipe específica
 */
export function useTeamExecutions(teamId: string, queryOptions: Partial<UseQueryOptions<TeamExecutionResponse[], Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: queryKeys.teamExecutions(teamId),
    queryFn: () => apiClient.listExecutions({ teamId }),
    
    enabled: !!teamId,
    ...queryOptions
  });
}

/**
 * Hook para obter status da execução
 */
export function useExecutionStatus(executionId: string, queryOptions: Partial<UseQueryOptions<TeamExecutionStatus, Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: queryKeys.executionStatus(executionId),
    queryFn: () => apiClient.getExecutionStatus(executionId),
    
    enabled: !!executionId,
    // Atualiza a cada 2 segundos por padrão
    refetchInterval: queryOptions.refetchInterval ?? 2000,
    ...queryOptions
  });
}

/**
 * Hook para obter resultado da execução
 */
export function useExecutionResult(executionId: string, queryOptions: Partial<UseQueryOptions<TeamExecutionResult, Error>> = {}) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: queryKeys.executionResult(executionId),
    queryFn: () => apiClient.getExecutionResult(executionId),
    
    enabled: !!executionId,
    ...queryOptions
  });
}

/**
 * Hook para obter logs da execução
 */
export function useExecutionLogs(
  executionId: string, 
  options: GetExecutionLogsOptions = {}, 
  queryOptions: Partial<UseQueryOptions<ExecutionLogEntry[], Error>> = {}
) {
  const apiClient = useApiClient();
  
  return useQuery({
    queryKey: [...queryKeys.executionLogs(executionId), options],
    queryFn: () => apiClient.getExecutionLogs(executionId, options),
    
    enabled: !!executionId,
    // Atualiza a cada 5 segundos por padrão
    refetchInterval: queryOptions.refetchInterval ?? 5000,
    ...queryOptions
  });
}

/**
 * Hook para executar uma equipe
 */
export function useExecuteTeam(
  teamId: string, 
  options: UseMutationOptions<TeamExecutionResponse, unknown, Omit<TeamExecutionCreate, 'team_id'>> = {}
) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<TeamExecutionResponse, unknown, Omit<TeamExecutionCreate, 'team_id'>>({
    mutationFn: (executionData) => apiClient.executeTeam(teamId, executionData),
    onSuccess: (data) => {
      // Invalida a consulta de execuções para forçar uma atualização
      queryClient.invalidateQueries({ queryKey: queryKeys.teamExecutions(teamId) });
    },
    
    ...options
  });
}

/**
 * Hook para parar uma execução
 */
export function useStopExecution(options: UseMutationOptions<{ success: boolean }, unknown, string> = {}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (executionId) => apiClient.stopExecution(executionId),
    onSuccess: (_, executionId) => {
      // Invalida a consulta de status para forçar uma atualização
      queryClient.invalidateQueries({ queryKey: queryKeys.executionStatus(executionId) });
    },
    
    ...options
  });
}

/**
 * Hook para monitorar uma execução via WebSocket
 */
export function useExecutionMonitor(executionId: string) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  const connect = () => {
    if (typeof window === 'undefined') {
      return null;
    }
    
    try {
      const ws = apiClient.createExecutionMonitor(executionId);
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'execution_update') {
            // Atualiza o cache de status
            queryClient.setQueryData(queryKeys.executionStatus(executionId), data.data);
          } else if (data.type === 'log_entry') {
            // Atualiza o cache de logs (mais complexo, requer manipulação do cache)
            queryClient.invalidateQueries({ queryKey: queryKeys.executionLogs(executionId) });
          }
        } catch (error) {
          console.error('Erro ao processar mensagem WebSocket:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('Erro na conexão WebSocket:', error);
      };
      
      return ws;
    } catch (error) {
      console.error('Erro ao criar conexão WebSocket:', error);
      return null;
    }
  };
  
  return { connect };
}
