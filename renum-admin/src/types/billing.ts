export interface BillingOverview {
  total_revenue: number;
  total_clients: number;
  active_clients: number;
  total_tokens: number;
  total_api_calls: number;
  period: string;
  previous_period_revenue: number;
  previous_period_tokens: number;
  previous_period_api_calls: number;
}

export interface ClientBilling {
  client_id: string;
  client_name: string;
  plan_type: string;
  revenue: number;
  tokens_used: number;
  api_calls: number;
  last_invoice_date: string;
  next_invoice_date: string;
  payment_status: 'paid' | 'pending' | 'overdue' | 'failed';
  is_active: boolean;
}

export interface BillingPeriod {
  start_date: string;
  end_date: string;
  label: string;
}

export interface UsageLimit {
  client_id: string;
  client_name?: string;
  resource_type: 'tokens' | 'api_calls' | 'storage' | 'users' | 'agents' | 'knowledge_bases';
  limit: number;
  current_usage: number;
  alert_threshold: number;
  is_hard_limit: boolean;
}

export interface UsageLimitFormData {
  client_id: string;
  resource_type: 'tokens' | 'api_calls' | 'storage' | 'users' | 'agents' | 'knowledge_bases';
  limit: number;
  alert_threshold: number;
  is_hard_limit: boolean;
}

export interface Invoice {
  id: string;
  client_id: string;
  client_name?: string;
  amount: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  issue_date: string;
  due_date: string;
  paid_date?: string;
  period_start: string;
  period_end: string;
  items: InvoiceItem[];
}

export interface InvoiceItem {
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
}

export interface UsageReport {
  period: string;
  data: {
    date: string;
    tokens: number;
    api_calls: number;
    storage_gb: number;
  }[];
  totals: {
    tokens: number;
    api_calls: number;
    storage_gb: number;
  };
}