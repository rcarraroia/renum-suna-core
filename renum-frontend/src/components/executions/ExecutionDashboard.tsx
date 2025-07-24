import React, { useState, useEffect } from 'react';
import { useRealTimeExecutions } from '../../hooks/useRealTimeExecutions';
import { RealTimeExecutionProgress } from './RealTimeExecutionProgress';
import { useWebSocket } from '../../hooks/useWebSocket';

interface ExecutionDashboardProps {
  teamId?: string;
  userId?: string;
  className?: string;
}

export const ExecutionDashboard: React.FC<ExecutionDashboardProps> = ({
  teamId,
  userId,
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  const {
    executions,
    activeExecutions,
    completedExecutions,
    failedExecutions,
    isLoading,
    error,
    totalCount,
    refreshExecutions,
    clearError
  } = useRealTimeExecutions({
    teamId,
    userId,
    autoSubscribe: true,
    includeCompleted: true,
    maxExecutions: 20
  });

  const [selectedTab, setSelectedTab] = useState<'active' | 'completed' | 'failed' | 'all'>('active');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh a cada 30 segundos se habilitado
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      refreshExecutions();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshExecutions]);

  const getTabData = () => {
    switch (selectedTab) {
      case 'active':
        return activeExecutions;
      case 'completed':
        return completedExecutions;
      case 'failed':
        return failedExecutions;
      case 'all':
      default:
        return executions;
    }
  };

  const getTabCount = (tab: string) => {
    switch (tab) {
      case 'active':
        return activeExecutions.length;
      case 'completed':
        return completedExecutions.length;
      case 'failed':
        return failedExecutions.length;
      case 'all':
      default:
        return totalCount;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return 'N/A';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
    
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800 font-medium">Erro ao carregar dashboard</span>
          </div>
          <button
            onClick={clearError}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Tentar novamente
          </button>
        </div>
        <p className="text-red-700 mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            Dashboard de Execuções
          </h2>
          
          <div className="flex items-center space-x-4">
            {/* Indicador de conexão */}
            <div className="flex items-center text-sm">
              <div className={`w-2 h-2 rounded-full mr-2 ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
                {isConnected ? 'Conectado' : 'Desconectado'}
              </span>
            </div>

            {/* Toggle auto-refresh */}
            <label className="flex items-center text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Auto-refresh
            </label>

            {/* Botão de refresh manual */}
            <button
              onClick={refreshExecutions}
              disabled={isLoading}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <svg className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Atualizar
            </button>
          </div>
        </div>
      </div>

      {/* Estatísticas rápidas */}
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{activeExecutions.length}</div>
            <div className="text-sm text-gray-600">Ativas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedExecutions.length}</div>
            <div className="text-sm text-gray-600">Concluídas</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{failedExecutions.length}</div>
            <div className="text-sm text-gray-600">Falharam</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{totalCount}</div>
            <div className="text-sm text-gray-600">Total</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {[
            { key: 'active', label: 'Ativas', count: getTabCount('active') },
            { key: 'completed', label: 'Concluídas', count: getTabCount('completed') },
            { key: 'failed', label: 'Falharam', count: getTabCount('failed') },
            { key: 'all', label: 'Todas', count: getTabCount('all') }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSelectedTab(tab.key as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  selectedTab === tab.key
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Conteúdo das tabs */}
      <div className="p-6">
        {isLoading && executions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-gray-600">Carregando execuções...</span>
          </div>
        ) : getTabData().length === 0 ? (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Nenhuma execução encontrada
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Não há execuções {selectedTab === 'all' ? '' : selectedTab} no momento.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {getTabData().map((execution) => (
              <div key={execution.id} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Header da execução */}
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                        {execution.status}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        {execution.team_name || `Equipe ${execution.team_id}`}
                      </span>
                      <span className="text-xs text-gray-500">
                        ID: {execution.id.slice(0, 8)}...
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-500">
                      Duração: {formatDuration(execution.started_at, execution.completed_at)}
                    </div>
                  </div>
                </div>

                {/* Progresso detalhado para execuções ativas */}
                {['pending', 'running'].includes(execution.status) && (
                  <div className="p-4">
                    <RealTimeExecutionProgress
                      executionId={execution.id}
                      teamId={execution.team_id}
                      className="border-0 shadow-none"
                    />
                  </div>
                )}

                {/* Informações para execuções concluídas/falhadas */}
                {['completed', 'failed', 'cancelled'].includes(execution.status) && (
                  <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Informações</h4>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p><span className="font-medium">Progresso:</span> {execution.progress}%</p>
                          <p><span className="font-medium">Iniciado:</span> {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'N/A'}</p>
                          {execution.completed_at && (
                            <p><span className="font-medium">Concluído:</span> {new Date(execution.completed_at).toLocaleString()}</p>
                          )}
                        </div>
                      </div>

                      {execution.error_message && (
                        <div>
                          <h4 className="text-sm font-medium text-red-700 mb-2">Erro</h4>
                          <p className="text-sm text-red-600 bg-red-50 p-2 rounded">
                            {execution.error_message}
                          </p>
                        </div>
                      )}

                      {execution.result && execution.status === 'completed' && (
                        <div className="md:col-span-2">
                          <details className="bg-green-50 border border-green-200 rounded p-3">
                            <summary className="text-sm font-medium text-green-800 cursor-pointer">
                              Ver resultado
                            </summary>
                            <pre className="mt-2 text-xs text-green-700 whitespace-pre-wrap overflow-x-auto">
                              {typeof execution.result === 'string' 
                                ? execution.result 
                                : JSON.stringify(execution.result, null, 2)
                              }
                            </pre>
                          </details>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};