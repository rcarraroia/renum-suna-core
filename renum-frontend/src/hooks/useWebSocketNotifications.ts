/**
 * Hook para gerenciar notificações WebSocket com sincronização
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { WebSocketMessageType, WebSocketNotification } from '../types/websocket';
import { notificationSyncService } from '../services/notification-sync-service';

/**
 * Opções do hook useWebSocketNotifications
 */
interface UseWebSocketNotificationsOptions {
  maxNotifications?: number;
  autoMarkAsRead?: boolean;
  autoMarkAsReadDelay?: number;
  enableSync?: boolean;
}

/**
 * Hook para gerenciar notificações WebSocket com sincronização
 * @param options Opções
 * @returns Objeto com notificações e funções auxiliares
 */
export function useWebSocketNotifications(options: UseWebSocketNotificationsOptions = {}) {
  const {
    maxNotifications = 50,
    autoMarkAsRead = false,
    autoMarkAsReadDelay = 5000,
    enableSync = true,
  } = options;

  const { on, sendCommand, isConnected } = useWebSocketContext();
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const syncIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Carrega notificações do armazenamento local na inicialização
  useEffect(() => {
    if (enableSync) {
      const stored = notificationSyncService.getStoredNotifications();
      const webSocketNotifications = stored.map(({ synced, lastModified, ...notification }) => notification);
      setNotifications(webSocketNotifications.slice(0, maxNotifications));
      
      const stats = notificationSyncService.getSyncStats();
      setLastSyncTime(stats.lastSyncTime);
    }
  }, [enableSync, maxNotifications]);

  // Atualiza o contador de não lidas
  useEffect(() => {
    const count = notifications.filter(notification => !notification.read).length;
    setUnreadCount(count);
  }, [notifications]);

  // Inscreve-se para receber notificações via WebSocket
  useEffect(() => {
    const unsubscribe = on(WebSocketMessageType.NOTIFICATION, (message) => {
      if (message.type === WebSocketMessageType.NOTIFICATION && message.data) {
        const notification = message.data as WebSocketNotification;
        
        // Adiciona ao armazenamento local se a sincronização estiver habilitada
        if (enableSync) {
          notificationSyncService.addNotification(notification, true);
        }
        
        setNotifications((prev) => {
          // Verifica se a notificação já existe
          const exists = prev.some(n => n.id === notification.id);
          if (exists) {
            // Atualiza a notificação existente
            return prev.map(n => n.id === notification.id ? notification : n);
          }
          
          // Adiciona a nova notificação no início da lista
          const updated = [notification, ...prev];
          
          // Limita o número de notificações
          return updated.slice(0, maxNotifications);
        });
      }
    });

    return unsubscribe;
  }, [on, maxNotifications, enableSync]);

  // Sincronização automática quando conectado
  useEffect(() => {
    if (isConnected && enableSync) {
      // Sincroniza imediatamente ao conectar
      syncWithServer();
      
      // Configura sincronização periódica
      syncIntervalRef.current = setInterval(() => {
        syncWithServer();
      }, 30000); // Sincroniza a cada 30 segundos
    } else {
      // Limpa o intervalo de sincronização
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
        syncIntervalRef.current = null;
      }
    }

    return () => {
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
      }
    };
  }, [isConnected, enableSync]);

  // Auto marca como lida
  useEffect(() => {
    if (!autoMarkAsRead) return;

    const timers: NodeJS.Timeout[] = [];

    notifications.forEach((notification) => {
      if (!notification.read) {
        const timer = setTimeout(() => {
          markAsRead(notification.id);
        }, autoMarkAsReadDelay);

        timers.push(timer);
      }
    });

    return () => {
      timers.forEach((timer) => clearTimeout(timer));
    };
  }, [notifications, autoMarkAsRead, autoMarkAsReadDelay]);

  // Sincroniza com o servidor
  const syncWithServer = useCallback(async () => {
    if (!enableSync || isLoading) return;

    try {
      setIsLoading(true);

      await notificationSyncService.syncWithServer(
        // Função para buscar notificações do servidor
        async (since: string) => {
          return new Promise((resolve) => {
            // Simula busca de notificações do servidor
            // Em uma implementação real, isso seria uma chamada de API
            sendCommand('get_notifications_since', { since });
            
            // Por enquanto, retorna array vazio
            setTimeout(() => resolve([]), 1000);
          });
        },
        
        // Função para enviar ações para o servidor
        async (action) => {
          return new Promise((resolve) => {
            try {
              switch (action.type) {
                case 'mark_read':
                  sendCommand('mark_notification_as_read', { notification_id: action.notificationId });
                  break;
                case 'delete':
                  sendCommand('delete_notification', { notification_id: action.notificationId });
                  break;
                default:
                  resolve(false);
                  return;
              }
              
              // Simula resposta do servidor
              setTimeout(() => resolve(true), 500);
            } catch (error) {
              resolve(false);
            }
          });
        }
      );

      // Atualiza as notificações na interface
      const stored = notificationSyncService.getStoredNotifications();
      const webSocketNotifications = stored.map(({ synced, lastModified, ...notification }) => notification);
      setNotifications(webSocketNotifications.slice(0, maxNotifications));
      
      const stats = notificationSyncService.getSyncStats();
      setLastSyncTime(stats.lastSyncTime);
      
    } catch (error) {
      console.error('Erro na sincronização:', error);
    } finally {
      setIsLoading(false);
    }
  }, [enableSync, isLoading, sendCommand, maxNotifications]);

  // Marca uma notificação como lida
  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true, read_at: new Date().toISOString() } : notification
      )
    );

    if (enableSync) {
      // Marca como lida localmente e adiciona à fila de sincronização
      notificationSyncService.markAsReadLocally(id);
    } else {
      // Envia comando diretamente para o servidor
      sendCommand('mark_notification_as_read', { notification_id: id });
    }
  }, [sendCommand, enableSync]);

  // Marca todas as notificações como lidas
  const markAllAsRead = useCallback(() => {
    const now = new Date().toISOString();
    setNotifications((prev) =>
      prev.map((notification) => ({ ...notification, read: true, read_at: now }))
    );

    if (enableSync) {
      // Marca todas como lidas localmente
      notifications.forEach(notification => {
        if (!notification.read) {
          notificationSyncService.markAsReadLocally(notification.id);
        }
      });
    } else {
      // Envia comando diretamente para o servidor
      sendCommand('mark_all_notifications_as_read');
    }
  }, [sendCommand, enableSync, notifications]);

  // Remove uma notificação
  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notification) => notification.id !== id));

    if (enableSync) {
      // Remove localmente e adiciona à fila de sincronização
      notificationSyncService.deleteLocally(id);
    } else {
      // Envia comando diretamente para o servidor
      sendCommand('delete_notification', { notification_id: id });
    }
  }, [sendCommand, enableSync]);

  // Remove todas as notificações
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);

    if (enableSync) {
      // Remove todas localmente
      notificationSyncService.clearAllLocally();
    } else {
      // Envia comando diretamente para o servidor
      sendCommand('clear_all_notifications');
    }
  }, [sendCommand, enableSync]);

  // Força sincronização manual
  const forceSync = useCallback(() => {
    if (enableSync && !isLoading) {
      syncWithServer();
    }
  }, [enableSync, isLoading, syncWithServer]);

  // Obtém estatísticas de sincronização
  const getSyncStats = useCallback(() => {
    if (enableSync) {
      return notificationSyncService.getSyncStats();
    }
    return null;
  }, [enableSync]);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    // Funcionalidades de sincronização
    isLoading,
    lastSyncTime,
    forceSync,
    getSyncStats,
    hasUnsyncedData: enableSync ? notificationSyncService.hasUnsyncedData() : false,
  };
}