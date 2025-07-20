import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Plus, Edit, Trash2, Play } from 'lucide-react';
import { useSettings } from '../../../hooks/useSettings';
import { IntegrationSetting } from '../../../types/settings';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import Table from '../../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import IntegrationForm from '../../../components/settings/IntegrationForm';
import { formatDate } from '../../../lib/utils';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function Integrations() {
  const {
    integrations,
    isLoadingIntegrations,
    updateIntegration,
    isUpdatingIntegration,
    deleteIntegration,
    isDeletingIntegration,
    testIntegration,
    isTestingIntegration,
    error,
    setError,
  } = useSettings();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<IntegrationSetting | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleOpenCreateModal = () => {
    setSelectedIntegration(null);
    setIsEditing(false);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (integration: IntegrationSetting) => {
    setSelectedIntegration(integration);
    setIsEditing(true);
    setIsFormModalOpen(true);
  };

  const handleOpenDeleteModal = (integration: IntegrationSetting) => {
    setSelectedIntegration(integration);
    setIsDeleteModalOpen(true);
  };

  const handleSubmitIntegration = async (data: any) => {
    try {
      await updateIntegration({
        id: selectedIntegration?.id,
        data,
      });
      setIsFormModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleDeleteIntegration = async () => {
    if (!selectedIntegration) return;

    try {
      await deleteIntegration(selectedIntegration.id);
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleTestIntegration = async (id: string) => {
    try {
      await testIntegration(id);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const columns = [
    { header: 'Nome', accessor: 'name' },
    { 
      header: 'Tipo', 
      accessor: (row: IntegrationSetting) => {
        const typeLabels: Record<string, string> = {
          'api': 'API',
          'oauth': 'OAuth',
          'webhook': 'Webhook',
          'smtp': 'SMTP',
          'other': 'Outro',
        };
        return typeLabels[row.type] || row.type;
      }
    },
    { 
      header: 'Status', 
      accessor: (row: IntegrationSetting) => {
        const statusClasses = {
          'active': 'bg-green-100 text-green-800',
          'inactive': 'bg-gray-100 text-gray-800',
          'error': 'bg-red-100 text-red-800',
        };
        
        const statusLabels = {
          'active': 'Ativo',
          'inactive': 'Inativo',
          'error': 'Erro',
        };
        
        return (
          <span
            className={`px-2 py-1 rounded-full text-xs ${statusClasses[row.status]}`}
          >
            {statusLabels[row.status]}
          </span>
        );
      }
    },
    { header: 'Última Verificação', accessor: (row: IntegrationSetting) => formatDate(row.last_checked) },
    {
      header: 'Ações',
      accessor: (row: IntegrationSetting) => (
        <div className="flex space-x-2">
          <button
            onClick={() => handleTestIntegration(row.id)}
            className="text-blue-600 hover:text-blue-800"
            disabled={isTestingIntegration}
          >
            <Play className="h-5 w-5" />
          </button>
          <button
            onClick={() => handleOpenEditModal(row)}
            className="text-blue-600 hover:text-blue-800"
          >
            <Edit className="h-5 w-5" />
          </button>
          <button
            onClick={() => handleOpenDeleteModal(row)}
            className="text-red-600 hover:text-red-800"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Integrações</title>
        <meta name="description" content="Gerenciamento de integrações" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/settings">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Integrações</h1>
          <div className="ml-auto">
            <Button onClick={handleOpenCreateModal}>
              <Plus className="h-4 w-4 mr-2" /> Nova Integração
            </Button>
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

        <Card>
          <CardHeader>
            <CardTitle>Integrações Configuradas</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              columns={columns}
              data={integrations || []}
              isLoading={isLoadingIntegrations}
              emptyMessage="Nenhuma integração encontrada"
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          title={isEditing ? 'Editar Integração' : 'Nova Integração'}
          size="lg"
        >
          <IntegrationForm
            defaultValues={
              selectedIntegration
                ? {
                    name: selectedIntegration.name,
                    type: selectedIntegration.type,
                    config: selectedIntegration.config,
                  }
                : undefined
            }
            onSubmit={handleSubmitIntegration}
            isSubmitting={isUpdatingIntegration}
            isEditMode={isEditing}
          />
        </Modal>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Integração"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir a integração{' '}
              <strong>{selectedIntegration?.name}</strong>?
            </p>
            <p className="mb-4 text-red-600">
              Esta ação não pode ser desfeita e pode afetar funcionalidades que dependem desta integração.
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                variant="outline"
                onClick={() => setIsDeleteModalOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                variant="destructive"
                onClick={handleDeleteIntegration}
                isLoading={isDeletingIntegration}
              >
                Excluir
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}