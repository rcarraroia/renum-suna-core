import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import {
  SystemSetting,
  SystemSettingFormData,
  SecuritySetting,
  IntegrationSetting,
  IntegrationSettingFormData,
  ChangeLog,
} from '../types/settings';

export const useSettings = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Buscar todas as configurações do sistema
  const {
    data: settings,
    isLoading: isLoadingSettings,
    error: settingsError,
    refetch: refetchSettings,
  } = useQuery<SystemSetting[]>({
    queryKey: ['settings'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/settings');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar configurações');
        throw error;
      }
    },
  });

  // Buscar uma configuração específica
  const getSetting = async (key: string) => {
    try {
      const response = await apiClient.get(`/admin/settings/${key}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar configuração');
      throw error;
    }
  };

  // Criar ou atualizar uma configuração
  const updateSettingMutation = useMutation({
    mutationFn: async (data: SystemSettingFormData) => {
      try {
        const response = await apiClient.put(`/admin/settings/${data.key}`, data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar configuração');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });

  // Excluir uma configuração
  const deleteSettingMutation = useMutation({
    mutationFn: async (key: string) => {
      try {
        const response = await apiClient.delete(`/admin/settings/${key}`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao excluir configuração');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });

  // Buscar configurações de segurança
  const {
    data: securitySettings,
    isLoading: isLoadingSecuritySettings,
    error: securitySettingsError,
    refetch: refetchSecuritySettings,
  } = useQuery<SecuritySetting>({
    queryKey: ['security-settings'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/settings/security');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar configurações de segurança');
        throw error;
      }
    },
  });

  // Atualizar configurações de segurança
  const updateSecuritySettingsMutation = useMutation({
    mutationFn: async (data: SecuritySetting) => {
      try {
        const response = await apiClient.put('/admin/settings/security', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar configurações de segurança');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-settings'] });
    },
  });

  // Buscar integrações
  const {
    data: integrations,
    isLoading: isLoadingIntegrations,
    error: integrationsError,
    refetch: refetchIntegrations,
  } = useQuery<IntegrationSetting[]>({
    queryKey: ['integrations'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/settings/integrations');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar integrações');
        throw error;
      }
    },
  });

  // Buscar uma integração específica
  const getIntegration = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/settings/integrations/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar integração');
      throw error;
    }
  };

  // Criar ou atualizar uma integração
  const updateIntegrationMutation = useMutation({
    mutationFn: async ({ id, data }: { id?: string; data: IntegrationSettingFormData }) => {
      try {
        let response;
        if (id) {
          response = await apiClient.put(`/admin/settings/integrations/${id}`, data);
        } else {
          response = await apiClient.post('/admin/settings/integrations', data);
        }
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar integração');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  // Excluir uma integração
  const deleteIntegrationMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.delete(`/admin/settings/integrations/${id}`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao excluir integração');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] });
    },
  });

  // Testar uma integração
  const testIntegrationMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.post(`/admin/settings/integrations/${id}/test`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao testar integração');
        throw error;
      }
    },
  });

  // Hook para buscar histórico de alterações
  const useChangeLogs = (key?: string) => {
    return useQuery<ChangeLog[]>({
      queryKey: ['change-logs', key],
      queryFn: async () => {
        try {
          const response = await apiClient.get('/admin/settings/logs', {
            params: { key },
          });
          return response.data;
        } catch (error: any) {
          setError(error.response?.data?.message || 'Erro ao buscar histórico de alterações');
          throw error;
        }
      },
    });
  };

  return {
    settings,
    isLoadingSettings,
    getSetting,
    updateSetting: updateSettingMutation.mutate,
    isUpdatingSetting: updateSettingMutation.isPending,
    deleteSetting: deleteSettingMutation.mutate,
    isDeletingSetting: deleteSettingMutation.isPending,
    securitySettings,
    isLoadingSecuritySettings,
    updateSecuritySettings: updateSecuritySettingsMutation.mutate,
    isUpdatingSecuritySettings: updateSecuritySettingsMutation.isPending,
    integrations,
    isLoadingIntegrations,
    getIntegration,
    updateIntegration: updateIntegrationMutation.mutate,
    isUpdatingIntegration: updateIntegrationMutation.isPending,
    deleteIntegration: deleteIntegrationMutation.mutate,
    isDeletingIntegration: deleteIntegrationMutation.isPending,
    testIntegration: testIntegrationMutation.mutate,
    isTestingIntegration: testIntegrationMutation.isPending,
    useChangeLogs,
    error,
    setError,
    refetchSettings,
    refetchSecuritySettings,
    refetchIntegrations,
  };
};