import { QueryClient } from '@tanstack/react-query';

// Configuração do React Query
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
});

// Chaves de consulta para React Query
export const queryKeys = {
  agents: {
    all: ['agents'] as const,
    detail: (id: string) => ['agents', id] as const,
    chat: (id: string) => ['agents', id, 'chat'] as const,
  },
  knowledgeBases: {
    all: ['knowledgeBases'] as const,
    detail: (id: string) => ['knowledgeBases', id] as const,
  },
  tools: {
    all: ['tools'] as const,
  },
  models: {
    all: ['models'] as const,
  },
  user: {
    profile: ['user', 'profile'] as const,
  },
};