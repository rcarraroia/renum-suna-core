import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { UsageReport } from '../../types/billing';

interface UsageChartProps {
  data: UsageReport;
  isLoading: boolean;
  showTokens?: boolean;
  showApiCalls?: boolean;
  showStorage?: boolean;
}

const UsageChart: React.FC<UsageChartProps> = ({
  data,
  isLoading,
  showTokens = true,
  showApiCalls = true,
  showStorage = true,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow animate-pulse h-80" />
    );
  }

  if (!data || !data.data || data.data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow h-80 flex items-center justify-center">
        <p className="text-gray-500">Nenhum dado disponível para o período selecionado</p>
      </div>
    );
  }

  // Formatar dados para o gráfico
  const chartData = data.data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('pt-BR'),
    tokens: item.tokens,
    api_calls: item.api_calls,
    storage_gb: item.storage_gb,
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Uso ao Longo do Tempo</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            {showTokens && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="tokens"
                name="Tokens"
                stroke="#8884d8"
                activeDot={{ r: 8 }}
              />
            )}
            {showApiCalls && (
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="api_calls"
                name="Chamadas API"
                stroke="#82ca9d"
              />
            )}
            {showStorage && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="storage_gb"
                name="Armazenamento (GB)"
                stroke="#ffc658"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default UsageChart;