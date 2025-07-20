import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, Edit, Eye, Trash2, AlertTriangle } from 'lucide-react';
import { useCredentials } from '../../hooks/useCredentials';
import { formatDate } from '../../lib/utils';
import Button from '../../components/ui/Button';
import Table from '../../components/ui/Table';
import Modal from '../../components/ui/Modal';
import Alert from '../../components/ui/Alert';
import CredentialViewer from '../../components/credentials/CredentialViewer';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function CredentialsList() {
  const {
    credentials,
    isLoadingCredentials,
    error,
    setError,
    deleteCredential,
    isDeletingCredential,
  } = useCredentials();

  const [selectedCredential, setSelectedCredential] = useState<{
    id: string;
    service_name: string;
    credential_type: 'api_key' | 'oauth_token' | 'service_account';
  } | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);

  const handleDelete = async () => {
    if (!selectedCredential) return;

    try {
      await deleteCredential(selectedCredential.id);
      setIsDeleteModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const columns = [
    { header: 'Serviço', accessor: 'service_name' },
    { header: 'Tipo', accessor: (row: any) => {
      const typeLabels: Record<string, string> = {
        'api_key': 'Chave de API',
        'oauth_token': 'Token OAuth',
        'service_account': 'Conta de Serviço',
      };
      return typeLabels[row.credential_type] || row.credential_type;
    }},
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
      header: 'Expiração',
      accessor: (row: any) => {
        if (!row.expires_at) return 'Não expira';
        
        const expiryDate = new Date(row.expires_at);
        const now = new Date();
        const isExpired = expiryDate < now;
        const isCloseToExpiry = !isExpired && (expiryDate.getTime() - now.getTime()) < (30 * 24 * 60 * 60 * 1000); // 30 dias
        
        return (
          <div className="flex items-center">
            {isExpired && <AlertTriangle className="h-4 w-4 text-red-500 mr-1" />}
            {!isExpired && isCloseToExpiry && <AlertTriangle className="h-4 w-4 text-yellow-500 mr-1" />}
            <span className={isExpired ? 'text-red-600' : isCloseToExpiry ? 'text-yellow-600' : ''}>
              {formatDate(row.expires_at)}
            </span>
          </div>
        );
      },
    },
    {
      header: 'Último Uso',
      accessor: (row: any) => row.last_used ? formatDate(row.last_used) : 'Nunca usado',
    },
    {
      header: 'Criado em',
      accessor: (row: any) => formatDate(row.created_at),
    },
    {
      header: 'Ações',
      accessor: (row: any) => (
        <div className="flex space-x-2">
          <button
            onClick={() => {
              setSelectedCredential({
                id: row.id,
                service_name: row.service_name,
                credential_type: row.credential_type,
              });
              setIsViewModalOpen(true);
            }}
            className="text-blue-600 hover:text-blue-800"
          >
            <Eye className="h-5 w-5" />
          </button>
          <Link href={`/credentials/${row.id}/edit`}>
            <a className="text-blue-600 hover:text-blue-800">
              <Edit className="h-5 w-5" />
            </a>
          </Link>
          <button
            onClick={() => {
              setSelectedCredential({
                id: row.id,
                service_name: row.service_name,
                credential_type: row.credential_type,
              });
              setIsDeleteModalOpen(true);
            }}
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
        <title>Renum Admin - Credenciais</title>
        <meta name="description" content="Gerenciamento de credenciais" />
      </Head>

      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Credenciais</h1>
            <p className="text-gray-600">Gerencie as credenciais de serviços externos</p>
          </div>
          <Link href="/credentials/new">
            <a>
              <Button>
                <Plus className="h-4 w-4 mr-2" /> Nova Credencial
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
            data={credentials || []}
            isLoading={isLoadingCredentials}
            emptyMessage="Nenhuma credencial encontrada"
          />
        </div>

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Credencial"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir a credencial{' '}
              <strong>{selectedCredential?.service_name}</strong>?
            </p>
            <p className="mb-4 text-red-600">
              Esta ação não pode ser desfeita e pode afetar serviços que dependem desta credencial.
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
                onClick={handleDelete}
                isLoading={isDeletingCredential}
              >
                Excluir
              </Button>
            </div>
          </div>
        </Modal>

        <Modal
          isOpen={isViewModalOpen}
          onClose={() => {
            setIsViewModalOpen(false);
            setSelectedCredential(null);
          }}
          title="Visualizar Credencial"
        >
          {selectedCredential && (
            <CredentialViewer
              credentialId={selectedCredential.id}
              credentialType={selectedCredential.credential_type}
              serviceName={selectedCredential.service_name}
            />
          )}
        </Modal>
      </div>
    </ProtectedRoute>
  );
}