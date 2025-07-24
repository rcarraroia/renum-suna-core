import React, { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
}

/**
 * Componente de estado vazio
 * 
 * Exibe uma mensagem quando não há dados para mostrar
 */
const EmptyState: React.FC<EmptyStateProps> = ({ title, description, icon, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center bg-white rounded-lg border border-gray-200">
      {icon && (
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-gray-500 max-w-md">{description}</p>
      )}
      {action && (
        <div className="mt-6">
          {action}
        </div>
      )}
    </div>
  );
};

export default EmptyState;