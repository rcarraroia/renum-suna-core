/**
 * Componente para exibir uma lista de notificações
 */

import React, { useState, useMemo } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { WebSocketNotification } from '../../types/websocket';
import NotificationItem from './NotificationItem';

interface NotificationListProps {
  maxNotifications?: number;
  showFilters?: boolean;
  compact?: boolean;
  className?: string;
}

type FilterType = 'all' | 'unread' | 'info' | 'success' | 'warning' | 'error';

/**
 * Componente para exibir uma lista de notificações
 */
const NotificationList: React.FC<NotificationListProps> = ({
  maxNotifications = 50,
  showFilters = true,
  compact = false,
  className = '',
}) => {
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    removeNotification, 
    clearAllNotifications 
  } = useWebSocketNotifications({ maxNotifications });

  const [filter, setFilter] = useState<FilterType>('all');
  const [sortBy, setSortBy] = useState<'date' | 'type'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Filtra e ordena as notificações
  const filteredAndSortedNotifications = useMemo(() => {
    let filtered = notifications;

    // Aplica filtro
    switch (filter) {
      case 'unread':
        filtered = notifications.filter(n => !n.read);
        break;
      case 'info':
      case 'success':
      case 'warning':
      case 'error':
        filtered = notifications.filter(n => n.type === filter);
        break;
      default:
        filtered = notifications;
    }

    // Aplica ordenação
    return filtered.sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'date') {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortBy === 'type') {
        comparison = a.type.localeCompare(b.type);
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [notifications, filter, sortBy, sortOrder]);

  // Manipula a ação de uma notificação
  const handleNotificationAction = (notification: WebSocketNotification) => {
    if (notification.action?.type === 'url' && notification.action?.payload) {
      window.open(notification.action.payload, '_blank');
    }
  };

  // Obtém a contagem por tipo
  const getTypeCount = (type: string) => {
    return notifications.filter(n => n.type === type).length;
  };

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {/* Cabeçalho */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            Notificações
            {unreadCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {unreadCount} não lidas
              </span>
            )}
          </h2>
          
          {/* Ações do cabeçalho */}
          <div className="flex items-center space-x-2">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Marcar todas como lidas
              </button>
            )}
            
            {notifications.length > 0 && (
              <button
                onClick={clearAllNotifications}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Limpar todas
              </button>
            )}
          </div>
        </div>

        {/* Filtros */}
        {showFilters && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-gray-700">Filtrar:</span>
            
            {/* Filtros por status */}
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === 'all'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Todas ({notifications.length})
            </button>
            
            <button
              onClick={() => setFilter('unread')}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === 'unread'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Não lidas ({unreadCount})
            </button>

            {/* Filtros por tipo */}
            {(['info', 'success', 'warning', 'error'] as const).map((type) => {
              const count = getTypeCount(type);
              if (count === 0) return null;
              
              const colors = {
                info: 'bg-blue-100 text-blue-800',
                success: 'bg-green-100 text-green-800',
                warning: 'bg-yellow-100 text-yellow-800',
                error: 'bg-red-100 text-red-800',
              };
              
              return (
                <button
                  key={type}
                  onClick={() => setFilter(type)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    filter === type
                      ? colors[type]
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
                </button>
              );
            })}

            {/* Ordenação */}
            <div className="ml-4 flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Ordenar:</span>
              
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'type')}
                className="text-xs border border-gray-300 rounded px-2 py-1"
              >
                <option value="date">Data</option>
                <option value="type">Tipo</option>
              </select>
              
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="text-xs text-gray-600 hover:text-gray-800"
                title={`Ordenar ${sortOrder === 'asc' ? 'decrescente' : 'crescente'}`}
              >
                <svg 
                  className={`h-4 w-4 transform ${sortOrder === 'desc' ? 'rotate-180' : ''}`} 
                  xmlns="http://www.w3.org/2000/svg" 
                  viewBox="0 0 20 20" 
                  fill="currentColor"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Lista de notificações */}
      <div className="max-h-96 overflow-y-auto">
        {filteredAndSortedNotifications.length === 0 ? (
          <div className="p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              {filter === 'all' ? 'Nenhuma notificação' : `Nenhuma notificação ${filter === 'unread' ? 'não lida' : `do tipo ${filter}`}`}
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {filter === 'all' 
                ? 'Você receberá notificações aqui quando houver atualizações importantes.'
                : 'Tente alterar o filtro para ver outras notificações.'
              }
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredAndSortedNotifications.map((notification) => (
              <div key={notification.id} className="p-4">
                <NotificationItem
                  notification={notification}
                  onMarkAsRead={markAsRead}
                  onDelete={removeNotification}
                  onAction={handleNotificationAction}
                  compact={compact}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Rodapé */}
      {filteredAndSortedNotifications.length > 0 && (
        <div className="p-3 bg-gray-50 border-t border-gray-200 text-center">
          <span className="text-xs text-gray-500">
            Mostrando {filteredAndSortedNotifications.length} de {notifications.length} notificações
          </span>
        </div>
      )}
    </div>
  );
};

export default NotificationList;