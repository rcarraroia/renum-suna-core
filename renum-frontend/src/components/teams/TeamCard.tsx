import React from 'react';
import { Team } from '../../services/api-types';
import { formatDate, truncateString } from '../../utils/string-utils';
import { getWorkflowTypeName, getWorkflowTypeColor } from '../../utils/workflow-utils';
import Link from 'next/link';

interface TeamCardProps {
  team: Team;
  onExecute?: (team: Team) => void;
  onEdit?: (team: Team) => void;
  onDelete?: (team: Team) => void;
}

/**
 * Componente de card de equipe
 * 
 * Exibe informações resumidas de uma equipe
 */
const TeamCard: React.FC<TeamCardProps> = ({ team, onExecute, onEdit, onDelete }) => {
  const workflowType = getWorkflowTypeName(team.workflow_definition.type);
  const workflowTypeColor = getWorkflowTypeColor(team.workflow_definition.type);
  const agentCount = team.agent_ids.length;
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              <Link href={`/teams/${team.team_id}`} className="hover:text-blue-600">
                {team.name}
              </Link>
            </h3>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${workflowTypeColor} mt-2`}>
              {workflowType}
            </span>
          </div>
          <div className="flex space-x-2">
            {onExecute && (
              <button
                onClick={() => onExecute(team)}
                className="p-1.5 text-green-600 hover:bg-green-50 rounded-full"
                title="Executar equipe"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              </button>
            )}
            {onEdit && (
              <button
                onClick={() => onEdit(team)}
                className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-full"
                title="Editar equipe"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                </svg>
              </button>
            )}
            {onDelete && (
              <button
                onClick={() => onDelete(team)}
                className="p-1.5 text-red-600 hover:bg-red-50 rounded-full"
                title="Excluir equipe"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
        </div>
        
        <p className="mt-2 text-sm text-gray-600">
          {truncateString(team.description || 'Sem descrição', 150)}
        </p>
        
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            <span className="font-medium">{agentCount}</span> agente{agentCount !== 1 ? 's' : ''}
          </div>
          <div className="text-sm text-gray-500">
            Atualizado em {formatDate(team.updated_at, { dateStyle: 'short' })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamCard;