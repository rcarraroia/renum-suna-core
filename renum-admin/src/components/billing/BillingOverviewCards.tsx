import React from 'react';
import { DollarSign, Users, Zap, Server } from 'lucide-react';
import { BillingOverview } from '../../types/billing';
import { formatCurrency } from '../../lib/utils';
import MetricsCard from '../dashboard/MetricsCard';

interface BillingOverviewCardsProps {
  data: BillingOverview;
  isLoading: boolean;
}

const BillingOverviewCards: React.FC<BillingOverviewCardsProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="bg-white p-6 rounded-lg shadow animate-pulse h-32"
          />
        ))}
      </div>
    );
  }

  const revenueChange = data.previous_period_revenue
    ? ((data.total_revenue - data.previous_period_revenue) / data.previous_period_revenue) * 100
    : 0;

  const tokensChange = data.previous_period_tokens
    ? ((data.total_tokens - data.previous_period_tokens) / data.previous_period_tokens) * 100
    : 0;

  const apiCallsChange = data.previous_period_api_calls
    ? ((data.total_api_calls - data.previous_period_api_calls) / data.previous_period_api_calls) * 100
    : 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricsCard
        title="Receita Total"
        value={formatCurrency(data.total_revenue)}
        change={revenueChange}
        icon={<DollarSign className="h-6 w-6 text-primary-600" />}
      />
      <MetricsCard
        title="Clientes Ativos"
        value={`${data.active_clients}/${data.total_clients}`}
        icon={<Users className="h-6 w-6 text-primary-600" />}
      />
      <MetricsCard
        title="Tokens Utilizados"
        value={data.total_tokens.toLocaleString()}
        change={tokensChange}
        icon={<Zap className="h-6 w-6 text-primary-600" />}
      />
      <MetricsCard
        title="Chamadas de API"
        value={data.total_api_calls.toLocaleString()}
        change={apiCallsChange}
        icon={<Server className="h-6 w-6 text-primary-600" />}
      />
    </div>
  );
};

export default BillingOverviewCards;