import React, { ReactNode } from 'react';

interface FormFieldProps {
  id: string;
  label: string;
  error?: string;
  required?: boolean;
  helpText?: string;
  children: ReactNode;
}

/**
 * Componente de campo de formulário
 * 
 * Wrapper para campos de formulário com label, mensagem de erro e texto de ajuda
 */
const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  error,
  required = false,
  helpText,
  children
}) => {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {children}
      
      {helpText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helpText}</p>
      )}
      
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

export default FormField;