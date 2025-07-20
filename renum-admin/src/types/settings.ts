export interface SystemSetting {
  id: string;
  key: string;
  value: any;
  description: string;
  is_sensitive: boolean;
  updated_by: string;
  updated_by_name?: string;
  created_at: string;
  updated_at: string;
}

export interface SystemSettingFormData {
  key: string;
  value: any;
  description: string;
  is_sensitive: boolean;
}

export interface SecuritySetting {
  password_policy: {
    min_length: number;
    require_uppercase: boolean;
    require_lowercase: boolean;
    require_numbers: boolean;
    require_special_chars: boolean;
    max_age_days: number;
  };
  session_timeout_minutes: number;
  max_login_attempts: number;
  lockout_duration_minutes: number;
  two_factor_auth: {
    enabled: boolean;
    required_for_admins: boolean;
    required_for_users: boolean;
  };
}

export interface IntegrationSetting {
  id: string;
  name: string;
  type: 'api' | 'oauth' | 'webhook' | 'smtp' | 'other';
  status: 'active' | 'inactive' | 'error';
  config: Record<string, any>;
  last_checked: string;
  error_message?: string;
}

export interface IntegrationSettingFormData {
  name: string;
  type: 'api' | 'oauth' | 'webhook' | 'smtp' | 'other';
  config: Record<string, any>;
}

export interface ChangeLog {
  id: string;
  setting_key: string;
  old_value: any;
  new_value: any;
  changed_by: string;
  changed_by_name?: string;
  changed_at: string;
}