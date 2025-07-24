import React, { useEffect, useState } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ExecutionNotification {
  id: string;
  type: 'execution_started' | 'execution_completed' | 'execution_failed' | 'execution_progress';
  title: string;
  message: string;
  execution_id: string;
  team_id: string;
  team_name?: string;
  timestamp: string;
  read: boolean;
  metadata?: {
    progress?: number;
    error_message?: string;
    result?: any;
  };
}

interface ExecutionNotificationsProps {
  userId?: string;
  teamId?: string;
  maxNotifications?: number;
  autoMarkAsRead?: boolean;
  showToasts?: boolean;
  className?: string;
}

export const ExecutionNotifications: React.FC<ExecutionNotificationsProps> = ({
  userId,
  teamId,
  maxNotifications = 50,
  autoMarkAsRead = false,
  showToasts = true,
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    deleteNotification 
  } = useWebSocketNotifications({
    userId,
    autoSubscribe: true,
    filterTypes: ['execution_started', 'execution_completed', 'execution_failed', 'execution_progress']
  });

  const [executionNotifications, setExecutionNotifications] = useState<ExecutionNotification[]>([]);
  const [showToastNotifications, setShowToastNotifications] = useState<ExecutionNotification[]>([]);

  // Filtrar notificações de execução
  useEffect(() => {
    const filtered = notifications
      .filter(notif => 
        ['execution_started', 'execution_completed', 'execution_failed', 'execution_progress'].includes(notif.type) &&
        (!teamId || notif.metadata?.team_id === teamId)
      )
      .map(notif => ({
        id: notif.id,
        type: notif.type as ExecutionNotification['type'],
        title: notif.title,
        message: notif.message,
        execution_id: notif.metadata?.execution_id || '',
        team_id: notif.metadata?.team_id || '',
        team_name: notif.metadata?.team_name,
        timestamp: notif.created_at,
        read: notif.status === 'read',
        metadata: notif.metadata
      }))
      .slice(0, maxNotifications);

    setExecutionNotifications(filtered);

    // Mostrar toasts para novas notificações
    if (showToasts) {
      const newNotifications = filtered.filter(notif => 
        !notif.read && 
        !showToastNotifications.find(toast => toast.id === notif.id)
      );

      if (newNotifications.length > 0) {
        setShowToastNotifications(prev => [...prev, ...newNotifications]);
        
        // Auto-remover toasts após 5 segundos
        newNotifications.forEach(notif => {
          setTimeout(() => {
            setShowToastNotifications(prev => prev.filter(toast => toast.id !== notif.id));
            
            if (autoMarkAsRead) {
              markAsRead(notif.id);
            }
          }, 5000);
        });
      }
    }
  }, [notifications, teamId, maxNotifications, showToasts, showToastNotifications, autoMarkAsRead, markAsRead]);

  const getNotificationIcon = (type: ExecutionNotification['type']) => {
    switch (type) {
      case 'execution_started':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'execution_completed':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'execution_failed':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'execution_progress':
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
        );
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return 'agora mesmo';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `há ${minutes} minuto${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `há ${hours} hora${hours > 1 ? 's' : ''}`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `há ${days} dia${days > 1 ? 's' : ''}`;
    }
  };

  const handleNotificationClick = (notification: ExecutionNotification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    
    // Navegar para a página da execução
    window.location.href = `/teams/${notification.team_id}/executions/${notification.execution_id}`;
  };

  const removeToast = (notificationId: string) => {
    setShowToastNotifications(prev => prev.filter(toast => toast.id !== notificationId));
  };

  return (
    <>
      {/* Toasts de notificação */}
      {showToastNotifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {showToastNotifications.map((notification) => (
            <div
              key={notification.id}
              className="max-w-sm bg-white border border-gray-200 rounded-lg shadow-lg p-4 cursor-pointer hover:shadow-xl transition-shadow"
              onClick={() => {
                handleNotificationClick(notification);
                removeToast(notification.id);
              }}
            >
              <div className="flex items-start">
                {getNotificationIcon(notification.type)}
                <div className="ml-3 flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {notification.title}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">
                    {notification.message}
                  </p>
                  {notification.team_name && (
                    <p className="text-xs text-gray-500 mt-1">
                      Equipe: {notification.team_name}
                    </p>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeToast(notification.id);
                  }}
                  className="ml-2 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lista de notificações */}
      <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              Notificações de Execução
              {unreadCount > 0 && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                  {unreadCount}
                </span>
              )}
            </h3>
            
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm text-gray-500">
                {isConnected ? 'Conectado' : 'Desconectado'}
              </span>
              
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  Marcar todas como lidas
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Lista */}
        <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
          {executionNotifications.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM4 19h10a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Nenhuma notificação
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Você não tem notificações de execução no momento.
              </p>
            </div>
          ) : (
            executionNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`px-6 py-4 cursor-pointer hover:bg-gray-50 transition-colors ${
                  !notification.read ? 'bg-blue-50' : ''
                }`}
                onClick={() => handleNotificationClick(notification)}
              >
                <div className="flex items-start">
                  {getNotificationIcon(notification.type)}
                  
                  <div className="ml-3 flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className={`text-sm font-medium ${
                        !notification.read ? 'text-gray-900' : 'text-gray-700'
                      }`}>
                        {notification.title}
                      </p>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">
                          {formatTimeAgo(notification.timestamp)}
                        </span>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-600 rounded-full"></div>
                        )}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-600 mt-1">
                      {notification.message}
                    </p>
                    
                    <div className="flex items-center justify-between mt-2">
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        {notification.team_name && (
                          <span>Equipe: {notification.team_name}</span>
                        )}
                        <span>ID: {notification.execution_id.slice(0, 8)}...</span>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteNotification(notification.id);
                        }}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
                          <path fillRule="evenodd" d="M4 5a1 1 0 011-1h10a1 1 0 011 1v12a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM8 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </div>

                    {/* Informações adicionais baseadas no tipo */}
                    {notification.type === 'execution_progress' && notification.metadata?.progress && (
                      <div className="mt-2">
                        <div className="flex items-center">
                          <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${notification.metadata.progress}%` }}
                            ></div>
                          </div>
                          <span className="ml-2 text-xs text-gray-600">
                            {notification.metadata.progress}%
                          </span>
                        </div>
                      </div>
                    )}

                    {notification.type === 'execution_failed' && notification.metadata?.error_message && (
                      <div className="mt-2 bg-red-50 border border-red-200 rounded p-2">
                        <p className="text-xs text-red-700">
                          {notification.metadata.error_message}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </>
  );
};