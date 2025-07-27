/**
 * Hooks para gerenciamento de agentes
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import RenumApiClient from './api-client';
import { Agent } from './api-types';

// Criar instância do cliente API
const apiClient = new RenumApiClient();

// Chaves de consulta
const queryKeys = {
  agents: ['agents'] as const,
  agent: (id: string) => ['agent', id] as const,
};

/**
 * Hook para buscar todos os agentes
 */
export function useAgents(queryOptions: Omit<UseQueryOptions<Agent[]>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: async () => {
      const response = await apiClient.listAgents();
      return response;
    },
    staleTime: 1000 * 60 * 5, // 5 minutos
    ...queryOptions
  });
}

/**
 * Hook para buscar um agente específico
 */
export function useAgent(agentId: string, queryOptions: Omit<UseQueryOptions<Agent>, 'queryKey' | 'queryFn'> = {}) {
  return useQuery({
    queryKey: queryKeys.agent(agentId),
    queryFn: async () => {
      const response = await apiClient.getAgent(agentId);
      return response;
    },
    enabled: !!agentId,
    staleTime: 1000 * 60 * 5, // 5 minutos
    ...queryOptions
  });
}

/**
 * Hook para criar um agente
 */
export function useCreateAgent(options: UseMutationOptions<Agent, Error, Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>) => {
      const response = await apiClient.createAgent(data);
      return response;
    },
    onSuccess: (data: Agent) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.setQueryData(queryKeys.agent(data.agent_id), data);
    },
    ...options
  });
}

/**
 * Hook para atualizar um agente
 */
export function useUpdateAgent(options: UseMutationOptions<Agent, Error, { agentId: string; data: Partial<Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>> }> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ agentId, data }: { agentId: string; data: Partial<Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>> }) => {
      const response = await apiClient.updateAgent(agentId, data);
      return response;
    },
    onSuccess: (data: Agent) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.setQueryData(queryKeys.agent(data.agent_id), data);
    },
    ...options
  });
}

/**
 * Hook para excluir um agente
 */
export function useDeleteAgent(options: UseMutationOptions<{ success: boolean }, Error, string> = {}) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (agentId: string) => {
      return await apiClient.deleteAgent(agentId);
    },
    onSuccess: (_: { success: boolean }, agentId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.agents });
      queryClient.removeQueries({ queryKey: queryKeys.agent(agentId) });
    },
    ...options
  });
}