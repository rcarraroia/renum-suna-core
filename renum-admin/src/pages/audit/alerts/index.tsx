import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Plus, Edit, Trash2, Power, PowerOff } from 'lucide-react';
import { useAudit } from '../../../hooks/useAudit';
import { AlertRule } from '../../../types/audit';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import Table from '../../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import AlertRuleForm from '../../../components/audit/AlertRuleForm';
import { formatDate } from '../../../lib/utils';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function AlertRules() {
  const {
    alertRules,
    isLoadingAlertRules,
    updateAlertRule,
    isUpdatingAlertRule,
    deleteAlertRule,
    isDeletingAlertRule,
    toggleAlertRule,
    isTogglingAlertRule,
    eventTypes,
    isLoadingEventTypes,
    entityTypes,
    isLoadingEntityTypes,
    error,
    setError,
  } = useAudit();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<AlertRule | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const handleOpenCreateModal = () => {
    setSelectedRule(null);
    setIsEditing(false);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (rule: AlertRule) => {
    setSelectedRule(rule);
    setIsEditing(true);
    setIsFormModalOpen(true);
  };

  const handleOpenDeleteModal = (rule: AlertRule) => {
    setSelectedRule(rule);
    setIsDeleteModalOpen(true);
  };

  const handleSubmitRule = async (data: any) => {
    try {
      await updateAlertRule({
        id: selectedRule?.id,
        data: {
          ...data,
          is_active: data.is_active === 'true' || data.is_active === true,
        },
      });
      setIsFormModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleDeleteRule = async () => {
    if (!selectedRule) return;

    try {
      await deleteAlertRule(selectedRule.id);
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleToggleRule = async (id: string, isActive: boolean) => {
    try {
      await toggleAlertRule({ id, isActive });
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const columns = [
    { header: 'Nome', accessor: 'name' },
    { header: 'Descrição', accessor: 'description' },
    { 
      header: 'Evento', 
      accessor: (row: AlertRule) => row.event_type || 'Todos'
    },
    { 
      header: 'Entidade', 
      accessor: (row: AlertRule) => row.entity_type || 'Todas'
    },
    { 
      header: 'Status', 
      accessor: (row: AlertRule) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
        >
          {row.is_active ? 'Ativo' : 'Inativo'}
        </span>
      )
    },
    { header: 'Atualizado Em', accessor: (row: AlertRule) => formatDate(row.updated_at) },
    {
      header: 'Ações',
      accessor: (row: AlertRule) => (
        <div className="flex space-x-2">
          <button
            onClick={() => handleToggleRule(row.id, !row.is_active)}
            className={`${row.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'}`}
            disabled={isTogglingAlertRule}
          >
            {row.is_active ? (
              <PowerOff className="h-5 w-5" />
            ) : (
              <Power className="h-5 w-5" />
            )}
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
        <title>Renum Admin - Alertas de Auditoria</title>
        <meta name="description" content="Gerenciamento de alertas de auditoria" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/audit/logs">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Alertas de Auditoria</h1>
          <div className="ml-auto">
            <Button onClick={handleOpenCreateModal}>
              <Plus className="h-4 w-4 mr-2" /> Nova Regra
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
            <CardTitle>Regras de Alerta</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              columns={columns}
              data={alertRules || []}
              isLoading={isLoadingAlertRules}
              emptyMessage="Nenhuma regra de alerta encontrada"
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          title={isEditing ? 'Editar Regra de Alerta' : 'Nova Regra de Alerta'}
          size="lg"
        >
          <AlertRuleForm
            defaultValues={
              selectedRule
                ? {
                    name: selectedRule.name,
                    description: selectedRule.description,
                    event_type: selectedRule.event_type,
                    entity_type: selectedRule.entity_type,
                    actor_type: selectedRule.actor_type,
                    conditions: selectedRule.conditions,
                    actions: selectedRule.actions,
                    is_active: selectedRule.is_active,
                  }
                : undefined
            }
            onSubmit={handleSubmitRule}
            isSubmitting={isUpdatingAlertRule}
            eventTypes={eventTypes || []}
            entityTypes={entityTypes || []}
            isEditMode={isEditing}
          />
        </Modal>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Regra de Alerta"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir a regra de alerta{' '}
              <strong>{selectedRule?.name}</strong>?
            </p>
            <p className="mb-4 text-red-600">
              Esta ação não pode ser desfeita.
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
                onClick={handleDeleteRule}
                isLoading={isDeletingAlertRule}
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