import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

interface Connection {
  connection_id: string;
  user_id?: string;
  ip_address: string;
  user_agent: string;
  connected_at: string;
  last_activity: string;
  channels: string[];
  message_count: number;
  bytes_sent: number;
  bytes_received: number;
  status: 'active' | 'idle' | 'disconnected';
}

interface ConnectionStats {
  total_connections: number;
  active_connections: number;
  idle_connections: number;
  authenticated_connections: number;
  anonymous_connections: number;
  total_channels: number;
  total_messages_sent: number;
  total_bytes_transferred: number;
  average_connection_duration: number;
  peak_connections: number;
  peak_connections_time?: string;
}

interface WebSocketConnectionsPanelProps {
  className?: string;
}

export const WebSocketConnectionsPanel: React.FC<WebSocketConnectionsPanelProps> = ({
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  
  const [connections, setConnections] = useState<Connection[]>([]);
  const [stats, setStats] = useState<ConnectionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'idle'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 segundos

  // Carregar dados
  const loadData = async () => {
    try {
      setError(null);
      
      // Carregar conexões e estatísticas em paralelo
      const [connectionsResponse, statsResponse] = await Promise.all([
        fetch('/api/v1/admin/websocket/connections'),
        fetch('/api/v1/admin/websocket/stats')
      ]);

      if (!connectionsResponse.ok || !statsResponse.ok) {
        throw new Error('Erro ao carregar dados');
      }

      const connectionsData = await connectionsResponse.json();
      const statsData = await statsResponse.json();

      setConnections(connectionsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh
  useEffect(() => {
    loadData();

    if (autoRefresh) {
      const interval = setInterval(loadData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Desconectar conexão
  const handleDisconnect = async (connectionId: string, reason: string = 'Admin disconnect') => {
    try {
      const response = await fetch(`/api/v1/admin/websocket/connections/${connectionId}/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      });

      if (response.ok) {
        // Atualizar lista
        setConnections(prev => 
          prev.map(conn => 
            conn.connection_id === connectionId 
              ? { ...conn, status: 'disconnected' as const }
              : conn
          )
        );
        
        // Fechar modal se estava aberto
        if (selectedConnection?.connection_id === connectionId) {
          setSelectedConnection(null);
        }
      } else {
        throw new Error('Erro ao desconectar');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao desconectar');
    }
  };

  // Desconectar usuário
  const handleDisconnectUser = async (userId: string) => {
    try {
      const response = await fetch(`/api/v1/admin/websocket/users/${userId}/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Admin disconnect user' })
      });

      if (response.ok) {
        // Recarregar dados
        await loadData();
      } else {
        throw new Error('Erro ao desconectar usuário');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao desconectar usuário');
    }
  };

  // Filtrar conexões
  const filteredConnections = connections.filter(conn => {
    const matchesSearch = !searchTerm || 
      conn.connection_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conn.user_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conn.ip_address.includes(searchTerm);
    
    const matchesStatus = statusFilter === 'all' || conn.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'idle':
        return 'text-yellow-600 bg-yellow-100';
      case 'disconnected':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMins % 60}m`;
    } else {
      return `${diffMins}m`;
    }
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando conexões...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            Conexões WebSocket
          </h2>
          
          <div className="flex items-center space-x-4">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-sm text-gray-500">
              {isConnected ? 'Conectado' : 'Desconectado'}
            </span>
            
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Auto-refresh
            </label>
            
            <button
              onClick={loadData}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Estatísticas */}
      {stats && (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total_connections}</div>
              <div className="text-xs text-gray-600">Total</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.active_connections}</div>
              <div className="text-xs text-gray-600">Ativas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.idle_connections}</div>
              <div className="text-xs text-gray-600">Inativas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.authenticated_connections}</div>
              <div className="text-xs text-gray-600">Autenticadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.total_channels}</div>
              <div className="text-xs text-gray-600">Canais</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.peak_connections}</div>
              <div className="text-xs text-gray-600">Pico</div>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar por ID, usuário ou IP..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">Todos os status</option>
            <option value="active">Ativas</option>
            <option value="idle">Inativas</option>
          </select>
        </div>
      </div>

      {/* Lista de conexões */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Conexão
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usuário
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Atividade
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Dados
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredConnections.map((connection) => (
              <tr key={connection.connection_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {connection.connection_id.slice(0, 8)}...
                    </div>
                    <div className="text-sm text-gray-500">
                      {connection.ip_address}
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {connection.user_id || 'Anônimo'}
                  </div>
                  <div className="text-sm text-gray-500">
                    {connection.channels.length} canais
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
                    {connection.status}
                  </span>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div>Conectado: {formatDuration(connection.connected_at)}</div>
                  <div>Última atividade: {formatDuration(connection.last_activity)}</div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div>{connection.message_count} mensagens</div>
                  <div>{formatBytes(connection.bytes_sent + connection.bytes_received)}</div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setSelectedConnection(connection)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Detalhes
                    </button>
                    
                    {connection.status !== 'disconnected' && (
                      <button
                        onClick={() => handleDisconnect(connection.connection_id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Desconectar
                      </button>
                    )}
                    
                    {connection.user_id && (
                      <button
                        onClick={() => handleDisconnectUser(connection.user_id!)}
                        className="text-orange-600 hover:text-orange-900"
                      >
                        Desconectar Usuário
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredConnections.length === 0 && (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.5-.816-6.207-2.175C5.25 12.09 5.25 11.438 5.25 10.5V6.75A2.25 2.25 0 017.5 4.5h9a2.25 2.25 0 012.25 2.25v3.75c0 .938 0 1.59-.543 2.325A7.962 7.962 0 0112 15z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhuma conexão encontrada
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm || statusFilter !== 'all' 
                ? 'Tente ajustar os filtros de busca.'
                : 'Não há conexões WebSocket ativas no momento.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Modal de detalhes */}
      {selectedConnection && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Detalhes da Conexão
              </h3>
              <button
                onClick={() => setSelectedConnection(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">ID da Conexão</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">{selectedConnection.connection_id}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <span className={`mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedConnection.status)}`}>
                    {selectedConnection.status}
                  </span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Usuário</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedConnection.user_id || 'Anônimo'}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">IP</label>
                  <p className="mt-1 text-sm text-gray-900 font-mono">{selectedConnection.ip_address}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Conectado em</label>
                  <p className="mt-1 text-sm text-gray-900">{new Date(selectedConnection.connected_at).toLocaleString()}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Última Atividade</label>
                  <p className="mt-1 text-sm text-gray-900">{new Date(selectedConnection.last_activity).toLocaleString()}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Mensagens</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedConnection.message_count}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Dados Transferidos</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {formatBytes(selectedConnection.bytes_sent + selectedConnection.bytes_received)}
                  </p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">User Agent</label>
                <p className="mt-1 text-sm text-gray-900 break-all">{selectedConnection.user_agent}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Canais Inscritos</label>
                <div className="mt-1 flex flex-wrap gap-2">
                  {selectedConnection.channels.map((channel, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {channel}
                    </span>
                  ))}
                  {selectedConnection.channels.length === 0 && (
                    <span className="text-sm text-gray-500">Nenhum canal</span>
                  )}
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              {selectedConnection.status !== 'disconnected' && (
                <button
                  onClick={() => {
                    handleDisconnect(selectedConnection.connection_id);
                    setSelectedConnection(null);
                  }}
                  className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Desconectar
                </button>
              )}
              
              <button
                onClick={() => setSelectedConnection(null)}
                className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="px-6 py-4 bg-red-50 border-t border-red-200">
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
  );
};