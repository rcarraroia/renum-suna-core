import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useCreateTeam } from '../../services/react-query-hooks';
import { TeamCreate, WorkflowType, WorkflowDefinition } from '../../services/api-types';
import { validateTeamCreate } from '../../utils/validation-utils';
import PageHeader from '../../components/common/PageHeader';
import TextField from '../../components/common/TextField';
import AgentSelector from '../../components/teams/AgentSelector';
import WorkflowConfigurator from '../../components/teams/WorkflowConfigurator';
import Link from 'next/link';

/**
 * Página de criação de equipe
 */
const CreateTeamPage: React.FC = () => {
  const router = useRouter();
  const [formData, setFormData] = useState<{
    name: string;
    description: string;
    selectedAgents: string[];
    workflow: WorkflowDefinition;
  }>({
    name: '',
    description: '',
    selectedAgents: [],
    workflow: {
      type: WorkflowType.SEQUENTIAL,
      agents: []
    }
  });
  
  const [errors, setErrors] = useState<{
    name?: string;
    description?: string;
    agents?: string;
    workflow?: string;
  }>({});
  
  // Hook para criar equipe
  const { mutate: createTeam, isLoading, error } = useCreateTeam({
    onSuccess: (data) => {
      // Redireciona para a página de detalhes da equipe
      router.push(`/teams/${data.team_id}`);
    }
  });
  
  // Manipuladores de eventos
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Limpa o erro do campo
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };
  
  const handleAgentsChange = (agentIds: string[]) => {
    setFormData(prev => ({ ...prev, selectedAgents: agentIds }));
    
    // Limpa o erro do campo
    if (errors.agents) {
      setErrors(prev => ({ ...prev, agents: undefined }));
    }
  };
  
  const handleWorkflowChange = (workflow: WorkflowDefinition) => {
    setFormData(prev => ({ ...prev, workflow }));
    
    // Limpa o erro do campo
    if (errors.workflow) {
      setErrors(prev => ({ ...prev, workflow: undefined }));
    }
  };
  
  const validateForm = (): boolean => {
    // Cria o objeto de equipe para validação
    const teamData: TeamCreate = {
      name: formData.name,
      description: formData.description,
      agent_ids: formData.selectedAgents,
      workflow_definition: formData.workflow
    };
    
    // Valida usando a função de validação
    const validationErrors = validateTeamCreate(teamData);
    
    // Mapeia os erros para o formato do estado
    const newErrors: typeof errors = {
      name: validationErrors.name,
      description: validationErrors.description,
      agents: validationErrors.agents,
      workflow: validationErrors.workflow
    };
    
    setErrors(newErrors);
    return Object.keys(validationErrors).length === 0;
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    // Cria o objeto de equipe
    const teamData: TeamCreate = {
      name: formData.name,
      description: formData.description,
      agent_ids: formData.selectedAgents,
      workflow_definition: formData.workflow
    };
    
    // Envia para a API
    createTeam(teamData);
  };
  
  // Renderiza as ações do cabeçalho
  const renderHeaderActions = () => (
    <Link
      href="/teams"
      className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      Voltar para Equipes
    </Link>
  );
  
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title="Criar Nova Equipe"
        description="Configure uma nova equipe de agentes para trabalhar em conjunto"
        actions={renderHeaderActions()}
      />
      
      {/* Mensagem de erro geral */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-800 rounded-lg p-4">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium">Erro ao criar equipe</p>
              <p className="text-sm">{error instanceof Error ? error.message : 'Ocorreu um erro desconhecido'}</p>
            </div>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="bg-white shadow-sm rounded-lg p-6">
        <div className="space-y-6">
          {/* Informações básicas */}
          <div>
            <h3 className="text-lg font-medium text-gray-900">Informações Básicas</h3>
            <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              <div className="sm:col-span-4">
                <TextField
                  id="name"
                  name="name"
                  label="Nome da Equipe"
                  value={formData.name}
                  onChange={handleInputChange}
                  error={errors.name}
                  required
                  placeholder="Ex: Equipe de Análise de Dados"
                  maxLength={100}
                />
              </div>
              
              <div className="sm:col-span-6">
                <TextField
                  id="description"
                  name="description"
                  label="Descrição"
                  value={formData.description}
                  onChange={handleInputChange}
                  error={errors.description}
                  required
                  placeholder="Descreva o propósito e as capacidades desta equipe"
                  multiline
                  rows={3}
                  maxLength={500}
                />
              </div>
            </div>
          </div>
          
          {/* Seleção de agentes */}
          <div>
            <h3 className="text-lg font-medium text-gray-900">Agentes</h3>
            <div className="mt-4">
              <AgentSelector
                selectedAgents={formData.selectedAgents}
                onChange={handleAgentsChange}
                error={errors.agents}
                maxAgents={10}
              />
            </div>
          </div>
          
          {/* Configuração de workflow */}
          <div>
            <h3 className="text-lg font-medium text-gray-900">Configuração de Workflow</h3>
            <div className="mt-4">
              <WorkflowConfigurator
                selectedAgents={formData.selectedAgents}
                value={formData.workflow}
                onChange={handleWorkflowChange}
                error={errors.workflow}
              />
            </div>
          </div>
        </div>
        
        {/* Botões de ação */}
        <div className="mt-8 pt-5 border-t border-gray-200 flex justify-end space-x-3">
          <Link
            href="/teams"
            className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancelar
          </Link>
          <button
            type="submit"
            disabled={isLoading}
            className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              isLoading ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Criando...
              </>
            ) : (
              'Criar Equipe'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateTeamPage;