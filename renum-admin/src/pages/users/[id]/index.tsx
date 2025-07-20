import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { Edit, ArrowLeft, MessageSquare, Bot, Calendar, Key } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUsers } from '../../../hooks/useUsers';
import { User, UserActivity } from '../../../types/user';
import { formatDate } from '../../../lib/utils';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import Modal from '../../../components/ui/Modal';
import ResetPasswordForm from '../../../components/users/ResetPasswordForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import MetricsCard from '../../../components/dashboard/MetricsCard';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function UserDetails() {
  const router = useRouter();
  const { id } = router.query;
  const { getUser, getUserActivity, resetPassword, isResettingPassword, error, setError } = useUsers();
  const [user, setUser] = useState<User | null>(null);
  const [isResetPasswordModalOpen, setIsResetPasswordModalOpen] = useState(false);

  // Buscar detalhes do usuário
  const {
    data: userData,
    isLoading: isLoadingUser,
    error: userError,
  } = useQuery<User>({
    queryKey: ['user', id],
    queryFn: () => getUser(id as string),
    enabled: !!id,
  });

  // Buscar atividade do usuário
  const {
    data: activityData,
    isLoading: isLoadingActivity,
    error: activityError,
  } = useQuery<UserActivity>({
    queryKey: ['user-activity', id],
    queryFn: () => getUserActivity(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (userData) {
      setUser(userData);
    }
  }, [userData]);

  useEffect(() => {
    if (userError) {
      setError(userError.message);
    }
    if (activityError) {
      setError(activityError.message);
    }
  }, [userError, activityError, setError]);

  const handleResetPassword = async (data: { password: string }) => {
    if (!id) return;

    try {
      await resetPassword({
        id: id as string,
        password: data.password,
      });
      setIsResetPasswordModalOpen(false);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  if (isLoadingUser) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!user && !isLoadingUser) {
    return (
      <Alert variant="error" title="Erro">
        Usuário não encontrado
      </Alert>
    );
  }

  const roleLabels: Record<string, string> = {
    user: 'Usuário',
    admin: 'Administrador',
    manager: 'Gerente',
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Detalhes do Usuário</title>
        <meta name="description" content="Detalhes do usuário" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/users">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{user?.name}</h1>
          <div className="ml-auto flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setIsResetPasswordModalOpen(true)}
            >
              <Key className="h-4 w-4 mr-2" /> Redefinir Senha
            </Button>
            <Link href={`/users/${id}/edit`}>
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
                  <dt className="text-sm font-medium text-gray-500">Email</dt>
                  <dd className="mt-1 text-sm text-gray-900">{user?.email}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Papel</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.role ? roleLabels[user.role] || user.role : 'Não definido'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${user?.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}
                    >
                      {user?.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Data de Criação
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.created_at
                      ? formatDate(user.created_at)
                      : 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">
                    Última Atualização
                  </dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.updated_at
                      ? formatDate(user.updated_at)
                      : 'Não disponível'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Informações do Cliente</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Cliente</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.client_name || 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">ID do Cliente</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.client_id || 'Não disponível'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">ID do Usuário Auth</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {user?.auth_user_id || 'Não disponível'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </div>

        <h2 className="text-xl font-bold text-gray-900 mb-4">Atividade do Usuário</h2>

        {isLoadingActivity ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <MetricsCard
              title="Total de Conversas"
              value={activityData?.total_threads || 0}
              icon={<MessageSquare className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Total de Mensagens"
              value={activityData?.total_messages || 0}
              icon={<MessageSquare className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Agentes Utilizados"
              value={activityData?.agents_used || 0}
              icon={<Bot className="h-6 w-6 text-primary-600" />}
            />
            <MetricsCard
              title="Último Login"
              value={activityData?.last_login ? formatDate(activityData.last_login) : 'Nunca'}
              icon={<Calendar className="h-6 w-6 text-primary-600" />}
            />
          </div>
        )}

        {activityData?.last_agent_used && (
          <Card>
            <CardHeader>
              <CardTitle>Último Agente Utilizado</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-900">
                {activityData.last_agent_name || 'Nome não disponível'} ({activityData.last_agent_used})
              </p>
            </CardContent>
          </Card>
        )}

        <Modal
          isOpen={isResetPasswordModalOpen}
          onClose={() => setIsResetPasswordModalOpen(false)}
          title="Redefinir Senha"
        >
          <div>
            <p className="mb-4">
              Definir nova senha para o usuário <strong>{user?.name}</strong>:
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