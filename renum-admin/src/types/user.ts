export interface User {
  id: string;
  client_id: string;
  name: string;
  email: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  status: 'active' | 'inactive' | 'pending';
  last_login?: Date;
  created_at: Date;
  updated_at: Date;
}