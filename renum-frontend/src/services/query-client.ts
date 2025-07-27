/**
 * Configuração do React Query Client
 */

import { QueryClient, QueryKey } from '@tanstack/react-query';

// Configuração padrão para o QueryClient
const defaultOptions = {
  queries: {
    refetchOnWindowFocus: false,
    refetchOnMount: true,
    refetchOnReconnect: true,
    retry: (failureCount: number, error: any) => {
      // Não tenta novamente para erros 4xx (client errors)
      if (error && typeof error === 'object' && 'status' in error) {
        const status = error.status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      // Tenta até 3 vezes para outros erros
      return failureCount < 3;
    },
    staleTime: 1000 * 60 * 5, // 5 minutos
    gcTime: 1000 * 60 * 30, // 30 minutos (anteriormente cacheTime)
  },
  mutations: {
    retry: (failureCount: number, error: any) => {
      // Não tenta novamente para erros 4xx (client errors)
      if (error && typeof error === 'object' && 'status' in error) {
        const status = error.status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      // Tenta até 2 vezes para outros erros
      return failureCount < 2;
    },
  },
};

// Cria uma instância do QueryClient com as configurações padrão
export const queryClient = new QueryClient({
  defaultOptions,
});

// Função para limpar o cache do React Query
export const clearQueryCache = () => {
  queryClient.clear();
};

// Função para invalidar consultas específicas
export const invalidateQueries = (queryKey: QueryKey) => {
  queryClient.invalidateQueries({ queryKey });
};

// Função para redefinir consultas específicas
export const resetQueries = (queryKey: QueryKey) => {
  queryClient.resetQueries({ queryKey });
};

// Função para pré-carregar dados
export const prefetchQuery = async (queryKey: QueryKey, queryFn: () => Promise<any>) => {
  await queryClient.prefetchQuery({ queryKey, queryFn });
};

// Função para definir dados de consulta manualmente
export const setQueryData = (queryKey: QueryKey, data: any) => {
  queryClient.setQueryData(queryKey, data);
};

// Função para obter dados de consulta do cache
export const getQueryData = (queryKey: QueryKey) => {
  return queryClient.getQueryData(queryKey);
};

export default queryClient;