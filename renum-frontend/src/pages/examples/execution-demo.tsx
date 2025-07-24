import React, { useState } from 'react';
import { 
  ExecutionDashboard, 
  RealTimeExecutionProgress, 
  ExecutionNotifications 
} from '../../components/executions';
import { RealTimeTeamExecutions } from '../../components/teams/RealTimeTeamExecutions';

const ExecutionDemoPage: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'dashboard' | 'progress' | 'notifications' | 'team'>('dashboard');
  const [executionId, setExecutionId] = useState('');
  const [teamId, setTeamId] = useState('');

  const tabs = [
    { key: 'dashboard', label: 'Dashboard', description: 'Visão geral de todas as execuções' },
    { key: 'progress', label: 'Progresso', description: 'Monitoramento de execução específica' },
    { key: 'notifications', label: 'Notificações', description: 'Notificações de execução em tempo real' },
    { key: 'team', label: 'Equipe', description: 'Execuções de uma equipe específica' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Demo - Componentes de Execução
          </h1>
          <p className="mt-2 text-gray-600">
            Demonstração dos componentes de monitoramento de execuções em tempo real
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTab(tab.key as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    selectedTab === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div>
                    <div>{tab.label}</div>
                    <div className="text-xs text-gray-400 mt-1">{tab.description}</div>
                  </div>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Configurações */}
        <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Configurações</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="executionId" className="block text-sm font-medium text-gray-700 mb-1">
                ID da Execução
              </label>
              <input
                type="text"
                id="executionId"
                value={executionId}
                onChange={(e) => setExecutionId(e.target.value)}
                placeholder="ex: exec-123456"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="teamId" className="block text-sm font-medium text-gray-700 mb-1">
                ID da Equipe
              </label>
              <input
                type="text"
                id="teamId"
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
                placeholder="ex: team-123456"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Conteúdo das tabs */}
        <div className="space-y-6">
          {selectedTab === 'dashboard' && (
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Dashboard de Execuções</h2>
                <p className="text-gray-600">
                  Visualização completa de todas as execuções com filtros e estatísticas em tempo real.
                </p>
              </div>
              
              <ExecutionDashboard
                teamId={teamId || undefined}
                className="shadow-lg"
              />
            </div>
          )}

          {selectedTab === 'progress' && (
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Progresso de Execução</h2>
                <p className="text-gray-600">
                  Monitoramento detalhado de uma execução específica em tempo real.
                </p>
              </div>

              {executionId ? (
                <RealTimeExecutionProgress
                  executionId={executionId}
                  teamId={teamId || undefined}
                  onStatusChange={(status) => {
                    console.log('Status mudou para:', status);
                  }}
                  onComplete={(result) => {
                    console.log('Execução concluída:', result);
                    alert('Execução concluída com sucesso!');
                  }}
                  onError={(error) => {
                    console.error('Erro na execução:', error);
                    alert(`Erro na execução: ${error}`);
                  }}
                  className="shadow-lg"
                />
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-yellow-800 font-medium">ID da execução necessário</span>
                  </div>
                  <p className="text-yellow-700 mt-1">
                    Digite um ID de execução válido no campo acima para visualizar o progresso em tempo real.
                  </p>
                </div>
              )}
            </div>
          )}

          {selectedTab === 'notifications' && (
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Notificações de Execução</h2>
                <p className="text-gray-600">
                  Notificações em tempo real sobre execuções com toasts e lista detalhada.
                </p>
              </div>

              <ExecutionNotifications
                teamId={teamId || undefined}
                maxNotifications={20}
                showToasts={true}
                autoMarkAsRead={false}
                className="shadow-lg"
              />
            </div>
          )}

          {selectedTab === 'team' && (
            <div>
              <div className="mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Execuções da Equipe</h2>
                <p className="text-gray-600">
                  Monitoramento de todas as execuções de uma equipe específica.
                </p>
              </div>

              {teamId ? (
                <RealTimeTeamExecutions
                  teamId={teamId}
                  onExecutionStart={(execution) => {
                    console.log('Nova execução iniciada:', execution);
                  }}
                  onExecutionComplete={(execution) => {
                    console.log('Execução concluída:', execution);
                    alert(`Execução ${execution.id} concluída!`);
                  }}
                  onExecutionError={(execution, error) => {
                    console.error('Erro na execução:', execution, error);
                    alert(`Erro na execução ${execution.id}: ${error}`);
                  }}
                  className="shadow-lg"
                />
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-yellow-800 font-medium">ID da equipe necessário</span>
                  </div>
                  <p className="text-yellow-700 mt-1">
                    Digite um ID de equipe válido no campo acima para visualizar as execuções da equipe.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Informações adicionais */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">
            Informações sobre a Demo
          </h3>
          <div className="text-blue-800 space-y-2">
            <p>
              • Esta demo mostra os componentes de monitoramento de execuções em tempo real
            </p>
            <p>
              • Os componentes se conectam automaticamente via WebSocket para atualizações em tempo real
            </p>
            <p>
              • Use IDs reais de execuções e equipes para ver dados reais
            </p>
            <p>
              • Os toasts de notificação aparecem automaticamente para novas execuções
            </p>
            <p>
              • Todos os componentes incluem indicadores de status de conexão
            </p>
          </div>
        </div>

        {/* Código de exemplo */}
        <div className="mt-8 bg-gray-900 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">
            Exemplo de Uso
          </h3>
          <pre className="text-green-400 text-sm overflow-x-auto">
{`import { 
  ExecutionDashboard, 
  RealTimeExecutionProgress, 
  ExecutionNotifications 
} from '../components/executions';

// Dashboard completo
<ExecutionDashboard teamId="team-123" />

// Monitoramento específico
<RealTimeExecutionProgress
  executionId="exec-456"
  onComplete={(result) => console.log(result)}
  onError={(error) => console.error(error)}
/>

// Notificações
<ExecutionNotifications
  teamId="team-123"
  showToasts={true}
  maxNotifications={20}
/>`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default ExecutionDemoPage;