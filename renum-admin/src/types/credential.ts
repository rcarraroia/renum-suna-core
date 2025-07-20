export interface Credential {
  id: string;
  admin_id: string;
  admin_name?: string; // Adicionado para exibir o nome do administrador na listagem
  service_name: string;
  credential_type: 'api_key' | 'oauth_token' | 'service_account';
  encrypted_value: string;
  is_active: boolean;
  last_used?: string;
  expires_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CredentialFormData {
  service_name: string;
  credential_type: 'api_key' | 'oauth_token' | 'service_account';
  value: string;
  is_active: boolean;
  expires_at?: string;
  metadata?: Record<string, any>;
}

export interface CredentialMetadata {
  provider?: string;
  description?: string;
  environment?: string;
  scope?: string[];
  rate_limit?: number;
  usage_notes?: string;
}

export interface CredentialUsage {
  credential_id: string;
  total_calls: number;
  last_30_days_calls: number;
  average_daily_calls: number;
  last_error?: string;
  last_error_date?: string;
}