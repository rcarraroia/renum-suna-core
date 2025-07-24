/**
 * Componente para exibir um contador de notificações não lidas
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketNotification } from '../../types/websocket';

/**
 * Propriedades do componente NotificationBadge
 */
interface NotificationBadgeProps {
  className?: string;
  onClick?: () => void;
}

/**
 * Componente para exibir um contador de notificações não lidas
 */
const NotificationBadge: React.FC<NotificationBadgeProps> = ({
  className = '',
  onClick,
}) => {
  const { on } = useWebSocketContext();
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);

  // Inscreve-se para receber notificações
  useEffect(() => {
    const unsubscribe = on(WebSocketMessageType.NOTIFICATION, (message) => {
      if (message.type === WebSocketMessageType.NOTIFICATION && message.data) {
        const notification = message.data as WebSocketNotification;
        
        setNotifications((prev) => {
          // Adiciona a nova notificação no início da lista
          return [notification, ...prev];
        });
        
        // Atualiza o contador de não lidas
        if (!notification.read) {
          setUnreadCount((prev) => prev + 1);
        }
      }
    });

    return unsubscribe;
  }, [on]);

  // Marca todas as notificações como lidas
  const markAllAsRead = () => {
    setUnreadCount(0);
    setNotifications((prev) =>
      prev.map((notification) => ({ ...notification, read: true }))
    );
  };

  // Manipula o clique no badge
  const handleClick = () => {
    if (onClick) {
      onClick();
    } else {
      markAllAsRead();
    }
  };

  if (unreadCount === 0) {
    return null;
  }

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-500 rounded-full ${className}`}
    >
      {unreadCount}
    </button>
  );
};

export default NotificationBadge;