import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Edit, ArrowLeft, MessageSquare, Users, Clock, Star } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAgents } from '../../../hooks/useAgents';
import { Agent, AgentUsageStats } from '../../../types/agent';
import { formatDate } from '../../../lib/utils';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import MetricsCard from '../../../components/dashboard/MetricsCard';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function AgentDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { getAgent, getAgentUsageStats, toggleAgentStatus, isTogglingAgentStatus, error, setError } = useAgents();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);

  // Buscar detalhes do agente
  const {
    data: agentData,
    isLoading: isLoadingAgent,
    error: agentError,
  } = useQuery<Agent>({
    queryKey: ['agent', id],
    queryFn: () => getAgent(id as string),
    enabled: !!id,
  });

  // Buscar estatísticas de uso do agente
  const {
    data: statsData,
    isLoading: isLoadingStats,
    error: statsError,
  } = useQuery<AgentUsageStats>({
    queryKey: ['agent-stats', id],
    queryFn: () => getAgentUsageStats(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (agentData) {
      setAgent(agentData);
    }
  }, [agentData]);

  useEffect(() => {
    if (agentError) {
      setError(agentError.message);
    }
    if (statsError) {
      setError(statsError.message);
    }
  }, [agentError, statsError, setError]);

  const handleToggleStatus = async () => {
    if (!agent) return;

    try {
      await toggleAgentStatus({
        id: agent.id,
        isActive: !agent.is_active,
      });
      setIsStatusModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  if (isLoadingAgent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!agent && !isLoadingAgent) {
    return (
      <Alert variant="error" title="Erro">
        Agente não encontrado
      </Alert>
    );
  }

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Detalhes do Agente</title>
        <meta name="description" content="Detalhes do agente" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/agents">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{agent?.name}</h1>
          <div className="ml-auto flex space-x-3">
            <Button
              variant={agent?.is_active ? 'destructive' : 'default'}
              onClick={() => setIsStatusModalOpen(true)}
            >
              {agent?.is_active ? 'Desativar' : 'Ativar'}
            </Button>
            <Link href={`/agents/${id}/edit`}>
              <a>
                <Button>
                  <Edit className="h-4 w-4 mr-2" /> Editar
                </Button>
              </a>
            </Link>
          </div>
        </div>

        {error && (
          <Alert
            variant="error"
            title="Erro"
            onClose={() => setError(null)}
            className="mb-4"
          >
            {error}
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <CardTitle>Informações Gerais</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Cliente</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {agent?.client_name || 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Modelo</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent?.model}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Temperatura</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent?.temperature}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Máximo de Tokens</dt>
                  <dd className="mt-1 text-sm text-gray-900">{agent?.max_tokens}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${agent?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {agent?.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Visibilidade</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${agent?.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}
                    >
                      {agent?.is_public ? 'Público' : 'Privado'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Data de Criação
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {agent?.created_at
                      ? formatDate(agent.created_at)
                      : 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Última Atualização
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {agent?.updated_at
                      ? formatDate(agent.updated_at)
                      : 'Não disponível'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Descrição</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-900">
                {agent?.description || 'Nenhuma descrição disponível.'}
              </p>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Prompt do Sistema</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm text-gray-900 whitespace-pre-wrap bg-gray-50 p-4 rounded-md border border-gray-200">
              {agent?.system_prompt || 'Nenhum prompt do sistema definido.'}
            </pre>
          </CardContent>
        </Card>

        <h2 className="text-xl font-bold text-gray-900 mb-4">Métricas de Uso</h2>

        {isLoadingStats ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <MetricsCard
              title="Total de Conversas"
              value={statsData?.total_conversations || 0}
              icon={<MessageSquare className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Total de Mensagens"
              value={statsData?.total_messages || 0}
              icon={<MessageSquare className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Usuários"
              value={statsData?.users_count || 0}
              icon={<Users className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Tempo Médio de Resposta"
              value={`${statsData?.avg_response_time?.toFixed(2) || 0}s`}
              icon={<Clock className="h-6 w-6 text-primary-600" />}
            />
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Total de Tokens</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-900">
                {statsData?.total_tokens?.toLocaleString() || 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Avaliação Média</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Star className="h-5 w-5 text-yellow-500 mr-1" />
                <p className="text-sm text-gray-900">
                  {statsData?.feedback_score?.toFixed(1) || 'N/A'}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <Modal
          isOpen={isStatusModalOpen}
          onClose={() => setIsStatusModalOpen(false)}
          title={`${agent?.is_active ? 'Desativar' : 'Ativar'} Agente`}
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja{' '}
              {agent?.is_active ? 'desativar' : 'ativar'} o agente{' '}
              <strong>{agent?.name}</strong>?
            </p>
            {agent?.is_active && (
              <p className="mb-4 text-red-600">
                Ao desativar o agente, ele não estará mais disponível para uso pelos clientes.
              </p>
            )}
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setIsStatusModalOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                variant={agent?.is_active ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                isLoading={isTogglingAgentStatus}
              >
                {agent?.is_active ? 'Desativar' : 'Ativar'}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}