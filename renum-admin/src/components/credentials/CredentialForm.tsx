import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { CredentialFormData, CredentialMetadata } from '../../types/credential';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { Card, CardContent } from '../ui/Card';

interface CredentialFormProps {
  defaultValues?: Partial<CredentialFormData>;
  onSubmit: (data: CredentialFormData) => void;
  isSubmitting: boolean;
  isEditMode?: boolean;
}

const CredentialForm: React.FC<CredentialFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  isEditMode = false,
}) => {
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [metadata, setMetadata] = useState<CredentialMetadata>(
    defaultValues?.metadata || {}
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CredentialFormData>({
    defaultValues: defaultValues || {
      service_name: '',
      credential_type: 'api_key',
      value: '',
      is_active: true,
      expires_at: '',
      metadata: {},
    },
  });

  const credentialType = watch('credential_type');

  const handleFormSubmit = (data: CredentialFormData) => {
    // Incluir os metadados no envio
    const formData = {
      ...data,
      metadata,
    };
    onSubmit(formData);
  };

  const updateMetadata = (field: keyof CredentialMetadata, value: any) => {
    setMetadata((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            htmlFor="service_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nome do Serviço *
          </label>
          <Input
            id="service_name"
            {...register('service_name', { required: 'Nome do serviço é obrigatório' })}
            error={errors.service_name?.message}
          />
        </div>

        <div>
          <label
            htmlFor="credential_type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tipo de Credencial *
          </label>
          <Select
            id="credential_type"
            {...register('credential_type', { required: 'Tipo é obrigatório' })}
            options={[
              { value: 'api_key', label: 'Chave de API' },
              { value: 'oauth_token', label: 'Token OAuth' },
              { value: 'service_account', label: 'Conta de Serviço' },
            ]}
            error={errors.credential_type?.message}
          />
        </div>

        <div className={isEditMode ? 'md:col-span-2' : ''}>
          <label
            htmlFor="value"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {isEditMode ? 'Nova Valor (deixe em branco para manter o atual)' : 'Valor *'}
          </label>
          <Input
            id="value"
            type="password"
            {...register('value', {
              required: isEditMode ? false : 'Valor é obrigatório',
            })}
            error={errors.value?.message}
          />
          <p className="mt-1 text-xs text-gray-500">
            {credentialType === 'api_key'
              ? 'Insira a chave de API completa'
              : credentialType === 'oauth_token'
              ? 'Insira o token OAuth completo'
              : 'Insira o JSON da conta de serviço'}
          </p>
        </div>

        {!isEditMode && (
          <div>
            <label
              htmlFor="expires_at"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Data de Expiração
            </label>
            <Input
              id="expires_at"
              type="date"
              {...register('expires_at')}
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

      <div>
        <button
          type="button"
          className="text-primary-600 hover:text-primary-800 text-sm font-medium"
          onClick={() => setShowMetadataForm(!showMetadataForm)}
        >
          {showMetadataForm ? 'Ocultar Metadados' : 'Adicionar Metadados'}
        </button>

        {showMetadataForm && (
          <Card className="mt-3">
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    htmlFor="provider"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Provedor
                  </label>
                  <Input
                    id="provider"
                    value={metadata.provider || ''}
                    onChange={(e) => updateMetadata('provider', e.target.value)}
                  />
                </div>

                <div>
                  <label
                    htmlFor="environment"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Ambiente
                  </label>
                  <Select
                    id="environment"
                    value={metadata.environment || ''}
                    onChange={(e) => updateMetadata('environment', e.target.value)}
                    options={[
                      { value: '', label: 'Selecione...' },
                      { value: 'development', label: 'Desenvolvimento' },
                      { value: 'staging', label: 'Homologação' },
                      { value: 'production', label: 'Produção' },
                    ]}
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
                    className="block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    value={metadata.description || ''}
                    onChange={(e) => updateMetadata('description', e.target.value)}
                    rows={2}
                  />
                </div>

                <div>
                  <label
                    htmlFor="rate_limit"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Limite de Requisições (por minuto)
                  </label>
                  <Input
                    id="rate_limit"
                    type="number"
                    min="0"
                    value={metadata.rate_limit || ''}
                    onChange={(e) =>
                      updateMetadata('rate_limit', parseInt(e.target.value) || '')
                    }
                  />
                </div>

                <div className="md:col-span-2">
                  <label
                    htmlFor="usage_notes"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Notas de Uso
                  </label>
                  <textarea
                    id="usage_notes"
                    className="block w-full rounded-md border border-gray-300 shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    value={metadata.usage_notes || ''}
                    onChange={(e) => updateMetadata('usage_notes', e.target.value)}
                    rows={2}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Credencial' : 'Criar Credencial'}
        </Button>
      </div>
    </form>
  );
};

export default CredentialForm;