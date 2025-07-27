import React, { useState, useEffect } from 'react';

interface ChannelInfo {
  name: string;
  connection_count: number;
  authenticated_users: string[];
  authenticated_user_count: number;
  anonymous_connections: number;
  created_at: string;
  last_activity: string;
}

interface WebSocketChannelsPanelProps {
  className?: string;
}

export const WebSocketChannelsPanel: React.FC<WebSocketChannelsPanelProps> = ({
  className = ''
}) => {
  const [channels, setChannels] = useState<Record<string, ChannelInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'connections' | 'activity'>('connections');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);

  const loadChannels = async () => {
    try {
      setError(null);
      const response = await fetch('/api/v1/admin/websocket/channels');
      
      if (!response.ok) {
        throw new Error('Erro ao carregar canais');
      }

      const data = await response.json();
      setChannels(data.channels || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChannels();
    
    // Auto-refresh a cada 10 segundos
    const interval = setInterval(loadChannels, 10000);
    return () => clearInterval(interval);
  }, []);

  const getChannelType = (channelName: string) => {
    if (channelName.startsWith('user_')) return 'user';
    if (channelName.startsWith('team_')) return 'team';
    if (channelName.startsWith('execution_')) return 'execution';
    if (channelName.startsWith('admin_')) return 'admin';
    return 'other';
  };

  const getChannelTypeColor = (type: string) => {
    switch (type) {
      case 'user':
        return 'bg-blue-100 text-blue-800';
      case 'team':
        return 'bg-green-100 text-green-800';
      case 'execution':
        return 'bg-purple-100 text-purple-800';
      case 'admin':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
      return `${diffDays}d atrás`;
    } else if (diffHours > 0) {
      return `${diffHours}h atrás`;
    } else if (diffMins > 0) {
      return `${diffMins}m atrás`;
    } else {
      return 'agora mesmo';
    }
  };

  const getSortedChannels = () => {
    const channelList = Object.entries(channels).map(([name, info]) => ({
      ...info,
      name
    }));

    // Filtrar por busca
    const filtered = channelList.filter(channel =>
      channel.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Ordenar
    return filtered.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name;
          bValue = b.name;
          break;
        case 'connections':
          aValue = a.connection_count;
          bValue = b.connection_count;
          break;
        case 'activity':
          aValue = new Date(a.last_activity).getTime();
          bValue = new Date(b.last_activity).getTime();
          break;
        default:
          return 0;
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  };

  const handleSort = (field: 'name' | 'connections' | 'activity') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getSortIcon = (field: string) => {
    if (sortBy !== field) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }

    return sortOrder === 'asc' ? (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h9m5-4v12m0 0l-4-4m4 4l4-4" />
      </svg>
    );
  };

  const sortedChannels = getSortedChannels();

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando canais...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Canais WebSocket
            <span className="ml-2 text-sm text-gray-500">
              ({Object.keys(channels).length} canais)
            </span>
          </h3>
          
          <button
            onClick={loadChannels}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Atualizar
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar canais..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {Object.values(channels).reduce((sum, ch) => sum + ch.connection_count, 0)}
            </div>
            <div className="text-xs text-gray-600">Total Conexões</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {Object.values(channels).reduce((sum, ch) => sum + ch.authenticated_user_count, 0)}
            </div>
            <div className="text-xs text-gray-600">Usuários Autenticados</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">
              {Object.values(channels).reduce((sum, ch) => sum + ch.anonymous_connections, 0)}
            </div>
            <div className="text-xs text-gray-600">Conexões Anônimas</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {Object.keys(channels).length}
            </div>
            <div className="text-xs text-gray-600">Canais Ativos</div>
          </div>
        </div>
      </div>

      {/* Tabela de canais */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center">
                  Canal
                  {getSortIcon('name')}
                </div>
              </th>
              
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tipo
              </th>
              
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('connections')}
              >
                <div className="flex items-center">
                  Conexões
                  {getSortIcon('connections')}
                </div>
              </th>
              
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usuários
              </th>
              
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('activity')}
              >
                <div className="flex items-center">
                  Última Atividade
                  {getSortIcon('activity')}
                </div>
              </th>
              
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedChannels.map((channel) => {
              const channelType = getChannelType(channel.name);
              
              return (
                <tr key={channel.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 font-mono">
                      {channel.name}
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getChannelTypeColor(channelType)}`}>
                      {channelType}
                    </span>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {channel.connection_count}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div>Autenticados: {channel.authenticated_user_count}</div>
                    <div>Anônimos: {channel.anonymous_connections}</div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimeAgo(channel.last_activity)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedChannel(channel.name)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Detalhes
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        
        {sortedChannels.length === 0 && (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhum canal encontrado
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm 
                ? 'Tente ajustar o termo de busca.'
                : 'Não há canais WebSocket ativos no momento.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Modal de detalhes do canal */}
      {selectedChannel && channels[selectedChannel] && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Detalhes do Canal
              </h3>
              <button
                onClick={() => setSelectedChannel(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nome do Canal</label>
                <p className="mt-1 text-sm text-gray-900 font-mono bg-gray-100 p-2 rounded">
                  {selectedChannel}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tipo</label>
                  <span className={`mt-1 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getChannelTypeColor(getChannelType(selectedChannel))}`}>
                    {getChannelType(selectedChannel)}
                  </span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Total de Conexões</label>
                  <p className="mt-1 text-sm text-gray-900">{channels[selectedChannel].connection_count}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Usuários Autenticados</label>
                  <p className="mt-1 text-sm text-gray-900">{channels[selectedChannel].authenticated_user_count}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Conexões Anônimas</label>
                  <p className="mt-1 text-sm text-gray-900">{channels[selectedChannel].anonymous_connections}</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Criado em</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Date(channels[selectedChannel].created_at).toLocaleString()}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Última Atividade</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Date(channels[selectedChannel].last_activity).toLocaleString()}
                  </p>
                </div>
              </div>
              
              {channels[selectedChannel].authenticated_users.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Usuários Conectados ({channels[selectedChannel].authenticated_users.length})
                  </label>
                  <div className="max-h-32 overflow-y-auto bg-gray-50 rounded p-3">
                    <div className="flex flex-wrap gap-2">
                      {channels[selectedChannel].authenticated_users.map((userId, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {userId}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedChannel(null)}
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