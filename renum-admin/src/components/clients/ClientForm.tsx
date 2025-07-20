import React from 'react';
import { useForm } from 'react-hook-form';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { Client } from '../../types/client';

interface ClientFormProps {
  onSubmit: (data: any) => void;
  isLoading: boolean;
  defaultValues?: Partial<Client>;
}

const ClientForm: React.FC<ClientFormProps> = ({
  onSubmit,
  isLoading,
  defaultValues = {},
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Nome
          </label>
          <Input
            id="name"
            {...register('name', { required: 'Nome é obrigatório' })}
            error={errors.name?.message as string}
          />
        </div>

        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <Input
            id="email"
            type="email"
            {...register('email', {
              required: 'Email é obrigatório',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Email inválido',
              },
            })}
            error={errors.email?.message as string}
          />
        </div>

        <div>
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
            Telefone
          </label>
          <Input
            id="phone"
            {...register('phone')}
            error={errors.phone?.message as string}
          />
        </div>

        <div>
          <label htmlFor="plan" className="block text-sm font-medium text-gray-700 mb-1">
            Plano
          </label>
          <Select
            id="plan"
            options={[
              { value: 'basic', label: 'Básico' },
              { value: 'standard', label: 'Padrão' },
              { value: 'premium', label: 'Premium' },
              { value: 'enterprise', label: 'Enterprise' },
            ]}
            {...register('plan', { required: 'Plano é obrigatório' })}
            error={errors.plan?.message as string}
          />
        </div>

        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <Select
            id="status"
            options={[
              { value: 'active', label: 'Ativo' },
              { value: 'inactive', label: 'Inativo' },
              { value: 'pending', label: 'Pendente' },
            ]}
            {...register('status', { required: 'Status é obrigatório' })}
            error={errors.status?.message as string}
          />
        </div>

        <div>
          <label htmlFor="usage_limit" className="block text-sm font-medium text-gray-700 mb-1">
            Limite de Uso
          </label>
          <Input
            id="usage_limit"
            type="number"
            {...register('usage_limit', {
              valueAsNumber: true,
              validate: (value) => !value || value > 0 || 'Limite deve ser maior que zero',
            })}
            error={errors.usage_limit?.message as string}
          />
        </div>
      </div>

      <div>
        <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-1">
          Endereço
        </label>
        <Input
          id="address"
          {...register('address')}
          error={errors.address?.message as string}
        />
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="button" variant="outline" onClick={() => window.history.back()}>
          Cancelar
        </Button>
        <Button type="submit" isLoading={isLoading}>
          {defaultValues.id ? 'Atualizar Cliente' : 'Criar Cliente'}
        </Button>
      </div>
    </form>
  );
};

export default ClientForm;