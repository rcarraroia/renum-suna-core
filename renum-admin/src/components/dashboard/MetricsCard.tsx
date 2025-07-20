import React from 'react';
import { Card } from '../ui/Card';

interface MetricsCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
}

const MetricsCard: React.FC<MetricsCardProps> = ({ title, value, change, icon }) => {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {change !== undefined && (
            <p className={`text-xs mt-1 ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {change >= 0 ? '+' : ''}{change}% desde o último período
            </p>
          )}
        </div>
        <div className="p-3 bg-primary-100 rounded-full">
          {icon}
        </div>
      </div>
    </Card>
  );
};

export default MetricsCard;