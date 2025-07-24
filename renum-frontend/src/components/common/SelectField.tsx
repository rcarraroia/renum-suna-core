import React from 'react';
import FormField from './FormField';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectFieldProps {
  id: string;
  name: string;
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  error?: string;
  required?: boolean;
  helpText?: string;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Componente de campo de seleção
 * 
 * Campo select com opções e integração com FormField
 */
const SelectField: React.FC<SelectFieldProps> = ({
  id,
  name,
  label,
  options,
  value,
  onChange,
  error,
  required = false,
  helpText,
  placeholder = 'Selecione uma opção',
  disabled = false
}) => {
  return (
    <FormField
      id={id}
      label={label}
      error={error}
      required={required}
      helpText={helpText}
    >
      <select
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        disabled={disabled}
        className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md ${
          error ? 'border-red-300' : 'border-gray-300'
        } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </FormField>
  );
};

export default SelectField;