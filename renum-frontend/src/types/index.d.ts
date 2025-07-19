// Tipos globais para o projeto

// Tipo para um agente
export interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'inactive' | 'error';
  created_at: string;
  updated_at: string;
  configuration: AgentConfiguration;
  knowledge_base_ids: string[];
}

// Tipo para a configuração de um agente
export interface AgentConfiguration {
  model: string;
  system_prompt: string;
  tools: AgentTool[];
}

// Tipo para uma ferramenta de agente
export interface AgentTool {
  name: string;
  description: string;
}

// Tipo para uma base de conhecimento
export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at?: string;
  updated_at?: string;
}

// Tipo para uma mensagem de chat
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}

// Tipo para uma chamada de ferramenta
export interface ToolCall {
  id: string;
  type: string;
  name: string;
  input: any;
  output?: any;
  error?: string;
  status: 'pending' | 'completed' | 'error';
}

// Tipo para um usuário
export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

// Declarações para módulos sem tipos
declare module '*.svg' {
  const content: React.FunctionComponent<React.SVGAttributes<SVGElement>>;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}