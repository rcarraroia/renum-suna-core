/**
 * Configuração do React Query Client
 */

import { QueryClient } from 'react-query';

// Configuração padrão para o QueryClient
const defaultOptions = {
  queries: {
    refetchOnWindowFocus: false,
    retry: 1,
    staleTime: 1000 * 60 * 5, // 5 minutos
    cacheTime: 1000 * 60 * 30, // 30 minutos
  },
  mutations: {
    retry: 1,
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
export const invalidateQueries = (queryKey: string | any[]) => {
  queryClient.invalidateQueries(queryKey);
};

// Função para redefinir consultas específicas
export const resetQueries = (queryKey: string | any[]) => {
  queryClient.resetQueries(queryKey);
};

// Função para pré-carregar dados
export const prefetchQuery = async (queryKey: string | any[], queryFn: () => Promise<any>) => {
  await queryClient.prefetchQuery(queryKey, queryFn);
};

// Função para definir dados de consulta manualmente
export const setQueryData = (queryKey: string | any[], data: any) => {
  queryClient.setQueryData(queryKey, data);
};

// Função para obter dados de consulta do cache
export const getQueryData = (queryKey: string | any[]) => {
  return queryClient.getQueryData(queryKey);
};

export default queryClient;