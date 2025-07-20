import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { AlertRuleFormData, AlertCondition, AlertAction } from '../../types/audit';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface AlertRuleFormProps {
  defaultValues?: Partial<AlertRuleFormData>;
  onSubmit: (data: AlertRuleFormData) => void;
  isSubmitting: boolean;
  eventTypes: string[];
  entityTypes: string[];
  isEditMode?: boolean;
}

const AlertRuleForm: React.FC<AlertRuleFormProps> = ({
  defaultValues,
  onSubmit,
  isSubmitting,
  eventTypes,
  entityTypes,
  isEditMode = false,
}) => {
  const [conditions, setConditions] = useState<AlertCondition[]>(
    defaultValues?.conditions || [{ field: '', operator: 'equals', value: '' }]
  );
  
  const [actions, setActions] = useState<AlertAction[]>(
    defaultValues?.actions || [{ type: 'email', config: { recipients: '' } }]
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AlertRuleFormData>({
    defaultValues: defaultValues || {
      name: '',
      description: '',
      event_type: '',
      entity_type: '',
      actor_type: undefined,
      conditions: [],
      actions: [],
      is_active: true,
    },
  });

  const handleAddCondition = () => {
    setConditions([...conditions, { field: '', operator: 'equals', value: '' }]);
  };

  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleConditionChange = (index: number, field: keyof AlertCondition, value: any) => {
    const newConditions = [...conditions];
    newConditions[index][field] = value;
    setConditions(newConditions);
  };

  const handleAddAction = () => {
    setActions([...actions, { type: 'email', config: { recipients: '' } }]);
  };

  const handleRemoveAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const handleActionChange = (index: number, field: keyof AlertAction, value: any) => {
    const newActions = [...actions];
    if (field === 'type') {
      // Reset config based on action type
      if (value === 'email') {
        newActions[index].config = { recipients: '' };
      } else if (value === 'webhook') {
        newActions[index].config = { url: '', method: 'POST' };
      } else if (value === 'notification') {
        newActions[index].config = { message: '' };
      }
    }
    newActions[index][field] = value;
    setActions(newActions);
  };

  const handleActionConfigChange = (index: number, configKey: string, value: any) => {
    const newActions = [...actions];
    newActions[index].config[configKey] = value;
    setActions(newActions);
  };

  const handleFormSubmit = (data: AlertRuleFormData) => {
    onSubmit({
      ...data,
      conditions,
      actions,
    });
  };

  const getOperatorOptions = () => [
    { value: 'equals', label: 'Igual a' },
    { value: 'not_equals', label: 'Diferente de' },
    { value: 'contains', label: 'Contém' },
    { value: 'not_contains', label: 'Não contém' },
    { value: 'starts_with', label: 'Começa com' },
    { value: 'ends_with', label: 'Termina com' },
    { value: 'greater_than', label: 'Maior que' },
    { value: 'less_than', label: 'Menor que' },
  ];

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Nome da Regra *
          </label>
          <Input
            id="name"
            {...register('name', { required: 'Nome é obrigatório' })}
            error={errors.name?.message}
          />
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
            rows={2}
            {...register('description', { required: 'Descrição é obrigatória' })}
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Filtros de Eventos</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label
              htmlFor="event_type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tipo de Evento
            </label>
            <Select
              id="event_type"
              {...register('event_type')}
              options={[
                { value: '', label: 'Todos os eventos' },
                ...(eventTypes || []).map((type) => ({
                  value: type,
                  label: type,
                })),
              ]}
            />
          </div>

          <div>
            <label
              htmlFor="entity_type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tipo de Entidade
            </label>
            <Select
              id="entity_type"
              {...register('entity_type')}
              options={[
                { value: '', label: 'Todas as entidades' },
                ...(entityTypes || []).map((type) => ({
                  value: type,
                  label: type,
                })),
              ]}
            />
          </div>

          <div>
            <label
              htmlFor="actor_type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Tipo de Ator
            </label>
            <Select
              id="actor_type"
              {...register('actor_type')}
              options={[
                { value: '', label: 'Todos os atores' },
                { value: 'user', label: 'Usuário' },
                { value: 'admin', label: 'Administrador' },
                { value: 'system', label: 'Sistema' },
              ]}
            />
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Condições</h3>
        <div className="space-y-4">
          {conditions.map((condition, index) => (
            <div key={index} className="flex items-start space-x-2">
              <div className="w-1/3">
                <Input
                  placeholder="Campo (ex: details.ip_address)"
                  value={condition.field}
                  onChange={(e) => handleConditionChange(index, 'field', e.target.value)}
                />
              </div>
              <div className="w-1/3">
                <Select
                  value={condition.operator}
                  onChange={(e) => handleConditionChange(index, 'operator', e.target.value as any)}
                  options={getOperatorOptions()}
                />
              </div>
              <div className="w-1/3">
                <Input
                  placeholder="Valor"
                  value={condition.value}
                  onChange={(e) => handleConditionChange(index, 'value', e.target.value)}
                />
              </div>
              <div className="flex-shrink-0">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleRemoveCondition(index)}
                  disabled={conditions.length === 1}
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
              onClick={handleAddCondition}
            >
              Adicionar Condição
            </Button>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Ações</h3>
        <div className="space-y-4">
          {actions.map((action, index) => (
            <div key={index} className="border border-gray-200 rounded-md p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="w-1/3">
                  <label
                    htmlFor={`action-type-${index}`}
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Tipo de Ação
                  </label>
                  <Select
                    id={`action-type-${index}`}
                    value={action.type}
                    onChange={(e) => handleActionChange(index, 'type', e.target.value as any)}
                    options={[
                      { value: 'email', label: 'Email' },
                      { value: 'webhook', label: 'Webhook' },
                      { value: 'notification', label: 'Notificação' },
                    ]}
                  />
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleRemoveAction(index)}
                  disabled={actions.length === 1}
                >
                  Remover
                </Button>
              </div>

              {action.type === 'email' && (
                <div>
                  <label
                    htmlFor={`action-email-${index}`}
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Destinatários (separados por vírgula)
                  </label>
                  <Input
                    id={`action-email-${index}`}
                    value={action.config.recipients || ''}
                    onChange={(e) => handleActionConfigChange(index, 'recipients', e.target.value)}
                  />
                </div>
              )}

              {action.type === 'webhook' && (
                <div className="space-y-4">
                  <div>
                    <label
                      htmlFor={`action-webhook-url-${index}`}
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      URL do Webhook
                    </label>
                    <Input
                      id={`action-webhook-url-${index}`}
                      value={action.config.url || ''}
                      onChange={(e) => handleActionConfigChange(index, 'url', e.target.value)}
                    />
                  </div>
                  <div>
                    <label
                      htmlFor={`action-webhook-method-${index}`}
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Método
                    </label>
                    <Select
                      id={`action-webhook-method-${index}`}
                      value={action.config.method || 'POST'}
                      onChange={(e) => handleActionConfigChange(index, 'method', e.target.value)}
                      options={[
                        { value: 'GET', label: 'GET' },
                        { value: 'POST', label: 'POST' },
                        { value: 'PUT', label: 'PUT' },
                      ]}
                    />
                  </div>
                </div>
              )}

              {action.type === 'notification' && (
                <div>
                  <label
                    htmlFor={`action-notification-${index}`}
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Mensagem
                  </label>
                  <Input
                    id={`action-notification-${index}`}
                    value={action.config.message || ''}
                    onChange={(e) => handleActionConfigChange(index, 'message', e.target.value)}
                  />
                </div>
              )}
            </div>
          ))}
          <div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddAction}
            >
              Adicionar Ação
            </Button>
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-3">
        <Button type="submit" isLoading={isSubmitting}>
          {isEditMode ? 'Atualizar Regra' : 'Criar Regra'}
        </Button>
      </div>
    </form>
  );
};

export default AlertRuleForm;