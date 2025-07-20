import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { AgentFormData, AgentModel } from '../../types/agent';
import { Client } from '../../types/client';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { useClients } from '../../hooks/useClients';
import { useAgents } from '../../hooks/useAgents';

interface AgentFormProps {
  defaultValues?: Partial<AgentFormData>;
  onSubmit: (data: AgentFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const AgentForm: React.FC<AgentFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const [clients, setClients] = useState<Client[]>([]);
  const [models, setModels] = useState<AgentModel[]>([]);
  
  const { clients: clientsList, isLoadingClients } = useClients();
  const { availableModels, isLoadingModels } = useAgents();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<AgentFormData>({
    defaultValues: defaultValues || {
      client_id: '',
      name: '',
      description: '',
      system_prompt: '',
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      max_tokens: 1000,
      is_active: true,
      is_public: false,
    },
  });

  const temperature = watch('temperature');

  useEffect(() => {
    if (clientsList) {
      setClients(clientsList);
    }
  }, [clientsList]);

  useEffect(() => {
    if (availableModels) {
      setModels(availableModels);
    }
  }, [availableModels]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            htmlFor="client_id"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Cliente *
          </label>
          <Select
            id="client_id"
            {...register('client_id', { required: 'Cliente é obrigatório' })}
            options={clients.map((client) => ({
              value: client.id,
              label: client.name,
            }))}
            error={errors.client_id?.message}
            disabled={isLoadingClients}
          />
        </div>

        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nome *
          </label>
          <Input
            id="name"
            {...register('name', { required: 'Nome é obrigatório' })}
            error={errors.name?.message}
          />
        </div>

        <div className="md:col-span-2">
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Descrição
          </label>
          <textarea
            id="description"
            rows={3}
            className="block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            {...register('description')}
          />
        </div>

        <div className="md:col-span-2">
          <label
            htmlFor="system_prompt"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Prompt do Sistema
          </label>
          <textarea
            id="system_prompt"
            rows={5}
            className="block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            {...register('system_prompt')}
          />
        </div>

        <div>
          <label
            htmlFor="model"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Modelo *
          </label>
          <Select
            id="model"
            {...register('model', { required: 'Modelo é obrigatório' })}
            options={
              models.length > 0
                ? models.map((model) => ({
                    value: model.id,
                    label: `${model.name} (${model.provider})`,
                  }))
                : [
                    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo (OpenAI)' },
                    { value: 'gpt-4', label: 'GPT-4 (OpenAI)' },
                    { value: 'claude-2', label: 'Claude 2 (Anthropic)' },
                  ]
            }
            error={errors.model?.message}
            disabled={isLoadingModels}
          />
        </div>

        <div>
          <label
            htmlFor="max_tokens"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Máximo de Tokens *
          </label>
          <Input
            id="max_tokens"
            type="number"
            min="100"
            max="32000"
            {...register('max_tokens', {
              required: 'Máximo de tokens é obrigatório',
              valueAsNumber: true,
              min: {
                value: 100,
                message: 'Deve ser pelo menos 100',
              },
              max: {
                value: 32000,
                message: 'Não pode exceder 32000',
              },
            })}
            error={errors.max_tokens?.message}
          />
        </div>

        <div>
          <label
            htmlFor="temperature"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Temperatura: {temperature}
          </label>
          <input
            id="temperature"
            type="range"
            min="0"
            max="1"
            step="0.1"
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            {...register('temperature', {
              required: 'Temperatura é obrigatória',
              valueAsNumber: true,
            })}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Mais determinístico</span>
            <span>Mais criativo</span>
          </div>
        </div>

        <div>
          <label
            htmlFor="is_active"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Status
          </label>
          <Select
            id="is_active"
            {...register('is_active')}
            options={[
              { value: 'true', label: 'Ativo' },
              { value: 'false', label: 'Inativo' },
            ]}
          />
        </div>

        <div>
          <label
            htmlFor="is_public"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Visibilidade
          </label>
          <Select
            id="is_public"
            {...register('is_public')}
            options={[
              { value: 'false', label: 'Privado' },
              { value: 'true', label: 'Público' },
            ]}
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {defaultValues ? 'Atualizar Agente' : 'Criar Agente'}
        </Button>
      </div>
    </form>
  );
};

export default AgentForm;