export interface Admin {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: 'admin' | 'superadmin';
  is_active: boolean;
  last_login?: Date;
  created_at: Date;
  updated_at: Date;
}