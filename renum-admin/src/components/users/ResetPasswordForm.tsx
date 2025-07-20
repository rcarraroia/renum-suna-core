import React from 'react';
import { useForm } from 'react-hook-form';
import Button from '../ui/Button';
import Input from '../ui/Input';

interface ResetPasswordFormProps {
  onSubmit: (data: { password: string }) => void;
  isSubmitting: boolean;
}

const ResetPasswordForm: React.FC<ResetPasswordFormProps> = ({
  onSubmit,
  isSubmitting,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<{ password: string; confirmPassword: string }>();

  const password = watch('password', '');

  const handleFormSubmit = (data: { password: string; confirmPassword: string }) => {
    onSubmit({ password: data.password });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="space-y-4">
        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nova Senha *
          </label>
          <Input
            id="password"
            type="password"
            {...register('password', {
              required: 'Nova senha é obrigatória',
              minLength: {
                value: 8,
                message: 'A senha deve ter pelo menos 8 caracteres',
              },
            })}
            error={errors.password?.message}
          />
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Confirmar Senha *
          </label>
          <Input
            id="confirmPassword"
            type="password"
            {...register('confirmPassword', {
              required: 'Confirmação de senha é obrigatória',
              validate: (value) =>
                value === password || 'As senhas não coincidem',
            })}
            error={errors.confirmPassword?.message}
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          Redefinir Senha
        </Button>
      </div>
    </form>
  );
};

export default ResetPasswordForm;