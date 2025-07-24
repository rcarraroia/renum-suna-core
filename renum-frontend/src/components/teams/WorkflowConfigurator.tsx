import React, { useState, useEffect } from 'react';
import { WorkflowDefinition, WorkflowType, WorkflowAgent, AgentRole, InputSource } from '../../services/api-types';
import { getWorkflowTypeName, getAgentRoleName } from '../../utils/workflow-utils';
import FormField from '../common/FormField';
import SelectField from '../common/SelectField';

interface WorkflowConfiguratorProps {
  selectedAgents: string[];
  value: WorkflowDefinition;
  onChange: (workflow: WorkflowDefinition) => void;
  error?: string;
}

/**
 * Componente para configuração de workflow
 * 
 * Permite configurar o tipo de workflow e as propriedades dos agentes
 */
const WorkflowConfigurator: React.FC<WorkflowConfiguratorProps> = ({
  selectedAgents,
  value,
  onChange,
  error
}) => {
  // Opções para os selects
  const workflowTypeOptions = Object.values(WorkflowType).map(type => ({
    value: type,
    label: getWorkflowTypeName(type)
  }));
  
  const agentRoleOptions = Object.values(AgentRole).map(role => ({
    value: role,
    label: getAgentRoleName(role)
  }));
  
  // Atualiza os agentes no workflow quando a seleção muda
  useEffect(() => {
    // Filtra os agentes que não estão mais selecionados
    const currentAgents = value.agents.filter(agent => 
      selectedAgents.includes(agent.agent_id)
    );
    
    // Adiciona novos agentes selecionados
    const newAgents = selectedAgents
      .filter(agentId => !currentAgents.some(a => a.agent_id === agentId))
      .map(agentId => createDefaultAgent(agentId, value.type));
    
    // Atualiza o workflow com todos os agentes
    onChange({
      ...value,
      agents: [...currentAgents, ...newAgents]
    });
  }, [selectedAgents]);
  
  // Cria um agente com configurações padrão
  const createDefaultAgent = (agentId: string, workflowType: WorkflowType): WorkflowAgent => {
    const baseAgent: WorkflowAgent = {
      agent_id: agentId,
      role: AgentRole.MEMBER,
      input: {
        source: InputSource.INITIAL_PROMPT
      }
    };
    
    // Adiciona ordem de execução para workflows sequenciais
    if (workflowType === WorkflowType.SEQUENTIAL) {
      return {
        ...baseAgent,
        execution_order: value.agents.length + 1
      };
    }
    
    return baseAgent;
  };
  
  // Manipuladores de eventos
  const handleWorkflowTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value as WorkflowType;
    
    // Atualiza o tipo de workflow
    onChange({
      ...value,
      type: newType,
      // Atualiza os agentes conforme necessário para o novo tipo
      agents: value.agents.map(agent => {
        if (newType === WorkflowType.SEQUENTIAL && agent.execution_order === undefined) {
          // Adiciona ordem de execução para workflows sequenciais
          return {
            ...agent,
            execution_order: value.agents.indexOf(agent) + 1
          };
        }
        return agent;
      })
    });
  };
  
  const handleAgentRoleChange = (agentId: string, role: AgentRole) => {
    onChange({
      ...value,
      agents: value.agents.map(agent => 
        agent.agent_id === agentId ? { ...agent, role } : agent
      )
    });
  };
  
  const handleAgentOrderChange = (agentId: string, order: number) => {
    onChange({
      ...value,
      agents: value.agents.map(agent => 
        agent.agent_id === agentId ? { ...agent, execution_order: order } : agent
      )
    });
  };
  
  // Renderiza a configuração específica para cada tipo de workflow
  const renderWorkflowTypeConfig = () => {
    switch (value.type) {
      case WorkflowType.SEQUENTIAL:
        return (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Ordem de Execução</h4>
            <p className="text-sm text-gray-500 mb-3">
              Defina a ordem em que os agentes serão executados.
            </p>
            <div className="space-y-2">
              {value.agents.map((agent, index) => (
                <div key={agent.agent_id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded-md">
                  <div className="w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-800 rounded-full">
                    {agent.execution_order || index + 1}
                  </div>
                  <div className="flex-grow">
                    <p className="text-sm font-medium">{agent.agent_id}</p>
                  </div>
                  <div className="w-32">
                    <select
                      value={agent.role}
                      onChange={(e) => handleAgentRoleChange(agent.agent_id, e.target.value as AgentRole)}
                      className="block w-full text-sm border-gray-300 rounded-md"
                    >
                      {agentRoleOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="w-20">
                    <input
                      type="number"
                      min="1"
                      value={agent.execution_order || index + 1}
                      onChange={(e) => handleAgentOrderChange(agent.agent_id, parseInt(e.target.value))}
                      className="block w-full text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
        
      case WorkflowType.PARALLEL:
        return (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Configuração Paralela</h4>
            <p className="text-sm text-gray-500 mb-3">
              Todos os agentes serão executados simultaneamente.
            </p>
            <div className="space-y-2">
              {value.agents.map((agent) => (
                <div key={agent.agent_id} className="flex items-center space-x-3 p-2 bg-gray-50 rounded-md">
                  <div className="w-8 h-8 flex items-center justify-center bg-green-100 text-green-800 rounded-full">
                    P
                  </div>
                  <div className="flex-grow">
                    <p className="text-sm font-medium">{agent.agent_id}</p>
                  </div>
                  <div className="w-32">
                    <select
                      value={agent.role}
                      onChange={(e) => handleAgentRoleChange(agent.agent_id, e.target.value as AgentRole)}
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
              ))}
            </div>
          </div>
        );
        
      case WorkflowType.CONDITIONAL:
        return (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Configuração Condicional</h4>
            <p className="text-sm text-gray-500 mb-3">
              A configuração avançada de condições estará disponível no editor visual.
            </p>
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-700">
                A configuração detalhada de condições será feita no editor visual após a criação da equipe.
              </p>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div>
      <FormField
        id="workflow-type"
        label="Tipo de Workflow"
        error={error}
        required
        helpText="Selecione como os agentes irão interagir entre si."
      >
        <div className="mt-1">
          <SelectField
            id="workflow-type"
            name="workflow-type"
            label=""
            options={workflowTypeOptions}
            value={value.type}
            onChange={handleWorkflowTypeChange}
            placeholder="Selecione o tipo de workflow"
          />
        </div>
      </FormField>
      
      {renderWorkflowTypeConfig()}
    </div>
  );
};

export default WorkflowConfigurator;