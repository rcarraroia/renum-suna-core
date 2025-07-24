import React from 'react';
import FormField from './FormField';

interface TextFieldProps {
  id: string;
  name: string;
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  error?: string;
  required?: boolean;
  helpText?: string;
  placeholder?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'tel';
  multiline?: boolean;
  rows?: number;
  disabled?: boolean;
  maxLength?: number;
}

/**
 * Componente de campo de texto
 * 
 * Campo de texto ou textarea com integração com FormField
 */
const TextField: React.FC<TextFieldProps> = ({
  id,
  name,
  label,
  value,
  onChange,
  error,
  required = false,
  helpText,
  placeholder = '',
  type = 'text',
  multiline = false,
  rows = 3,
  disabled = false,
  maxLength
}) => {
  return (
    <FormField
      id={id}
      label={label}
      error={error}
      required={required}
      helpText={helpText}
    >
      {multiline ? (
        <textarea
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          rows={rows}
          disabled={disabled}
          maxLength={maxLength}
          placeholder={placeholder}
          className={`mt-1 block w-full shadow-sm sm:text-sm rounded-md ${
            error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
        />
      ) : (
        <input
          type={type}
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          disabled={disabled}
          maxLength={maxLength}
          placeholder={placeholder}
          className={`mt-1 block w-full shadow-sm sm:text-sm rounded-md ${
            error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : 'border-gray-300 focus:ring-blue-500 focus:border-blue-500'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
        />
      )}
    </FormField>
  );
};

export default TextField;