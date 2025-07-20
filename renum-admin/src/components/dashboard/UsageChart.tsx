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

// Dados de exemplo
const data = [
  { name: '01/07', tokens: 4000, chamadas: 240, custo: 1200 },
  { name: '02/07', tokens: 3000, chamadas: 198, custo: 900 },
  { name: '03/07', tokens: 2000, chamadas: 120, custo: 600 },
  { name: '04/07', tokens: 2780, chamadas: 167, custo: 834 },
  { name: '05/07', tokens: 1890, chamadas: 113, custo: 567 },
  { name: '06/07', tokens: 2390, chamadas: 143, custo: 717 },
  { name: '07/07', tokens: 3490, chamadas: 209, custo: 1047 },
  { name: '08/07', tokens: 3490, chamadas: 209, custo: 1047 },
  { name: '09/07', tokens: 2490, chamadas: 149, custo: 747 },
  { name: '10/07', tokens: 2790, chamadas: 167, custo: 837 },
  { name: '11/07', tokens: 3090, chamadas: 185, custo: 927 },
  { name: '12/07', tokens: 3290, chamadas: 197, custo: 987 },
  { name: '13/07', tokens: 3490, chamadas: 209, custo: 1047 },
  { name: '14/07', tokens: 4000, chamadas: 240, custo: 1200 },
];

interface UsageChartProps {
  height?: number;
}

const UsageChart: React.FC<UsageChartProps> = ({ height = 300 }) => {
  const [activeMetric, setActiveMetric] = React.useState<'tokens' | 'chamadas' | 'custo'>('tokens');

  const metrics = [
    { id: 'tokens', name: 'Tokens', color: '#0ea5e9' },
    { id: 'chamadas', name: 'Chamadas API', color: '#10b981' },
    { id: 'custo', name: 'Custo (R$)', color: '#f59e0b' },
  ];

  return (
    <div>
      <div className="flex space-x-4 mb-4">
        {metrics.map((metric) => (
          <button
            key={metric.id}
            className={`px-3 py-1 rounded-md text-sm font-medium ${
              activeMetric === metric.id
                ? 'bg-primary-100 text-primary-800'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            onClick={() => setActiveMetric(metric.id as any)}
          >
            {metric.name}
          </button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          {activeMetric === 'tokens' && (
            <Line
              type="monotone"
              dataKey="tokens"
              stroke="#0ea5e9"
              activeDot={{ r: 8 }}
              name="Tokens"
            />
          )}
          {activeMetric === 'chamadas' && (
            <Line
              type="monotone"
              dataKey="chamadas"
              stroke="#10b981"
              activeDot={{ r: 8 }}
              name="Chamadas API"
            />
          )}
          {activeMetric === 'custo' && (
            <Line
              type="monotone"
              dataKey="custo"
              stroke="#f59e0b"
              activeDot={{ r: 8 }}
              name="Custo (R$)"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UsageChart;