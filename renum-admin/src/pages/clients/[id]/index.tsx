import React, { useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Edit, ArrowLeft, Users, Bot, Database, CreditCard, Clock } from 'lucide-react';
import Button from '../../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import { formatDate, formatCurrency } from '../../../lib/utils';
import { apiClient } from '../../../lib/api-client';
import { Client } from '../../../types/client';

export default function ClientDetailsPage() {
  const router = useRouter();
  const { id } = router.query;
  const [activeTab, setActiveTab] = useState('overview');

  // Função para buscar detalhes do cliente
  const fetchClientDetails = async () => {
    if (!id) return null;

    // Simulação de API - remover quando integrar com API real
    // Na implementação real:
    // const { data } = await apiClient.get(`/api/v2/admin/clients/${id}`);
    // return data;

    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay

    // Dados mockados para desenvolvimento
    const mockClient: Client = {
      id: id as string,
      name: 'Empresa ABC',
      email: 'contato@empresaabc.com',
      phone: '(11) 1234-5678',
      address: 'Av. Paulista, 1000, São Paulo, SP',
      logo_url: 'https://via.placeholder.com/150',
      plan: 'enterprise',
      status: 'active',
      usage_limit: 10000,
      current_usage: 7500,
      created_at: new Date('2023-01-15'),
      updated_at: new Date('2023-06-20'),
    };

    return mockClient;
  };

  // Query para buscar detalhes do cliente
  const { data: client, isLoading, error } = useQuery({
    queryKey: ['client', id],
    queryFn: fetchClientDetails,
    enabled: !!id,
  });

  // Função para buscar métricas de uso do cliente
  const fetchClientMetrics = async () => {
    if (!id) return null;

    // Simulação de API - remover quando integrar com API real
    // Na implementação real:
    // const { data } = await apiClient.get(`/api/v2/admin/clients/${id}/metrics`);
    // return data;

    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay

    // Dados mockados para desenvolvimento
    return {
      users: 15,
      agents: 8,
      knowledge_bases: 3,
      monthly_cost: 1250,
      usage_history: [
        { date: '2023-06-01', tokens: 240000, cost: 120 },
        { date: '2023-06-02', tokens: 320000, cost: 160 },
        { date: '2023-06-03', tokens: 180000, cost: 90 },
        { date: '2023-06-04', tokens: 420000, cost: 210 },
        { date: '2023-06-05', tokens: 280000, cost: 140 },
        { date: '2023-06-06', tokens: 350000, cost: 175 },
        { date: '2023-06-07', tokens: 290000, cost: 145 },
      ],
    };
  };

  // Query para buscar métricas de uso do cliente
  const { data: metrics, isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['client-metrics', id],
    queryFn: fetchClientMetrics,
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error || !client) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
        <p>Erro ao carregar detalhes do cliente. Por favor, tente novamente.</p>
      </div>
    );
  }

  const planLabels: Record<string, string> = {
    basic: 'Básico',
    standard: 'Padrão',
    premium: 'Premium',
    enterprise: 'Enterprise',
  };

  const statusLabels: Record<string, string> = {
    active: 'Ativo',
    inactive: 'Inativo',
    pending: 'Pendente',
  };

  const statusClasses: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    inactive: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800',
  };

  return (
    <>
      <Head>
        <title>{client.name} | Renum Admin</title>
      </Head>

      <div className="mb-6">
        <div className="flex items-center mb-4">
          <Link href="/clients">
            <a className="text-gray-500 hover:text-gray-700 mr-2">
              <ArrowLeft className="h-5 w-5" />
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{client.name}</h1>
          <span className={`ml-3 px-2 py-1 rounded-full text-xs ${statusClasses[client.status]}`}>
            {statusLabels[client.status] || client.status}
          </span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <p className="text-gray-600">
            Cliente desde {formatDate(client.created_at, 'dd/MM/yyyy')}
          </p>
          <div className="mt-2 sm:mt-0">
            <Link href={`/clients/${client.id}/edit`}>
              <a>
                <Button>
                  <Edit className="h-4 w-4 mr-2" />
                  Editar Cliente
                </Button>
              </a>
            </Link>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              className={`py-4 px-6 text-sm font-medium ${
                activeTab === 'overview'
                  ? 'border-b-2 border-primary-500 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('overview')}
            >
              Visão Geral
            </button>
            <button
              className={`py-4 px-6 text-sm font-medium ${
                activeTab === 'users'
                  ? 'border-b-2 border-primary-500 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('users')}
            >
              Usuários
            </button>
            <button
              className={`py-4 px-6 text-sm font-medium ${
                activeTab === 'agents'
                  ? 'border-b-2 border-primary-500 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('agents')}
            >
              Agentes
            </button>
            <button
              className={`py-4 px-6 text-sm font-medium ${
                activeTab === 'billing'
                  ? 'border-b-2 border-primary-500 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('billing')}
            >
              Faturamento
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Informações do Cliente</h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500">Nome</p>
                      <p className="font-medium">{client.name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium">{client.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Telefone</p>
                      <p className="font-medium">{client.phone || 'Não informado'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Endereço</p>
                      <p className="font-medium">{client.address || 'Não informado'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Plano</p>
                      <p className="font-medium">{planLabels[client.plan] || client.plan}</p>
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-medium mb-4">Uso e Limites</h3>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500">Limite de Uso</p>
                      <p className="font-medium">{client.usage_limit?.toLocaleString() || 'Ilimitado'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Uso Atual</p>
                      <p className="font-medium">{client.current_usage?.toLocaleString() || '0'}</p>
                    </div>
                    {client.usage_limit && (
                      <div>
                        <p className="text-sm text-gray-500">Porcentagem de Uso</p>
                        <div className="flex items-center">
                          <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                            <div
                              className={`h-2.5 rounded-full ${
                                (client.current_usage / client.usage_limit) * 100 > 90
                                  ? 'bg-red-500'
                                  : (client.current_usage / client.usage_limit) * 100 > 70
                                  ? 'bg-yellow-500'
                                  : 'bg-green-500'
                              }`}
                              style={{
                                width: `${Math.min(
                                  (client.current_usage / client.usage_limit) * 100,
                                  100
                                )}%`,
                              }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">
                            {Math.round((client.current_usage / client.usage_limit) * 100)}%
                          </span>
                        </div>
                      </div>
                    )}
                    <div>
                      <p className="text-sm text-gray-500">Última Atualização</p>
                      <p className="font-medium">{formatDate(client.updated_at)}</p>
                    </div>
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-medium mb-4">Métricas</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center">
                      <div className="p-2 bg-blue-100 rounded-full mr-3">
                        <Users className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Usuários</p>
                        <p className="text-xl font-bold">
                          {isLoadingMetrics ? '...' : metrics?.users || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-full mr-3">
                        <Bot className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Agentes</p>
                        <p className="text-xl font-bold">
                          {isLoadingMetrics ? '...' : metrics?.agents || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 rounded-full mr-3">
                        <Database className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Bases de Conhecimento</p>
                        <p className="text-xl font-bold">
                          {isLoadingMetrics ? '...' : metrics?.knowledge_bases || 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center">
                      <div className="p-2 bg-yellow-100 rounded-full mr-3">
                        <CreditCard className="h-5 w-5 text-yellow-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Custo Mensal</p>
                        <p className="text-xl font-bold">
                          {isLoadingMetrics
                            ? '...'
                            : formatCurrency(metrics?.monthly_cost || 0)}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'users' && (
            <div className="text-center py-8">
              <p className="text-gray-500">
                Detalhes dos usuários serão implementados em breve.
              </p>
            </div>
          )}

          {activeTab === 'agents' && (
            <div className="text-center py-8">
              <p className="text-gray-500">
                Detalhes dos agentes serão implementados em breve.
              </p>
            </div>
          )}

          {activeTab === 'billing' && (
            <div className="text-center py-8">
              <p className="text-gray-500">
                Detalhes de faturamento serão implementados em breve.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}