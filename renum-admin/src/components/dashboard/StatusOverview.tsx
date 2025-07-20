import React from 'react';

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'outage';
}

const statusClasses = {
  operational: 'bg-green-100 text-green-800',
  degraded: 'bg-yellow-100 text-yellow-800',
  outage: 'bg-red-100 text-red-800',
};

const statusLabels = {
  operational: 'Operacional',
  degraded: 'Degradado',
  outage: 'Fora do ar',
};

// Dados de exemplo
const services: ServiceStatus[] = [
  { name: 'API Renum', status: 'operational' },
  { name: 'API Suna', status: 'operational' },
  { name: 'Supabase', status: 'operational' },
  { name: 'OpenAI', status: 'degraded' },
  { name: 'Anthropic', status: 'operational' },
];

interface StatusOverviewProps {
  className?: string;
}

const StatusOverview: React.FC<StatusOverviewProps> = ({ className }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {services.map((service, index) => (
        <div key={index} className="flex items-center justify-between">
          <span>{service.name}</span>
          <span
            className={`px-2 py-1 ${
              statusClasses[service.status]
            } rounded-full text-xs`}
          >
            {statusLabels[service.status]}
          </span>
        </div>
      ))}
    </div>
  );
};

export default StatusOverview;