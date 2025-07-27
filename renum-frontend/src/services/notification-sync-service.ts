/**
 * Serviço de sincronização de notificações
 */

import { WebSocketNotification } from '../types/websocket';

interface StoredNotification extends WebSocketNotification {
  synced: boolean;
  lastModified: string;
}

interface SyncState {
  lastSyncTime: string;
  pendingActions: PendingAction[];
}

interface PendingAction {
  id: string;
  type: 'mark_read' | 'delete' | 'create';
  notificationId: string;
  timestamp: string;
  data?: any;
}

/**
 * Serviço para sincronização de notificações entre cliente e servidor
 */
export class NotificationSyncService {
  private storageKey = 'renum_notifications';
  private syncStateKey = 'renum_notifications_sync';
  private maxStoredNotifications = 100;

  /**
   * Obtém todas as notificações armazenadas localmente
   */
  getStoredNotifications(): StoredNotification[] {
    try {
      const stored = localStorage.getItem(this.storageKey);
      if (!stored) return [];
      
      const notifications = JSON.parse(stored) as StoredNotification[];
      return notifications.slice(0, this.maxStoredNotifications);
    } catch (error) {
      console.error('Erro ao carregar notificações do localStorage:', error);
      return [];
    }
  }

  /**
   * Salva notificações no armazenamento local
   */
  saveNotifications(notifications: StoredNotification[]): void {
    try {
      // Limita o número de notificações armazenadas
      const limited = notifications
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, this.maxStoredNotifications);
      
      localStorage.setItem(this.storageKey, JSON.stringify(limited));
    } catch (error) {
      console.error('Erro ao salvar notificações no localStorage:', error);
    }
  }

  /**
   * Adiciona uma nova notificação ao armazenamento local
   */
  addNotification(notification: WebSocketNotification, synced: boolean = true): void {
    const stored = this.getStoredNotifications();
    
    // Verifica se a notificação já existe
    const existingIndex = stored.findIndex(n => n.id === notification.id);
    
    const storedNotification: StoredNotification = {
      ...notification,
      synced,
      lastModified: new Date().toISOString(),
    };
    
    if (existingIndex >= 0) {
      // Atualiza notificação existente
      stored[existingIndex] = storedNotification;
    } else {
      // Adiciona nova notificação
      stored.unshift(storedNotification);
    }
    
    this.saveNotifications(stored);
  }

  /**
   * Atualiza uma notificação no armazenamento local
   */
  updateNotification(id: string, updates: Partial<WebSocketNotification>, synced: boolean = false): void {
    const stored = this.getStoredNotifications();
    const index = stored.findIndex(n => n.id === id);
    
    if (index >= 0) {
      stored[index] = {
        ...stored[index],
        ...updates,
        synced,
        lastModified: new Date().toISOString(),
      };
      
      this.saveNotifications(stored);
    }
  }

  /**
   * Remove uma notificação do armazenamento local
   */
  removeNotification(id: string): void {
    const stored = this.getStoredNotifications();
    const filtered = stored.filter(n => n.id !== id);
    this.saveNotifications(filtered);
  }

  /**
   * Marca uma notificação como lida localmente
   */
  markAsReadLocally(id: string): void {
    this.updateNotification(id, { read: true });
    this.addPendingAction('mark_read', id);
  }

  /**
   * Remove uma notificação localmente
   */
  deleteLocally(id: string): void {
    this.removeNotification(id);
    this.addPendingAction('delete', id);
  }

  /**
   * Limpa todas as notificações localmente
   */
  clearAllLocally(): void {
    const stored = this.getStoredNotifications();
    stored.forEach(notification => {
      this.addPendingAction('delete', notification.id);
    });
    
    localStorage.removeItem(this.storageKey);
  }

  /**
   * Obtém o estado de sincronização
   */
  getSyncState(): SyncState {
    try {
      const stored = localStorage.getItem(this.syncStateKey);
      if (!stored) {
        return {
          lastSyncTime: new Date(0).toISOString(),
          pendingActions: [],
        };
      }
      
      return JSON.parse(stored);
    } catch (error) {
      console.error('Erro ao carregar estado de sincronização:', error);
      return {
        lastSyncTime: new Date(0).toISOString(),
        pendingActions: [],
      };
    }
  }

  /**
   * Salva o estado de sincronização
   */
  saveSyncState(state: SyncState): void {
    try {
      localStorage.setItem(this.syncStateKey, JSON.stringify(state));
    } catch (error) {
      console.error('Erro ao salvar estado de sincronização:', error);
    }
  }

  /**
   * Adiciona uma ação pendente
   */
  addPendingAction(type: PendingAction['type'], notificationId: string, data?: any): void {
    const state = this.getSyncState();
    
    // Remove ações pendentes duplicadas para a mesma notificação
    state.pendingActions = state.pendingActions.filter(
      action => !(action.notificationId === notificationId && action.type === type)
    );
    
    // Adiciona nova ação
    state.pendingActions.push({
      id: `${type}_${notificationId}_${Date.now()}`,
      type,
      notificationId,
      timestamp: new Date().toISOString(),
      data,
    });
    
    this.saveSyncState(state);
  }

  /**
   * Remove uma ação pendente
   */
  removePendingAction(actionId: string): void {
    const state = this.getSyncState();
    state.pendingActions = state.pendingActions.filter(action => action.id !== actionId);
    this.saveSyncState(state);
  }

  /**
   * Obtém ações pendentes
   */
  getPendingActions(): PendingAction[] {
    return this.getSyncState().pendingActions;
  }

  /**
   * Atualiza o timestamp da última sincronização
   */
  updateLastSyncTime(): void {
    const state = this.getSyncState();
    state.lastSyncTime = new Date().toISOString();
    this.saveSyncState(state);
  }

  /**
   * Sincroniza notificações com o servidor
   */
  async syncWithServer(
    fetchNotifications: (since: string) => Promise<WebSocketNotification[]>,
    sendAction: (action: PendingAction) => Promise<boolean>
  ): Promise<void> {
    try {
      const state = this.getSyncState();
      
      // 1. Busca notificações do servidor desde a última sincronização
      const serverNotifications = await fetchNotifications(state.lastSyncTime);
      
      // 2. Mescla notificações do servidor com as locais
      this.mergeServerNotifications(serverNotifications);
      
      // 3. Envia ações pendentes para o servidor
      await this.syncPendingActions(sendAction);
      
      // 4. Atualiza timestamp da última sincronização
      this.updateLastSyncTime();
      
      console.log('Sincronização de notificações concluída');
    } catch (error) {
      console.error('Erro na sincronização de notificações:', error);
      throw error;
    }
  }

  /**
   * Mescla notificações do servidor com as locais
   */
  private mergeServerNotifications(serverNotifications: WebSocketNotification[]): void {
    const stored = this.getStoredNotifications();
    const storedMap = new Map(stored.map(n => [n.id, n]));
    
    serverNotifications.forEach(serverNotification => {
      const localNotification = storedMap.get(serverNotification.id);
      
      if (!localNotification) {
        // Nova notificação do servidor
        this.addNotification(serverNotification, true);
      } else if (!localNotification.synced) {
        // Notificação local não sincronizada - mantém a versão local
        return;
      } else {
        // Atualiza com a versão do servidor se for mais recente
        const serverTime = new Date(serverNotification.created_at).getTime();
        const localTime = new Date(localNotification.lastModified).getTime();
        
        if (serverTime > localTime) {
          this.addNotification(serverNotification, true);
        }
      }
    });
  }

  /**
   * Sincroniza ações pendentes com o servidor
   */
  private async syncPendingActions(sendAction: (action: PendingAction) => Promise<boolean>): Promise<void> {
    const pendingActions = this.getPendingActions();
    
    for (const action of pendingActions) {
      try {
        const success = await sendAction(action);
        
        if (success) {
          // Remove a ação pendente se foi executada com sucesso
          this.removePendingAction(action.id);
          
          // Marca a notificação como sincronizada
          if (action.type !== 'delete') {
            const stored = this.getStoredNotifications();
            const notification = stored.find(n => n.id === action.notificationId);
            if (notification) {
              notification.synced = true;
              this.saveNotifications(stored);
            }
          }
        }
      } catch (error) {
        console.error(`Erro ao sincronizar ação ${action.id}:`, error);
        // Mantém a ação pendente para tentar novamente depois
      }
    }
  }

  /**
   * Verifica se há dados não sincronizados
   */
  hasUnsyncedData(): boolean {
    const stored = this.getStoredNotifications();
    const hasUnsyncedNotifications = stored.some(n => !n.synced);
    const hasPendingActions = this.getPendingActions().length > 0;
    
    return hasUnsyncedNotifications || hasPendingActions;
  }

  /**
   * Obtém estatísticas de sincronização
   */
  getSyncStats(): {
    totalNotifications: number;
    unsyncedNotifications: number;
    pendingActions: number;
    lastSyncTime: string;
  } {
    const stored = this.getStoredNotifications();
    const state = this.getSyncState();
    
    return {
      totalNotifications: stored.length,
      unsyncedNotifications: stored.filter(n => !n.synced).length,
      pendingActions: state.pendingActions.length,
      lastSyncTime: state.lastSyncTime,
    };
  }

  /**
   * Limpa todos os dados de sincronização
   */
  clearSyncData(): void {
    localStorage.removeItem(this.storageKey);
    localStorage.removeItem(this.syncStateKey);
  }
}

// Instância singleton do serviço
export const notificationSyncService = new NotificationSyncService();