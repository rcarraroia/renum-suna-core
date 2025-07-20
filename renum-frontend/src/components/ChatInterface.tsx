import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, RefreshCw } from 'lucide-react';
import { formatDate } from '../lib/utils';
import Button from './ui/Button';
import ToolUsageDisplay from './ToolUsageDisplay';
import ChatErrorHandler from './ChatErrorHandler';
import { ChatMessage } from '../types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error?: string | null;
  onSendMessage: (message: string) => void;
  onRetry?: () => void;
}

const ChatInterface = ({ messages, isLoading, error, onSendMessage, onRetry }: ChatInterfaceProps) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Rolar para o final quando novas mensagens são adicionadas
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;
    
    onSendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Enviar mensagem com Enter (sem Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Ajustar altura do textarea conforme o conteúdo
  const adjustTextareaHeight = () => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Exibir erro se houver */}
        {error && (
          <ChatErrorHandler 
            error={error} 
            onRetry={onRetry}
            className="mb-4"
          />
        )}
        
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <Bot className="h-12 w-12 mb-4 text-indigo-300" />
            <p className="text-lg font-medium">Comece uma conversa com o agente</p>
            <p className="text-sm">Digite sua mensagem abaixo para iniciar</p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="flex flex-col">
              <div className={`flex items-start ${message.role === 'user' ? 'justify-end' : ''}`}>
                <div
                  className={`
                    flex items-start space-x-2 max-w-3xl rounded-lg px-4 py-3
                    ${message.role === 'user' 
                      ? 'bg-indigo-50 text-indigo-900 ml-12' 
                      : 'bg-white border border-gray-200 mr-12'}
                  `}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 mt-1">
                      <Bot className="h-5 w-5 text-indigo-600" />
                    </div>
                  )}
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 mt-1 order-last">
                      <User className="h-5 w-5 text-indigo-600" />
                    </div>
                  )}
                  <div className="flex-1 space-y-2">
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    
                    {/* Exibir chamadas de ferramentas */}
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-2">
                        {message.tool_calls.map((toolCall) => (
                          <ToolUsageDisplay key={toolCall.id} toolCall={toolCall} />
                        ))}
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500">
                      {formatDate(message.created_at, {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {/* Indicador de digitação */}
        {isLoading && (
          <div className="flex items-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 max-w-3xl mr-12">
              <div className="flex items-center space-x-2">
                <Bot className="h-5 w-5 text-indigo-600" />
                <div className="flex space-x-1">
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Elemento para rolar para o final */}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Área de input */}
      <div className="border-t border-gray-200 bg-white p-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-2">
          <div className="flex-1 min-h-[40px]">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                adjustTextareaHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua mensagem..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
              rows={1}
              disabled={isLoading}
            />
          </div>
          <Button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="h-10 w-10 p-0"
            size="sm"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </Button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Pressione Enter para enviar, Shift+Enter para nova linha
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;