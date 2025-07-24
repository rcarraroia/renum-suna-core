/**
 * Componente para exibir uma notificação individual
 */

import React, { useState } from 'react';
import { WebSocketNotification } from '../../types/websocket';

interface NotificationItemProps {
  notification: WebSocketNotification;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
  onAction?: (notification: WebSocketNotification) => void;
  compact?: boolean;
  showActions?: boolean;
}

/**
 * Componente para exibir uma notificação individual
 */
const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  onMarkAsRead,
  onDelete,
  onAction,
  compact = false,
  showActions = true,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  // Define a cor com base no tipo de notificação
  const getTypeColor = () => {
    switch (notification.type) {
      case 'success':
        return 'border-green-400 bg-green-50';
      case 'warning':
        return 'border-yellow-400 bg-yellow-50';
      case 'error':
        return 'border-red-400 bg-red-50';
      case 'info':
      default:
        return 'border-blue-400 bg-blue-50';
    }
  };

  // Define a cor do texto com base no tipo
  const getTextColor = () => {
    switch (notification.type) {
      case 'success':
        return 'text-green-800';
      case 'warning':
        return 'text-yellow-800';
      case 'error':
        return 'text-red-800';
      case 'info':
      default:
        return 'text-blue-800';
    }
  };

  // Define o ícone com base no tipo de notificação
  const getTypeIcon = () => {
    const iconClass = `h-5 w-5 ${getTextColor()}`;
    
    switch (notification.type) {
      case 'success':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  // Formata a data
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) {
      return 'Agora';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m atrás`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours}h atrás`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `${days}d atrás`;
    }
  };

  // Manipula o clique na notificação
  const handleClick = () => {
    if (!notification.read) {
      onMarkAsRead(notification.id);
    }
    
    if (notification.action && onAction) {
      onAction(notification);
    }
  };

  // Manipula o clique no botão de deletar
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(notification.id);
  };

  // Manipula o clique no botão de marcar como lida
  const handleMarkAsRead = (e: React.MouseEvent) => {
    e.stopPropagation();
    onMarkAsRead(notification.id);
  };

  return (
    <div
      className={`
        ${getTypeColor()} 
        border-l-4 rounded-r-lg shadow-sm transition-all duration-200 cursor-pointer
        ${!notification.read ? 'opacity-100' : 'opacity-75'}
        ${isHovered ? 'shadow-md transform scale-[1.02]' : ''}
        ${compact ? 'p-3' : 'p-4'}
      `}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-start">
        {/* Ícone */}
        <div className="flex-shrink-0 mr-3">
          {getTypeIcon()}
        </div>

        {/* Conteúdo */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <h4 className={`font-medium ${getTextColor()} ${compact ? 'text-sm' : 'text-base'}`}>
              {notification.title}
            </h4>
            
            {/* Indicador de não lida */}
            {!notification.read && (
              <div className="flex-shrink-0 ml-2">
                <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              </div>
            )}
          </div>

          <p className={`${getTextColor()} ${compact ? 'text-xs' : 'text-sm'} mb-2`}>
            {notification.message}
          </p>

          <div className="flex items-center justify-between">
            <span className={`text-xs ${getTextColor()} opacity-75`}>
              {formatDate(notification.created_at)}
            </span>

            {/* Ações */}
            {showActions && (
              <div className="flex items-center space-x-2">
                {notification.action && (
                  <button
                    onClick={handleClick}
                    className={`text-xs ${getTextColor()} hover:underline font-medium`}
                  >
                    {notification.action.type === 'url' ? 'Ver detalhes' : 'Executar ação'}
                  </button>
                )}
                
                {!notification.read && (
                  <button
                    onClick={handleMarkAsRead}
                    className="text-xs text-gray-600 hover:text-gray-800"
                    title="Marcar como lida"
                  >
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                )}
                
                <button
                  onClick={handleDelete}
                  className="text-xs text-gray-600 hover:text-red-600"
                  title="Remover notificação"
                >
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationItem;