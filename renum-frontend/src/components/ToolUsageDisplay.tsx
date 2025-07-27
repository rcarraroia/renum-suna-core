import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Wrench as Tool, Check, AlertCircle, Loader2 } from 'lucide-react';
import { ToolCall } from '../types/index.d';

interface ToolUsageDisplayProps {
  toolCall: ToolCall;
}

const ToolUsageDisplay: React.FC<ToolUsageDisplayProps> = ({ toolCall }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Formatar nome da ferramenta para exibição
  const formatToolName = (name: string) => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Determinar ícone de status
  const getStatusIcon = () => {
    switch (toolCall.status) {
      case 'completed':
        return <Check className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
      default:
        return <Loader2 className="h-4 w-4 text-indigo-500 animate-spin" />;
    }
  };

  // Determinar cor de fundo baseada no status
  const getStatusColor = () => {
    switch (toolCall.status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'pending':
      default:
        return 'bg-indigo-50 border-indigo-200';
    }
  };

  return (
    <div className={`mt-2 border rounded-md ${getStatusColor()}`}>
      <div 
        className="flex items-center justify-between p-2 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <Tool className="h-4 w-4 text-indigo-600" />
          <span className="font-medium text-sm">
            {formatToolName(toolCall.name)}
          </span>
          <span className="text-xs text-gray-500">
            {toolCall.status === 'completed' ? 'Concluído' : 
             toolCall.status === 'error' ? 'Falhou' : 'Em andamento'}
          </span>
        </div>
        <div className="flex items-center">
          {getStatusIcon()}
          {isExpanded ? 
            <ChevronUp className="h-4 w-4 ml-1" /> : 
            <ChevronDown className="h-4 w-4 ml-1" />
          }
        </div>
      </div>
      
      {isExpanded && (
        <div className="p-2 border-t border-gray-200 text-sm">
          <div className="mb-2">
            <h4 className="font-medium text-xs text-gray-700 mb-1">Entrada:</h4>
            <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
              {JSON.stringify(toolCall.input, null, 2)}
            </pre>
          </div>
          
          {toolCall.output && (
            <div>
              <h4 className="font-medium text-xs text-gray-700 mb-1">Saída:</h4>
              <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(toolCall.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolUsageDisplay;