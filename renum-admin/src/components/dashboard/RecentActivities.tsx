import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface Activity {
  id: string;
  description: string;
  timestamp: Date;
}

// Dados de exemplo
const activities: Activity[] = [
  {
    id: '1',
    description: 'Novo cliente registrado: Empresa XYZ',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutos atrás
  },
  {
    id: '2',
    description: 'Agente "Assistente de Vendas" criado por Cliente ABC',
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutos atrás
  },
  {
    id: '3',
    description: 'Limite de uso atingido para Cliente DEF',
    timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1 hora atrás
  },
  {
    id: '4',
    description: 'Nova base de conhecimento criada: "Documentação Técnica"',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000), // 3 horas atrás
  },
];

interface RecentActivitiesProps {
  className?: string;
}

const RecentActivities: React.FC<RecentActivitiesProps> = ({ className }) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {activities.map((activity) => (
        <div key={activity.id} className="border-l-4 border-primary-500 pl-4">
          <p className="text-sm text-gray-600">
            {formatDistanceToNow(activity.timestamp, {
              addSuffix: true,
              locale: ptBR,
            })}
          </p>
          <p className="font-medium">{activity.description}</p>
        </div>
      ))}
    </div>
  );
};

export default RecentActivities;