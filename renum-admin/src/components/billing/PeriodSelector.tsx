import React from 'react';
import { BillingPeriod } from '../../types/billing';
import Select from '../ui/Select';

interface PeriodSelectorProps {
  periods: BillingPeriod[];
  currentPeriod: BillingPeriod | null;
  onChange: (period: BillingPeriod) => void;
  isLoading: boolean;
}

const PeriodSelector: React.FC<PeriodSelectorProps> = ({
  periods,
  currentPeriod,
  onChange,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="w-64 h-10 bg-gray-200 animate-pulse rounded" />
    );
  }

  if (!periods || periods.length === 0) {
    return (
      <div className="text-sm text-gray-500">
        Nenhum período disponível
      </div>
    );
  }

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedPeriod = periods.find(p => p.label === e.target.value);
    if (selectedPeriod) {
      onChange(selectedPeriod);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm font-medium text-gray-700">Período:</span>
      <div className="w-64">
        <Select
          value={currentPeriod?.label || ''}
          onChange={handleChange}
          options={periods.map(period => ({
            value: period.label,
            label: period.label,
          }))}
        />
      </div>
    </div>
  );
};

export default PeriodSelector;