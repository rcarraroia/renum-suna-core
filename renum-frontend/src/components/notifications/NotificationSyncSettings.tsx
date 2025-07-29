/**
 * Componente para configurações avançadas de sincronização de notificações
 */

import React, { useState } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { notificationSyncService } from '../../services/notification-sync-service';
import NotificationSyncStatus from './NotificationSyncStatus';

interface NotificationSyncSettingsProps {
  className?: string;
}

/**
 * Componente para configurações avançadas de sincronização de notificações
 */
const NotificationSyncSettings: React.FC<NotificationSyncSettingsProps> = ({
  className = '',
}) => {
  const { forceSync, getSyncStats } = useWebSocketNotifications({ enableSync: true });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);

  const syncStats = getSyncStats();

  // Limpa todos os dados de sincronização
  const handleClearSyncData = () => {
    if (confirmClear) {
      notificationSyncService.clearSyncData();
      setConfirmClear(false);
      window.location.reload(); // Recarrega para refletir as mudanças
    } else {
      setConfirmClear(true);
      setTimeout(() => setConfirmClear(false), 5000); // Auto-cancela após 5 segundos
    }
  };

  // Exporta dados de sincronização
  const handleExportData = () => {
    const data = {
      notifications: notificationSyncService.getStoredNotifications(),
      syncState: notificationSyncService.getSyncState(),
      stats: syncStats,
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notifications-sync-data-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Formata bytes para exibição
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Calcula o tamanho aproximado dos dados armazenados
  const getStorageSize = () => {
    try {
      if (typeof window === 'undefined') return 0;
      const notificationsData = localStorage.getItem('renum_notifications') || '';
      const syncStateData = localStorage.getItem('renum_notifications_sync') || '';
      return notificationsData.length + syncStateData.length;
    } catch {
      return 0;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          Sincronização de Notificações
        </h2>
        <p className="text-sm text-gray-600">
          Configure como as notificações são sincronizadas entre dispositivos.
        </p>
      </div>

      {/* Status de sincronização */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Status Atual</h3>
        <NotificationSyncStatus showDetails={true} />
      </div>

      {/* Estatísticas */}
      {syncStats && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Estatísticas</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {syncStats.totalNotifications}
              </div>
              <div className="text-xs text-blue-800">Total</div>
            </div>
            
            <div className="bg-orange-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {syncStats.unsyncedNotifications}
              </div>
              <div className="text-xs text-orange-800">Não sincronizadas</div>
            </div>
            
            <div className="bg-yellow-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {syncStats.pendingActions}
              </div>
              <div className="text-xs text-yellow-800">Ações pendentes</div>
            </div>
            
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {formatBytes(getStorageSize())}
              </div>
              <div className="text-xs text-gray-800">Armazenamento</div>
            </div>
          </div>
        </div>
      )}

      {/* Ações rápidas */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Ações</h3>
        
        <div className="flex flex-wrap gap-2">
          <button
            onClick={forceSync}
            className="bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Sincronizar Agora
          </button>
          
          <button
            onClick={handleExportData}
            className="bg-gray-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            Exportar Dados
          </button>
          
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="bg-gray-200 text-gray-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
          >
            {showAdvanced ? 'Ocultar' : 'Mostrar'} Avançado
          </button>
        </div>
      </div>

      {/* Configurações avançadas */}
      {showAdvanced && (
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Configurações Avançadas
          </h3>
          
          <div className="space-y-4">
            {/* Informações de armazenamento */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">
                Armazenamento Local
              </h4>
              <p className="text-sm text-yellow-700 mb-3">
                As notificações são armazenadas localmente no seu navegador para permitir 
                acesso offline e sincronização entre sessões.
              </p>
              
              <div className="text-xs text-yellow-600 space-y-1">
                <div>• Tamanho atual: {formatBytes(getStorageSize())}</div>
                <div>• Limite máximo: 100 notificações</div>
                <div>• Limpeza automática: notificações antigas são removidas automaticamente</div>
              </div>
            </div>

            {/* Ações perigosas */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-red-800 mb-2">
                Zona de Perigo
              </h4>
              <p className="text-sm text-red-700 mb-3">
                Estas ações são irreversíveis e podem causar perda de dados.
              </p>
              
              <button
                onClick={handleClearSyncData}
                className={`px-3 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  confirmClear
                    ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
                    : 'bg-red-100 text-red-800 hover:bg-red-200 focus:ring-red-500'
                }`}
              >
                {confirmClear ? 'Confirmar: Limpar Todos os Dados' : 'Limpar Dados de Sincronização'}
              </button>
              
              {confirmClear && (
                <p className="mt-2 text-xs text-red-600">
                  Clique novamente para confirmar. Esta ação removerá todas as notificações 
                  e dados de sincronização armazenados localmente.
                </p>
              )}
            </div>

            {/* Informações técnicas */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-2">
                Informações Técnicas
              </h4>
              
              <div className="text-xs text-gray-600 space-y-1">
                <div>• Sincronização automática: a cada 30 segundos quando conectado</div>
                <div>• Armazenamento: localStorage do navegador</div>
                <div>• Conflitos: versão do servidor tem prioridade</div>
                <div>• Offline: ações são enfileiradas e sincronizadas quando conectar</div>
                <div>• Privacidade: dados ficam apenas no seu dispositivo e servidor</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSyncSettings;