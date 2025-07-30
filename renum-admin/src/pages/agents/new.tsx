import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ArrowLeft } from 'lucide-react';
import { useAgents } from '../../hooks/useAgents';
import { AgentFormData } from '../../types/agent';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import AgentForm from '../../components/agents/AgentForm';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/Card';
import ProtectedRoute from '../../components/layout/ProtectedRoute';

export default function NewAgent() {
  const router = useRouter();
  const { createAgent, isCreatingAgent, error, setError } = useAgents();

  const handleSubmit = async (data: AgentFormData) => {
    try {
      // Converter strings para tipos apropriados
      const formattedData = {
        ...data,
        is_active: Boolean(data.is_active),
        is_public: Boolean(data.is_public),
        temperature: parseFloat(data.temperature.toString()),
        max_tokens: parseInt(data.max_tokens.toString(), 10),
      };

      await createAgent(formattedData);
      router.push('/agents');
    } catch (error) {
      // Erro já tratado no hook
    }
  };

  return (
    <ProtectedRoute>
      <Head>
        <title>Renum Admin - Novo Agente</title>
        <meta name="description" content="Criar novo agente" />
      </Head>

      <div>
        <div className="flex items-center mb-6">
          <Link href="/agents">
            <a className="mr-4">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" /> Voltar
              </Button>
            </a>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Novo Agente</h1>
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
            <AgentForm onSubmit={handleSubmit} isSubmitting={isCreatingAgent} />
          </CardContent>
        </Card>
      </div>
    </ProtectedRoute>
  );
}