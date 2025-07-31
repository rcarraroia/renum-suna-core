import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useAgents } from '../../../hooks/useAgents';
import { Agent, AgentFormData } from '../../../types/agent';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import AgentForm from '../../../components/agents/AgentForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui/Card';
import ProtectedRoute from '../../../components/layout/ProtectedRoute';

export default function EditAgent() {
  const router = useRouter();
  const { id } = router.query;
  const { getAgent, updateAgent, isUpdatingAgent, error, setError } = useAgents();
  const [agent, setAgent] = useState<Agent | null>(null);

  // Buscar detalhes do agente
  const {
    data: agentData,
    isLoading: isLoadingAgent,
    error: agentError,
  } = useQuery<Agent>({
    queryKey: ['agent', id],
    queryFn: () => getAgent(id as string),
    enabled: !!id,
  });

  useEffect(() => {
    if (agentData) {
      setAgent(agentData);
    }
  }, [agentData]);

  useEffect(() => {
    if (agentError) {
      setError(agentError.message);
    }
  }, [agentError, setError]);

  const handleSubmit = async (data: AgentFormData) => {
    if (!id) return;

    try {
      // Converter strings para tipos apropriados
      const formattedData = {
        ...data,
        is_active: Boolean(data.is_active),
        is_public: Boolean(data.is_public),
        temperature: parseFloat(data.temperature.toString()),
        max_tokens: parseInt(data.max_tokens.toString(), 10),
      };

      await updateAgent({ id: id as string, data: formattedData });
      router.push(`/agents/${id}`);
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  if (isLoadingAgent) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!agent && !isLoadingAgent) {
    return (
      <Alert variant="error" title="Erro">
        Agente não encontrado
      </Alert>
    );
  }

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Editar Agente</title>
        <meta name="description" content="Editar agente" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href={`/agents/${id}`}>
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Editar Agente: {agent?.name}
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
            <CardTitle>Informações do Agente</CardTitle>
          </CardHeader>
          <CardContent>
            {agent && (
              <AgentForm
                defaultValues={{
                  client_id: agent.client_id,
                  name: agent.name,
                  description: agent.description || '',
                  system_prompt: agent.system_prompt || '',
                  model: agent.model,
                  temperature: agent.temperature,
                  max_tokens: agent.max_tokens,
                  is_active: agent.is_active,
                  is_public: agent.is_public,
                }}
                onSubmit={handleSubmit}
                isSubmitting={isUpdatingAgent}
                isEditMode={true}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}