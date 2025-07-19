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

// Chaves de consulta
export const queryKeys = {
  agents: {
    all: ['agents'],
    detail: (id: string) => ['agents', id],
    tools: ['agents', 'tools'],
    models: ['agents', 'models'],
  },
  knowledgeBases: {
    all: ['knowledgeBases'],
    detail: (id: string) => ['knowledgeBases', id],
  },
  chat: {
    messages: (agentId: string) => ['chat', 'messages', agentId],
  },
  auth: {
    user: ['auth', 'user'],
  },
};

// Funções de invalidação de cache
export const invalidateQueries = {
  agents: {
    all: () => queryClient.invalidateQueries({ queryKey: queryKeys.agents.all }),
    detail: (id: string) => queryClient.invalidateQueries({ queryKey: queryKeys.agents.detail(id) }),
  },
  knowledgeBases: {
    all: () => queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeBases.all }),
    detail: (id: string) => queryClient.invalidateQueries({ queryKey: queryKeys.knowledgeBases.detail(id) }),
  },
  chat: {
    messages: (agentId: string) => queryClient.invalidateQueries({ queryKey: queryKeys.chat.messages(agentId) }),
  },
};