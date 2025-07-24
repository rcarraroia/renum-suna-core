// Exportação de todos os contextos e provider combinado

import React, { ReactNode, useEffect, useState } from 'react';
import { TeamProvider } from './TeamContext';
import { ExecutionProvider } from './ExecutionContext';
import { AuthProvider } from './AuthContext';
import { WebSocketProvider } from './WebSocketContext';
import { useAuth } from './AuthContext';

interface AppProvidersProps {
  children: ReactNode;
}

// Provider interno para WebSocket que depende do contexto de autenticação
function WebSocketProviderWithAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  
  useEffect(() => {
    // Configura a URL do WebSocket com base no ambiente
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const wsBaseUrl = baseUrl.replace(/^http/, 'ws');
    setWsUrl(`${wsBaseUrl}/ws/auth`);
  }, []);

  if (!wsUrl) {
    return <>{children}</>;
  }

  return (
    <WebSocketProvider
      options={{
        url: wsUrl,
        token: user?.token || '',
        autoConnect: isAuthenticated,
        debug: process.env.NODE_ENV === 'development',
      }}
    >
      {children}
    </WebSocketProvider>
  );
}

// Provider combinado para todos os contextos da aplicação
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <AuthProvider>
      <WebSocketProviderWithAuth>
        <TeamProvider>
          <ExecutionProvider>
            {children}
          </ExecutionProvider>
        </TeamProvider>
      </WebSocketProviderWithAuth>
    </AuthProvider>
  );
}

// Exporta todos os contextos
export * from './TeamContext';
export * from './ExecutionContext';
export * from './AuthContext';
export * from './WebSocketContext';