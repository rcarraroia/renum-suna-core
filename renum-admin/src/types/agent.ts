export interface Agent {
  id: string;
  client_id: string;
  client_name?: string; // Adicionado para exibir o nome do cliente na listagem
  created_by: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface AgentFormData {
  client_id: string;
  name: string;
  description?: string;
  system_prompt?: string;
  model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  is_public: boolean;
}

export interface AgentUsageStats {
  agent_id: string;
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  avg_response_time: number;
  last_used?: string;
  users_count: number;
  feedback_score?: number;
}

export interface AgentModel {
  id: string;
  name: string;
  provider: string;
  max_tokens: number;
  cost_per_1k_tokens: number;
  is_available: boolean;
}