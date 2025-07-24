/**
 * Página de demonstração dos componentes de notificações
 */

import React, { useState } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import WebSocketAwareLayout from '../../components/layout/WebSocketAwareLayout';
import {
  NotificationList,
  NotificationDropdown,
  NotificationToast,
  NotificationSettings,
  NotificationSyncSettings,
} from '../../components/notifications';

/**
 * Página de demonstração dos componentes de notificações
 */
export default function NotificationsDemo() {
  const { sendCommand, isConnected } = useWebSocketContext();
  const [selectedType, setSelectedType] = useState<'info' | 'success' | 'warning' | 'error'>('info');
  const [title, setTitle] = useState('Notificação de teste');
  const [message, setMessage] = useState('Esta é uma notificação de teste enviada via WebSocket.');

  // Envia uma notificação de teste
  const sendTestNotification = () => {
    if (!isConnected) {
      alert('WebSocket não está conectado');
      return;
    }

    sendCommand('send_test_notification', {
      type: selectedType,
      title,
      message,
      action: {
        type: 'url',
        payload: 'https://example.com',
      },
    });

    // Limpa os campos
    setTitle('Notificação de teste');
    setMessage('Esta é uma notificação de teste enviada via WebSocket.');
  };

  // Envia múltiplas notificações de teste
  const sendMultipleNotifications = () => {
    if (!isConnected) {
      alert('WebSocket não está conectado');
      return;
    }

    const types: Array<'info' | 'success' | 'warning' | 'error'> = ['info', 'success', 'warning', 'error'];
    
    types.forEach((type, index) => {
      setTimeout(() => {
        sendCommand('send_test_notification', {
          type,
          title: `Notificação ${type}`,
          message: `Esta é uma notificação do tipo ${type} (${index + 1}/4)`,
        });
      }, index * 1000);
    });
  };

  return (
    <WebSocketAwareLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Demonstração de Notificações
          </h1>
          <p className="text-gray-600">
            Esta página demonstra todos os componentes de notificações disponíveis.
          </p>
        </div>

        {/* Controles de teste */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Enviar Notificação de Teste
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo
              </label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value as any)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="info">Info</option>
                <option value="success">Success</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Título
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mensagem
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={sendTestNotification}
              disabled={!isConnected}
              className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Enviar Notificação
            </button>
            
            <button
              onClick={sendMultipleNotifications}
              disabled={!isConnected}
              className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Enviar Múltiplas
            </button>
          </div>
          
          {!isConnected && (
            <p className="mt-2 text-sm text-red-600">
              WebSocket não está conectado. Conecte-se para enviar notificações.
            </p>
          )}
        </div>

        {/* Componentes de demonstração */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Lista de notificações */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Lista de Notificações
            </h2>
            <NotificationList maxNotifications={10} />
          </div>

          {/* Configurações */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Configurações de Notificações
            </h2>
            <NotificationSettings />
          </div>
        </div>

        {/* Configurações de sincronização */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Sincronização de Notificações
          </h2>
          <NotificationSyncSettings />
        </div>

        {/* Informações sobre os componentes */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Componentes Disponíveis
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">NotificationDropdown</h3>
              <p className="text-sm text-gray-600 mb-2">
                Dropdown de notificações no cabeçalho (visível no canto superior direito).
              </p>
              <div className="flex justify-end">
                <NotificationDropdown />
              </div>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">NotificationToast</h3>
              <p className="text-sm text-gray-600">
                Toasts que aparecem automaticamente para novas notificações (canto superior direito da tela).
              </p>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">NotificationList</h3>
              <p className="text-sm text-gray-600">
                Lista completa de notificações com filtros e ordenação (mostrada acima).
              </p>
            </div>
          </div>
        </div>

        {/* Instruções */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-medium text-blue-900 mb-2">
            Como Testar
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
            <li>Certifique-se de que o WebSocket está conectado (indicador verde no cabeçalho)</li>
            <li>Use o formulário acima para enviar notificações de teste</li>
            <li>Observe os toasts aparecerem no canto superior direito</li>
            <li>Clique no ícone de notificações no cabeçalho para ver o dropdown</li>
            <li>Use a lista de notificações para gerenciar todas as notificações</li>
            <li>Configure suas preferências na seção de configurações</li>
          </ol>
        </div>
      </div>

      {/* Toast de notificações */}
      <NotificationToast />
    </WebSocketAwareLayout>
  );
}