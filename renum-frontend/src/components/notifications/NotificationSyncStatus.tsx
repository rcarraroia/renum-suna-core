/**
 * Componente para exibir o status de sincronização de notificações
 */

import React from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';

interface NotificationSyncStatusProps {
  className?: string;
  showDetails?: boolean;
}

/**
 * Componente para exibir o status de sincronização de notificações
 */
const NotificationSyncStatus: React.FC<NotificationSyncStatusProps> = ({
  className = '',
  showDetails = false,
}) => {
  const { 
    isLoading, 
    lastSyncTime, 
    forceSync, 
    getSyncStats, 
    hasUnsyncedData 
  } = useWebSocketNotifications({ enableSync: true });

  const syncStats = getSyncStats();

  // Formata a data da última sincronização
  const formatLastSync = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) {
      return 'Agora mesmo';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m atrás`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours}h atrás`;
    } else {
      return date.toLocaleDateString();
    }
  };

  // Define a cor do status
  const getStatusColor = () => {
    if (isLoading) return 'text-yellow-600';
    if (hasUnsyncedData) return 'text-orange-600';
    return 'text-green-600';
  };

  // Define o ícone do status
  const getStatusIcon = () => {
    const iconClass = `h-4 w-4 ${getStatusColor()}`;
    
    if (isLoading) {
      return (
        <svg className={`${iconClass} animate-spin`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      );
    }
    
    if (hasUnsyncedData) {
      return (
        <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      );
    }
    
    return (
      <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    );
  };

  // Define o texto do status
  const getStatusText = () => {
    if (isLoading) return 'Sincronizando...';
    if (hasUnsyncedData) return 'Dados não sincronizados';
    return 'Sincronizado';
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      {/* Ícone e status */}
      <div className="flex items-center space-x-1">
        {getStatusIcon()}
        <span className={`text-sm ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>

      {/* Última sincronização */}
      <span className="text-xs text-gray-500">
        • {formatLastSync(lastSyncTime)}
      </span>

      {/* Botão de sincronização manual */}
      <button
        onClick={forceSync}
        disabled={isLoading}
        className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
        title="Sincronizar agora"
      >
        <svg className="h-3 w-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
        </svg>
      </button>

      {/* Detalhes de sincronização */}
      {showDetails && syncStats && (
        <div className="text-xs text-gray-500">
          ({syncStats.totalNotifications} total, {syncStats.unsyncedNotifications} não sync, {syncStats.pendingActions} pendentes)
        </div>
      )}
    </div>
  );
};

export default NotificationSyncStatus;