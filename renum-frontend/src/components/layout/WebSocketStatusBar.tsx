/**
 * Barra de status WebSocket
 */

import React from 'react';
import { WebSocketStatus } from '../websocket';
import NotificationsCenter from '../notifications/NotificationsCenter';
import { ConnectionLostBanner } from '../websocket';

interface WebSocketStatusBarProps {
  className?: string;
}

/**
 * Barra de status WebSocket
 */
const WebSocketStatusBar: React.FC<WebSocketStatusBarProps> = ({
  className = '',
}) => {
  return (
    <>
      {/* Banner de conexão perdida */}
      <ConnectionLostBanner />
      
      {/* Barra de status */}
      <div className={`flex items-center justify-end space-x-4 p-2 ${className}`}>
        <WebSocketStatus showStatusText={true} />
        <NotificationsCenter />
      </div>
    </>
  );
};

export default WebSocketStatusBar;