import React, { useState } from 'react';
import { AuditFilter } from '../../types/audit';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface AuditLogFilterProps {
  filter: AuditFilter;
  onFilterChange: (filter: AuditFilter) => void;
  eventTypes: string[];
  entityTypes: string[];
  isLoading: boolean;
}

const AuditLogFilter: React.FC<AuditLogFilterProps> = ({
  filter,
  onFilterChange,
  eventTypes,
  entityTypes,
  isLoading,
}) => {
  const [localFilter, setLocalFilter] = useState<AuditFilter>(filter);

  const handleInputChange = (field: keyof AuditFilter, value: string) => {
    setLocalFilter((prev) => ({
      ...prev,
      [field]: value || undefined,
    }));
  };

  const handleApplyFilter = () => {
    onFilterChange(localFilter);
  };

  const handleClearFilter = () => {
    const emptyFilter: AuditFilter = {};
    setLocalFilter(emptyFilter);
    onFilterChange(emptyFilter);
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Filtros</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label
            htmlFor="event_type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tipo de Evento
          </label>
          <Select
            id="event_type"
            value={localFilter.event_type || ''}
            onChange={(e) => handleInputChange('event_type', e.target.value)}
            options={[
              { value: '', label: 'Todos os eventos' },
              ...(eventTypes || []).map((type) => ({
                value: type,
                label: type,
              })),
            ]}
            disabled={isLoading}
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
            value={localFilter.entity_type || ''}
            onChange={(e) => handleInputChange('entity_type', e.target.value)}
            options={[
              { value: '', label: 'Todas as entidades' },
              ...(entityTypes || []).map((type) => ({
                value: type,
                label: type,
              })),
            ]}
            disabled={isLoading}
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
            value={localFilter.actor_type || ''}
            onChange={(e) => handleInputChange('actor_type', e.target.value as any)}
            options={[
              { value: '', label: 'Todos os atores' },
              { value: 'user', label: 'Usuário' },
              { value: 'admin', label: 'Administrador' },
              { value: 'system', label: 'Sistema' },
            ]}
          />
        </div>

        <div>
          <label
            htmlFor="entity_id"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            ID da Entidade
          </label>
          <Input
            id="entity_id"
            value={localFilter.entity_id || ''}
            onChange={(e) => handleInputChange('entity_id', e.target.value)}
          />
        </div>

        <div>
          <label
            htmlFor="start_date"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Data Inicial
          </label>
          <Input
            id="start_date"
            type="date"
            value={localFilter.start_date || ''}
            onChange={(e) => handleInputChange('start_date', e.target.value)}
          />
        </div>

        <div>
          <label
            htmlFor="end_date"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Data Final
          </label>
          <Input
            id="end_date"
            type="date"
            value={localFilter.end_date || ''}
            onChange={(e) => handleInputChange('end_date', e.target.value)}
          />
        </div>
      </div>

      <div className="flex justify-end mt-4 space-x-3">
        <Button
          variant="outline"
          onClick={handleClearFilter}
        >
          Limpar Filtros
        </Button>
        <Button
          onClick={handleApplyFilter}
        >
          Aplicar Filtros
        </Button>
      </div>
    </div>
  );
};

export default AuditLogFilter;