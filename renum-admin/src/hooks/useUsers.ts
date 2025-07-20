import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { User, UserFormData, UserActivity } from '../types/user';

export const useUsers = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Buscar todos os usuários
  const {
    data: users,
    isLoading: isLoadingUsers,
    error: usersError,
    refetch: refetchUsers,
  } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/users');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar usuários');
        throw error;
      }
    },
  });

  // Buscar usuários por cliente
  const getUsersByClient = async (clientId: string) => {
    try {
      const response = await apiClient.get(`/admin/clients/${clientId}/users`);
      return response.data;
    } catch (error: any) {
      setError(
        error.response?.data?.message || 'Erro ao buscar usuários do cliente'
      );
      throw error;
    }
  };

  // Buscar um usuário específico
  const getUser = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/users/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar usuário');
      throw error;
    }
  };

  // Criar um novo usuário
  const createUserMutation = useMutation({
    mutationFn: async (data: UserFormData) => {
      try {
        const response = await apiClient.post('/admin/users', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao criar usuário');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Atualizar um usuário existente
  const updateUserMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UserFormData }) => {
      try {
        const response = await apiClient.put(`/admin/users/${id}`, data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar usuário');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Desativar/ativar um usuário
  const toggleUserStatusMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      try {
        const response = await apiClient.patch(`/admin/users/${id}/status`, {
          is_active: isActive,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message ||
            `Erro ao ${isActive ? 'ativar' : 'desativar'} usuário`
        );
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  // Redefinir senha de um usuário
  const resetPasswordMutation = useMutation({
    mutationFn: async ({
      id,
      password,
    }: {
      id: string;
      password: string;
    }) => {
      try {
        const response = await apiClient.post(`/admin/users/${id}/reset-password`, {
          password,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message || 'Erro ao redefinir senha do usuário'
        );
        throw error;
      }
    },
  });

  // Buscar atividade de um usuário
  const getUserActivity = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/users/${id}/activity`);
      return response.data;
    } catch (error: any) {
      setError(
        error.response?.data?.message || 'Erro ao buscar atividade do usuário'
      );
      throw error;
    }
  };

  return {
    users,
    isLoadingUsers,
    error,
    setError,
    refetchUsers,
    getUsersByClient,
    getUser,
    createUser: createUserMutation.mutate,
    isCreatingUser: createUserMutation.isPending,
    updateUser: updateUserMutation.mutate,
    isUpdatingUser: updateUserMutation.isPending,
    toggleUserStatus: toggleUserStatusMutation.mutate,
    isTogglingUserStatus: toggleUserStatusMutation.isPending,
    resetPassword: resetPasswordMutation.mutate,
    isResettingPassword: resetPasswordMutation.isPending,
    getUserActivity,
  };
};