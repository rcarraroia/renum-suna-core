import React, { useState, useEffect } from 'react';
import { useAgents } from '../../services/react-query-hooks';
import FormField from '../common/FormField';

interface Agent {
  agent_id: string;
  name: string;
  description?: string;
  model?: string;
  capabilities?: string[];
}

interface AgentSelectorProps {
  selectedAgents: string[];
  onChange: (agentIds: string[]) => void;
  error?: string;
  maxAgents?: number;
}

/**
 * Componente para seleção de agentes
 * 
 * Permite selecionar múltiplos agentes para uma equipe
 */
const AgentSelector: React.FC<AgentSelectorProps> = ({
  selectedAgents,
  onChange,
  error,
  maxAgents = 10
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: agents, isLoading } = useAgents();
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  
  // Filtra os agentes com base no termo de busca
  useEffect(() => {
    if (!agents) return;
    
    if (!searchTerm) {
      setFilteredAgents(agents);
      return;
    }
    
    const lowerSearchTerm = searchTerm.toLowerCase();
    const filtered = agents.filter(
      agent => 
        agent.name.toLowerCase().includes(lowerSearchTerm) ||
        agent.description?.toLowerCase().includes(lowerSearchTerm) ||
        agent.agent_id.toLowerCase().includes(lowerSearchTerm)
    );
    
    setFilteredAgents(filtered);
  }, [agents, searchTerm]);
  
  // Manipuladores de eventos
  const handleAgentToggle = (agentId: string) => {
    if (selectedAgents.includes(agentId)) {
      // Remove o agente se já estiver selecionado
      onChange(selectedAgents.filter(id => id !== agentId));
    } else if (selectedAgents.length < maxAgents) {
      // Adiciona o agente se não exceder o limite
      onChange([...selectedAgents, agentId]);
    }
  };
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  // Renderiza um agente na lista
  const renderAgentItem = (agent: Agent) => {
    const isSelected = selectedAgents.includes(agent.agent_id);
    
    return (
      <li 
        key={agent.agent_id}
        className={`flex items-center justify-between p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
          isSelected ? 'bg-blue-50' : ''
        }`}
        onClick={() => handleAgentToggle(agent.agent_id)}
      >
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => {}} // Controlado pelo onClick do li
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">{agent.name}</p>
            <p className="text-xs text-gray-500">{agent.agent_id}</p>
          </div>
        </div>
        {agent.model && (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {agent.model}
          </span>
        )}
      </li>
    );
  };
  
  return (
    <FormField
      id="agents"
      label="Selecione os agentes"
      error={error}
      required
      helpText={`Selecione até ${maxAgents} agentes para sua equipe.`}
    >
      <div className="mt-1 border border-gray-300 rounded-md overflow-hidden">
        {/* Barra de busca */}
        <div className="p-2 bg-gray-50 border-b border-gray-300">
          <input
            type="text"
            placeholder="Buscar agentes..."
            value={searchTerm}
            onChange={handleSearchChange}
            className="w-full p-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
        
        {/* Lista de agentes */}
        <div className="max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-gray-500">Carregando agentes...</div>
          ) : filteredAgents.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              {searchTerm ? 'Nenhum agente encontrado' : 'Nenhum agente disponível'}
            </div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {filteredAgents.map(renderAgentItem)}
            </ul>
          )}
        </div>
        
        {/* Contador de selecionados */}
        <div className="p-2 bg-gray-50 border-t border-gray-300 text-sm text-gray-500">
          {selectedAgents.length} de {maxAgents} agentes selecionados
        </div>
      </div>
    </FormField>
  );
};

export default AgentSelector;