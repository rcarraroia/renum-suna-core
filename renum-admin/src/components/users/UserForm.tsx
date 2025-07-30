import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { UserFormData } from '../../types/user';
import { Client } from '../../types/client';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { useClients } from '../../hooks/useClients';

interface UserFormProps {
  defaultValues?: Partial<UserFormData>;
  onSubmit: (data: UserFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const UserForm: React.FC<UserFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const [clients, setClients] = useState<Client[]>([]);
  const { clients: clientsList, isLoading: isLoadingClients, error: clientsError } = useClients();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserFormData>({
    defaultValues: defaultValues || {
      client_id: '',
      name: '',
      email: '',
      role: 'user',
      password: '',
      is_active: true,
    },
  });

  useEffect(() => {
    if (clientsList) {
      setClients(clientsList);
    }
  }, [clientsList]);

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

        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Email *
          </label>
          <Input
            id="email"
            type="email"
            {...register('email', {
              required: 'Email é obrigatório',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}$/i,
                message: 'Email inválido',
              },
            })}
            error={errors.email?.message}
          />
        </div>

        <div>
          <label
            htmlFor="role"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Papel *
          </label>
          <Select
            id="role"
            {...register('role', { required: 'Papel é obrigatório' })}
            options={[
              { value: 'user', label: 'Usuário' },
              { value: 'admin', label: 'Administrador' },
              { value: 'manager', label: 'Gerente' },
            ]}
            error={errors.role?.message}
          />
        </div>

        {!isEditMode && (
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Senha *
            </label>
            <Input
              id="password"
              type="password"
              {...register('password', {
                required: 'Senha é obrigatória',
                minLength: {
                  value: 8,
                  message: 'A senha deve ter pelo menos 8 caracteres',
                },
              })}
              error={errors.password?.message}
            />
          </div>
        )}

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
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Usuário' : 'Criar Usuário'}
        </Button>
      </div>
    </form>
  );
};

export default UserForm;