import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useCredentials } from '../../../hooks/useCredentials';
import { Credential, CredentialFormData } from '../../../types/credential';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import CredentialForm from '../../../components/credentials/CredentialForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function EditCredential() {
  const router = useRouter();
  const { id } = router.query;
  const { getCredential, updateCredential, isUpdatingCredential, error, setError } = useCredentials();
  const [credential, setCredential] = useState<Credential | null>(null);

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

  useEffect(() => {
    if (credentialData) {
      setCredential(credentialData);
    }
  }, [credentialData]);

  useEffect(() => {
    if (credentialError) {
      setError(credentialError.message);
    }
  }, [credentialError, setError]);

  const handleSubmit = async (data: CredentialFormData) => {
    if (!id) return;

    try {
      // Converter string para boolean (do select)
      const formattedData = {
        ...data,
        is_active: data.is_active === 'true' || data.is_active === true,
      };

      // Se o valor estiver vazio, não o envie (para manter o valor atual)
      if (!formattedData.value) {
        delete formattedData.value;
      }

      await updateCredential({ id: id as string, data: formattedData });
      router.push('/credentials');
    } catch (error) {
      // Erro já tratado no hook
    }
  };

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

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Editar Credencial</title>
        <meta name="description" content="Editar credencial" />
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
          <h1 className="text-2xl font-bold text-gray-900">
            Editar Credencial: {credential?.service_name}
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
            <CardTitle>Informações da Credencial</CardTitle>
          </CardHeader>
          <CardContent>
            {credential && (
              <CredentialForm
                defaultValues={{
                  service_name: credential.service_name,
                  credential_type: credential.credential_type,
                  value: '', // Não enviamos o valor atual por segurança
                  is_active: credential.is_active,
                  expires_at: credential.expires_at,
                  metadata: credential.metadata,
                }}
                onSubmit={handleSubmit}
                isSubmitting={isUpdatingCredential}
                isEditMode={true}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}