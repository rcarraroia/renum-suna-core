export interface Agent {
  id: string;
  client_id?: string; // Opcional para agentes administrativos
  name: string;
  description?: string;
  type: 'chat' | 'assistant' | 'admin' | 'custom';
  status: 'active' | 'inactive' | 'draft';
  configuration: AgentConfiguration;
  usage_stats: AgentUsageStats;
  created_at: Date;
  updated_at: Date;
}

export interface AgentConfiguration {
  model: string;
  temperature: number;
  max_tokens: number;
  tools: AgentTool[];
  system_prompt?: string;
  knowledge_base_ids?: string[];
  [key: string]: any;
}

export interface AgentTool {
  id: string;
  name: string;
  description?: string;
  type: 'function' | 'retrieval' | 'web' | 'custom';
  configuration: Record<string, any>;
}

export interface AgentUsageStats {
  total_conversations: number;
  total_messages: number;
  total_tokens: number;
  avg_response_time: number;
  last_used?: Date;
}