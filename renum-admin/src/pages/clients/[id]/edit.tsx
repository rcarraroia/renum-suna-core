import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useClients } from '../../../hooks/useClients';
import ClientForm from '../../../components/clients/ClientForm';
import Alert from '../../../components/ui/Alert';
import { apiClient } from '../../../lib/api-client';
import { Client } from '../../../types/client';

export default function EditClientPage() {
  const router = useRouter();
  const { id } = router.query;
  const { updateClient } = useClients();
  const [error, setError] = React.useState<string | null>(null);

  // Função para buscar detalhes do cliente
  const fetchClientDetails = async () => {
    if (!id) return null;

    // Simulação de API - remover quando integrar com API real
    // Na implementação real:
    // const { data } = await apiClient.get(`/api/v2/admin/clients/${id}`);
    // return data;

    await new Promise(resolve => setTimeout(resolve, 500)); // Simular delay

    // Dados mockados para desenvolvimento
    const mockClient: Client = {
      id: id as string,
      name: 'Empresa ABC',
      email: 'contato@empresaabc.com',
      phone: '(11) 1234-5678',
      address: 'Av. Paulista, 1000, São Paulo, SP',
      logo_url: 'https://via.placeholder.com/150',
      plan: 'enterprise',
      status: 'active',
      usage_limit: 10000,
      current_usage: 7500,
      created_at: new Date('2023-01-15'),
      updated_at: new Date('2023-06-20'),
    };

    return mockClient;
  };

  // Query para buscar detalhes do cliente
  const { data: client, isLoading, error: fetchError } = useQuery({
    queryKey: ['client', id],
    queryFn: fetchClientDetails,
    enabled: !!id,
  });

  const handleSubmit = async (data: any) => {
    if (!id) return;

    try {
      setError(null);
      await updateClient.mutateAsync({ id, ...data });
      router.push(`/clients/${id}`);
    } catch (err: any) {
      setError(err.message || 'Ocorreu um erro ao atualizar o cliente');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (fetchError || !client) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 rounded-md p-4">
        <p>Erro ao carregar detalhes do cliente. Por favor, tente novamente.</p>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>Editar Cliente | Renum Admin</title>
      </Head>

      <div className="mb-6">
        <div className="flex items-center mb-4">
          <Link href={`/clients/${id}`}>
            <a className="text-gray-500 hover:text-gray-700 mr-2">
              <ArrowLeft className="h-5 w-5" />
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Editar Cliente</h1>
        </div>
        <p className="text-gray-600">Atualize os dados do cliente</p>
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
            isLoading={updateClient.isPending}
            defaultValues={client}
          />
        </div>
      </div>
    </>
  );
}