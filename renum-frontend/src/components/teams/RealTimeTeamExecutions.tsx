import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useWebSocketChannels } from '../../hooks/useWebSocketChannels';
import { RealTimeExecutionProgress } from '../executions/RealTimeExecutionProgress';

interface TeamExecution {
  id: string;
  team_id: string;
  team_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  started_at?: string;
  completed_at?: string;
  created_by: string;
  current_agent?: string;
  total_agents: number;
  completed_agents: number;
  error_message?: string;
  result?: any;
}

export interface RealTimeTeamExecutionsProps {
  teamId: string;
  userId?: string;
  onExecutionStart?: (execution: TeamExecution) => void;
  onExecutionComplete?: (execution: TeamExecution) => void;
  onExecutionError?: (execution: TeamExecution, error: string) => void;
  className?: string;
}

export const RealTimeTeamExecutions: React.FC<RealTimeTeamExecutionsProps> = ({
  teamId,
  userId,
  onExecutionStart,
  onExecutionComplete,
  onExecutionError,
  className = ''
}) => {
  const { isConnected } = useWebSocket();
  const { subscribeToChannel, unsubscribeFromChannel } = useWebSocketChannels();
  
  const [executions, setExecutions] = useState<TeamExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Inscrever-se no canal da equipe
  useEffect(() => {
    if (!teamId || !isConnected) return;

    const channelName = `team_${teamId}`;
    
    const handleTeamUpdate = (data: any) => {
      if (data.type === 'execution_started') {
        const newExecution: TeamExecution = data.execution;
        setExecutions(prev => {
          const exists = prev.find(e => e.id === newExecution.id);
          if (exists) {
            return prev.map(e => e.id === newExecution.id ? newExecution : e);
          }
          return [newExecution, ...prev];
        });
        
        if (onExecutionStart) {
          onExecutionStart(newExecution);
        }
      } else if (data.type === 'execution_updated') {
        const updatedExecution: TeamExecution = data.execution;
        setExecutions(prev => 
          prev.map(e => e.id === updatedExecution.id ? updatedExecution : e)
        );
      } else if (data.type === 'execution_completed') {
        const completedExecution: TeamExecution = data.execution;
        setExecutions(prev => 
          prev.map(e => e.id === completedExecution.id ? completedExecution : e)
        );
        
        if (onExecutionComplete) {
          onExecutionComplete(completedExecution);
        }
      } else if (data.type === 'execution_failed') {
        const failedExecution: TeamExecution = data.execution;
        setExecutions(prev => 
          prev.map(e => e.id === failedExecution.id ? failedExecution : e)
        );
        
        if (onExecutionError) {
          onExecutionError(failedExecution, failedExecution.error_message || 'Erro desconhecido');
        }
      }
    };

    subscribeToChannel(channelName, handleTeamUpdate);

    return () => {
      unsubscribeFromChannel(channelName);
    };
  }, [teamId, isConnected, subscribeToChannel, unsubscribeFromChannel, onExecutionStart, onExecutionComplete, onExecutionError]);

  // Carregar execuções iniciais
  useEffect(() => {
    const loadInitialExecutions = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch(`/api/v1/teams/${teamId}/executions?limit=10&status=active`);
        if (!response.ok) {
          throw new Error('Erro ao carregar execuções');
        }
        
        const data = await response.json();
        setExecutions(data.executions || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro desconhecido');
      } finally {
        setLoading(false);
      }
    };

    if (teamId) {
      loadInitialExecutions();
    }
  }, [teamId]);

  const getStatusBadge = (status: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      case 'running':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'cancelled':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return 'há poucos segundos';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `há ${minutes} minuto${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `há ${hours} hora${hours > 1 ? 's' : ''}`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `há ${days} dia${days > 1 ? 's' : ''}`;
    }
  };

  if (loading) {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-3"></div>
          <span className="text-gray-600">Carregando execuções...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-red-800 font-medium">Erro ao carregar execuções</span>
        </div>
        <p className="text-red-700 mt-1">{error}</p>
      </div>
    );
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Execuções da Equipe
          </h3>
          
          <div className="flex items-center text-sm text-gray-500">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span>{isConnected ? 'Conectado' : 'Desconectado'}</span>
          </div>
        </div>
      </div>

      {/* Lista de execuções */}
      <div className="divide-y divide-gray-200">
        {executions.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma execução</h3>
            <p className="mt-1 text-sm text-gray-500">
              Não há execuções ativas para esta equipe no momento.
            </p>
          </div>
        ) : (
          executions.map((execution) => (
            <div key={execution.id} className="px-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <span className={getStatusBadge(execution.status)}>
                    {execution.status}
                  </span>
                  <span className="ml-3 text-sm text-gray-600">
                    ID: {execution.id.slice(0, 8)}...
                  </span>
                </div>
                
                <div className="text-sm text-gray-500">
                  {execution.started_at && formatTimeAgo(execution.started_at)}
                </div>
              </div>

              {/* Progresso detalhado para execuções ativas */}
              {(execution.status === 'running' || execution.status === 'pending') && (
                <div className="mb-3">
                  <RealTimeExecutionProgress
                    executionId={execution.id}
                    teamId={teamId}
                    className="border-0 shadow-none bg-gray-50"
                  />
                </div>
              )}

              {/* Informações da execução */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Progresso:</span>
                  <div className="mt-1">
                    <div className="flex items-center">
                      <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            execution.status === 'completed' ? 'bg-green-500' :
                            execution.status === 'failed' ? 'bg-red-500' :
                            'bg-blue-500'
                          }`}
                          style={{ width: `${execution.progress}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-gray-600">{execution.progress}%</span>
                    </div>
                  </div>
                </div>

                <div>
                  <span className="font-medium text-gray-700">Agentes:</span>
                  <p className="mt-1 text-gray-600">
                    {execution.completed_agents} de {execution.total_agents} concluídos
                  </p>
                  {execution.current_agent && (
                    <p className="text-xs text-gray-500 mt-1">
                      Atual: {execution.current_agent}
                    </p>
                  )}
                </div>

                <div>
                  <span className="font-medium text-gray-700">Duração:</span>
                  <p className="mt-1 text-gray-600">
                    {execution.started_at && execution.completed_at ? (
                      (() => {
                        const start = new Date(execution.started_at);
                        const end = new Date(execution.completed_at);
                        const duration = Math.floor((end.getTime() - start.getTime()) / 1000);
                        const minutes = Math.floor(duration / 60);
                        const seconds = duration % 60;
                        return `${minutes}m ${seconds}s`;
                      })()
                    ) : execution.started_at ? (
                      (() => {
                        const start = new Date(execution.started_at);
                        const now = new Date();
                        const duration = Math.floor((now.getTime() - start.getTime()) / 1000);
                        const minutes = Math.floor(duration / 60);
                        const seconds = duration % 60;
                        return `${minutes}m ${seconds}s (em andamento)`;
                      })()
                    ) : (
                      'Não iniciado'
                    )}
                  </p>
                </div>
              </div>

              {/* Mensagem de erro */}
              {execution.status === 'failed' && execution.error_message && (
                <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-700">{execution.error_message}</p>
                </div>
              )}

              {/* Resultado */}
              {execution.status === 'completed' && execution.result && (
                <div className="mt-3">
                  <details className="bg-green-50 border border-green-200 rounded-lg p-3">
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
          ))
        )}
      </div>
    </div>
  );
};

export default RealTimeTeamExecutions;