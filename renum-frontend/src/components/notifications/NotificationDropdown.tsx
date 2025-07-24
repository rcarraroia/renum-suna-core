/**
 * Componente dropdown para notificações
 */

import React, { useState, useRef, useEffect } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { WebSocketNotification } from '../../types/websocket';
import NotificationItem from './NotificationItem';

interface NotificationDropdownProps {
  maxNotifications?: number;
  className?: string;
}

/**
 * Componente dropdown para notificações
 */
const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  maxNotifications = 5,
  className = '',
}) => {
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    removeNotification 
  } = useWebSocketNotifications({ maxNotifications });

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Fecha o dropdown quando clica fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Manipula a ação de uma notificação
  const handleNotificationAction = (notification: WebSocketNotification) => {
    if (notification.action?.type === 'url' && notification.action?.payload) {
      window.open(notification.action.payload, '_blank');
    }
    setIsOpen(false);
  };

  // Manipula marcar como lida
  const handleMarkAsRead = (id: string) => {
    markAsRead(id);
  };

  // Manipula remover notificação
  const handleRemoveNotification = (id: string) => {
    removeNotification(id);
  };

  // Manipula marcar todas como lidas
  const handleMarkAllAsRead = () => {
    markAllAsRead();
    setIsOpen(false);
  };

  // Obtém as notificações mais recentes
  const recentNotifications = notifications.slice(0, maxNotifications);

  return (
    <div className={`relative ${className}`}>
      {/* Botão de notificações */}
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-full"
        aria-label="Notificações"
      >
        <svg 
          className="h-6 w-6" 
          xmlns="http://www.w3.org/2000/svg" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" 
          />
        </svg>
        
        {/* Badge de contagem */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full min-w-[1.25rem] h-5">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden"
        >
          {/* Cabeçalho */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Notificações</h3>
              
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Marcar todas como lidas
                </button>
              )}
            </div>
            
            {unreadCount > 0 && (
              <p className="mt-1 text-sm text-gray-500">
                Você tem {unreadCount} notificação{unreadCount !== 1 ? 'ões' : ''} não lida{unreadCount !== 1 ? 's' : ''}
              </p>
            )}
          </div>

          {/* Lista de notificações */}
          <div className="max-h-80 overflow-y-auto">
            {recentNotifications.length === 0 ? (
              <div className="p-8 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma notificação</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Você receberá notificações aqui quando houver atualizações importantes.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {recentNotifications.map((notification) => (
                  <div key={notification.id} className="p-3">
                    <NotificationItem
                      notification={notification}
                      onMarkAsRead={handleMarkAsRead}
                      onDelete={handleRemoveNotification}
                      onAction={handleNotificationAction}
                      compact={true}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Rodapé */}
          {recentNotifications.length > 0 && (
            <div className="p-3 bg-gray-50 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {notifications.length > maxNotifications && (
                    <>Mostrando {maxNotifications} de {notifications.length}</>
                  )}
                </span>
                
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Ver todas
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown;