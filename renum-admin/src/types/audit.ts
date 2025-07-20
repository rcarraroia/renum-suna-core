export interface AuditLog {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_id: string;
  actor_type: 'user' | 'admin' | 'system';
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
  created_at: Date;
}

export interface AuditFilter {
  event_type?: string;
  entity_type?: string;
  entity_id?: string;
  actor_id?: string;
  actor_type?: 'user' | 'admin' | 'system';
  start_date?: Date;
  end_date?: Date;
  search?: string;
}