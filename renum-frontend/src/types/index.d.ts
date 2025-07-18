// Declarações de tipos globais para o projeto

// Tipos para agentes
export interface Agent {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  configuration: AgentConfiguration;
  knowledge_base_ids: string[];
}

export interface AgentConfiguration {
  model: string;
  system_prompt: string;
  tools: AgentTool[];
}

export interface AgentTool {
  name: string;
  description: string;
}

// Tipos para bases de conhecimento
export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at?: string;
  updated_at?: string;
}

// Tipos para ferramentas
export interface ToolItem {
  id: string;
  name: string;
  description: string;
  category?: string;
  icon?: string;
  requires_configuration?: boolean;
}

// Tipos para chat
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  tool: string;
  input: Record<string, any>;
  output?: Record<string, any>;
  status: 'pending' | 'completed' | 'failed';
}

// Tipos para autenticação
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

// Tipos para respostas da API
export interface ApiResponse<T> {
  data: T;
  error?: string;
}