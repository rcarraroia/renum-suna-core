/**
 * Cliente de API para comunicação com o backend Renum
 */

// Definir a URL base da API com base no ambiente
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Opções para requisições à API
 */
interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  requiresAuth?: boolean;
}

/**
 * Verifica se estamos em um ambiente de navegador
 */
const isBrowser = typeof window !== 'undefined';

/**
 * Obtém o token de autenticação do localStorage
 */
const getAuthToken = (): string | null => {
  if (!isBrowser) return null;
  try {
    return localStorage.getItem('token');
  } catch (error) {
    console.error('Erro ao acessar localStorage:', error);
    return null;
  }
};

/**
 * Salva o token de autenticação no localStorage
 */
const setAuthToken = (token: string): void => {
  if (!isBrowser) return;
  try {
    localStorage.setItem('token', token);
  } catch (error) {
    console.error('Erro ao salvar token no localStorage:', error);
  }
};

/**
 * Salva os dados do usuário no localStorage
 */
const setUserData = (user: any): void => {
  if (!isBrowser) return;
  try {
    localStorage.setItem('user', JSON.stringify(user));
  } catch (error) {
    console.error('Erro ao salvar dados do usuário no localStorage:', error);
  }
};

/**
 * Remove os dados de autenticação do localStorage
 */
const clearAuthData = (): void => {
  if (!isBrowser) return;
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  } catch (error) {
    console.error('Erro ao remover dados de autenticação do localStorage:', error);
  }
};

/**
 * Realiza uma requisição à API
 * @param endpoint - Endpoint da API (sem a URL base)
 * @param options - Opções da requisição
 * @returns Resposta da API
 */
export async function apiRequest<T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    requiresAuth = true,
  } = options;

  // Configurar headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Adicionar token de autenticação se necessário
  if (requiresAuth) {
    const token = getAuthToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    } else if (requiresAuth && isBrowser) {
      // Redirecionar para login se não houver token
      window.location.href = '/login';
      throw new Error('Autenticação necessária');
    }
  }

  // Configurar opções da requisição
  const requestOptions: RequestInit = {
    method,
    headers: requestHeaders,
    credentials: 'include',
  };

  // Adicionar body se necessário
  if (body) {
    requestOptions.body = JSON.stringify(body);
  }

  try {
    // Realizar requisição
    const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions);

    // Verificar se a resposta é JSON
    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    
    // Processar resposta
    const data = isJson ? await response.json() : await response.text();

    // Verificar se a requisição foi bem-sucedida
    if (!response.ok) {
      // Tratar erro de autenticação
      if (response.status === 401 && isBrowser) {
        clearAuthData();
        window.location.href = '/login';
      }
      
      // Lançar erro com detalhes da resposta
      throw new Error(
        isJson && data.detail 
          ? data.detail 
          : `Erro ${response.status}: ${response.statusText || 'Erro desconhecido'}`
      );
    }

    return data as T;
  } catch (error: any) {
    console.error('Erro na requisição à API:', error);
    
    // Verificar se é um erro de rede (CORS, conexão, etc.)
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Erro de conexão com o servidor. Verifique sua conexão de internet ou tente novamente mais tarde.');
    }
    
    throw error;
  }
}

/**
 * Cliente de API para autenticação
 */
export const authApi = {
  /**
   * Realiza login na plataforma
   * @param email - Email do usuário
   * @param password - Senha do usuário
   * @returns Dados do usuário e token
   */
  login: async (email: string, password: string) => {
    try {
      const response = await apiRequest<{ user: any; token: string }>('/api/auth/login', {
        method: 'POST',
        body: { email, password },
        requiresAuth: false,
      });
      
      // Salvar token e dados do usuário
      if (response.token) {
        setAuthToken(response.token);
      }
      
      if (response.user) {
        setUserData(response.user);
      }
      
      return response;
    } catch (error) {
      // Limpar dados de autenticação em caso de erro
      clearAuthData();
      throw error;
    }
  },

  /**
   * Realiza registro na plataforma
   * @param name - Nome do usuário
   * @param email - Email do usuário
   * @param password - Senha do usuário
   * @returns Dados do usuário registrado
   */
  register: async (name: string, email: string, password: string) => {
    return apiRequest<{ user: any }>('/api/auth/register', {
      method: 'POST',
      body: { name, email, password },
      requiresAuth: false,
    });
  },

  /**
   * Realiza logout na plataforma
   */
  logout: async () => {
    clearAuthData();
    if (isBrowser) {
      window.location.href = '/login';
    }
  },
};

/**
 * Cliente de API para agentes
 */
export const agentApi = {
  /**
   * Lista todos os agentes do usuário
   * @returns Lista de agentes
   */
  listAgents: async () => {
    return apiRequest<{ agents: any[] }>('/api/agents');
  },

  /**
   * Obtém detalhes de um agente específico
   * @param id - ID do agente
   * @returns Detalhes do agente
   */
  getAgent: async (id: string) => {
    return apiRequest<{ agent: any }>(`/api/agents/${id}`);
  },

  /**
   * Cria um novo agente
   * @param agentData - Dados do agente
   * @returns Agente criado
   */
  createAgent: async (agentData: any) => {
    return apiRequest<{ agent: any }>('/api/agents', {
      method: 'POST',
      body: agentData,
    });
  },

  /**
   * Atualiza um agente existente
   * @param id - ID do agente
   * @param agentData - Dados atualizados do agente
   * @returns Agente atualizado
   */
  updateAgent: async (id: string, agentData: any) => {
    return apiRequest<{ agent: any }>(`/api/agents/${id}`, {
      method: 'PUT',
      body: agentData,
    });
  },

  /**
   * Exclui um agente
   * @param id - ID do agente
   */
  deleteAgent: async (id: string) => {
    return apiRequest(`/api/agents/${id}`, {
      method: 'DELETE',
    });
  },

  /**
   * Lista modelos de IA disponíveis
   * @returns Lista de modelos
   */
  listModels: async () => {
    return apiRequest<{ models: any[] }>('/api/models');
  },

  /**
   * Lista ferramentas disponíveis
   * @returns Lista de ferramentas
   */
  listTools: async () => {
    return apiRequest<{ tools: any[] }>('/api/tools');
  },
};

/**
 * Cliente de API para bases de conhecimento
 */
export const knowledgeBaseApi = {
  /**
   * Lista todas as bases de conhecimento do usuário
   * @returns Lista de bases de conhecimento
   */
  listKnowledgeBases: async () => {
    return apiRequest<{ knowledge_bases: any[] }>('/api/knowledge-bases');
  },

  /**
   * Obtém detalhes de uma base de conhecimento específica
   * @param id - ID da base de conhecimento
   * @returns Detalhes da base de conhecimento
   */
  getKnowledgeBase: async (id: string) => {
    return apiRequest<{ knowledge_base: any }>(`/api/knowledge-bases/${id}`);
  },
};

/**
 * Cliente de API para chat com agentes
 */
export const chatApi = {
  /**
   * Envia uma mensagem para um agente
   * @param agentId - ID do agente
   * @param message - Mensagem a ser enviada
   * @returns Resposta do agente
   */
  sendMessage: async (agentId: string, message: string) => {
    return apiRequest<{ response: any }>(`/api/agents/${agentId}/chat`, {
      method: 'POST',
      body: { message },
    });
  },

  /**
   * Obtém o histórico de conversas com um agente
   * @param agentId - ID do agente
   * @returns Histórico de conversas
   */
  getConversationHistory: async (agentId: string) => {
    return apiRequest<{ messages: any[] }>(`/api/agents/${agentId}/conversations`);
  },
};