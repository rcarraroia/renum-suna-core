import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../lib/api-client';
import { useToast } from './useToast';

// Tipos
export type PermissionLevel = 'view' | 'use' | 'edit' | 'admin';

export interface AgentShare {
  id: string;
  agent_id: string;
  user_id: string;
  permission_level: PermissionLevel;
  created_at: string;
  created_by: string;
  expires_at: string | null;
  user?: {
    name: string;
    email: string;
  };
}

export interface ShareAgentData {
  user_id: string;
  permission_level: PermissionLevel;
  days_valid?: number | null;
  metadata?: Record<string, any>;
}

export interface UpdateShareData {
  permission_level?: PermissionLevel;
  days_valid?: number | null;
  metadata?: Record<string, any>;
}

/**
 * Hook para gerenciar o compartilhamento de agentes
 */
export function useAgentSharing(agentId?: string) {
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  // Buscar compartilhamentos de um agente
  const {
    data: shares,
    isLoading: isLoadingShares,
    isError: isErrorShares,
    error: sharesError,
    refetch: refetchShares
  } = useQuery({
    queryKey: ['agent-shares', agentId],
    queryFn: async () => {
      if (!agentId) return { shares: [], count: 0 };
      const response = await apiClient.get(`/api/v2/agents/${agentId}/shares`);
      return response.data;
    },
    enabled: !!agentId,
  });

  // Buscar agentes compartilhados com o usuário atual
  const {
    data: sharedWithMe,
    isLoading: isLoadingSharedWithMe,
    isError: isErrorSharedWithMe,
    error: sharedWithMeError,
    refetch: refetchSharedWithMe
  } = useQuery({
    queryKey: ['shared-with-me'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v2/agents/shared-with-me');
      return response.data;
    },
  });

  // Compartilhar agente
  const shareAgentMutation = useMutation({
    mutationFn: async (data: ShareAgentData) => {
      if (!agentId) throw new Error('ID do agente não fornecido');
      return apiClient.post(`/api/v2/agents/${agentId}/share`, data);
    },
    onSuccess: () => {
      showToast({
        title: 'Agente compartilhado',
        description: 'O agente foi compartilhado com sucesso.',
        type: 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao compartilhar',
        description: error.response?.data?.detail || 'Ocorreu um erro ao compartilhar o agente.',
        type: 'error',
      });
    },
  });

  // Atualizar compartilhamento
  const updateShareMutation = useMutation({
    mutationFn: async ({ shareId, data }: { shareId: string, data: UpdateShareData }) => {
      if (!agentId) throw new Error('ID do agente não fornecido');
      return apiClient.put(`/api/v2/agents/${agentId}/shares/${shareId}`, data);
    },
    onSuccess: () => {
      showToast({
        title: 'Compartilhamento atualizado',
        description: 'O compartilhamento foi atualizado com sucesso.',
        type: 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao atualizar',
        description: error.response?.data?.detail || 'Ocorreu um erro ao atualizar o compartilhamento.',
        type: 'error',
      });
    },
  });

  // Remover compartilhamento
  const removeShareMutation = useMutation({
    mutationFn: async (shareId: string) => {
      if (!agentId) throw new Error('ID do agente não fornecido');
      return apiClient.delete(`/api/v2/agents/${agentId}/shares/${shareId}`);
    },
    onSuccess: () => {
      showToast({
        title: 'Compartilhamento removido',
        description: 'O compartilhamento foi removido com sucesso.',
        type: 'success',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-shares', agentId] });
    },
    onError: (error: any) => {
      showToast({
        title: 'Erro ao remover',
        description: error.response?.data?.detail || 'Ocorreu um erro ao remover o compartilhamento.',
        type: 'error',
      });
    },
  });

  // Abrir modal de compartilhamento
  const openShareModal = () => {
    setIsShareModalOpen(true);
  };

  // Fechar modal de compartilhamento
  const closeShareModal = () => {
    setIsShareModalOpen(false);
  };

  return {
    // Estado
    isShareModalOpen,
    
    // Dados
    shares: shares?.shares || [],
    sharesCount: shares?.count || 0,
    sharedWithMe,
    
    // Loading states
    isLoadingShares,
    isLoadingSharedWithMe,
    isShareAgentLoading: shareAgentMutation.isPending,
    isUpdateShareLoading: updateShareMutation.isPending,
    isRemoveShareLoading: removeShareMutation.isPending,
    
    // Error states
    isErrorShares,
    isErrorSharedWithMe,
    sharesError,
    sharedWithMeError,
    
    // Ações
    shareAgent: (data: ShareAgentData) => shareAgentMutation.mutate(data),
    updateShare: (shareId: string, data: UpdateShareData) => 
      updateShareMutation.mutate({ shareId, data }),
    removeShare: (shareId: string) => removeShareMutation.mutate(shareId),
    refetchShares,
    refetchSharedWithMe,
    
    // Modal
    openShareModal,
    closeShareModal,
  };
}