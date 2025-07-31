import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, Edit, Eye, Power, PowerOff } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { Agent } from '../../types/agent';
import { formatDate } from '../../lib/utils';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Alert from '../../components/ui/Alert';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function AgentsList() {
  const {
    agents,
    isLoadingAgents,
    error,
    setError,
    toggleAgentStatus,
    isTogglingAgentStatus,
  } = useAgents();

  const [selectedAgent, setSelectedAgent] = useState<{
    id: string;
    name: string;
    isActive: boolean;
  } | null>(null);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);

  const handleToggleStatus = async () => {
    if (!selectedAgent) return;

    try {
      await toggleAgentStatus({
        id: selectedAgent.id,
        isActive: !selectedAgent.isActive,
      });
      setIsStatusModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const columns = [
    { header: 'Nome', accessor: (row: Agent) => row.name },
    { header: 'Cliente', accessor: (row: Agent) => row.client_name },
    { header: 'Modelo', accessor: (row: Agent) => row.model },
    {
      header: 'Visibilidade',
      accessor: (row: any) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_public ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}
        >
          {row.is_public ? 'Público' : 'Privado'}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: (row: any) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
        >
          {row.is_active ? 'Ativo' : 'Inativo'}
        </span>
      ),
    },
    {
      header: 'Criado em',
      accessor: (row: any) => formatDate(row.created_at),
    },
    {
      header: 'Ações',
      accessor: (row: any) => (
        <div className="flex space-x-2">
          <Link href={`/agents/${row.id}`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Eye className="h-5 w-5" />
            </a>
          </Link>
          <Link href={`/agents/${row.id}/edit`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Edit className="h-5 w-5" />
            </a>
          </Link>
          <button
            onClick={() => {
              setSelectedAgent({
                id: row.id,
                name: row.name,
                isActive: row.is_active,
              });
              setIsStatusModalOpen(true);
            }}
            className={`${row.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`}
          >
            {row.is_active ? (
              <PowerOff className="h-5 w-5" />
            ) : (
              <Power className="h-5 w-5" />
            )}
          </button>
        </div>
      ),
    },
  ];

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Agentes</title>
        <meta name="description" content="Gerenciamento de agentes" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agentes</h1>
            <p className="text-gray-600">Gerencie os agentes da plataforma</p>
          </div>
          <Link href="/agents/new">
            <a>
              <Button>
                <Plus className="h-4 w-4 mr-2" /> Novo Agente
              </Button>
            </a>
          </Link>
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

        <div className="bg-white shadow rounded-lg overflow-hidden">
          <Table
            columns={columns}
            data={agents || []}
            isLoading={isLoadingAgents}
            emptyMessage="Nenhum agente encontrado"
          />
        </div>

        <Modal
          isOpen={isStatusModalOpen}
          onClose={() => setIsStatusModalOpen(false)}
          title={`${selectedAgent?.isActive ? 'Desativar' : 'Ativar'} Agente`}
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja{' '}
              {selectedAgent?.isActive ? 'desativar' : 'ativar'} o agente{' '}
              <strong>{selectedAgent?.name}</strong>?
            </p>
            {selectedAgent?.isActive && (
              <p className="mb-4 text-red-600">
                Ao desativar o agente, ele não estará mais disponível para uso.
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
                variant={selectedAgent?.isActive ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                isLoading={isTogglingAgentStatus}
              >
                {selectedAgent?.isActive ? 'Desativar' : 'Ativar'}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}