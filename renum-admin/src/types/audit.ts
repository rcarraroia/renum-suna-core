export interface AuditLog {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id?: string;
  actor_id?: string;
  actor_type: 'user' | 'admin' | 'system';
  actor_name?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface AuditFilter {
  event_type?: string;
  entity_type?: string;
  entity_id?: string;
  actor_id?: string;
  actor_type?: 'user' | 'admin' | 'system';
  start_date?: string;
  end_date?: string;
}

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  event_type?: string;
  entity_type?: string;
  actor_type?: 'user' | 'admin' | 'system';
  conditions: AlertCondition[];
  actions: AlertAction[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than';
  value: any;
}

export interface AlertAction {
  type: 'email' | 'webhook' | 'notification';
  config: Record<string, any>;
}

export interface AlertRuleFormData {
  name: string;
  description: string;
  event_type?: string;
  entity_type?: string;
  actor_type?: 'user' | 'admin' | 'system';
  conditions: AlertCondition[];
  actions: AlertAction[];
  is_active: boolean;
}