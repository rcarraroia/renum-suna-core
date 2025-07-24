import React, { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
}

/**
 * Componente de cabeçalho de página
 * 
 * Exibe o título da página, uma descrição opcional e ações
 */
const PageHeader: React.FC<PageHeaderProps> = ({ title, description, actions }) => {
  return (
    <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
      </div>
      {actions && (
        <div className="mt-4 flex flex-shrink-0 md:mt-0 md:ml-4">
          {actions}
        </div>
      )}
    </div>
  );
};

export default PageHeader;