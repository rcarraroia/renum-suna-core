import React from 'react';

interface Service {
  name: string;
  status: 'operational' | 'degraded' | 'outage';
  lastUpdated: Date;
}

interface StatusOverviewProps {
  services?: Service[];
}

const StatusOverview: React.FC<StatusOverviewProps> = ({ services }) => {
  // Dados de exemplo se não forem fornecidos
  const defaultServices: Service[] = [
    {
      name: 'API Renum',
      status: 'operational',
      lastUpdated: new Date(),
    },
    {
      name: 'API Suna',
      status: 'operational',
      lastUpdated: new Date(),
    },
    {
      name: 'Supabase',
      status: 'operational',
      lastUpdated: new Date(),
    },
    {
      name: 'OpenAI',
      status: 'degraded',
      lastUpdated: new Date(),
    },
    {
      name: 'Anthropic',
      status: 'operational',
      lastUpdated: new Date(),
    },
  ];

  const displayServices = services || defaultServices;

  const getStatusBadge = (status: Service['status']) => {
    switch (status) {
      case 'operational':
        return (
          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
            Operacional
          </span>
        );
      case 'degraded':
        return (
          <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs">
            Degradado
          </span>
        );
      case 'outage':
        return (
          <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">
            Fora do ar
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {displayServices.map((service, index) => (
        <div key={index} className="flex items-center justify-between">
          <span>{service.name}</span>
          {getStatusBadge(service.status)}
        </div>
      ))}
    </div>
  );
};

export default StatusOverview;