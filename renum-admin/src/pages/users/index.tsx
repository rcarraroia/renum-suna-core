import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, Edit, Eye, Power, PowerOff, Key } from 'lucide-react';
import { useUsers } from '../../hooks/useUsers';
import { formatDate } from '../../lib/utils';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Alert from '../../components/ui/Alert';
import ResetPasswordForm from '../../components/users/ResetPasswordForm';
import ProtectedRoute from '../../components/layout/ProtectedRoute';
import { User } from '../../types/user';

export default function UsersList() {
  const {
    users,
    isLoadingUsers,
    error,
    setError,
    toggleUserStatus,
    isTogglingUserStatus,
    resetPassword,
    isResettingPassword,
  } = useUsers();

  const [selectedUser, setSelectedUser] = useState<{
    id: string;
    name: string;
    isActive: boolean;
  } | null>(null);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [isResetPasswordModalOpen, setIsResetPasswordModalOpen] = useState(false);

  const handleToggleStatus = async () => {
    if (!selectedUser) return;

    try {
      await toggleUserStatus({
        id: selectedUser.id,
        isActive: !selectedUser.isActive,
      });
      setIsStatusModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const handleResetPassword = async (data: { password: string }) => {
    if (!selectedUser) return;

    try {
      await resetPassword({
        id: selectedUser.id,
        password: data.password,
      });
      setIsResetPasswordModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const columns = [
    { header: 'Nome', accessor: (row: User) => row.name },
    { header: 'Email', accessor: (row: User) => row.email },
    { header: 'Cliente', accessor: (row: User) => row.client_name },
    { header: 'Papel', accessor: (row: User) => row.role },
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
          <Link href={`/users/${row.id}`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Eye className="h-5 w-5" />
            </a>
          </Link>
          <Link href={`/users/${row.id}/edit`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Edit className="h-5 w-5" />
            </a>
          </Link>
          <button
            onClick={() => {
              setSelectedUser({
                id: row.id,
                name: row.name,
                isActive: row.is_active,
              });
              setIsResetPasswordModalOpen(true);
            }}
            className="text-yellow-600 hover:text-yellow-800"
          >
            <Key className="h-5 w-5" />
          </button>
          <button
            onClick={() => {
              setSelectedUser({
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
        <title>Renum Admin - Usuários</title>
        <meta name="description" content="Gerenciamento de usuários" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Usuários</h1>
            <p className="text-gray-600">Gerencie os usuários da plataforma</p>
          </div>
          <Link href="/users/new">
            <a>
              <Button>
                <Plus className="h-4 w-4 mr-2" /> Novo Usuário
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
            data={users || []}
            isLoading={isLoadingUsers}
            emptyMessage="Nenhum usuário encontrado"
          />
        </div>

        <Modal
          isOpen={isStatusModalOpen}
          onClose={() => setIsStatusModalOpen(false)}
          title={`${selectedUser?.isActive ? 'Desativar' : 'Ativar'} Usuário`}
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja{' '}
              {selectedUser?.isActive ? 'desativar' : 'ativar'} o usuário{' '}
              <strong>{selectedUser?.name}</strong>?
            </p>
            {selectedUser?.isActive && (
              <p className="mb-4 text-red-600">
                Ao desativar o usuário, ele perderá acesso à plataforma.
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
                variant={selectedUser?.isActive ? 'destructive' : 'default'}
                onClick={handleToggleStatus}
                isLoading={isTogglingUserStatus}
              >
                {selectedUser?.isActive ? 'Desativar' : 'Ativar'}
              </Button>
            </div>
          </div>
        </Modal>

        <Modal
          isOpen={isResetPasswordModalOpen}
          onClose={() => setIsResetPasswordModalOpen(false)}
          title="Redefinir Senha"
        >
          <div>
            <p className="mb-4">
              Definir nova senha para o usuário <strong>{selectedUser?.name}</strong>:
            </p>
            <ResetPasswordForm
              onSubmit={handleResetPassword}
              isSubmitting={isResettingPassword}
            />
          </div>
        </Modal>
      </div>
    </ProtectedRoute>
  );
}