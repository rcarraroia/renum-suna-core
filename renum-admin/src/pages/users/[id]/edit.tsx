import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useUsers } from '../../../hooks/useUsers';
import { User, UserFormData } from '../../../types/user';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import UserForm from '../../../components/users/UserForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function EditUser() {
  const router = useRouter();
  const { id } = router.query;
  const { getUser, updateUser, isUpdatingUser, error, setError } = useUsers();
  const [user, setUser] = useState<User | null>(null);

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

  useEffect(() => {
    if (userData) {
      setUser(userData);
    }
  }, [userData]);

  useEffect(() => {
    if (userError) {
      setError(userError.message);
    }
  }, [userError, setError]);

  const handleSubmit = async (data: UserFormData) => {
    if (!id) return;

    try {
      // Converter string para boolean (do select)
      const formattedData = {
        ...data,
        is_active: data.is_active === 'true' || data.is_active === true,
      };

      await updateUser({ id: id as string, data: formattedData });
      router.push(`/users/${id}`);
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

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Editar Usuário</title>
        <meta name="description" content="Editar usuário" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href={`/users/${id}`}>
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Editar Usuário: {user?.name}
          </h1>
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
            <CardTitle>Informações do Usuário</CardTitle>
          </CardHeader>
          <CardContent>
            {user && (
              <UserForm
                defaultValues={{
                  client_id: user.client_id,
                  name: user.name,
                  email: user.email,
                  role: user.role,
                  is_active: user.is_active,
                }}
                onSubmit={handleSubmit}
                isSubmitting={isUpdatingUser}
                isEditMode={true}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}