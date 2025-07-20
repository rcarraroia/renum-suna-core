import Link from 'next/link';
import { formatDate, getAgentStatusColor, translateAgentStatus, truncateText } from '../lib/utils';
import { Bot, Info, Share2, Users } from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  model?: string;
  is_shared?: boolean;
  shared_with_me?: boolean;
  shared_by?: string;
  permission_level?: string;
}

interface AgentCardProps {
  agent: Agent;
}

const AgentCard = ({ agent }: AgentCardProps) => {
  return (
    <div className="bg-white shadow rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-200">
      <div className="p-5">
        <div className="flex justify-between items-start">
          <h3 className="text-lg font-medium text-gray-900 truncate">{agent.name}</h3>
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getAgentStatusColor(agent.status)}`}>
            {translateAgentStatus(agent.status)}
          </span>
        </div>
        <p className="mt-2 text-gray-600 text-sm line-clamp-2">
          {truncateText(agent.description || 'Sem descrição', 100)}
        </p>
        <div className="mt-3 flex items-center justify-between">
          <p className="text-xs text-gray-500">Criado em {formatDate(agent.created_at)}</p>
          <div className="flex items-center space-x-2">
            {agent.shared_with_me && (
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded flex items-center">
                <Share2 className="h-3 w-3 mr-1" />
                Compartilhado comigo
              </span>
            )}
            {agent.is_shared && (
              <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded flex items-center">
                <Users className="h-3 w-3 mr-1" />
                Compartilhado
              </span>
            )}
            {agent.model && (
              <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded">
                {agent.model}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="bg-gray-50 px-5 py-3 flex justify-between">
        <Link
          href={`/agents/${agent.id}`}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500 flex items-center"
        >
          <Info className="h-4 w-4 mr-1" />
          Detalhes
        </Link>
        <Link
          href={`/agents/${agent.id}/chat`}
          className="text-sm font-medium text-green-600 hover:text-green-500 flex items-center"
        >
          <Bot className="h-4 w-4 mr-1" />
          Conversar
        </Link>
      </div>
    </div>
  );
};

export default AgentCard;