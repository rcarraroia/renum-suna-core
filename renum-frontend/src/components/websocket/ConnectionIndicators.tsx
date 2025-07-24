/**
 * Componente que combina todos os indicadores visuais de estado da conexão
 */

import React from 'react';
import ConnectionLostBanner from './ConnectionLostBanner';
import ConnectionToast from './ConnectionToast';
import ReconnectionProgress from './ReconnectionProgress';
import { useWebSocketContext } from '../../contexts/WebSocketContext';

interface ConnectionIndicatorsProps {
  showBanner?: boolean;
  showToast?: boolean;
  showProgress?: boolean;
  showOverlay?: boolean;
  children?: React.ReactNode;
}

/**
 * Componente que combina todos os indicadores visuais de estado da conexão
 */
const ConnectionIndicators: React.FC<ConnectionIndicatorsProps> = ({
  showBanner = true,
  showToast = true,
  showProgress = true,
  showOverlay = false,
  children,
}) => {
  const { isConnected } = useWebSocketContext();

  return (
    <>
      {/* Banner de conexão perdida */}
      {showBanner && <ConnectionLostBanner />}
      
      {/* Toast de notificação de estado */}
      {showToast && <ConnectionToast />}
      
      {/* Barra de progresso de reconexão */}
      {showProgress && <ReconnectionProgress />}
      
      {/* Conteúdo */}
      {children}
    </>
  );
};

export default ConnectionIndicators;