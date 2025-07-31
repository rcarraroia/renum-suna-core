import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, Edit, Trash2, History } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';
import { SystemSetting, SystemSettingFormData } from '../../types/settings';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import Modal from '../../components/ui/Modal';
import Table from '../../components/ui/Table';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import SettingForm from '../../components/settings/SettingForm';
import ChangeLogList from '../../components/settings/ChangeLogList';
import { formatDate } from '../../lib/utils';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function Settings() {
  const {
    settings,
    isLoadingSettings,
    updateSetting,
    isUpdatingSetting,
    deleteSetting,
    isDeletingSetting,
    useChangeLogs,
    error,
    setError,
  } = useSettings();

  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [selectedSetting, setSelectedSetting] = useState<SystemSetting | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const {
    data: changeLogs,
    isLoading: isLoadingChangeLogs,
  } = useChangeLogs(selectedKey || undefined);

  const handleOpenCreateModal = () => {
    setSelectedSetting(null);
    setIsEditing(false);
    setIsFormModalOpen(true);
  };

  const handleOpenEditModal = (setting: SystemSetting) => {
    setSelectedSetting(setting);
    setIsEditing(true);
    setIsFormModalOpen(true);
  };

  const handleOpenDeleteModal = (setting: SystemSetting) => {
    setSelectedSetting(setting);
    setIsDeleteModalOpen(true);
  };

  const handleOpenHistoryModal = (key: string) => {
    setSelectedKey(key);
    setIsHistoryModalOpen(true);
  };

  const handleSubmitSetting = async (data: SystemSettingFormData) => {
    try {
      await updateSetting(data);
      setIsFormModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleDeleteSetting = async () => {
    if (!selectedSetting) return;

    try {
      await deleteSetting(selectedSetting.key);
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const formatValue = (setting: SystemSetting) => {
    if (setting.is_sensitive) {
      return '••••••••••';
    }

    const value = setting.value;
    if (value === null || value === undefined) {
      return 'null';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  const columns = [
    { header: 'Chave', accessor: (row: SystemSetting) => row.key },
    { 
      header: 'Valor', 
      accessor: (row: SystemSetting) => {
        const value = formatValue(row);
        return value.length > 50 ? `${value.substring(0, 50)}...` : value;
      }
    },
    { header: 'Descrição', accessor: (row: SystemSetting) => row.description },
    { 
      header: 'Sensível', 
      accessor: (row: SystemSetting) => (
        <span
          className={`px-2 py-1 rounded-full text-xs ${row.is_sensitive ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}
        >
          {row.is_sensitive ? 'Sim' : 'Não'}
        </span>
      )
    },
    { header: 'Atualizado Por', accessor: (row: SystemSetting) => row.updated_by_name },
    { header: 'Atualizado Em', accessor: (row: SystemSetting) => formatDate(row.updated_at) },
    {
      header: 'Ações',
      accessor: (row: SystemSetting) => (
        <div className="flex space-x-2">
          <button
            onClick={() => handleOpenEditModal(row)}
            className="text-blue-600 hover:text-blue-800"
          >
            <Edit className="h-5 w-5" />
          </button>
          <button
            onClick={() => handleOpenHistoryModal(row.key)}
            className="text-blue-600 hover:text-blue-800"
          >
            <History className="h-5 w-5" />
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
        <title>Renum Admin - Configurações</title>
        <meta name="description" content="Configurações do sistema" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
            <p className="text-gray-600">Gerenciar configurações do sistema</p>
          </div>
          <div className="flex space-x-3">
            <Button onClick={handleOpenCreateModal}>
              <Plus className="h-4 w-4 mr-2" /> Nova Configuração
            </Button>
            <Link href="/settings/security">
              <a>
                <Button variant="outline">
                  Segurança
                </Button>
              </a>
            </Link>
            <Link href="/settings/integrations">
              <a>
                <Button variant="outline">
                  Integrações
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

        <Card>
          <CardHeader>
            <CardTitle>Configurações do Sistema</CardTitle>
          </CardHeader>
          <CardContent>
            <Table
              columns={columns}
              data={settings || []}
              isLoading={isLoadingSettings}
              emptyMessage="Nenhuma configuração encontrada"
            />
          </CardContent>
        </Card>

        <Modal
          isOpen={isFormModalOpen}
          onClose={() => setIsFormModalOpen(false)}
          title={isEditing ? 'Editar Configuração' : 'Nova Configuração'}
        >
          <SettingForm
            defaultValues={
              selectedSetting
                ? {
                    key: selectedSetting.key,
                    value: selectedSetting.value,
                    description: selectedSetting.description,
                    is_sensitive: selectedSetting.is_sensitive,
                  }
                : undefined
            }
            onSubmit={handleSubmitSetting}
            isSubmitting={isUpdatingSetting}
            isEditMode={isEditing}
          />
        </Modal>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Configuração"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir a configuração{' '}
              <strong>{selectedSetting?.key}</strong>?
            </p>
            <p className="mb-4 text-red-600">
              Esta ação não pode ser desfeita e pode afetar o funcionamento do sistema.
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
                onClick={handleDeleteSetting}
                isLoading={isDeletingSetting}
              >
                Excluir
              </Button>
            </div>
          </div>
        </Modal>

        <Modal
          isOpen={isHistoryModalOpen}
          onClose={() => setIsHistoryModalOpen(false)}
          title={`Histórico de Alterações - ${selectedKey}`}
        >
          <ChangeLogList
            data={changeLogs || []}
            isLoading={isLoadingChangeLogs}
          />
        </Modal>
      </div>
    </ProtectedRoute>
  );
}