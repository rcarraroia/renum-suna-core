import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { UsageLimitFormData } from '../../types/billing';
import { Client } from '../../types/client';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { useClients } from '../../hooks/useClients';

interface UsageLimitFormProps {
  defaultValues?: Partial<UsageLimitFormData>;
  onSubmit: (data: UsageLimitFormData) => void;
  isSubmitting: boolean;
  clientId?: string;
}

const UsageLimitForm: React.FC<UsageLimitFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  clientId,
}) => {
  const [clients, setClients] = useState<Client[]>([]);
  const { clients: clientsList, isLoadingClients } = useClients();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<UsageLimitFormData>({
    defaultValues: defaultValues || {
      client_id: clientId || '',
      resource_type: 'tokens',
      limit: 1000000,
      alert_threshold: 80,
      is_hard_limit: false,
    },
  });

  const resourceType = watch('resource_type');

  useEffect(() => {
    if (clientsList) {
      setClients(clientsList);
    }
  }, [clientsList]);

  const getResourceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'tokens': 'Tokens',
      'api_calls': 'Chamadas de API',
      'storage': 'Armazenamento (GB)',
      'users': 'Usuários',
      'agents': 'Agentes',
      'knowledge_bases': 'Bases de Conhecimento',
    };
    return labels[type] || type;
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {!clientId && (
          <div className="md:col-span-2">
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
              disabled={isLoadingClients || !!clientId}
            />
          </div>
        )}

        <div>
          <label
            htmlFor="resource_type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tipo de Recurso *
          </label>
          <Select
            id="resource_type"
            {...register('resource_type', { required: 'Tipo de recurso é obrigatório' })}
            options={[
              { value: 'tokens', label: 'Tokens' },
              { value: 'api_calls', label: 'Chamadas de API' },
              { value: 'storage', label: 'Armazenamento (GB)' },
              { value: 'users', label: 'Usuários' },
              { value: 'agents', label: 'Agentes' },
              { value: 'knowledge_bases', label: 'Bases de Conhecimento' },
            ]}
            error={errors.resource_type?.message}
          />
        </div>

        <div>
          <label
            htmlFor="limit"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Limite *
          </label>
          <Input
            id="limit"
            type="number"
            min="1"
            {...register('limit', {
              required: 'Limite é obrigatório',
              valueAsNumber: true,
              min: {
                value: 1,
                message: 'Deve ser pelo menos 1',
              },
            })}
            error={errors.limit?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            {resourceType === 'tokens' && 'Número máximo de tokens que podem ser consumidos'}
            {resourceType === 'api_calls' && 'Número máximo de chamadas de API permitidas'}
            {resourceType === 'storage' && 'Limite de armazenamento em GB'}
            {resourceType === 'users' && 'Número máximo de usuários permitidos'}
            {resourceType === 'agents' && 'Número máximo de agentes permitidos'}
            {resourceType === 'knowledge_bases' && 'Número máximo de bases de conhecimento permitidas'}
          </p>
        </div>

        <div>
          <label
            htmlFor="alert_threshold"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Limite de Alerta (%) *
          </label>
          <Input
            id="alert_threshold"
            type="number"
            min="1"
            max="100"
            {...register('alert_threshold', {
              required: 'Limite de alerta é obrigatório',
              valueAsNumber: true,
              min: {
                value: 1,
                message: 'Deve ser pelo menos 1%',
              },
              max: {
                value: 100,
                message: 'Não pode exceder 100%',
              },
            })}
            error={errors.alert_threshold?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            Porcentagem do limite em que alertas serão enviados
          </p>
        </div>

        <div className="flex items-center">
          <input
            id="is_hard_limit"
            type="checkbox"
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            {...register('is_hard_limit')}
          />
          <label
            htmlFor="is_hard_limit"
            className="ml-2 block text-sm text-gray-900"
          >
            Limite Rígido
          </label>
          <p className="ml-2 text-xs text-gray-500">
            Se ativado, o acesso será bloqueado quando o limite for atingido
          </p>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {defaultValues ? 'Atualizar Limite' : 'Criar Limite'}
        </Button>
      </div>
    </form>
  );
};

export default UsageLimitForm;