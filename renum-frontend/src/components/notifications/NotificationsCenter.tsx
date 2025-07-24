/**
 * Centro de notificações em tempo real
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { WebSocketNotification } from '../../types/websocket';

interface NotificationsCenterProps {
  maxNotifications?: number;
  className?: string;
}

/**
 * Centro de notificações em tempo real
 */
const NotificationsCenter: React.FC<NotificationsCenterProps> = ({
  maxNotifications = 10,
  className = '',
}) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, removeNotification, clearAllNotifications } = useWebSocketNotifications();
  const [isOpen, setIsOpen] = useState(false);

  // Fecha o painel quando não há notificações
  useEffect(() => {
    if (notifications.length === 0 && isOpen) {
      setIsOpen(false);
    }
  }, [notifications, isOpen]);

  // Abre o painel quando chega uma nova notificação
  useEffect(() => {
    if (unreadCount > 0 && !isOpen) {
      setIsOpen(true);
    }
  }, [unreadCount, isOpen]);

  // Define a cor com base no tipo de notificação
  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'border-green-500 bg-green-50';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50';
      case 'error':
        return 'border-red-500 bg-red-50';
      case 'info':
      default:
        return 'border-blue-500 bg-blue-50';
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

  // Formata a data
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Manipula o clique em uma notificação
  const handleNotificationClick = (notification: WebSocketNotification) => {
    markAsRead(notification.id);
    
    // Executa a ação se houver
    if (notification.action?.type === 'url' && notification.action?.payload) {
      window.open(notification.action.payload, '_blank');
    }
  };

  return (
    <div className={`relative ${className}`}>
      {/* Botão de notificações */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none"
      >
        <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {/* Badge de contagem */}
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Painel de notificações */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50 overflow-hidden border border-gray-200">
          {/* Cabeçalho */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="font-medium">Notificações</h3>
            <div className="flex space-x-2">
              {unreadCount > 0 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  {unreadCount} não lidas
                </span>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          {/* Lista de notificações */}
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-gray-500">
                Nenhuma notificação
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {notifications.slice(0, maxNotifications).map((notification) => (
                  <li
                    key={notification.id}
                    className={`p-4 hover:bg-gray-50 cursor-pointer ${!notification.read ? 'bg-gray-50' : ''}`}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div className="flex">
                      <div className="flex-shrink-0 mr-3">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeNotification(notification.id);
                            }}
                            className="ml-2 text-gray-400 hover:text-gray-500"
                          >
                            <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </button>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">{notification.message}</p>
                        <p className="mt-1 text-xs text-gray-500">{formatDate(notification.created_at)}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Rodapé */}
          {notifications.length > 0 && (
            <div className="p-2 border-t border-gray-200 flex justify-between">
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Marcar todas como lidas
              </button>
              <button
                onClick={clearAllNotifications}
                className="text-xs text-gray-600 hover:text-gray-800"
              >
                Limpar todas
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationsCenter;