export interface Client {
  id: string;
  name: string;
  email: string;
  phone?: string;
  address?: string;
  logo_url?: string;
  plan: 'basic' | 'standard' | 'premium' | 'enterprise';
  status: 'active' | 'inactive' | 'pending';
  usage_limit?: number;
  current_usage?: number;
  created_at: Date;
  updated_at: Date;
}