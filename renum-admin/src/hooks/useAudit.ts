import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import {
  AuditLog,
  AuditFilter,
  AlertRule,
  AlertRuleFormData,
} from '../types/audit';

export const useAudit = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<AuditFilter>({});

  // Buscar logs de auditoria
  const {
    data: auditLogs,
    isLoading: isLoadingAuditLogs,
    error: auditLogsError,
    refetch: refetchAuditLogs,
  } = useQuery<AuditLog[]>({
    queryKey: ['audit-logs', filter],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/audit/logs', {
          params: filter,
        });
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar logs de auditoria');
        throw error;
      }
    },
  });

  // Buscar detalhes de um log de auditoria
  const getAuditLog = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/audit/logs/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar detalhes do log');
      throw error;
    }
  };

  // Exportar logs de auditoria
  const exportAuditLogsMutation = useMutation({
    mutationFn: async ({ format, filter }: { format: 'csv' | 'pdf'; filter?: AuditFilter }) => {
      try {
        const response = await apiClient.post(
          '/admin/audit/logs/export',
          {
            format,
            filter: filter || {},
          },
          { responseType: 'blob' }
        );
        
        // Criar URL para download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `audit-logs-${new Date().toISOString()}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        
        return true;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao exportar logs');
        throw error;
      }
    },
  });

  // Buscar regras de alerta
  const {
    data: alertRules,
    isLoading: isLoadingAlertRules,
    error: alertRulesError,
    refetch: refetchAlertRules,
  } = useQuery<AlertRule[]>({
    queryKey: ['alert-rules'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/audit/alerts');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar regras de alerta');
        throw error;
      }
    },
  });

  // Buscar uma regra de alerta específica
  const getAlertRule = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/audit/alerts/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar regra de alerta');
      throw error;
    }
  };

  // Criar ou atualizar uma regra de alerta
  const updateAlertRuleMutation = useMutation({
    mutationFn: async ({ id, data }: { id?: string; data: AlertRuleFormData }) => {
      try {
        let response;
        if (id) {
          response = await apiClient.put(`/admin/audit/alerts/${id}`, data);
        } else {
          response = await apiClient.post('/admin/audit/alerts', data);
        }
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar regra de alerta');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  // Excluir uma regra de alerta
  const deleteAlertRuleMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.delete(`/admin/audit/alerts/${id}`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao excluir regra de alerta');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  // Ativar/desativar uma regra de alerta
  const toggleAlertRuleMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      try {
        const response = await apiClient.patch(`/admin/audit/alerts/${id}/status`, {
          is_active: isActive,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message ||
            `Erro ao ${isActive ? 'ativar' : 'desativar'} regra de alerta`
        );
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  // Buscar tipos de eventos disponíveis
  const {
    data: eventTypes,
    isLoading: isLoadingEventTypes,
  } = useQuery<string[]>({
    queryKey: ['event-types'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/audit/event-types');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar tipos de eventos');
        throw error;
      }
    },
  });

  // Buscar tipos de entidades disponíveis
  const {
    data: entityTypes,
    isLoading: isLoadingEntityTypes,
  } = useQuery<string[]>({
    queryKey: ['entity-types'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/audit/entity-types');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar tipos de entidades');
        throw error;
      }
    },
  });

  return {
    auditLogs,
    isLoadingAuditLogs,
    filter,
    setFilter,
    getAuditLog,
    exportAuditLogs: exportAuditLogsMutation.mutate,
    isExportingAuditLogs: exportAuditLogsMutation.isPending,
    alertRules,
    isLoadingAlertRules,
    getAlertRule,
    updateAlertRule: updateAlertRuleMutation.mutate,
    isUpdatingAlertRule: updateAlertRuleMutation.isPending,
    deleteAlertRule: deleteAlertRuleMutation.mutate,
    isDeletingAlertRule: deleteAlertRuleMutation.isPending,
    toggleAlertRule: toggleAlertRuleMutation.mutate,
    isTogglingAlertRule: toggleAlertRuleMutation.isPending,
    eventTypes,
    isLoadingEventTypes,
    entityTypes,
    isLoadingEntityTypes,
    error,
    setError,
    refetchAuditLogs,
    refetchAlertRules,
  };
};