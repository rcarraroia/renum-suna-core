import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { 
  Bot, 
  Calendar, 
  Clock, 
  Edit, 
  Trash2, 
  ArrowLeft, 
  Database, 
  Wrench as Tool, 
  MessageSquare,
  BarChart3,
  RefreshCw,
  Share2
} from 'lucide-react';
import Layout from '../../../components/Layout';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import ShareAgentModal from '../../../components/ShareAgentModal';
import { useAgentSharing } from '../../../hooks/useAgentSharing';
import { agentApi } from '../../../lib/api-client';
import { useAgentStore } from '../../../lib/store';
import { formatDate, getAgentStatusColor, translateAgentStatus } from '../../../lib/utils';

export default function AgentDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { agents, selectedAgent, setSelectedAgent, removeAgent, addAgent } = useAgentStore();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const { isShareModalOpen, openShareModal, closeShareModal } = useAgentSharing(id as string);

  const fetchAgentDetails = useCallback(async (agentId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      // Verificar se o agente já está no store
      const existingAgent = agents.find(agent => agent.id === agentId);
      
      if (existingAgent) {
        setSelectedAgent(existingAgent);
        setIsLoading(false);
        return;
      }

      // Se não estiver no store, buscar da API
      const response = await fetch(`/api/v1/agents/${agentId}`);
      
      if (!response.ok) {
        throw new Error('Agente não encontrado');
      }

      const agentData = await response.json();
      setSelectedAgent(agentData);
      
      // Adicionar ao store para cache
      addAgent(agentData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao carregar agente';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [agents, addAgent]);

  useEffect(() => {
    if (id) {
      fetchAgentDetails(id as string);
    }
  }, [id, fetchAgentDetails]);

  const handleDeleteAgent = async () => {
    if (!selectedAgent) return;
    
    try {
      setIsLoading(true);
      
      // TODO: Implementar integração real com a API
      // Por enquanto, simular chamada de API
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Remover agente do store
      removeAgent(selectedAgent.id);
      
      // Redirecionar para o dashboard
      router.push('/dashboard');
    } catch (err: any) {
      console.error('Erro ao excluir agente:', err);
      setError(err.message || 'Erro ao excluir agente');
    } finally {
      setIsLoading(false);
      setDeleteConfirmOpen(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Detalhes do Agente">
        <div className="flex justify-center items-center h-full">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
        </div>
      </Layout>
    );
  }

  if (error || !selectedAgent) {
    return (
      <Layout title="Detalhes do Agente">
        <div className="py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
          <Alert variant="error" className="mb-6">
            {error || 'Agente não encontrado'}
          </Alert>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar para o Dashboard
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Agente: ${selectedAgent.name}`}>
      <div className="py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center mb-6">
          <button
            type="button"
            onClick={() => router.push('/dashboard')}
            className="mr-4 text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Bot className="h-6 w-6 mr-2 text-indigo-600" />
                {selectedAgent.name}
              </h1>
              <span className={`ml-3 px-2 py-1 text-xs font-medium rounded-full ${getAgentStatusColor(selectedAgent.status)}`}>
                {translateAgentStatus(selectedAgent.status)}
              </span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {selectedAgent.description || 'Sem descrição'}
            </p>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              onClick={() => router.push(`/agents/${selectedAgent.id}/edit`)}
            >
              <Edit className="h-4 w-4 mr-2" />
              Editar
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push(`/agents/${selectedAgent.id}/chat`)}
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Conversar
            </Button>
            <Button
              variant="outline"
              onClick={openShareModal}
            >
              <Share2 className="h-4 w-4 mr-2" />
              Compartilhar
            </Button>
            <Button
              variant="destructive"
              onClick={() => setDeleteConfirmOpen(true)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Excluir
            </Button>
          </div>
        </div>

        {deleteConfirmOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Confirmar exclusão</h3>
              <p className="text-gray-600 mb-6">
                Tem certeza que deseja excluir o agente "{selectedAgent.name}"? Esta ação não pode ser desfeita.
              </p>
              <div className="flex justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setDeleteConfirmOpen(false)}
                >
                  Cancelar
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDeleteAgent}
                  isLoading={isLoading}
                >
                  Excluir
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {/* Modal de compartilhamento */}
        {isShareModalOpen && (
          <ShareAgentModal
            agentId={selectedAgent.id}
            isOpen={isShareModalOpen}
            onClose={closeShareModal}
          />
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Coluna principal */}
          <div className="lg:col-span-2 space-y-6">
            {/* Informações básicas */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Informações do Agente</h2>
              </div>
              <div className="px-6 py-5">
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-6">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Modelo</dt>
                    <dd className="mt-1 text-sm text-gray-900">{selectedAgent.configuration.model}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Status</dt>
                    <dd className="mt-1 text-sm text-gray-900">{translateAgentStatus(selectedAgent.status)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Data de criação</dt>
                    <dd className="mt-1 text-sm text-gray-900 flex items-center">
                      <Calendar className="h-4 w-4 mr-1 text-gray-400" />
                      {formatDate(selectedAgent.created_at)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Última atualização</dt>
                    <dd className="mt-1 text-sm text-gray-900 flex items-center">
                      <Clock className="h-4 w-4 mr-1 text-gray-400" />
                      {formatDate(selectedAgent.updated_at)}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Prompt do sistema */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Prompt do Sistema</h2>
              </div>
              <div className="px-6 py-5">
                <div className="bg-gray-50 rounded-md p-4 text-sm text-gray-800 whitespace-pre-wrap">
                  {selectedAgent.configuration.system_prompt || 'Nenhum prompt do sistema definido'}
                </div>
              </div>
            </div>

            {/* Ferramentas */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Ferramentas</h2>
              </div>
              <div className="px-6 py-5">
                {selectedAgent.configuration.tools && selectedAgent.configuration.tools.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {selectedAgent.configuration.tools.map((tool: any) => (
                      <li key={tool.name} className="py-4 flex">
                        <div className="mr-4 flex-shrink-0">
                          <Tool className="h-5 w-5 text-indigo-500" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{tool.name}</p>
                          <p className="text-sm text-gray-500">{tool.description}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">Nenhuma ferramenta configurada</p>
                )}
              </div>
            </div>

            {/* Bases de conhecimento */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Bases de Conhecimento</h2>
              </div>
              <div className="px-6 py-5">
                {selectedAgent.knowledge_bases && selectedAgent.knowledge_bases.length > 0 ? (
                  <ul className="divide-y divide-gray-200">
                    {selectedAgent.knowledge_bases.map((kb: any) => (
                      <li key={kb.id} className="py-4 flex">
                        <div className="mr-4 flex-shrink-0">
                          <Database className="h-5 w-5 text-indigo-500" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{kb.name}</p>
                          <p className="text-sm text-gray-500">{kb.document_count} documentos</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">Nenhuma base de conhecimento associada</p>
                )}
              </div>
            </div>
          </div>

          {/* Coluna lateral */}
          <div className="space-y-6">
            {/* Métricas de uso */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-lg font-medium text-gray-900">Métricas de Uso</h2>
                <button className="text-indigo-600 hover:text-indigo-500">
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
              <div className="px-6 py-5">
                {selectedAgent.usage ? (
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Total de execuções</p>
                      <p className="mt-1 text-2xl font-semibold text-indigo-600">
                        {selectedAgent.usage.total_executions}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Última execução</p>
                      <p className="mt-1 text-sm text-gray-900">
                        {formatDate(selectedAgent.usage.last_execution, {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Tempo médio de resposta</p>
                      <p className="mt-1 text-sm text-gray-900">
                        {selectedAgent.usage.average_response_time.toFixed(1)} segundos
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Uso de tokens</p>
                      <div className="mt-1 grid grid-cols-3 gap-2 text-sm">
                        <div className="bg-indigo-50 p-2 rounded-md">
                          <p className="text-xs text-gray-500">Prompt</p>
                          <p className="font-medium text-indigo-700">
                            {selectedAgent.usage.token_usage.prompt_tokens.toLocaleString()}
                          </p>
                        </div>
                        <div className="bg-green-50 p-2 rounded-md">
                          <p className="text-xs text-gray-500">Completion</p>
                          <p className="font-medium text-green-700">
                            {selectedAgent.usage.token_usage.completion_tokens.toLocaleString()}
                          </p>
                        </div>
                        <div className="bg-gray-50 p-2 rounded-md">
                          <p className="text-xs text-gray-500">Total</p>
                          <p className="font-medium text-gray-700">
                            {selectedAgent.usage.token_usage.total_tokens.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto" />
                    <p className="mt-2 text-sm text-gray-500">
                      Nenhuma métrica de uso disponível
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Ações rápidas */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Ações Rápidas</h2>
              </div>
              <div className="px-6 py-5 space-y-3">
                <Button
                  fullWidth
                  onClick={() => router.push(`/agents/${selectedAgent.id}/chat`)}
                >
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Iniciar Conversa
                </Button>
                <Button
                  variant="outline"
                  fullWidth
                  onClick={() => router.push(`/agents/${selectedAgent.id}/edit`)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Editar Configurações
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}