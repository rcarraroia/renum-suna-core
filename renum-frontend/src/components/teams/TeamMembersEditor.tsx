import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd';
import { WorkflowAgent, AgentRole, WorkflowType } from '../../services/api-types';
import { getAgentRoleName, getAgentRoleColor } from '../../utils/workflow-utils';
import FormField from '../common/FormField';
import SelectField from '../common/SelectField';

interface TeamMembersEditorProps {
  agents: WorkflowAgent[];
  workflowType: WorkflowType;
  onChange: (agents: WorkflowAgent[]) => void;
  error?: string;
}

/**
 * Componente para edição de membros da equipe
 * 
 * Permite reordenar agentes com drag & drop e configurar suas propriedades
 */
const TeamMembersEditor: React.FC<TeamMembersEditorProps> = ({
  agents,
  workflowType,
  onChange,
  error
}) => {
  // Estado local para os agentes
  const [localAgents, setLocalAgents] = useState<WorkflowAgent[]>([]);
  
  // Opções para os selects
  const agentRoleOptions = Object.values(AgentRole).map(role => ({
    value: role,
    label: getAgentRoleName(role)
  }));
  
  // Sincroniza o estado local com as props
  useEffect(() => {
    setLocalAgents([...agents]);
  }, [agents]);
  
  // Manipuladores de eventos
  const handleDragEnd = (result: DropResult) => {
    const { destination, source } = result;
    
    // Se não houver destino ou o destino for o mesmo que a origem, não faz nada
    if (!destination || destination.index === source.index) {
      return;
    }
    
    // Reordena os agentes
    const newAgents = Array.from(localAgents);
    const [removed] = newAgents.splice(source.index, 1);
    newAgents.splice(destination.index, 0, removed);
    
    // Atualiza a ordem de execução para workflows sequenciais
    if (workflowType === WorkflowType.SEQUENTIAL) {
      const updatedAgents = newAgents.map((agent, index) => ({
        ...agent,
        execution_order: index + 1
      }));
      
      setLocalAgents(updatedAgents);
      onChange(updatedAgents);
    } else {
      setLocalAgents(newAgents);
      onChange(newAgents);
    }
  };
  
  const handleRoleChange = (agentId: string, role: AgentRole) => {
    const updatedAgents = localAgents.map(agent => 
      agent.agent_id === agentId ? { ...agent, role } : agent
    );
    
    setLocalAgents(updatedAgents);
    onChange(updatedAgents);
  };
  
  const handleOrderChange = (agentId: string, order: number) => {
    // Valida a ordem
    if (order < 1) {
      order = 1;
    }
    
    const updatedAgents = localAgents.map(agent => 
      agent.agent_id === agentId ? { ...agent, execution_order: order } : agent
    );
    
    setLocalAgents(updatedAgents);
    onChange(updatedAgents);
  };
  
  // Renderiza um agente na lista
  const renderAgentItem = (agent: WorkflowAgent, index: number) => {
    return (
      <Draggable key={agent.agent_id} draggableId={agent.agent_id} index={index}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.draggableProps}
            className={`mb-2 border rounded-md ${
              snapshot.isDragging ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200'
            }`}
          >
            <div className="flex items-center p-3">
              {/* Handle de arrasto */}
              <div
                {...provided.dragHandleProps}
                className="mr-3 cursor-grab"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M7 2a1 1 0 011 1v1h3a1 1 0 110 2H9.20l-.8 2H12a1 1 0 110 2H8.2l-.8 2H10a1 1 0 110 2H7.2l-.8 2H9a1 1 0 010 2H5a1 1 0 01-.93-.47L.27 9a1 1 0 010-1.06l3.8-4.47A1 1 0 015 3h2V2a1 1 0 011-1zm0 14.5a1.5 1.5 0 113 0 1.5 1.5 0 01-3 0zm9-14a1 1 0 011 1v1h3a1 1 0 110 2h-3v2h2a1 1 0 110 2h-2v2h3a1 1 0 110 2h-3v1a1 1 0 11-2 0v-1h-1a1 1 0 110-2h1v-2h-2a1 1 0 110-2h2V5h-3a1 1 0 110-2h3V2a1 1 0 011-1z" />
                </svg>
              </div>
              
              {/* Ordem de execução (apenas para workflow sequencial) */}
              {workflowType === WorkflowType.SEQUENTIAL && (
                <div className="mr-3 w-12">
                  <input
                    type="number"
                    min="1"
                    value={agent.execution_order || index + 1}
                    onChange={(e) => handleOrderChange(agent.agent_id, parseInt(e.target.value))}
                    className="block w-full text-sm border-gray-300 rounded-md"
                  />
                </div>
              )}
              
              {/* ID do agente */}
              <div className="flex-grow">
                <p className="text-sm font-medium">{agent.agent_id}</p>
              </div>
              
              {/* Papel do agente */}
              <div className="w-40">
                <select
                  value={agent.role}
                  onChange={(e) => handleRoleChange(agent.agent_id, e.target.value as AgentRole)}
                  className="block w-full text-sm border-gray-300 rounded-md"
                >
                  {agentRoleOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}
      </Draggable>
    );
  };
  
  return (
    <FormField
      id="team-members"
      label="Membros da Equipe"
      error={error}
      helpText={
        workflowType === WorkflowType.SEQUENTIAL
          ? "Arraste para reordenar os agentes e definir a ordem de execução."
          : "Arraste para reordenar os agentes e definir suas funções."
      }
    >
      <div className="mt-1">
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="team-members">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="border border-gray-300 rounded-md p-3 bg-gray-50 min-h-[200px]"
              >
                {localAgents.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    Nenhum agente selecionado
                  </div>
                ) : (
                  localAgents.map((agent, index) => renderAgentItem(agent, index))
                )}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
        
        {/* Legenda */}
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.values(AgentRole).map(role => (
            <div key={role} className="flex items-center">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getAgentRoleColor(role)}`}>
                {getAgentRoleName(role)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </FormField>
  );
};

export default TeamMembersEditor;