/**
 * Componente para exibir notificações WebSocket
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketNotification } from '../../types/websocket';

/**
 * Propriedades do componente WebSocketNotifications
 */
interface WebSocketNotificationsProps {
  maxNotifications?: number;
  autoHide?: boolean;
  autoHideDelay?: number;
  className?: string;
}

/**
 * Componente para exibir notificações WebSocket
 */
const WebSocketNotifications: React.FC<WebSocketNotificationsProps> = ({
  maxNotifications = 5,
  autoHide = true,
  autoHideDelay = 5000,
  className = '',
}) => {
  const { on } = useWebSocketContext();
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);

  // Inscreve-se para receber notificações
  useEffect(() => {
    const unsubscribe = on(WebSocketMessageType.NOTIFICATION, (message) => {
      if (message.type === WebSocketMessageType.NOTIFICATION && message.data) {
        const notification = message.data as WebSocketNotification;
        
        setNotifications((prev) => {
          // Adiciona a nova notificação no início da lista
          const updated = [notification, ...prev];
          
          // Limita o número de notificações
          return updated.slice(0, maxNotifications);
        });
      }
    });

    return unsubscribe;
  }, [on, maxNotifications]);

  // Remove uma notificação
  const removeNotification = (id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));
  };

  // Marca uma notificação como lida
  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  // Auto-esconde notificações após um tempo
  useEffect(() => {
    if (!autoHide) return;

    const timers: NodeJS.Timeout[] = [];

    notifications.forEach((notification) => {
      if (!notification.read) {
        const timer = setTimeout(() => {
          markAsRead(notification.id);
        }, autoHideDelay);

        timers.push(timer);
      }
    });

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [notifications, autoHide, autoHideDelay]);

  // Define a cor de fundo com base no tipo de notificação
  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-100 border-green-500 text-green-800';
      case 'warning':
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      case 'error':
        return 'bg-red-100 border-red-500 text-red-800';
      case 'info':
      default:
        return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  // Define o ícone com base no tipo de notificação
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success':
        return (
          <svg className="h-5 w-5 text-green-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className="h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className={`fixed bottom-4 right-4 z-50 space-y-2 ${className}`}>
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`${
            getNotificationColor(notification.type)
          } border-l-4 p-4 rounded shadow-md transition-opacity duration-300 ${
            notification.read ? 'opacity-50' : 'opacity-100'
          } max-w-md`}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              {getNotificationIcon(notification.type)}
            </div>
            <div className="ml-3 flex-1">
              <p className="font-medium">{notification.title}</p>
              <p className="text-sm mt-1">{notification.message}</p>
              {notification.action && (
                <button
                  className="mt-2 text-sm font-medium underline"
                  onClick={() => {
                    // Executa a ação
                    if (notification.action?.type === 'url' && notification.action?.payload) {
                      window.open(notification.action.payload, '_blank');
                    }
                    markAsRead(notification.id);
                  }}
                >
                  {notification.action.type === 'url' ? 'Abrir link' : 'Executar ação'}
                </button>
              )}
            </div>
            <div className="ml-auto pl-3">
              <button
                className="inline-flex text-gray-400 hover:text-gray-500"
                onClick={() => removeNotification(notification.id)}
              >
                <span className="sr-only">Fechar</span>
                <svg
                  className="h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default WebSocketNotifications;