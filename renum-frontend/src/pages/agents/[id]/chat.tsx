import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, Bot, Info } from 'lucide-react';
import Layout from '../../../components/Layout';
import ChatInterface from '../../../components/ChatInterface';
import Button from '../../../components/ui/Button';
import Alert from '../../../components/ui/Alert';
import { useChat } from '../../../hooks/useChat';
import { agentApi } from '../../../lib/api-client';
import { Agent } from '../../../types';

export default function AgentChat() {
  const router = useRouter();
  const { id } = router.query;
  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoadingAgent, setIsLoadingAgent] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Inicializar hook de chat com o ID do agente
  const { messages, isLoading, error: chatError, sendMessage, retry } = useChat({
    agentId: id as string,
  });

  // Carregar detalhes do agente
  useEffect(() => {
    if (!id) return;

    const fetchAgent = async () => {
      setIsLoadingAgent(true);
      setError(null);

      try {
        // Tentar buscar agente da API real
        try {
          const response = await agentApi.getAgent(id as string);
          setAgent(response.agent);
          return;
        } catch (apiError: any) {
          console.warn('Falha ao buscar agente via API, usando simulação:', apiError);
        }
        
        // Simulação para desenvolvimento
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Simular resposta da API
        setAgent({
          id: id as string,
          name: 'Agente Demo',
          description: 'Este é um agente de demonstração para fins de desenvolvimento.',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          configuration: {
            model: 'gpt-4',
            system_prompt: 'Você é um assistente útil e amigável.',
            tools: [
              { name: 'tavily_search', description: 'Pesquisa na web usando a API Tavily' }
            ]
          },
          knowledge_base_ids: ['1', '2']
        });
      } catch (err: any) {
        setError(err.message || 'Erro ao carregar detalhes do agente');
        console.error('Erro ao carregar detalhes do agente:', err);
      } finally {
        setIsLoadingAgent(false);
      }
    };

    fetchAgent();
  }, [id]);

  // Exibir mensagem de erro se houver
  const displayError = error || chatError;

  return (
    <Layout title={agent ? `Chat com ${agent.name}` : 'Carregando...'}>
      <div className="flex flex-col h-screen">
        {/* Cabeçalho */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center">
          <button
            type="button"
            onClick={() => router.push(`/agents/${id}`)}
            className="mr-4 text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          
          {isLoadingAgent ? (
            <div className="h-6 w-48 bg-gray-200 animate-pulse rounded"></div>
          ) : agent ? (
            <div className="flex-1">
              <div className="flex items-center">
                <Bot className="h-5 w-5 text-indigo-600 mr-2" />
                <h1 className="text-lg font-medium text-gray-900">{agent.name}</h1>
                <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
                  agent.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}>
                  {agent.status === 'active' ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <p className="text-sm text-gray-500 mt-1">{agent.description}</p>
            </div>
          ) : null}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/agents/${id}`)}
            className="ml-4"
          >
            <Info className="h-4 w-4 mr-1" />
            Detalhes
          </Button>
        </div>
        
        {/* Área de conteúdo */}
        <div className="flex-1 overflow-hidden">
          {displayError && (
            <Alert variant="error" className="m-4">
              {displayError}
            </Alert>
          )}
          
          {!isLoadingAgent && agent ? (
            <ChatInterface
              messages={messages}
              isLoading={isLoading}
              onSendMessage={sendMessage}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Bot className="h-12 w-12 text-indigo-300 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-500">Carregando agente...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}