export interface SystemSetting {
  id: string;
  key: string;
  value: any;
  description: string;
  is_sensitive: boolean;
  updated_by: string;
  created_at: Date;
  updated_at: Date;
}

export interface SecuritySettings {
  password_policy: {
    min_length: number;
    require_uppercase: boolean;
    require_lowercase: boolean;
    require_number: boolean;
    require_special: boolean;
    expiration_days: number;
  };
  session_timeout: number;
  two_factor_auth: boolean;
  ip_restrictions: string[];
}

export interface IntegrationSettings {
  openai: {
    enabled: boolean;
    default_model: string;
    organization_id?: string;
  };
  anthropic: {
    enabled: boolean;
    default_model: string;
  };
  supabase: {
    enabled: boolean;
    project_url: string;
  };
  [key: string]: any;
}