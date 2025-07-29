import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { LocalStorageManager } from '../utils/localStorage';

/**
 * Interface para o usuário autenticado
 */
interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

/**
 * Interface para o estado de autenticação
 */
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

/**
 * Verifica se estamos em um ambiente de navegador
 */
const isBrowser = typeof window !== 'undefined';

/**
 * Store para gerenciar o estado de autenticação
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => {
        // Salvar no localStorage manualmente para garantir
        LocalStorageManager.setToken(token);
        LocalStorageManager.setItem('user', JSON.stringify(user));
        set({ user, token, isAuthenticated: true });
      },
      clearAuth: () => {
        // Limpar do localStorage manualmente para garantir
        LocalStorageManager.removeToken();
        LocalStorageManager.removeItem('user');
        set({ user: null, token: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => {
        // Usar LocalStorageManager que já trata SSR
        if (LocalStorageManager.isAvailable()) {
          return localStorage;
        } else if (isBrowser) {
          console.warn('localStorage não disponível, usando sessionStorage');
          return sessionStorage;
        }
        
        // Fallback para quando não estamos no navegador (SSR)
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        };
      }),
    }
  )
);

/**
 * Interface para um agente
 */
interface Agent {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  configuration: {
    model: string;
    system_prompt: string;
    tools: any[];
  };
  knowledge_base_ids: string[];
  knowledge_bases?: Array<{
    id: string;
    name: string;
    description?: string;
    document_count?: number;
  }>;
  usage?: {
    total_executions: number;
    last_execution: string;
    average_response_time: number;
    token_usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
  };
}

/**
 * Interface para o estado de agentes
 */
interface AgentState {
  agents: Agent[];
  selectedAgent: Agent | null;
  isLoading: boolean;
  error: string | null;
  setAgents: (agents: Agent[]) => void;
  setSelectedAgent: (agent: Agent | null) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (updatedAgent: Agent) => void;
  removeAgent: (agentId: string) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * Store para gerenciar o estado de agentes
 */
export const useAgentStore = create<AgentState>()(
  persist(
    (set) => ({
      agents: [],
      selectedAgent: null,
      isLoading: false,
      error: null,
      setAgents: (agents) => set({ agents }),
      setSelectedAgent: (selectedAgent) => set({ selectedAgent }),
      addAgent: (agent) => set((state) => ({ agents: [...state.agents, agent] })),
      updateAgent: (updatedAgent) =>
        set((state) => ({
          agents: state.agents.map((agent) =>
            agent.id === updatedAgent.id ? updatedAgent : agent
          ),
          selectedAgent:
            state.selectedAgent?.id === updatedAgent.id
              ? updatedAgent
              : state.selectedAgent,
        })),
      removeAgent: (agentId) =>
        set((state) => ({
          agents: state.agents.filter((agent) => agent.id !== agentId),
          selectedAgent:
            state.selectedAgent?.id === agentId ? null : state.selectedAgent,
        })),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'agent-storage',
      storage: createJSONStorage(() => {
        // Usar LocalStorageManager que já trata SSR
        if (LocalStorageManager.isAvailable()) {
          return localStorage;
        } else if (isBrowser) {
          console.warn('localStorage não disponível, usando sessionStorage');
          return sessionStorage;
        }
        
        // Fallback para quando não estamos no navegador (SSR)
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        };
      }),
    }
  )
);

/**
 * Interface para uma mensagem de chat
 */
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tool_calls?: any[];
}

/**
 * Interface para o estado de chat
 */
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

/**
 * Store para gerenciar o estado de chat
 */
export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isLoading: false,
  error: null,
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));