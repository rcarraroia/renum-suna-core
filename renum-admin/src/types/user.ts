export interface User {
  id: string;
  auth_user_id: string;
  client_id: string;
  client_name?: string; // Adicionado para exibir o nome do cliente na listagem
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserFormData {
  client_id: string;
  name: string;
  email: string;
  role: string;
  password?: string; // Opcional, usado apenas na criação
  is_active: boolean;
}

export interface UserActivity {
  user_id: string;
  last_login: string;
  total_threads: number;
  total_messages: number;
  agents_used: number;
  last_agent_used?: string;
  last_agent_name?: string;
}