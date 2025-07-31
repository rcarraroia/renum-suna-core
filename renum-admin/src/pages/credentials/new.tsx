import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useCredentials } from '../../hooks/useCredentials';
import { CredentialFormData } from '../../types/credential';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import CredentialForm from '../../components/credentials/CredentialForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function NewCredential() {
  const router = useRouter();
  const { createCredential, isCreatingCredential, error, setError } = useCredentials();

  const handleSubmit = async (data: CredentialFormData) => {
    try {
      // Converter string para boolean (do select)
      const formattedData = {
        ...data,
        is_active: Boolean(data.is_active),
      };

      await createCredential(formattedData);
      router.push('/credentials');
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Nova Credencial</title>
        <meta name="description" content="Criar nova credencial" />
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
          <h1 className="text-2xl font-bold text-gray-900">Nova Credencial</h1>
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
            <CardTitle>Informações da Credencial</CardTitle>
          </CardHeader>
          <CardContent>
            <CredentialForm onSubmit={handleSubmit} isSubmitting={isCreatingCredential} />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}