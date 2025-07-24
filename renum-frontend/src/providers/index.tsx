/**
 * Exportações de providers
 */

import React, { ReactNode } from 'react';
import { QueryProvider } from './QueryProvider';
import { AppProviders } from '../contexts';

interface ProvidersProps {
  children: ReactNode;
}

/**
 * Providers combinados para a aplicação
 * 
 * Este componente combina todos os providers necessários para a aplicação.
 * A ordem é importante: QueryProvider deve envolver AppProviders para que
 * os hooks do React Query possam ser usados dentro dos contextos.
 */
export function Providers({ children }: ProvidersProps) {
  return (
    <QueryProvider>
      <AppProviders>
        {children}
      </AppProviders>
    </QueryProvider>
  );
}

// Exportações individuais
export * from './QueryProvider';
export { AppProviders } from '../contexts';