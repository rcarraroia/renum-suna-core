import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import {
  BillingOverview,
  ClientBilling,
  BillingPeriod,
  UsageLimit,
  UsageLimitFormData,
  Invoice,
  UsageReport,
} from '../types/billing';

export const useBilling = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [currentPeriod, setCurrentPeriod] = useState<BillingPeriod | null>(null);

  // Buscar períodos de faturamento disponíveis
  const {
    data: billingPeriods,
    isLoading: isLoadingPeriods,
    error: periodsError,
  } = useQuery<BillingPeriod[]>({
    queryKey: ['billing-periods'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/billing/periods');
        // Definir o período atual como o mais recente
        if (response.data.length > 0) {
          setCurrentPeriod(response.data[0]);
        }
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar períodos de faturamento');
        throw error;
      }
    },
  });

  // Hook para buscar visão geral de faturamento
  const useBillingOverview = (period?: string) => {
    return useQuery<BillingOverview>({
      queryKey: ['billing-overview', period],
      queryFn: async () => {
        try {
          const response = await apiClient.get('/admin/billing/overview', {
            params: { period },
          });
          return response.data;
        } catch (error: any) {
          setError(error.response?.data?.message || 'Erro ao buscar visão geral de faturamento');
          throw error;
        }
      },
      enabled: !!period || !!currentPeriod,
    });
  };

  // Hook para buscar faturamento por cliente
  const useClientBilling = (period?: string) => {
    return useQuery<ClientBilling[]>({
      queryKey: ['client-billing', period],
      queryFn: async () => {
        try {
          const response = await apiClient.get('/admin/billing/clients', {
            params: { period },
          });
          return response.data;
        } catch (error: any) {
          setError(error.response?.data?.message || 'Erro ao buscar faturamento por cliente');
          throw error;
        }
      },
      enabled: !!period || !!currentPeriod,
    });
  };

  // Buscar limites de uso
  const {
    data: usageLimits,
    isLoading: isLoadingLimits,
    error: limitsError,
    refetch: refetchLimits,
  } = useQuery<UsageLimit[]>({
    queryKey: ['usage-limits'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/billing/limits');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao buscar limites de uso');
        throw error;
      }
    },
  });

  // Buscar limites de uso por cliente
  const getClientLimits = async (clientId: string) => {
    try {
      const response = await apiClient.get(`/admin/billing/clients/${clientId}/limits`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar limites do cliente');
      throw error;
    }
  };

  // Criar ou atualizar limite de uso
  const updateLimitMutation = useMutation({
    mutationFn: async (data: UsageLimitFormData) => {
      try {
        const response = await apiClient.post('/admin/billing/limits', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao atualizar limite de uso');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });
    },
  });

  // Excluir limite de uso
  const deleteLimitMutation = useMutation({
    mutationFn: async ({ clientId, resourceType }: { clientId: string; resourceType: string }) => {
      try {
        const response = await apiClient.delete(`/admin/billing/limits`, {
          data: { client_id: clientId, resource_type: resourceType },
        });
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao excluir limite de uso');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usage-limits'] });
    },
  });

  // Hook para buscar faturas
  const useInvoices = (clientId?: string, status?: string, period?: string) => {
    return useQuery<Invoice[]>({
      queryKey: ['invoices', clientId, status, period],
      queryFn: async () => {
        try {
          const response = await apiClient.get('/admin/billing/invoices', {
            params: { client_id: clientId, status, period },
          });
          return response.data;
        } catch (error: any) {
          setError(error.response?.data?.message || 'Erro ao buscar faturas');
          throw error;
        }
      },
    });
  };

  // Buscar detalhes de uma fatura
  const getInvoice = async (invoiceId: string) => {
    try {
      const response = await apiClient.get(`/admin/billing/invoices/${invoiceId}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Erro ao buscar detalhes da fatura');
      throw error;
    }
  };

  // Hook para gerar relatório de uso
  const useUsageReport = (clientId?: string, period?: string) => {
    return useQuery<UsageReport>({
      queryKey: ['usage-report', clientId, period],
      queryFn: async () => {
        try {
          const response = await apiClient.get('/admin/billing/reports/usage', {
            params: { client_id: clientId, period },
          });
          return response.data;
        } catch (error: any) {
          setError(error.response?.data?.message || 'Erro ao gerar relatório de uso');
          throw error;
        }
      },
      enabled: !!period || !!currentPeriod,
    });
  };

  // Exportar relatório
  const exportReportMutation = useMutation({
    mutationFn: async ({
      type,
      format,
      period,
      clientId,
    }: {
      type: 'usage' | 'billing' | 'invoices';
      format: 'csv' | 'pdf';
      period?: string;
      clientId?: string;
    }) => {
      try {
        const response = await apiClient.post(
          '/admin/billing/reports/export',
          {
            type,
            format,
            period,
            client_id: clientId,
          },
          { responseType: 'blob' }
        );
        
        // Criar URL para download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `${type}-report-${period || 'all'}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        
        return true;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Erro ao exportar relatório');
        throw error;
      }
    },
  });

  return {
    billingPeriods,
    isLoadingPeriods,
    currentPeriod,
    setCurrentPeriod,
    useBillingOverview,
    useClientBilling,
    usageLimits,
    isLoadingLimits,
    getClientLimits,
    updateLimit: updateLimitMutation.mutate,
    isUpdatingLimit: updateLimitMutation.isPending,
    deleteLimit: deleteLimitMutation.mutate,
    isDeletingLimit: deleteLimitMutation.isPending,
    useInvoices,
    getInvoice,
    useUsageReport,
    exportReport: exportReportMutation.mutate,
    isExportingReport: exportReportMutation.isPending,
    error,
    setError,
    refetchLimits,
  };
};