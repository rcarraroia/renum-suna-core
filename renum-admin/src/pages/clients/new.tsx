import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useClients } from '../../hooks/useClients';
import ClientForm from '../../components/clients/ClientForm';
import Alert from '../../components/ui/Alert';

export default function NewClientPage() {
  const router = useRouter();
  const { createClient } = useClients();
  const [error, setError] = React.useState<string | null>(null);

  const handleSubmit = async (data: any) => {
    try {
      setError(null);
      await createClient.mutateAsync(data);
      router.push('/clients');
    } catch (err: any) {
      setError(err.message || 'Ocorreu um erro ao criar o cliente');
    }
  };

  return (
    <>
      <Head>
        <title>Novo Cliente | Renum Admin</title>
      </Head>

      <div className="mb-6">
        <div className="flex items-center mb-4">
          <Link href="/clients">
            <a className="text-gray-500 hover:text-gray-700 mr-2">
              <ArrowLeft className="h-5 w-5" />
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Novo Cliente</h1>
        </div>
        <p className="text-gray-600">Preencha os dados para criar um novo cliente</p>
      </div>

      {error && (
        <Alert variant="error" title="Erro" onClose={() => setError(null)} className="mb-6">
          {error}
        </Alert>
      )}

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-6">
          <ClientForm
            onSubmit={handleSubmit}
            isLoading={createClient.isPending}
          />
        </div>
      </div>
    </>
  );
}