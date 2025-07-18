import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import Button from './ui/Button';

interface ChatErrorHandlerProps {
  error: string;
  onRetry?: () => void;
  className?: string;
}

const ChatErrorHandler: React.FC<ChatErrorHandlerProps> = ({ 
  error, 
  onRetry,
  className = ''
}) => {
  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-red-800">Erro na comunicação</h3>
          <p className="mt-1 text-sm text-red-700">{error}</p>
          
          {onRetry && (
            <div className="mt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                className="border-red-300 text-red-700 hover:bg-red-50"
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Tentar novamente
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatErrorHandler;