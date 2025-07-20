import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import SecuritySettingsForm from '../../components/settings/SecuritySettingsForm';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function SecuritySettings() {
  const {
    securitySettings,
    isLoadingSecuritySettings,
    updateSecuritySettings,
    isUpdatingSecuritySettings,
    error,
    setError,
  } = useSettings();

  const handleSubmit = async (data: any) => {
    try {
      await updateSecuritySettings(data);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  if (isLoadingSecuritySettings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Configurações de Segurança</title>
        <meta name="description" content="Configurações de segurança do sistema" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/settings">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Configurações de Segurança</h1>
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
            <CardTitle>Segurança do Sistema</CardTitle>
          </CardHeader>
          <CardContent>
            {securitySettings && (
              <SecuritySettingsForm
                defaultValues={securitySettings}
                onSubmit={handleSubmit}
                isSubmitting={isUpdatingSecuritySettings}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}