import React from 'react';
import { WorkflowAgent, WorkflowType, AgentRole } from '../../services/api-types';
import { getAgentRoleName, getAgentRoleColor } from '../../utils/workflow-utils';

interface ExecutionOrderPreviewProps {
  agents: WorkflowAgent[];
  workflowType: WorkflowType;
}

/**
 * Componente para visualização da ordem de execução
 * 
 * Exibe uma representação visual da ordem de execução dos agentes
 */
const ExecutionOrderPreview: React.FC<ExecutionOrderPreviewProps> = ({
  agents,
  workflowType
}) => {
  // Ordena os agentes conforme o tipo de workflow
  const getOrderedAgents = (): WorkflowAgent[] => {
    if (workflowType === WorkflowType.SEQUENTIAL) {
      // Ordena por ordem de execução
      return [...agents].sort((a, b) => {
        const orderA = a.execution_order || 0;
        const orderB = b.execution_order || 0;
        return orderA - orderB;
      });
    }
    
    // Para outros tipos, mantém a ordem original
    return agents;
  };
  
  // Renderiza o preview conforme o tipo de workflow
  const renderPreview = () => {
    const orderedAgents = getOrderedAgents();
    
    switch (workflowType) {
      case WorkflowType.SEQUENTIAL:
        return (
          <div className="flex flex-col space-y-2">
            {orderedAgents.map((agent, index) => (
              <div key={agent.agent_id} className="flex items-center">
                <div className="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full">
                  {agent.execution_order || index + 1}
                </div>
                <div className="ml-2 flex-grow">
                  <p className="text-sm font-medium">{agent.agent_id}</p>
                  <p className="text-xs text-gray-500">{getAgentRoleName(agent.role)}</p>
                </div>
                {index < orderedAgents.length - 1 && (
                  <div className="h-6 border-l-2 border-blue-300 ml-4 my-1"></div>
                )}
              </div>
            ))}
          </div>
        );
        
      case WorkflowType.PARALLEL:
        return (
          <div className="flex flex-col">
            <div className="flex items-center justify-center mb-4">
              <div className="w-8 h-8 flex items-center justify-center bg-green-100 text-green-800 rounded-full">
                P
              </div>
              <p className="ml-2 text-sm font-medium">Execução Paralela</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {orderedAgents.map((agent) => (
                <div key={agent.agent_id} className="border border-gray-200 rounded-md p-2 bg-white">
                  <p className="text-sm font-medium">{agent.agent_id}</p>
                  <p className="text-xs text-gray-500">{getAgentRoleName(agent.role)}</p>
                </div>
              ))}
            </div>
          </div>
        );
        
      case WorkflowType.CONDITIONAL:
        return (
          <div className="flex flex-col">
            <div className="flex items-center justify-center mb-4">
              <div className="w-8 h-8 flex items-center justify-center bg-purple-100 text-purple-800 rounded-full">
                C
              </div>
              <p className="ml-2 text-sm font-medium">Execução Condicional</p>
            </div>
            <div className="border border-gray-200 rounded-md p-4 bg-white">
              <p className="text-sm text-center mb-2">
                A execução condicional depende de regras definidas no editor avançado.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-4">
                {orderedAgents.map((agent) => (
                  <div key={agent.agent_id} className="border border-gray-200 rounded-md p-2 bg-gray-50">
                    <p className="text-sm font-medium">{agent.agent_id}</p>
                    <p className="text-xs text-gray-500">{getAgentRoleName(agent.role)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
        
      default:
        return (
          <div className="text-center py-4 text-gray-500">
            Selecione um tipo de workflow para visualizar a ordem de execução.
          </div>
        );
    }
  };
  
  return (
    <div className="border border-gray-300 rounded-md p-4 bg-gray-50">
      <h3 className="text-sm font-medium text-gray-700 mb-3">Preview da Ordem de Execução</h3>
      {agents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          Nenhum agente selecionado
        </div>
      ) : (
        renderPreview()
      )}
    </div>
  );
};

export default ExecutionOrderPreview;