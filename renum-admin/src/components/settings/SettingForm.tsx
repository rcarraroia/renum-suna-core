import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { SystemSettingFormData } from '../../types/settings';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface SettingFormProps {
  defaultValues?: Partial<SystemSettingFormData>;
  onSubmit: (data: SystemSettingFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const SettingForm: React.FC<SettingFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const [valueType, setValueType] = useState<string>(
    defaultValues?.value !== undefined
      ? typeof defaultValues.value === 'boolean'
        ? 'boolean'
        : typeof defaultValues.value === 'number'
        ? 'number'
        : Array.isArray(defaultValues.value)
        ? 'array'
        : typeof defaultValues.value === 'object'
        ? 'object'
        : 'string'
      : 'string'
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<SystemSettingFormData & { valueType: string }>({
    defaultValues: {
      ...defaultValues,
      value:
        defaultValues?.value !== undefined
          ? typeof defaultValues.value === 'object' || Array.isArray(defaultValues.value)
            ? JSON.stringify(defaultValues.value, null, 2)
            : String(defaultValues.value)
          : '',
      valueType,
    },
  });

  const watchValueType = watch('valueType');
  const watchIsSensitive = watch('is_sensitive');

  const handleFormSubmit = (data: SystemSettingFormData & { valueType: string }) => {
    const { valueType, ...rest } = data;
    let parsedValue: any = data.value;

    // Converter o valor para o tipo correto
    if (valueType === 'number') {
      parsedValue = Number(data.value);
    } else if (valueType === 'boolean') {
      parsedValue = data.value === 'true';
    } else if (valueType === 'object' || valueType === 'array') {
      try {
        parsedValue = JSON.parse(data.value as string);
      } catch (e) {
        // Se não for um JSON válido, manter como string
        parsedValue = data.value;
      }
    }

    onSubmit({
      ...rest,
      value: parsedValue,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            htmlFor="key"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Chave *
          </label>
          <Input
            id="key"
            {...register('key', { required: 'Chave é obrigatória' })}
            error={errors.key?.message}
            disabled={isEditMode}
          />
        </div>

        <div>
          <label
            htmlFor="valueType"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tipo de Valor *
          </label>
          <Select
            id="valueType"
            {...register('valueType', { required: 'Tipo de valor é obrigatório' })}
            options={[
              { value: 'string', label: 'Texto' },
              { value: 'number', label: 'Número' },
              { value: 'boolean', label: 'Booleano' },
              { value: 'object', label: 'Objeto (JSON)' },
              { value: 'array', label: 'Array (JSON)' },
            ]}
            onChange={(e) => setValueType(e.target.value)}
            error={errors.valueType?.message}
          />
        </div>

        <div className="md:col-span-2">
          <label
            htmlFor="value"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Valor *
          </label>
          {watchValueType === 'boolean' ? (
            <Select
              id="value"
              {...register('value', { required: 'Valor é obrigatório' })}
              options={[
                { value: 'true', label: 'Verdadeiro' },
                { value: 'false', label: 'Falso' },
              ]}
              error={errors.value?.message as string}
            />
          ) : watchValueType === 'object' || watchValueType === 'array' ? (
            <textarea
              id="value"
              className={`block w-full rounded-md border ${
                errors.value ? 'border-red-300' : 'border-gray-300'
              } shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm font-mono`}
              rows={8}
              {...register('value', { required: 'Valor é obrigatório' })}
            />
          ) : (
            <Input
              id="value"
              type={watchIsSensitive ? 'password' : watchValueType === 'number' ? 'number' : 'text'}
              {...register('value', { required: 'Valor é obrigatório' })}
              error={errors.value?.message as string}
            />
          )}
          {errors.value && (
            <p className="mt-1 text-sm text-red-600">{errors.value.message as string}</p>
          )}
        </div>

        <div className="md:col-span-2">
          <label
            htmlFor="description"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Descrição *
          </label>
          <textarea
            id="description"
            className={`block w-full rounded-md border ${
              errors.description ? 'border-red-300' : 'border-gray-300'
            } shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm`}
            rows={3}
            {...register('description', { required: 'Descrição é obrigatória' })}
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
          )}
        </div>

        <div className="flex items-center">
          <input
            id="is_sensitive"
            type="checkbox"
            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            {...register('is_sensitive')}
          />
          <label
            htmlFor="is_sensitive"
            className="ml-2 block text-sm text-gray-900"
          >
            Valor Sensível
          </label>
          <p className="ml-2 text-xs text-gray-500">
            Se marcado, o valor será mascarado na interface
          </p>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Configuração' : 'Criar Configuração'}
        </Button>
      </div>
    </form>
  );
};

export default SettingForm;