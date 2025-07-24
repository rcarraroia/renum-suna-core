/**
 * Componente para configurações de notificações
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketContext } from '../../contexts/WebSocketContext';

interface NotificationPreferences {
  email_enabled: boolean;
  websocket_enabled: boolean;
  types_enabled: {
    info: boolean;
    success: boolean;
    warning: boolean;
    error: boolean;
  };
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone: string;
}

interface NotificationSettingsProps {
  className?: string;
}

/**
 * Componente para configurações de notificações
 */
const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  className = '',
}) => {
  const { sendCommand } = useWebSocketContext();
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_enabled: true,
    websocket_enabled: true,
    types_enabled: {
      info: true,
      success: true,
      warning: true,
      error: true,
    },
    timezone: 'UTC',
  });
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  // Carrega as preferências ao montar o componente
  useEffect(() => {
    loadPreferences();
  }, []);

  // Carrega as preferências do servidor
  const loadPreferences = async () => {
    try {
      setLoading(true);
      sendCommand('get_notification_preferences');
      
      // Simula resposta (em uma implementação real, você escutaria a resposta via WebSocket)
      setTimeout(() => {
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Erro ao carregar preferências:', error);
      setLoading(false);
    }
  };

  // Salva as preferências
  const savePreferences = async () => {
    try {
      setLoading(true);
      sendCommand('update_notification_preferences', preferences);
      
      // Simula resposta
      setTimeout(() => {
        setLoading(false);
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }, 1000);
    } catch (error) {
      console.error('Erro ao salvar preferências:', error);
      setLoading(false);
    }
  };

  // Atualiza uma preferência
  const updatePreference = (key: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  // Atualiza uma preferência de tipo
  const updateTypePreference = (type: keyof NotificationPreferences['types_enabled'], enabled: boolean) => {
    setPreferences(prev => ({
      ...prev,
      types_enabled: {
        ...prev.types_enabled,
        [type]: enabled,
      },
    }));
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          Configurações de Notificações
        </h2>
        <p className="text-sm text-gray-600">
          Configure como e quando você deseja receber notificações.
        </p>
      </div>

      <div className="space-y-6">
        {/* Canais de notificação */}
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">
            Canais de Notificação
          </h3>
          
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.websocket_enabled}
                onChange={(e) => updatePreference('websocket_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-700">
                Notificações em tempo real (WebSocket)
              </span>
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.email_enabled}
                onChange={(e) => updatePreference('email_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-700">
                Notificações por email
              </span>
            </label>
          </div>
        </div>

        {/* Tipos de notificação */}
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">
            Tipos de Notificação
          </h3>
          
          <div className="space-y-3">
            {Object.entries(preferences.types_enabled).map(([type, enabled]) => {
              const typeLabels = {
                info: 'Informações',
                success: 'Sucessos',
                warning: 'Avisos',
                error: 'Erros',
              };
              
              const typeColors = {
                info: 'text-blue-600',
                success: 'text-green-600',
                warning: 'text-yellow-600',
                error: 'text-red-600',
              };
              
              return (
                <label key={type} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => updateTypePreference(type as keyof NotificationPreferences['types_enabled'], e.target.checked)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className={`ml-3 text-sm ${typeColors[type as keyof typeof typeColors]}`}>
                    {typeLabels[type as keyof typeof typeLabels]}
                  </span>
                </label>
              );
            })}
          </div>
        </div>

        {/* Horário silencioso */}
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">
            Horário Silencioso
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Início
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_start || ''}
                onChange={(e) => updatePreference('quiet_hours_start', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fim
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_end || ''}
                onChange={(e) => updatePreference('quiet_hours_end', e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
          
          <p className="mt-2 text-xs text-gray-500">
            Durante o horário silencioso, você não receberá notificações em tempo real.
          </p>
        </div>

        {/* Fuso horário */}
        <div>
          <h3 className="text-base font-medium text-gray-900 mb-3">
            Fuso Horário
          </h3>
          
          <select
            value={preferences.timezone}
            onChange={(e) => updatePreference('timezone', e.target.value)}
            className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="UTC">UTC</option>
            <option value="America/Sao_Paulo">América/São Paulo</option>
            <option value="America/New_York">América/Nova York</option>
            <option value="Europe/London">Europa/Londres</option>
            <option value="Asia/Tokyo">Ásia/Tóquio</option>
          </select>
        </div>
      </div>

      {/* Botões de ação */}
      <div className="mt-8 flex items-center justify-between">
        <button
          onClick={loadPreferences}
          disabled={loading}
          className="text-sm text-gray-600 hover:text-gray-800 disabled:opacity-50"
        >
          Restaurar padrões
        </button>
        
        <div className="flex items-center space-x-3">
          {saved && (
            <span className="text-sm text-green-600 flex items-center">
              <svg className="h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Salvo!
            </span>
          )}
          
          <button
            onClick={savePreferences}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;