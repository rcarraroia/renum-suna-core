import React, { useState } from 'react';

interface ExecutionError {
  error_type: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  details: Record<string, any>;
  recoverable: boolean;
  retry_count: number;
  max_retries: number;
  agent_id?: string;
  step_name?: string;
  timestamp: string;
  stack_trace?: string;
}

interface ExecutionErrorDisplayProps {
  error: ExecutionError;
  executionId: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showStackTrace?: boolean;
  className?: string;
}

export const ExecutionErrorDisplay: React.FC<ExecutionErrorDisplayProps> = ({
  error,
  executionId,
  onRetry,
  onDismiss,
  showStackTrace = false,
  className = ''
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [showStack, setShowStack] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'border-yellow-200 bg-yellow-50 text-yellow-800';
      case 'medium':
        return 'border-orange-200 bg-orange-50 text-orange-800';
      case 'high':
        return 'border-red-200 bg-red-50 text-red-800';
      case 'critical':
        return 'border-red-300 bg-red-100 text-red-900';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'low':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'medium':
        return (
          <svg className="w-5 h-5 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'high':
      case 'critical':
        return (
          <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const formatErrorType = (errorType: string) => {
    return errorType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getRecoverySuggestions = (errorType: string) => {
    const suggestions: Record<string, string[]> = {
      'agent_timeout': [
        'Verifique a conectividade de rede',
        'Considere aumentar o timeout do agente',
        'Verifique se o agente está sobrecarregado'
      ],
      'network_error': [
        'Verifique a conexão com a internet',
        'Teste a conectividade com os serviços externos',
        'Considere usar um proxy ou VPN'
      ],
      'authentication_error': [
        'Verifique as credenciais de autenticação',
        'Confirme se os tokens não expiraram',
        'Verifique as permissões do usuário'
      ],
      'resource_exhausted': [
        'Libere recursos do sistema',
        'Considere executar em horário de menor carga',
        'Otimize o uso de memória/CPU'
      ],
      'invalid_input': [
        'Verifique os dados de entrada',
        'Confirme o formato dos parâmetros',
        'Valide os tipos de dados'
      ],
      'dependency_error': [
        'Verifique se todas as dependências estão instaladas',
        'Confirme as versões das bibliotecas',
        'Reinstale as dependências se necessário'
      ],
      'quota_exceeded': [
        'Aguarde o reset da cota',
        'Considere usar uma conta diferente',
        'Otimize o uso de recursos'
      ]
    };

    return suggestions[error.error_type] || ['Contate o suporte técnico'];
  };

  return (
    <div className={`border rounded-lg p-4 ${getSeverityColor(error.severity)} ${className}`}>
      {/* Header do erro */}
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          {getSeverityIcon(error.severity)}
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium">
              {formatErrorType(error.error_type)}
              <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                error.severity === 'critical' ? 'bg-red-200 text-red-800' :
                error.severity === 'high' ? 'bg-red-100 text-red-700' :
                error.severity === 'medium' ? 'bg-orange-100 text-orange-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {error.severity.toUpperCase()}
              </span>
            </h3>
            <p className="mt-1 text-sm">{error.message}</p>
            
            {/* Informações básicas */}
            <div className="mt-2 text-xs space-y-1">
              <p><span className="font-medium">Horário:</span> {formatTimestamp(error.timestamp)}</p>
              {error.agent_id && (
                <p><span className="font-medium">Agente:</span> {error.agent_id}</p>
              )}
              {error.step_name && (
                <p><span className="font-medium">Etapa:</span> {error.step_name}</p>
              )}
              {error.recoverable && (
                <p>
                  <span className="font-medium">Tentativas:</span> {error.retry_count}/{error.max_retries}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Botões de ação */}
        <div className="flex items-center space-x-2 ml-4">
          {error.recoverable && onRetry && error.retry_count < error.max_retries && (
            <button
              onClick={onRetry}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Tentar Novamente
            </button>
          )}
          
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            {showDetails ? 'Ocultar Detalhes' : 'Ver Detalhes'}
          </button>
          
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Detalhes expandidos */}
      {showDetails && (
        <div className="mt-4 border-t pt-4 space-y-4">
          {/* Sugestões de recuperação */}
          <div>
            <h4 className="text-sm font-medium mb-2">Sugestões de Recuperação:</h4>
            <ul className="text-sm space-y-1">
              {getRecoverySuggestions(error.error_type).map((suggestion, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-gray-400 mr-2">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Detalhes técnicos */}
          {Object.keys(error.details).length > 0 && (
            <div>
              <h4 className="text-sm font-medium mb-2">Detalhes Técnicos:</h4>
              <div className="bg-gray-100 rounded p-3 text-xs">
                <pre className="whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(error.details, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Stack trace */}
          {showStackTrace && error.stack_trace && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium">Stack Trace:</h4>
                <button
                  onClick={() => setShowStack(!showStack)}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  {showStack ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
              {showStack && (
                <div className="bg-gray-900 text-green-400 rounded p-3 text-xs font-mono">
                  <pre className="whitespace-pre-wrap overflow-x-auto">
                    {error.stack_trace}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* Status de recuperação */}
          {error.recoverable && (
            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <div className="flex items-center">
                <svg className="w-4 h-4 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                </svg>
                <span className="text-sm text-blue-800">
                  Este erro é recuperável. 
                  {error.retry_count < error.max_retries ? (
                    ` Restam ${error.max_retries - error.retry_count} tentativas.`
                  ) : (
                    ' Todas as tentativas foram esgotadas.'
                  )}
                </span>
              </div>
            </div>
          )}

          {/* Informações da execução */}
          <div className="text-xs text-gray-600 border-t pt-2">
            <p><span className="font-medium">ID da Execução:</span> {executionId}</p>
            <p><span className="font-medium">Tipo de Erro:</span> {error.error_type}</p>
            <p><span className="font-medium">Recuperável:</span> {error.recoverable ? 'Sim' : 'Não'}</p>
          </div>
        </div>
      )}
    </div>
  );
};