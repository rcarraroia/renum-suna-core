import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { Agent, AgentFormData, AgentUsageStats, AgentModel } from '../types/agent';

export const useAgents = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Buscar todos os agentes
  const {
    data: agents,
    isLoading: isLoadingAgents,
    error: agentsError,
    refetch: refetchAgents,
  } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/agents');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar agentes');
        throw error;
      }
    },
  });

  // Buscar agentes por cliente
  const getAgentsByClient = async (clientId: string) => {
    try {
      const response = await apiClient.get(`/admin/clients/${clientId}/agents`);
      return response.data;
    } catch (error: any) {
      setError(
        error.response?.data?.message || 'Erro ao buscar agentes do cliente'
      );
      throw error;
    }
  };

  // Buscar um agente específico
  const getAgent = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/agents/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar agente');
      throw error;
    }
  };

  // Criar um novo agente
  const createAgentMutation = useMutation({
    mutationFn: async (data: AgentFormData) => {
      try {
        const response = await apiClient.post('/admin/agents', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao criar agente');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Atualizar um agente existente
  const updateAgentMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: AgentFormData }) => {
      try {
        const response = await apiClient.put(`/admin/agents/${id}`, data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar agente');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Desativar/ativar um agente
  const toggleAgentStatusMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      try {
        const response = await apiClient.patch(`/admin/agents/${id}/status`, {
          is_active: isActive,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message ||
            `Erro ao ${isActive ? 'ativar' : 'desativar'} agente`
        );
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });

  // Buscar estatísticas de uso de um agente
  const getAgentUsageStats = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/agents/${id}/stats`);
      return response.data;
    } catch (error: any) {
      setError(
        error.response?.data?.message || 'Erro ao buscar estatísticas do agente'
      );
      throw error;
    }
  };

  // Buscar modelos de LLM disponíveis
  const {
    data: availableModels,
    isLoading: isLoadingModels,
    error: modelsError,
  } = useQuery<AgentModel[]>({
    queryKey: ['agent-models'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/agent-models');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar modelos disponíveis');
        throw error;
      }
    },
  });

  return {
    agents,
    isLoadingAgents,
    error,
    setError,
    refetchAgents,
    getAgentsByClient,
    getAgent,
    createAgent: createAgentMutation.mutate,
    isCreatingAgent: createAgentMutation.isPending,
    updateAgent: updateAgentMutation.mutate,
    isUpdatingAgent: updateAgentMutation.isPending,
    toggleAgentStatus: toggleAgentStatusMutation.mutate,
    isTogglingAgentStatus: toggleAgentStatusMutation.isPending,
    getAgentUsageStats,
    availableModels,
    isLoadingModels,
  };
};