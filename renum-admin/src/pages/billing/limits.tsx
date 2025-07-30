import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Plus, Edit, Trash2, AlertTriangle } from 'lucide-react';
import { useBilling } from '../../hooks/useBilling';
import { UsageLimit } from '../../types/billing';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import Modal from '../../components/ui/Modal';
import Table from '../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import UsageLimitForm from '../../components/billing/UsageLimitForm';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function UsageLimits() {
  const {
    usageLimits,
    isLoadingLimits,
    updateLimit,
    isUpdatingLimit,
    deleteLimit,
    isDeletingLimit,
    error,
    setError,
  } = useBilling();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedLimit, setSelectedLimit] = useState<UsageLimit | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleOpenCreateModal = () => {
    setSelectedLimit(null);
    setIsEditing(false);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (limit: UsageLimit) => {
    setSelectedLimit(limit);
    setIsEditing(true);
    setIsFormModalOpen(true);
  };

  const handleOpenDeleteModal = (limit: UsageLimit) => {
    setSelectedLimit(limit);
    setIsDeleteModalOpen(true);
  };

  const handleSubmitLimit = async (data: any) => {
    try {
      await updateLimit({
        ...data,
        limit: Number(data.limit),
        alert_threshold: Number(data.alert_threshold),
        is_hard_limit: data.is_hard_limit === 'true' || data.is_hard_limit === true,
      });
      setIsFormModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleDeleteLimit = async () => {
    if (!selectedLimit) return;

    try {
      await deleteLimit({
        clientId: selectedLimit.client_id,
        resourceType: selectedLimit.resource_type,
      });
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const getResourceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'tokens': 'Tokens',
      'api_calls': 'Chamadas de API',
      'storage': 'Armazenamento (GB)',
      'users': 'Usuários',
      'agents': 'Agentes',
      'knowledge_bases': 'Bases de Conhecimento',
    };
    return labels[type] || type;
  };

  const columns = [
    { header: 'Cliente', accessor: (row: UsageLimit) => row.client_name },
    { header: 'Recurso', accessor: (row: UsageLimit) => getResourceTypeLabel(row.resource_type) },
    { header: 'Limite', accessor: (row: UsageLimit) => row.limit.toLocaleString() },
    { 
      header: 'Uso Atual', 
      accessor: (row: UsageLimit) => {
        const usagePercentage = (row.current_usage / row.limit) * 100;
        const isWarning = usagePercentage >= row.alert_threshold;
        const isExceeded = usagePercentage >= 100;
        
        return (
          <div className="flex items-center">
            {isExceeded && <AlertTriangle className="h-4 w-4 text-red-500 mr-1" />}
            {!isExceeded && isWarning && <AlertTriangle className="h-4 w-4 text-yellow-500 mr-1" />}
            <span className={isExceeded ? 'text-red-600' : isWarning ? 'text-yellow-600' : ''}>
              {row.current_usage.toLocaleString()} ({usagePercentage.toFixed(1)}%)
            </span>
          </div>
        );
      }
    },
    { header: 'Alerta em', accessor: (row: UsageLimit) => `${row.alert_threshold}%` },
    { 
      header: 'Tipo de Limite', 
      accessor: (row: UsageLimit) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_hard_limit ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}
        >
          {row.is_hard_limit ? 'Rígido' : 'Flexível'}
        </span>
      )
    },
    {
      header: 'Ações',
      accessor: (row: UsageLimit) => (
        <div className="flex space-x-2">
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
        <title>Renum Admin - Limites de Uso</title>
        <meta name="description" content="Gerenciamento de limites de uso" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/billing">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Limites de Uso</h1>
          <div className="ml-auto">
            <Button onClick={handleOpenCreateModal}>
              <Plus className="h-4 w-4 mr-2" /> Novo Limite
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
            <CardTitle>Limites Configurados</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              columns={columns}
              data={usageLimits || []}
              isLoading={isLoadingLimits}
              emptyMessage="Nenhum limite configurado"
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          title={isEditing ? 'Editar Limite de Uso' : 'Novo Limite de Uso'}
        >
          <UsageLimitForm
            defaultValues={
              selectedLimit
                ? {
                    client_id: selectedLimit.client_id,
                    resource_type: selectedLimit.resource_type,
                    limit: selectedLimit.limit,
                    alert_threshold: selectedLimit.alert_threshold,
                    is_hard_limit: selectedLimit.is_hard_limit,
                  }
                : undefined
            }
            onSubmit={handleSubmitLimit}
            isSubmitting={isUpdatingLimit}
          />
        </Modal>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Limite de Uso"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir o limite de{' '}
              <strong>{selectedLimit && getResourceTypeLabel(selectedLimit.resource_type)}</strong>{' '}
              para o cliente <strong>{selectedLimit?.client_name}</strong>?
            </p>
            <p className="mb-4 text-yellow-600">
              Ao excluir este limite, o cliente não terá mais restrições para este recurso.
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
                onClick={handleDeleteLimit}
                isLoading={isDeletingLimit}
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