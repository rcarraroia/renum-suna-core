export interface BillingOverview {
  total_revenue: number;
  active_clients: number;
  total_usage: number;
  period: string;
  comparison: {
    percentage: number;
    previous_period: string;
  };
}

export interface ClientUsage {
  client_id: string;
  client_name: string;
  plan: string;
  usage: {
    tokens: number;
    conversations: number;
    api_calls: number;
    storage: number;
  };
  cost: number;
  limit_percentage: number;
  period: string;
}

export interface UsageReport {
  period: {
    start: Date;
    end: Date;
  };
  total_usage: {
    tokens: number;
    conversations: number;
    api_calls: number;
    storage: number;
  };
  clients: ClientUsage[];
  daily_usage: {
    date: string;
    tokens: number;
    conversations: number;
    api_calls: number;
  }[];
}