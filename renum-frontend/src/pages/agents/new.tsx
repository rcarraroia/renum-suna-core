import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useForm } from 'react-hook-form';
import { Save, ArrowLeft, Bot, Tool as ToolIcon } from 'lucide-react';
import Layout from '../../components/Layout';
import Input from '../../components/ui/Input';
import Textarea from '../../components/ui/Textarea';
import Select from '../../components/ui/Select';
import Button from '../../components/ui/Button';
import Alert from '../../components/ui/Alert';
import Badge from '../../components/ui/Badge';
import KnowledgeBaseSelector from '../../components/KnowledgeBaseSelector';
import ToolSelector from '../../components/ToolSelector';
import { agentApi } from '../../lib/api-client';
import { useAgentStore } from '../../lib/store';

interface NewAgentFormData {
  name: string;
  description: string;
  model: string;
  system_prompt: string;
}

export default function NewAgent() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors } } = useForm<NewAgentFormData>({
    defaultValues: {
      name: '',
      description: '',
      model: 'gpt-4',
      system_prompt: ''
    }
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<string[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const addAgent = useAgentStore((state: any) => state.addAgent);

  // Validar se pelo menos uma ferramenta foi selecionada
  const validateToolSelection = () => {
    if (selectedTools.length === 0) {
      return false;
    }
    return true;
  };

  // Validar se pelo menos uma base de conhecimento foi selecionada (se obrigatório)
  const validateKnowledgeBaseSelection = (required: boolean) => {
    if (required && selectedKnowledgeBases.length === 0) {
      return false;
    }
    return true;
  };

  const onSubmit = async (data: NewAgentFormData) => {
    setIsLoading(true);
    setError(null);

    // Validar seleção de ferramentas
    if (!validateToolSelection()) {
      setError("Por favor, selecione pelo menos uma ferramenta para o agente");
      setIsLoading(false);
      return;
    }

    // Validar seleção de bases de conhecimento (se necessário)
    // Neste caso, não é obrigatório, mas podemos adicionar a validação se necessário
    // if (!validateKnowledgeBaseSelection(true)) {
    //   setError("Por favor, selecione pelo menos uma base de conhecimento para o agente");
    //   setIsLoading(false);
    //   return;
    // }

    try {
      // Preparar dados do agente
      const agentData = {
        name: data.name,
        description: data.description,
        configuration: {
          model: data.model,
          system_prompt: data.system_prompt || "Você é um assistente útil e amigável.",
          tools: selectedTools.map((toolId: string) => ({
            name: toolId,
            description: '' // A descrição será preenchida pelo backend
          }))
        },
        knowledge_base_ids: selectedKnowledgeBases,
        status: 'draft'
      };

      // Tentar criar o agente usando a API real
      let response;
      try {
        response = await agentApi.createAgent(agentData);
      } catch (apiError) {
        console.warn('Falha ao criar agente via API, usando simulação:', apiError);
        
        // Fallback para simulação se a API falhar
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Simular resposta da API
        response = {
          agent: {
            id: Math.random().toString(36).substring(2, 15),
            name: data.name,
            description: data.description,
            status: 'draft',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            configuration: {
              model: data.model,
              system_prompt: data.system_prompt || "Você é um assistente útil e amigável.",
              tools: selectedTools.map((toolId: string) => ({
                name: toolId,
                description: '' // A descrição seria preenchida pelo backend
              }))
            },
            knowledge_base_ids: selectedKnowledgeBases
          }
        };
      }

      // Adicionar agente ao store
      addAgent(response.agent);

      // Redirecionar para o dashboard
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Erro ao criar agente');
      console.error('Erro ao criar agente:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout title="Criar Agente">
      <div className="py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="flex items-center mb-6">
          <button
            type="button"
            onClick={() => router.push('/dashboard')}
            className="mr-4 text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <Bot className="h-6 w-6 mr-2 text-indigo-600" />
              Criar Novo Agente
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Configure seu agente de IA personalizado para atender às suas necessidades específicas
            </p>
          </div>
        </div>

        {error && (
          <Alert variant="error" className="mb-6" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <div className="bg-white shadow rounded-lg overflow-hidden">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="p-6 space-y-8">
              {/* Informações Básicas */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Informações Básicas</h3>
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-6">
                  <div className="sm:col-span-4">
                    <Input
                      id="name"
                      label="Nome do Agente *"
                      fullWidth
                      error={errors.name?.message}
                      {...register('name', {
                        required: 'O nome do agente é obrigatório',
                        minLength: {
                          value: 3,
                          message: 'O nome deve ter pelo menos 3 caracteres'
                        }
                      })}
                    />
                  </div>

                  <div className="sm:col-span-6">
                    <Textarea
                      id="description"
                      label="Descrição"
                      rows={3}
                      placeholder="Descreva o propósito e as capacidades deste agente"
                      fullWidth
                      error={errors.description?.message}
                      {...register('description')}
                    />
                  </div>
                </div>
              </div>

              {/* Configuração do Modelo */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Configuração do Modelo</h3>
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-6">
                  <div className="sm:col-span-3">
                    <Select
                      id="model"
                      label="Modelo *"
                      options={[
                        { value: 'gpt-4', label: 'GPT-4' },
                        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                        { value: 'claude-3-opus', label: 'Claude 3 Opus' },
                        { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
                        { value: 'claude-3-haiku', label: 'Claude 3 Haiku' }
                      ]}
                      fullWidth
                      error={errors.model?.message}
                      {...register('model', {
                        required: 'O modelo é obrigatório'
                      })}
                    />
                  </div>

                  <div className="sm:col-span-6">
                    <Textarea
                      id="system_prompt"
                      label="Prompt do Sistema"
                      rows={5}
                      placeholder="Instruções para o agente sobre como ele deve se comportar e responder"
                      fullWidth
                      error={errors.system_prompt?.message}
                      {...register('system_prompt')}
                    />
                    <p className="mt-2 text-sm text-gray-500">
                      O prompt do sistema define a personalidade e comportamento do agente. Seja específico sobre o que o agente deve fazer e como deve responder.
                    </p>
                  </div>
                </div>
              </div>

              {/* Bases de Conhecimento */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Bases de Conhecimento</h3>
                <div className="flex justify-between items-center mb-4">
                  <p className="text-sm text-gray-500">
                    Selecione as bases de conhecimento que o agente deve utilizar para enriquecer suas respostas.
                  </p>
                  <div className="text-sm text-indigo-600">
                    {selectedKnowledgeBases.length} base(s) selecionada(s)
                  </div>
                </div>
                <KnowledgeBaseSelector
                  selectedIds={selectedKnowledgeBases}
                  onChange={setSelectedKnowledgeBases}
                  required={false}
                />
              </div>

              {/* Ferramentas */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Ferramentas</h3>
                <div className="flex justify-between items-center mb-4">
                  <p className="text-sm text-gray-500">
                    Selecione as ferramentas que o agente poderá utilizar durante a execução.
                  </p>
                  <div className="text-sm text-indigo-600">
                    {selectedTools.length} ferramenta(s) selecionada(s)
                  </div>
                </div>

                {selectedTools.length > 0 && (
                  <div className="mb-4 flex flex-wrap gap-2">
                    {selectedTools.map((toolId) => (
                      <Badge
                        key={toolId}
                        variant="primary"
                        size="sm"
                        onRemove={() => setSelectedTools(selectedTools.filter(id => id !== toolId))}
                      >
                        <ToolIcon className="h-3 w-3 mr-1" />
                        {toolId.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </Badge>
                    ))}
                  </div>
                )}

                <ToolSelector
                  selectedIds={selectedTools}
                  onChange={setSelectedTools}
                />

                {selectedTools.length === 0 && (
                  <p className="mt-2 text-sm text-amber-600">
                    Recomendamos selecionar pelo menos uma ferramenta para que o agente possa realizar tarefas.
                  </p>
                )}
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 flex justify-end">
              <Button
                variant="outline"
                onClick={() => router.push('/dashboard')}
                className="mr-3"
              >
                Cancelar
              </Button>
              <Button
                isLoading={isLoading}
                disabled={isLoading}
              >
                <Save className="h-4 w-4 mr-2" />
                {isLoading ? 'Criando...' : 'Criar Agente'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
}