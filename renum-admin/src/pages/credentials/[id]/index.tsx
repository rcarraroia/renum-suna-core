import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Edit, ArrowLeft, Trash2, AlertTriangle, Calendar, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useCredentials } from '../../../hooks/useCredentials';
import { Credential, CredentialUsage } from '../../../types/credential';
import { formatDate } from '../../../lib/utils';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import CredentialViewer from '../../../components/credentials/CredentialViewer';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import MetricsCard from '../../../components/dashboard/MetricsCard';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function CredentialDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { getCredential, getCredentialUsage, deleteCredential, isDeletingCredential, error, setError } = useCredentials();
  const [credential, setCredential] = useState<Credential | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);

  // Buscar detalhes da credencial
  const {
    data: credentialData,
    isLoading: isLoadingCredential,
    error: credentialError,
  } = useQuery<Credential>({
    queryKey: ['credential', id],
    queryFn: () => getCredential(id as string),
    enabled: !!id,
  });

  // Buscar estatísticas de uso da credencial
  const {
    data: usageData,
    isLoading: isLoadingUsage,
    error: usageError,
  } = useQuery<CredentialUsage>({
    queryKey: ['credential-usage', id],
    queryFn: () => getCredentialUsage(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (credentialData) {
      setCredential(credentialData);
    }
  }, [credentialData]);

  useEffect(() => {
    if (credentialError) {
      setError(credentialError.message);
    }
    if (usageError) {
      setError(usageError.message);
    }
  }, [credentialError, usageError, setError]);

  const handleDelete = async () => {
    if (!id) return;

    try {
      await deleteCredential(id as string);
      router.push('/credentials');
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  const isExpired = credential?.expires_at 
    ? new Date(credential.expires_at) < new Date() 
    : false;

  const isCloseToExpiry = credential?.expires_at 
    ? !isExpired && (new Date(credential.expires_at).getTime() - new Date().getTime()) < (30 * 24 * 60 * 60 * 1000) 
    : false;

  if (isLoadingCredential) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!credential && !isLoadingCredential) {
    return (
      <Alert variant="error" title="Erro">
        Credencial não encontrada
      </Alert>
    );
  }

  const typeLabels: Record<string, string> = {
    'api_key': 'Chave de API',
    'oauth_token': 'Token OAuth',
    'service_account': 'Conta de Serviço',
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Detalhes da Credencial</title>
        <meta name="description" content="Detalhes da credencial" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/credentials">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{credential?.service_name}</h1>
          <div className="ml-auto flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setIsViewModalOpen(true)}
            >
              Visualizar Valor
            </Button>
            <Link href={`/credentials/${id}/edit`}>
              <a>
                <Button>
                  <Edit className="h-4 w-4 mr-2" /> Editar
                </Button>
              </a>
            </Link>
            <Button
              variant="destructive"
              onClick={() => setIsDeleteModalOpen(true)}
            >
              <Trash2 className="h-4 w-4 mr-2" /> Excluir
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

        {isExpired && (
          <Alert
            variant="warning"
            title="Credencial Expirada"
            className="mb-4"
          >
            Esta credencial expirou em {formatDate(credential?.expires_at || '')}. Considere atualizá-la ou desativá-la.
          </Alert>
        )}

        {!isExpired && isCloseToExpiry && (
          <Alert
            variant="warning"
            title="Credencial Próxima da Expiração"
            className="mb-4"
          >
            Esta credencial expirará em {formatDate(credential?.expires_at || '')}. Considere atualizá-la em breve.
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
                  <dt className="text-sm font-medium text-gray-500">Tipo</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {credential?.credential_type ? typeLabels[credential.credential_type] || credential.credential_type : 'Não definido'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${credential?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {credential?.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Expiração</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {credential?.expires_at ? (
                      <div className="flex items-center">
                        {isExpired && <AlertTriangle className="h-4 w-4 text-red-500 mr-1" />}
                        {!isExpired && isCloseToExpiry && <AlertTriangle className="h-4 w-4 text-yellow-500 mr-1" />}
                        <span className={isExpired ? 'text-red-600' : isCloseToExpiry ? 'text-yellow-600' : ''}>
                          {formatDate(credential.expires_at)}
                        </span>
                      </div>
                    ) : (
                      'Não expira'
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Data de Criação
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {credential?.created_at
                      ? formatDate(credential.created_at)
                      : 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Última Atualização
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {credential?.updated_at
                      ? formatDate(credential.updated_at)
                      : 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Último Uso
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {credential?.last_used
                      ? formatDate(credential.last_used)
                      : 'Nunca usado'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Metadados</CardTitle>
            </CardHeader>
            <CardContent>
              {credential?.metadata && Object.keys(credential.metadata).length > 0 ? (
                <dl className="grid grid-cols-1 gap-4">
                  {credential.metadata.provider && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Provedor</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {credential.metadata.provider}
                      </dd>
                    </div>
                  )}
                  {credential.metadata.environment && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Ambiente</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {credential.metadata.environment === 'production' ? 'Produção' :
                         credential.metadata.environment === 'staging' ? 'Homologação' :
                         credential.metadata.environment === 'development' ? 'Desenvolvimento' :
                         credential.metadata.environment}
                      </dd>
                    </div>
                  )}
                  {credential.metadata.description && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Descrição</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {credential.metadata.description}
                      </dd>
                    </div>
                  )}
                  {credential.metadata.rate_limit && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Limite de Requisições</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {credential.metadata.rate_limit} por minuto
                      </dd>
                    </div>
                  )}
                  {credential.metadata.usage_notes && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Notas de Uso</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {credential.metadata.usage_notes}
                      </dd>
                    </div>
                  )}
                </dl>
              ) : (
                <p className="text-sm text-gray-500">Nenhum metadado disponível</p>
              )}
            </CardContent>
          </Card>
        </div>

        <h2 className="text-xl font-bold text-gray-900 mb-4">Estatísticas de Uso</h2>

        {isLoadingUsage ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <MetricsCard
              title="Total de Chamadas"
              value={usageData?.total_calls || 0}
              icon={<Activity className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Chamadas (Últimos 30 dias)"
              value={usageData?.last_30_days_calls || 0}
              icon={<Activity className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Média Diária"
              value={usageData?.average_daily_calls || 0}
              icon={<Calendar className="h-6 w-6 text-primary-600" />}
            />
          </div>
        )}

        {usageData?.last_error && (
          <Card>
            <CardHeader>
              <CardTitle>Último Erro</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm text-gray-900">
                  <span className="font-medium">Data:</span> {formatDate(usageData.last_error_date || '')}
                </p>
                <p className="text-sm text-red-600">
                  {usageData.last_error}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        <Modal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          title="Excluir Credencial"
        >
          <div>
            <p className="mb-4">
              Tem certeza que deseja excluir a credencial{' '}
              <strong>{credential?.service_name}</strong>?
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
          onClose={() => setIsViewModalOpen(false)}
          title="Visualizar Credencial"
        >
          {credential && (
            <CredentialViewer
              credentialId={credential.id}
              credentialType={credential.credential_type}
              serviceName={credential.service_name}
            />
          )}
        </Modal>
      </div>
    </ProtectedRoute>
  );
}