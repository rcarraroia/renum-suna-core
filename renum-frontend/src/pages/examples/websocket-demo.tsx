/**
 * Página de demonstração do WebSocket
 */

import React, { useState } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';
import { useWebSocketChannel } from '../../hooks/useWebSocketChannels';
import WebSocketAwareLayout from '../../components/layout/WebSocketAwareLayout';
import { WebSocketStatus, NotificationBadge } from '../../components/websocket';

/**
 * Página de demonstração do WebSocket
 */
export default function WebSocketDemo() {
  const { status, isConnected, sendCommand } = useWebSocketContext();
  const [message, setMessage] = useState('');
  const [channel, setChannel] = useState('demo');

  // Usa o hook de canal WebSocket
  const {
    messages,
    subscribers,
    isSubscribed,
    subscribeToChannel,
    unsubscribeFromChannel,
    sendMessage,
  } = useWebSocketChannel(channel, {
    autoSubscribe: true,
  });

  // Envia uma mensagem para o canal
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    sendMessage(message);
    setMessage('');
  };

  // Envia uma notificação de teste
  const sendTestNotification = () => {
    sendCommand('send_notification', {
      title: 'Notificação de teste',
      message: 'Esta é uma notificação de teste enviada pelo WebSocket.',
      type: 'info',
    });
  };

  return (
    <WebSocketAwareLayout>
      <h1 className="text-2xl font-bold mb-6">Demonstração do WebSocket</h1>

      {/* Status da conexão */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <h2 className="text-lg font-medium mb-4">Status da Conexão</h2>
        <div className="flex items-center space-x-4">
          <WebSocketStatus showStatusText={true} />
          <NotificationBadge />
        </div>
      </div>

      {/* Canal de chat */}
      <div className="bg-white shadow rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">Canal: {channel}</h2>
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
              placeholder="Nome do canal"
            />
            {isSubscribed ? (
              <button
                onClick={unsubscribeFromChannel}
                className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors text-sm"
                disabled={!isConnected}
              >
                Cancelar inscrição
              </button>
            ) : (
              <button
                onClick={subscribeToChannel}
                className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm"
                disabled={!isConnected}
              >
                Inscrever-se
              </button>
            )}
          </div>
        </div>

        {/* Lista de mensagens */}
        <div className="bg-gray-100 rounded-lg p-4 h-64 overflow-y-auto mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500">Nenhuma mensagem</div>
          ) : (
            <div className="space-y-2">
              {messages.map((msg, index) => (
                <div key={index} className="bg-white p-3 rounded shadow-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm">{msg.sender || 'Anônimo'}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(msg.timestamp || Date.now()).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm">{msg.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Formulário de envio */}
        <form onSubmit={handleSendMessage} className="flex">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="flex-1 border border-gray-300 rounded-l px-3 py-2"
            placeholder="Digite sua mensagem..."
            disabled={!isConnected || !isSubscribed}
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded-r hover:bg-blue-600 transition-colors"
            disabled={!isConnected || !isSubscribed}
          >
            Enviar
          </button>
        </form>
      </div>

      {/* Ações */}
      <div className="bg-white shadow rounded-lg p-4">
        <h2 className="text-lg font-medium mb-4">Ações</h2>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={sendTestNotification}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
            disabled={!isConnected}
          >
            Enviar notificação de teste
          </button>
          <button
            onClick={() => sendCommand('ping')}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
            disabled={!isConnected}
          >
            Enviar ping
          </button>
          <button
            onClick={() => sendCommand('get_stats')}
            className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors"
            disabled={!isConnected}
          >
            Obter estatísticas
          </button>
        </div>
      </div>
    </WebSocketAwareLayout>
  );
}