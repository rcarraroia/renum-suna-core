/**
 * Provider para o React Query
 */

import React, { ReactNode } from 'react';
import { QueryClientProvider } from 'react-query';
import { ReactQueryDevtools } from 'react-query/devtools';
import queryClient from '../services/query-client';

interface QueryProviderProps {
  children: ReactNode;
}

/**
 * Provider para o React Query
 * 
 * Este componente configura o React Query para toda a aplicação.
 * Inclui o React Query Devtools em ambiente de desenvolvimento.
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

export default QueryProvider;