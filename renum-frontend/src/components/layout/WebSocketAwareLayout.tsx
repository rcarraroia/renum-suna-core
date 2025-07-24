/**
 * Layout que inclui todos os indicadores visuais de estado da conexão WebSocket
 */

import React from 'react';
import { ConnectionIndicators, ConnectionLostOverlay } from '../websocket';
import HeaderConnectionIndicator from './HeaderConnectionIndicator';
import WebSocketStatusBar from './WebSocketStatusBar';

interface WebSocketAwareLayoutProps {
  children: React.ReactNode;
  showHeader?: boolean;
  showStatusBar?: boolean;
  showOverlay?: boolean;
  className?: string;
}

/**
 * Layout que inclui todos os indicadores visuais de estado da conexão WebSocket
 */
const WebSocketAwareLayout: React.FC<WebSocketAwareLayoutProps> = ({
  children,
  showHeader = true,
  showStatusBar = true,
  showOverlay = true,
  className = '',
}) => {
  return (
    <ConnectionIndicators>
      <ConnectionLostOverlay showAfterMs={15000}>
        <div className={`flex flex-col min-h-screen ${className}`}>
          {/* Cabeçalho com indicador de conexão */}
          {showHeader && (
            <header className="bg-white shadow">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
                <h1 className="text-xl font-bold text-gray-900">Aplicação</h1>
                <HeaderConnectionIndicator showText={true} />
              </div>
            </header>
          )}

          {/* Conteúdo principal */}
          <main className="flex-1">
            {showStatusBar && <WebSocketStatusBar />}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              {children}
            </div>
          </main>

          {/* Rodapé */}
          <footer className="bg-gray-100 border-t border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-center text-sm text-gray-500">
              © {new Date().getFullYear()} Renum. Todos os direitos reservados.
            </div>
          </footer>
        </div>
      </ConnectionLostOverlay>
    </ConnectionIndicators>
  );
};

export default WebSocketAwareLayout;