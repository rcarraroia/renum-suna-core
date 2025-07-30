import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useUsers } from '../../hooks/useUsers';
import { UserFormData } from '../../types/user';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import UserForm from '../../components/users/UserForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function NewUser() {
  const router = useRouter();
  const { createUser, isCreatingUser, error, setError } = useUsers();

  const handleSubmit = async (data: UserFormData) => {
    try {
      // Converter string para boolean (do select)
      const formattedData = {
        ...data,
        is_active: Boolean(data.is_active),
      };

      await createUser(formattedData);
      router.push('/users');
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Novo Usuário</title>
        <meta name="description" content="Criar novo usuário" />
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
          <h1 className="text-2xl font-bold text-gray-900">Novo Usuário</h1>
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
            <UserForm onSubmit={handleSubmit} isSubmitting={isCreatingUser} />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}