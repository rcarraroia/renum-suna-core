import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { IntegrationSettingFormData } from '../../types/settings';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface IntegrationFormProps {
  defaultValues?: Partial<IntegrationSettingFormData>;
  onSubmit: (data: IntegrationSettingFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const IntegrationForm: React.FC<IntegrationFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const [configFields, setConfigFields] = useState<{ key: string; value: string; type: string }[]>(
    defaultValues?.config
      ? Object.entries(defaultValues.config).map(([key, value]) => ({
          key,
          value: typeof value === 'object' ? JSON.stringify(value) : String(value),
          type: typeof value === 'object' ? 'json' : typeof value === 'boolean' ? 'boolean' : 'string',
        }))
      : [{ key: '', value: '', type: 'string' }]
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<IntegrationSettingFormData>({
    defaultValues: defaultValues || {
      name: '',
      type: 'api',
      config: {},
    },
  });

  const integrationType = watch('type');

  const handleAddConfigField = () => {
    setConfigFields([...configFields, { key: '', value: '', type: 'string' }]);
  };

  const handleRemoveConfigField = (index: number) => {
    setConfigFields(configFields.filter((_, i) => i !== index));
  };

  const handleConfigFieldChange = (index: number, field: 'key' | 'value' | 'type', value: string) => {
    const newConfigFields = [...configFields];
    newConfigFields[index][field] = value;
    setConfigFields(newConfigFields);
  };

  const handleFormSubmit = (data: IntegrationSettingFormData) => {
    // Construir o objeto de configuração a partir dos campos
    const config: Record<string, any> = {};
    configFields.forEach((field) => {
      if (field.key) {
        if (field.type === 'boolean') {
          config[field.key] = field.value === 'true';
        } else if (field.type === 'number') {
          config[field.key] = Number(field.value);
        } else if (field.type === 'json') {
          try {
            config[field.key] = JSON.parse(field.value);
          } catch (e) {
            config[field.key] = field.value;
          }
        } else {
          config[field.key] = field.value;
        }
      }
    });

    onSubmit({
      ...data,
      config,
    });
  };

  const getIntegrationTypeFields = () => {
    switch (integrationType) {
      case 'api':
        return ['base_url', 'api_key', 'timeout_seconds'];
      case 'oauth':
        return ['client_id', 'client_secret', 'redirect_uri', 'auth_url', 'token_url', 'scope'];
      case 'webhook':
        return ['webhook_url', 'secret_token', 'events'];
      case 'smtp':
        return ['host', 'port', 'username', 'password', 'from_email', 'use_ssl'];
      default:
        return [];
    }
  };

  const suggestedFields = getIntegrationTypeFields();

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nome da Integração *
          </label>
          <Input
            id="name"
            {...register('name', { required: 'Nome é obrigatório' })}
            error={errors.name?.message}
          />
        </div>

        <div>
          <label
            htmlFor="type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tipo de Integração *
          </label>
          <Select
            id="type"
            {...register('type', { required: 'Tipo é obrigatório' })}
            options={[
              { value: 'api', label: 'API' },
              { value: 'oauth', label: 'OAuth' },
              { value: 'webhook', label: 'Webhook' },
              { value: 'smtp', label: 'SMTP' },
              { value: 'other', label: 'Outro' },
            ]}
            error={errors.type?.message}
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Configuração</h3>
        <div className="space-y-4">
          {configFields.map((field, index) => (
            <div key={index} className="flex items-start space-x-2">
              <div className="w-1/3">
                <Input
                  placeholder="Chave"
                  value={field.key}
                  onChange={(e) => handleConfigFieldChange(index, 'key', e.target.value)}
                  list={`suggested-keys-${index}`}
                />
                <datalist id={`suggested-keys-${index}`}>
                  {suggestedFields.map((key) => (
                    <option key={key} value={key} />
                  ))}
                </datalist>
              </div>
              <div className="w-1/3">
                {field.type === 'boolean' ? (
                  <Select
                    value={field.value}
                    onChange={(e) => handleConfigFieldChange(index, 'value', e.target.value)}
                    options={[
                      { value: 'true', label: 'Verdadeiro' },
                      { value: 'false', label: 'Falso' },
                    ]}
                  />
                ) : (
                  <Input
                    placeholder="Valor"
                    value={field.value}
                    onChange={(e) => handleConfigFieldChange(index, 'value', e.target.value)}
                    type={field.key.includes('password') || field.key.includes('secret') ? 'password' : 'text'}
                  />
                )}
              </div>
              <div className="w-1/6">
                <Select
                  value={field.type}
                  onChange={(e) => handleConfigFieldChange(index, 'type', e.target.value)}
                  options={[
                    { value: 'string', label: 'Texto' },
                    { value: 'number', label: 'Número' },
                    { value: 'boolean', label: 'Booleano' },
                    { value: 'json', label: 'JSON' },
                  ]}
                />
              </div>
              <div className="flex-shrink-0">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleRemoveConfigField(index)}
                  disabled={configFields.length === 1}
                >
                  Remover
                </Button>
              </div>
            </div>
          ))}
          <div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddConfigField}
            >
              Adicionar Campo
            </Button>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Integração' : 'Criar Integração'}
        </Button>
      </div>
    </form>
  );
};

export default IntegrationForm;