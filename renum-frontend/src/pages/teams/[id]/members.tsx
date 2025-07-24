import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useTeam, useUpdateTeam } from '../../../services/react-query-hooks';
import { WorkflowAgent, WorkflowType } from '../../../services/api-types';
import PageHeader from '../../../components/common/PageHeader';
import TeamMembersEditor from '../../../components/teams/TeamMembersEditor';
import ExecutionOrderPreview from '../../../components/teams/ExecutionOrderPreview';
import Link from 'next/link';

/**
 * Página de edição de membros da equipe
 */
const TeamMembersPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const teamId = typeof id === 'string' ? id : '';
  
  // Busca os dados da equipe
  const { data: team, isLoading: isLoadingTeam, error: teamError } = useTeam(teamId);
  
  // Hook para atualizar a equipe
  const { mutate: updateTeam, isLoading: isUpdating, error: updateError } = useUpdateTeam({
    onSuccess: () => {
      // Exibe mensagem de sucesso
      setSuccessMessage('Membros da equipe atualizados com sucesso');
      
      // Limpa a mensagem após alguns segundos
      setTimeout(() => {
        setSuccessMessage('');
      }, 5000);
    }
  });
  
  // Estados locais
  const [agents, setAgents] = useState<WorkflowAgent[]>([]);
  const [workflowType, setWorkflowType] = useState<WorkflowType>(WorkflowType.SEQUENTIAL);
  const [successMessage, setSuccessMessage] = useState<string>('');
  
  // Atualiza os estados locais quando os dados da equipe são carregados
  useEffect(() => {
    if (team) {
      setAgents(team.workflow_definition.agents);
      setWorkflowType(team.workflow_definition.type);
    }
  }, [team]);
  
  // Manipuladores de eventos
  const handleAgentsChange = (updatedAgents: WorkflowAgent[]) => {
    setAgents(updatedAgents);
  };
  
  const handleSave = () => {
    if (!team) return;
    
    // Atualiza a equipe
    updateTeam({
      teamId,
      data: {
        workflow_definition: {
          ...team.workflow_definition,
          agents
        }
      }
    });
  };
  
  // Renderiza as ações do cabeçalho
  const renderHeaderActions = () => (
    <div className="flex space-x-2">
      <Link
        href={`/teams/${teamId}`}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Voltar para Detalhes
      </Link>
      <button
        onClick={handleSave}
        disabled={isUpdating}
        className={`inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
          isUpdating ? 'opacity-70 cursor-not-allowed' : ''
        }`}
      >
        {isUpdating ? 'Salvando...' : 'Salvar Alterações'}
      </button>
    </div>
  );
  
  // Renderiza o conteúdo principal
  const renderContent = () => {
    if (isLoadingTeam) {
      return (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      );
    }
    
    if (teamError) {
      return (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-4">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium">Erro ao carregar equipe</p>
              <p className="text-sm">{teamError instanceof Error ? teamError.message : 'Ocorreu um erro desconhecido'}</p>
              <button
                onClick={() => router.reload()}
                className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        </div>
      );
    }
    
    if (!team) {
      return (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
          <div className="flex">
            <svg className="h-5 w-5 text-yellow-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="font-medium">Equipe não encontrada</p>
              <p className="text-sm">A equipe solicitada não foi encontrada ou você não tem permissão para acessá-la.</p>
              <Link
                href="/teams"
                className="mt-2 text-sm font-medium text-yellow-600 hover:text-yellow-500"
              >
                Voltar para a lista de equipes
              </Link>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Mensagem de sucesso */}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded-lg p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-green-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="font-medium">{successMessage}</p>
            </div>
          </div>
        )}
        
        {/* Mensagem de erro de atualização */}
        {updateError && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4">
            <div className="flex">
              <svg className="h-5 w-5 text-red-400 mr-2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <p className="font-medium">Erro ao atualizar membros da equipe</p>
                <p className="text-sm">{updateError instanceof Error ? updateError.message : 'Ocorreu um erro desconhecido'}</p>
              </div>
            </div>
          </div>
        )}
        
        <div className="bg-white shadow-sm rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Configuração de Membros</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Editor de membros */}
            <div>
              <TeamMembersEditor
                agents={agents}
                workflowType={workflowType}
                onChange={handleAgentsChange}
              />
            </div>
            
            {/* Preview da ordem de execução */}
            <div>
              <ExecutionOrderPreview
                agents={agents}
                workflowType={workflowType}
              />
            </div>
          </div>
          
          {/* Botões de ação */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={handleSave}
              disabled={isUpdating}
              className={`inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                isUpdating ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isUpdating ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Salvando...
                </>
              ) : (
                'Salvar Alterações'
              )}
            </button>
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title={team ? `Editar Membros: ${team.name}` : 'Editar Membros da Equipe'}
        description="Configure os membros da equipe e sua ordem de execução"
        actions={renderHeaderActions()}
      />
      
      {renderContent()}
    </div>
  );
};

export default TeamMembersPage;