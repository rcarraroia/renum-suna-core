import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

// Dados de exemplo
const data = [
  { name: 'Jan', tokens: 4000, calls: 2400 },
  { name: 'Fev', tokens: 3000, calls: 1398 },
  { name: 'Mar', tokens: 2000, calls: 9800 },
  { name: 'Abr', tokens: 2780, calls: 3908 },
  { name: 'Mai', tokens: 1890, calls: 4800 },
  { name: 'Jun', tokens: 2390, calls: 3800 },
  { name: 'Jul', tokens: 3490, calls: 4300 },
];

interface UsageChartProps {
  className?: string;
}

const UsageChart: React.FC<UsageChartProps> = ({ className }) => {
  return (
    <div className={`h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
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
          <Line
            type="monotone"
            dataKey="tokens"
            stroke="#0ea5e9"
            activeDot={{ r: 8 }}
          />
          <Line type="monotone" dataKey="calls" stroke="#6366f1" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UsageChart;