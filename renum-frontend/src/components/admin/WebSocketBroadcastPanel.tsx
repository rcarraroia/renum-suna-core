import React, { useState } from 'react';

interface BroadcastMessage {
  id: string;
  message: string;
  target_type: 'all' | 'user' | 'channel';
  target_id?: string;
  sent_count: number;
  timestamp: string;
  status: 'sending' | 'sent' | 'failed';
}

interface WebSocketBroadcastPanelProps {
  className?: string;
}

export const WebSocketBroadcastPanel: React.FC<WebSocketBroadcastPanelProps> = ({
  className = ''
}) => {
  const [message, setMessage] = useState('');
  const [targetType, setTargetType] = useState<'all' | 'user' | 'channel'>('all');
  const [targetId, setTargetId] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal');
  const [sending, setSending] = useState(false);
  const [broadcastHistory, setBroadcastHistory] = useState<BroadcastMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSendBroadcast = async () => {
    if (!message.trim()) {
      setError('Mensagem não pode estar vazia');
      return;
    }

    if (targetType !== 'all' && !targetId.trim()) {
      setError('ID do alvo é obrigatório para este tipo de broadcast');
      return;
    }

    try {
      setSending(true);
      setError(null);

      const broadcastData = {
        message: message.trim(),
        target_type: targetType,
        target_id: targetType === 'all' ? undefined : targetId.trim(),
        priority
      };

      const response = await fetch('/api/v1/admin/websocket/broadcast', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(broadcastData)
      });

      if (!response.ok) {
        throw new Error(`Erro ao enviar broadcast: ${response.statusText}`);
      }

      const result = await response.json();

      // Adicionar ao histórico
      const newBroadcast: BroadcastMessage = {
        id: Date.now().toString(),
        message: message.trim(),
        target_type: targetType,
        target_id: targetType === 'all' ? undefined : targetId.trim(),
        sent_count: result.sent_count,
        timestamp: new Date().toISOString(),
        status: 'sent'
      };

      setBroadcastHistory(prev => [newBroadcast, ...prev.slice(0, 19)]); // Manter apenas 20 últimas

      // Limpar formulário
      setMessage('');
      setTargetId('');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setSending(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'normal':
        return 'text-blue-600 bg-blue-100';
      case 'low':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTargetTypeLabel = (type: string) => {
    switch (type) {
      case 'all':
        return 'Todas as conexões';
      case 'user':
        return 'Usuário específico';
      case 'channel':
        return 'Canal específico';
      default:
        return type;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">
          Broadcast Administrativo
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Envie mensagens administrativas para conexões WebSocket
        </p>
      </div>

      {/* Formulário de broadcast */}
      <div className="p-6 border-b border-gray-200">
        <div className="space-y-4">
          {/* Mensagem */}
          <div>
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
              Mensagem
            </label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Digite sua mensagem administrativa..."
              disabled={sending}
            />
          </div>

          {/* Configurações de alvo */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="targetType" className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Alvo
              </label>
              <select
                id="targetType"
                value={targetType}
                onChange={(e) => setTargetType(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={sending}
              >
                <option value="all">Todas as conexões</option>
                <option value="user">Usuário específico</option>
                <option value="channel">Canal específico</option>
              </select>
            </div>

            {targetType !== 'all' && (
              <div>
                <label htmlFor="targetId" className="block text-sm font-medium text-gray-700 mb-2">
                  {targetType === 'user' ? 'ID do Usuário' : 'Nome do Canal'}
                </label>
                <input
                  type="text"
                  id="targetId"
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={targetType === 'user' ? 'user123' : 'team_456'}
                  disabled={sending}
                />
              </div>
            )}
          </div>

          {/* Prioridade */}
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-2">
              Prioridade
            </label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={sending}
            >
              <option value="low">Baixa</option>
              <option value="normal">Normal</option>
              <option value="high">Alta</option>
            </select>
          </div>

          {/* Botão de envio */}
          <div className="flex justify-end">
            <button
              onClick={handleSendBroadcast}
              disabled={sending || !message.trim()}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Enviando...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                  Enviar Broadcast
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-red-800 font-medium">{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Histórico de broadcasts */}
      <div className="p-6">
        <h4 className="text-md font-medium text-gray-900 mb-4">
          Histórico de Broadcasts
          {broadcastHistory.length > 0 && (
            <span className="ml-2 text-sm text-gray-500">
              ({broadcastHistory.length})
            </span>
          )}
        </h4>

        {broadcastHistory.length === 0 ? (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhum broadcast enviado
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Os broadcasts enviados aparecerão aqui.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {broadcastHistory.map((broadcast) => (
              <div
                key={broadcast.id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(priority)}`}>
                        {priority}
                      </span>
                      
                      <span className="text-sm text-gray-600">
                        {getTargetTypeLabel(broadcast.target_type)}
                        {broadcast.target_id && `: ${broadcast.target_id}`}
                      </span>
                      
                      <span className="text-sm text-gray-500">
                        • {broadcast.sent_count} conexões
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-900 mb-2">
                      {broadcast.message}
                    </p>
                    
                    <div className="text-xs text-gray-500">
                      {formatTimestamp(broadcast.timestamp)}
                    </div>
                  </div>
                  
                  <div className="ml-4">
                    {broadcast.status === 'sent' ? (
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : broadcast.status === 'failed' ? (
                      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Templates de mensagem */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <h5 className="text-sm font-medium text-gray-700 mb-3">Templates Rápidos</h5>
        <div className="flex flex-wrap gap-2">
          {[
            'Sistema entrará em manutenção em 5 minutos',
            'Manutenção concluída. Sistema operacional',
            'Nova versão disponível. Atualize sua página',
            'Problemas de conectividade detectados',
            'Sistema funcionando normalmente'
          ].map((template, index) => (
            <button
              key={index}
              onClick={() => setMessage(template)}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={sending}
            >
              {template}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};