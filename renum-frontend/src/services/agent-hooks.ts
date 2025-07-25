/**
 * Hooks para gerenciamento de agentes
 */

import { useQuery, useMutation, useQueryClient } from 'react-query';
import RenumApiClient from './api-client';

// Criar instância do cliente API
const apiClient = new RenumApiClient();

// Interface para agente
export interface Agent {
  agent_id: string;
  name: string;
  description?: string;
  model?: string;
  capabilities?: string[];
  created_at: string;
  updated_at: string;
}

// Chaves de consulta
const queryKeys = {
  agents: 'agents',
  agent: (id: string) => ['agent', id],
};

/**
 * Hook para buscar todos os agentes
 */
export function useAgents() {
  return useQuery<Agent[]>(
    queryKeys.agents,
    async () => {
      const response = await apiClient.get<Agent[]>('/agents');
      return response;
    },
    {
      staleTime: 1000 * 60 * 5, // 5 minutos
    }
  );
}

/**
 * Hook para buscar um agente específico
 */
export function useAgent(agentId: string) {
  return useQuery<Agent>(
    queryKeys.agent(agentId),
    async () => {
      const response = await apiClient.get<Agent>(`/agents/${agentId}`);
      return response;
    },
    {
      enabled: !!agentId,
      staleTime: 1000 * 60 * 5, // 5 minutos
    }
  );
}

/**
 * Hook para criar um agente
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation<Agent, Error, Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>>(
    async (data) => {
      const response = await apiClient.post<Agent>('/agents', data);
      return response;
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.agents);
        queryClient.setQueryData(queryKeys.agent(data.agent_id), data);
      },
    }
  );
}

/**
 * Hook para atualizar um agente
 */
export function useUpdateAgent() {
  const queryClient = useQueryClient();
  
  return useMutation<
    Agent,
    Error,
    { agentId: string; data: Partial<Omit<Agent, 'agent_id' | 'created_at' | 'updated_at'>> }
  >(
    async ({ agentId, data }) => {
      const response = await apiClient.put<Agent>(`/agents/${agentId}`, data);
      return response;
    },
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(queryKeys.agents);
        queryClient.setQueryData(queryKeys.agent(data.agent_id), data);
      },
    }
  );
}

/**
 * Hook para excluir um agente
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, string>(
    async (agentId) => {
      await apiClient.delete(`/agents/${agentId}`);
    },
    {
      onSuccess: (_, agentId) => {
        queryClient.invalidateQueries(queryKeys.agents);
        queryClient.removeQueries(queryKeys.agent(agentId));
      },
    }
  );
}