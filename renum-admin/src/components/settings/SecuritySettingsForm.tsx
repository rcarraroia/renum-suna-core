import React from 'react';
import { useForm } from 'react-hook-form';
import { SecuritySetting } from '../../types/settings';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface SecuritySettingsFormProps {
  defaultValues: SecuritySetting;
  onSubmit: (data: SecuritySetting) => void;
  isSubmitting: boolean;
}

const SecuritySettingsForm: React.FC<SecuritySettingsFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SecuritySetting>({
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Política de Senha</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              htmlFor="password_policy.min_length"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Comprimento Mínimo
            </label>
            <Input
              id="password_policy.min_length"
              type="number"
              min="6"
              max="32"
              {...register('password_policy.min_length', {
                required: 'Campo obrigatório',
                valueAsNumber: true,
                min: {
                  value: 6,
                  message: 'Mínimo de 6 caracteres',
                },
                max: {
                  value: 32,
                  message: 'Máximo de 32 caracteres',
                },
              })}
              error={errors.password_policy?.min_length?.message}
            />
          </div>

          <div>
            <label
              htmlFor="password_policy.max_age_days"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Validade Máxima (dias)
            </label>
            <Input
              id="password_policy.max_age_days"
              type="number"
              min="0"
              max="365"
              {...register('password_policy.max_age_days', {
                required: 'Campo obrigatório',
                valueAsNumber: true,
                min: {
                  value: 0,
                  message: 'Valor mínimo é 0 (sem expiração)',
                },
                max: {
                  value: 365,
                  message: 'Valor máximo é 365 dias',
                },
              })}
              error={errors.password_policy?.max_age_days?.message}
            />
            <p className="mt-1 text-xs text-gray-500">
              Use 0 para senhas que não expiram
            </p>
          </div>

          <div className="flex items-center">
            <input
              id="password_policy.require_uppercase"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('password_policy.require_uppercase')}
            />
            <label
              htmlFor="password_policy.require_uppercase"
              className="ml-2 block text-sm text-gray-900"
            >
              Exigir letra maiúscula
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="password_policy.require_lowercase"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('password_policy.require_lowercase')}
            />
            <label
              htmlFor="password_policy.require_lowercase"
              className="ml-2 block text-sm text-gray-900"
            >
              Exigir letra minúscula
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="password_policy.require_numbers"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('password_policy.require_numbers')}
            />
            <label
              htmlFor="password_policy.require_numbers"
              className="ml-2 block text-sm text-gray-900"
            >
              Exigir números
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="password_policy.require_special_chars"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('password_policy.require_special_chars')}
            />
            <label
              htmlFor="password_policy.require_special_chars"
              className="ml-2 block text-sm text-gray-900"
            >
              Exigir caracteres especiais
            </label>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Configurações de Sessão</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label
              htmlFor="session_timeout_minutes"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tempo Limite de Sessão (minutos)
            </label>
            <Input
              id="session_timeout_minutes"
              type="number"
              min="5"
              max="1440"
              {...register('session_timeout_minutes', {
                required: 'Campo obrigatório',
                valueAsNumber: true,
                min: {
                  value: 5,
                  message: 'Mínimo de 5 minutos',
                },
                max: {
                  value: 1440,
                  message: 'Máximo de 1440 minutos (24 horas)',
                },
              })}
              error={errors.session_timeout_minutes?.message}
            />
          </div>

          <div>
            <label
              htmlFor="max_login_attempts"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tentativas Máximas de Login
            </label>
            <Input
              id="max_login_attempts"
              type="number"
              min="1"
              max="10"
              {...register('max_login_attempts', {
                required: 'Campo obrigatório',
                valueAsNumber: true,
                min: {
                  value: 1,
                  message: 'Mínimo de 1 tentativa',
                },
                max: {
                  value: 10,
                  message: 'Máximo de 10 tentativas',
                },
              })}
              error={errors.max_login_attempts?.message}
            />
          </div>

          <div>
            <label
              htmlFor="lockout_duration_minutes"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Duração do Bloqueio (minutos)
            </label>
            <Input
              id="lockout_duration_minutes"
              type="number"
              min="5"
              max="1440"
              {...register('lockout_duration_minutes', {
                required: 'Campo obrigatório',
                valueAsNumber: true,
                min: {
                  value: 5,
                  message: 'Mínimo de 5 minutos',
                },
                max: {
                  value: 1440,
                  message: 'Máximo de 1440 minutos (24 horas)',
                },
              })}
              error={errors.lockout_duration_minutes?.message}
            />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Autenticação de Dois Fatores</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex items-center">
            <input
              id="two_factor_auth.enabled"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('two_factor_auth.enabled')}
            />
            <label
              htmlFor="two_factor_auth.enabled"
              className="ml-2 block text-sm text-gray-900"
            >
              Habilitar 2FA
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="two_factor_auth.required_for_admins"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('two_factor_auth.required_for_admins')}
            />
            <label
              htmlFor="two_factor_auth.required_for_admins"
              className="ml-2 block text-sm text-gray-900"
            >
              Obrigatório para administradores
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="two_factor_auth.required_for_users"
              type="checkbox"
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              {...register('two_factor_auth.required_for_users')}
            />
            <label
              htmlFor="two_factor_auth.required_for_users"
              className="ml-2 block text-sm text-gray-900"
            >
              Obrigatório para usuários
            </label>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          Salvar Configurações
        </Button>
      </div>
    </form>
  );
};

export default SecuritySettingsForm;