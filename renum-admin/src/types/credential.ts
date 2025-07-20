export interface AdminCredential {
  id: string;
  admin_id: string;
  service_name: string;
  credential_type: 'api_key' | 'oauth_token' | 'service_account';
  is_active: boolean;
  last_used?: Date;
  expires_at?: Date;
  metadata: Record<string, any>;
  created_at: Date;
  updated_at: Date;
}