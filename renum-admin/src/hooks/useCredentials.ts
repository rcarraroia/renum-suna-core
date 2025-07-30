import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { Credential, CredentialFormData, CredentialUsage } from '../types/credential';

export const useCredentials = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Buscar todas as credenciais
  const {
    data: credentials,
    isLoading: isLoadingCredentials,
    error: credentialsError,
    refetch: refetchCredentials,
  } = useQuery<Credential[]>({
    queryKey: ['credentials'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/credentials');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar credenciais');
        throw error;
      }
    },
  });

  // Buscar uma credencial específica
  const getCredential = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/credentials/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar credencial');
      throw error;
    }
  };

  // Criar uma nova credencial
  const createCredentialMutation = useMutation({
    mutationFn: async (data: CredentialFormData) => {
      try {
        const response = await apiClient.post('/admin/credentials', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao criar credencial');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });

  // Atualizar uma credencial existente
  const updateCredentialMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CredentialFormData> }) => {
      try {
        const response = await apiClient.put(`/admin/credentials/${id}`, data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar credencial');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });

  // Desativar/ativar uma credencial
  const toggleCredentialStatusMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      try {
        const response = await apiClient.patch(`/admin/credentials/${id}/status`, {
          is_active: isActive,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message ||
            `Erro ao ${isActive ? 'ativar' : 'desativar'} credencial`
        );
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });

  // Excluir uma credencial
  const deleteCredentialMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.delete(`/admin/credentials/${id}`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao excluir credencial');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
    },
  });

  // Buscar uso de uma credencial
  const getCredentialUsage = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/credentials/${id}/usage`);
      return response.data;
    } catch (error: any) {
      setError(
        error.response?.data?.message || 'Erro ao buscar uso da credencial'
      );
      throw error;
    }
  };

  // Revelar valor da credencial (operação sensível)
  const revealCredentialMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.post(`/admin/credentials/${id}/reveal`);
        return response.data.value;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao revelar credencial');
        throw error;
      }
    },
  });

  return {
    credentials,
    isLoadingCredentials,
    error,
    setError,
    refetchCredentials,
    getCredential,
    createCredential: createCredentialMutation.mutate,
    isCreatingCredential: createCredentialMutation.isPending,
    updateCredential: updateCredentialMutation.mutate,
    isUpdatingCredential: updateCredentialMutation.isPending,
    toggleCredentialStatus: toggleCredentialStatusMutation.mutate,
    isTogglingCredentialStatus: toggleCredentialStatusMutation.isPending,
    deleteCredential: deleteCredentialMutation.mutate,
    isDeletingCredential: deleteCredentialMutation.isPending,
    getCredentialUsage,
    revealCredential: revealCredentialMutation.mutateAsync,
    isRevealingCredential: revealCredentialMutation.isPending,
  };
};