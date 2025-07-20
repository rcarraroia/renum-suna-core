import React from 'react';
import { formatDate } from '../../lib/utils';

interface Activity {
  id: string;
  description: string;
  timestamp: Date;
  type: 'client' | 'agent' | 'user' | 'system' | 'billing';
}

interface RecentActivitiesProps {
  activities?: Activity[];
  limit?: number;
}

const RecentActivities: React.FC<RecentActivitiesProps> = ({ 
  activities,
  limit = 5
}) => {
  // Dados de exemplo se não forem fornecidos
  const defaultActivities: Activity[] = [
    {
      id: '1',
      description: 'Novo cliente registrado: Empresa XYZ',
      timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutos atrás
      type: 'client',
    },
    {
      id: '2',
      description: 'Agente "Assistente de Vendas" criado por Cliente ABC',
      timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutos atrás
      type: 'agent',
    },
    {
      id: '3',
      description: 'Limite de uso atingido para Cliente DEF',
      timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hora atrás
      type: 'billing',
    },
    {
      id: '4',
      description: 'Nova base de conhecimento criada: "Documentação Técnica"',
      timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000), // 3 horas atrás
      type: 'agent',
    },
    {
      id: '5',
      description: 'Usuário João Silva adicionado ao Cliente GHI',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 horas atrás
      type: 'user',
    },
  ];

  const displayActivities = activities || defaultActivities;
  const limitedActivities = displayActivities.slice(0, limit);

  const getTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Agora mesmo';
    if (diffMins < 60) return `Há ${diffMins} minutos`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Há ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `Há ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
    
    return formatDate(date, 'dd/MM/yyyy');
  };

  return (
    <div className="space-y-4">
      {limitedActivities.map((activity) => (
        <div key={activity.id} className="border-l-4 border-primary-500 pl-4">
          <p className="text-sm text-gray-600">{getTimeAgo(activity.timestamp)}</p>
          <p className="font-medium">{activity.description}</p>
        </div>
      ))}
    </div>
  );
};

export default RecentActivities;