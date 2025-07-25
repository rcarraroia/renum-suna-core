import React, { useState, useEffect } from 'react';

interface RateLimitRule {
  id: string;
  name: string;
  type: 'global' | 'user' | 'ip' | 'channel';
  target?: string;
  limit: number;
  window_seconds: number;
  action: 'throttle' | 'disconnect' | 'block';
  enabled: boolean;
  created_at: string;
  violations_count: number;
}

interface RateLimitStats {
  total_rules: number;
  active_rules: number;
  total_violations: number;
  violations_last_hour: number;
  blocked_connections: number;
  throttled_connections: number;
}

interface WebSocketRateLimitPanelProps {
  className?: string;
}

export const WebSocketRateLimitPanel: React.FC<WebSocketRateLimitPanelProps> = ({
  className = ''
}) => {
  const [rules, setRules] = useState<RateLimitRule[]>([]);
  const [stats, setStats] = useState<RateLimitStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRule, setEditingRule] = useState<RateLimitRule | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'global' as 'global' | 'user' | 'ip' | 'channel',
    target: '',
    limit: 100,
    window_seconds: 60,
    action: 'throttle' as 'throttle' | 'disconnect' | 'block',
    enabled: true
  });

  const loadData = async () => {
    try {
      setError(null);
      
      const [rulesResponse, statsResponse] = await Promise.all([
        fetch('/api/v1/admin/websocket/rate-limits'),
        fetch('/api/v1/admin/websocket/rate-limits/stats')
      ]);

      if (!rulesResponse.ok || !statsResponse.ok) {
        throw new Error('Erro ao carregar dados');
      }

      const rulesData = await rulesResponse.json();
      const statsData = await statsResponse.json();

      setRules(rulesData.rules || []);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateRule = async () => {
    try {
      setError(null);
      
      const response = await fetch('/api/v1/admin/websocket/rate-limits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Erro ao criar regra');
      }

      await loadData();
      setShowCreateForm(false);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar regra');
    }
  };

  const handleUpdateRule = async (ruleId: string) => {
    try {
      setError(null);
      
      const response = await fetch(`/api/v1/admin/websocket/rate-limits/${ruleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Erro ao atualizar regra');
      }

      await loadData();
      setEditingRule(null);
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar regra');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Tem certeza que deseja excluir esta regra?')) {
      return;
    }

    try {
      setError(null);
      
      const response = await fetch(`/api/v1/admin/websocket/rate-limits/${ruleId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Erro ao excluir regra');
      }

      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao excluir regra');
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      setError(null);
      
      const response = await fetch(`/api/v1/admin/websocket/rate-limits/${ruleId}/toggle`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled })
      });

      if (!response.ok) {
        throw new Error('Erro ao alterar status da regra');
      }

      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao alterar status');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'global',
      target: '',
      limit: 100,
      window_seconds: 60,
      action: 'throttle',
      enabled: true
    });
  };

  const startEdit = (rule: RateLimitRule) => {
    setFormData({
      name: rule.name,
      type: rule.type,
      target: rule.target || '',
      limit: rule.limit,
      window_seconds: rule.window_seconds,
      action: rule.action,
      enabled: rule.enabled
    });
    setEditingRule(rule);
    setShowCreateForm(true);
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'global':
        return 'bg-blue-100 text-blue-800';
      case 'user':
        return 'bg-green-100 text-green-800';
      case 'ip':
        return 'bg-yellow-100 text-yellow-800';
      case 'channel':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'throttle':
        return 'bg-yellow-100 text-yellow-800';
      case 'disconnect':
        return 'bg-orange-100 text-orange-800';
      case 'block':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando controles de taxa...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Controles de Limitação de Taxa
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Gerencie limites de taxa para conexões WebSocket
            </p>
          </div>
          
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nova Regra
          </button>
        </div>
      </div>

      {/* Estatísticas */}
      {stats && (
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.total_rules}</div>
              <div className="text-xs text-gray-600">Total de Regras</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.active_rules}</div>
              <div className="text-xs text-gray-600">Regras Ativas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{stats.total_violations}</div>
              <div className="text-xs text-gray-600">Total Violações</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.violations_last_hour}</div>
              <div className="text-xs text-gray-600">Última Hora</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.blocked_connections}</div>
              <div className="text-xs text-gray-600">Bloqueadas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.throttled_connections}</div>
              <div className="text-xs text-gray-600">Limitadas</div>
            </div>
          </div>
        </div>
      )}

      {/* Lista de regras */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Regra
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Limite
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ação
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Violações
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Ações
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rules.map((rule) => (
              <tr key={rule.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{rule.name}</div>
                    {rule.target && (
                      <div className="text-sm text-gray-500">Alvo: {rule.target}</div>
                    )}
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTypeColor(rule.type)}`}>
                    {rule.type}
                  </span>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rule.limit} / {rule.window_seconds}s
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(rule.action)}`}>
                    {rule.action}
                  </span>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rule.violations_count}
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={rule.enabled}
                      onChange={(e) => handleToggleRule(rule.id, e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-600">
                      {rule.enabled ? 'Ativa' : 'Inativa'}
                    </span>
                  </label>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => startEdit(rule)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => handleDeleteRule(rule.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {rules.length === 0 && (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhuma regra configurada
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Crie regras de limitação de taxa para controlar o uso do WebSocket.
            </p>
          </div>
        )}
      </div>

      {/* Modal de criação/edição */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                {editingRule ? 'Editar Regra' : 'Nova Regra de Rate Limit'}
              </h3>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingRule(null);
                  resetForm();
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nome da Regra</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ex: Limite global de mensagens"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tipo</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="global">Global</option>
                    <option value="user">Por Usuário</option>
                    <option value="ip">Por IP</option>
                    <option value="channel">Por Canal</option>
                  </select>
                </div>
                
                {formData.type !== 'global' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Alvo</label>
                    <input
                      type="text"
                      value={formData.target}
                      onChange={(e) => setFormData({ ...formData, target: e.target.value })}
                      className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder={
                        formData.type === 'user' ? 'ID do usuário' :
                        formData.type === 'ip' ? 'Endereço IP' :
                        'Nome do canal'
                      }
                    />
                  </div>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Limite</label>
                  <input
                    type="number"
                    value={formData.limit}
                    onChange={(e) => setFormData({ ...formData, limit: parseInt(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Janela (segundos)</label>
                  <input
                    type="number"
                    value={formData.window_seconds}
                    onChange={(e) => setFormData({ ...formData, window_seconds: parseInt(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    min="1"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">Ação</label>
                <select
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value as any })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="throttle">Limitar Taxa</option>
                  <option value="disconnect">Desconectar</option>
                  <option value="block">Bloquear</option>
                </select>
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Regra ativa</span>
                </label>
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingRule(null);
                  resetForm();
                }}
                className="px-4 py-2 bg-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancelar
              </button>
              
              <button
                onClick={() => editingRule ? handleUpdateRule(editingRule.id) : handleCreateRule()}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {editingRule ? 'Atualizar' : 'Criar'} Regra
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