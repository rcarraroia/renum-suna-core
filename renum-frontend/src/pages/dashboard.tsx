import { useEffect, useState } from 'react';
import Link from 'next/link';
import { PlusCircle, BarChart3, Users, Database, Share2 } from 'lucide-react';
import Layout from '../components/Layout';
import AgentCard from '../components/AgentCard';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import { useAuthStore, useAgentStore } from '../lib/store';
import { apiRequest } from '../lib/api-client';
import { useAgentSharing } from '../hooks/useAgentSharing';

export default function Dashboard() {
  const { user } = useAuthStore();
  const { agents, setAgents, isLoading, setLoading, error, setError } = useAgentStore();
  const [statusFilter, setStatusFilter] = useState('all');
  const { sharedWithMe, isLoadingSharedWithMe } = useAgentSharing();

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      // TODO: Implementar integração real com a API
      // Por enquanto, usar dados de exemplo
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockAgents = [
        {
          id: '1',
          name: 'Assistente de Pesquisa',
          description: 'Agente que ajuda a pesquisar informações na web e em bases de conhecimento',
          status: 'active',
          created_at: '2025-07-17T14:30:00Z',
          updated_at: '2025-07-17T14:30:00Z',
          configuration: {
            model: 'gpt-4',
            system_prompt: 'Você é um assistente de pesquisa especializado.',
            tools: []
          },
          knowledge_base_ids: ['1', '2']
        },
        {
          id: '2',
          name: 'Analista de Dados',
          description: 'Agente especializado em análise de dados e geração de relatórios',
          status: 'draft',
          created_at: '2025-07-15T10:20:00Z',
          updated_at: '2025-07-15T10:20:00Z',
          configuration: {
            model: 'claude-3-opus',
            system_prompt: 'Você é um analista de dados especializado.',
            tools: []
          },
          knowledge_base_ids: []
        },
        {
          id: '3',
          name: 'Assistente de Atendimento',
          description: 'Agente para atendimento ao cliente com base em documentação interna',
          status: 'active',
          created_at: '2025-07-16T09:15:00Z',
          updated_at: '2025-07-16T09:15:00Z',
          configuration: {
            model: 'gpt-4',
            system_prompt: 'Você é um assistente de atendimento ao cliente.',
            tools: []
          },
          knowledge_base_ids: ['3']
        }
      ];
      
      setAgents(mockAgents);
    } catch (err: any) {
      console.error('Erro ao carregar agentes:', err);
      setError(err.message || 'Erro ao carregar agentes');
    } finally {
      setLoading(false);
    }
  };

  // Filtrar agentes por status
  const filteredAgents = statusFilter === 'all'
    ? agents
    : agents.filter(agent => agent.status === statusFilter);

  return (
    <Layout title="Dashboard">
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">
              Bem-vindo, {user?.name || 'Usuário'}
            </p>
          </div>
          <Link href="/agents/new">
            <Button>
              <PlusCircle className="h-4 w-4 mr-2" />
              Criar Novo Agente
            </Button>
          </Link>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Visão Geral</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Agentes Ativos</h3>
                <Users className="h-6 w-6 text-indigo-500" />
              </div>
              <p className="text-3xl font-bold text-indigo-600 mt-2">
                {agents.filter(a => a.status === 'active').length}
              </p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Execuções Hoje</h3>
                <BarChart3 className="h-6 w-6 text-indigo-500" />
              </div>
              <p className="text-3xl font-bold text-indigo-600 mt-2">12</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Bases de Conhecimento</h3>
                <Database className="h-6 w-6 text-indigo-500" />
              </div>
              <p className="text-3xl font-bold text-indigo-600 mt-2">3</p>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* Seus Agentes */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Seus Agentes</h2>
              <div>
                <Select
                  id="status-filter"
                  options={[
                    { value: 'all', label: 'Todos' },
                    { value: 'active', label: 'Ativos' },
                    { value: 'draft', label: 'Rascunhos' },
                    { value: 'inactive', label: 'Inativos' },
                    { value: 'archived', label: 'Arquivados' },
                  ]}
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                />
              </div>
            </div>

            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
                <p>{error}</p>
                <button
                  onClick={fetchAgents}
                  className="mt-2 text-sm font-medium text-red-600 hover:text-red-500"
                >
                  Tentar novamente
                </button>
              </div>
            ) : filteredAgents.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAgents.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={{
                      ...agent,
                      model: agent.configuration?.model,
                      is_shared: Math.random() > 0.5 // Simulação - remover em produção
                    }} 
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white p-8 rounded-lg shadow text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {statusFilter === 'all' 
                    ? 'Nenhum agente encontrado' 
                    : `Nenhum agente com status "${statusFilter}" encontrado`}
                </h3>
                <p className="text-gray-600 mb-4">
                  {statusFilter === 'all'
                    ? 'Você ainda não criou nenhum agente. Comece criando seu primeiro agente agora!'
                    : 'Tente selecionar outro filtro ou crie um novo agente.'}
                </p>
                <Link href="/agents/new">
                  <Button>
                    <PlusCircle className="h-4 w-4 mr-2" />
                    Criar Novo Agente
                  </Button>
                </Link>
              </div>
            )}
          </div>
          
          {/* Agentes Compartilhados Comigo */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold flex items-center">
                <Share2 className="h-5 w-5 mr-2 text-blue-600" />
                Compartilhados Comigo
              </h2>
            </div>
            
            {isLoadingSharedWithMe ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : sharedWithMe && sharedWithMe.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sharedWithMe.map((share: any) => (
                  <AgentCard 
                    key={share.id} 
                    agent={{
                      ...share.agent,
                      model: share.agent?.configuration?.model,
                      shared_with_me: true,
                      shared_by: share.shared_by,
                      permission_level: share.permission_level
                    }} 
                  />
                ))}
              </div>
            ) : (
              <div className="bg-white p-6 rounded-lg shadow text-center">
                <h3 className="text-base font-medium text-gray-900 mb-2">
                  Nenhum agente compartilhado com você
                </h3>
                <p className="text-sm text-gray-600">
                  Quando outros usuários compartilharem agentes com você, eles aparecerão aqui.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}