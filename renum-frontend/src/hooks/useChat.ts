import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { chatApi } from '../lib/api-client';
import { ChatMessage, ToolCall } from '../types';

interface UseChatOptions {
  agentId: string;
  initialMessages?: ChatMessage[];
}

export function useChat({ agentId, initialMessages = [] }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Função para enviar mensagem para o agente
  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;
    
    setIsLoading(true);
    setError(null);

    // Criar mensagem do usuário
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    // Adicionar mensagem do usuário ao estado
    setMessages(prev => [...prev, userMessage]);

    try {
      // Tentar enviar mensagem para a API real
      try {
        const response = await chatApi.sendMessage(agentId, content);
        
        // Adicionar resposta do agente ao estado
        setMessages(prev => [...prev, response.response]);
        return;
      } catch (apiError: any) {
        console.warn('Falha ao enviar mensagem via API, usando simulação:', apiError);
        
        // Se o erro for específico, mostrar o erro
        if (apiError.message?.includes('agente') || apiError.message?.includes('agent')) {
          throw apiError;
        }
      }
      
      // Simulação de resposta para desenvolvimento
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simular uso de ferramentas (em 30% das mensagens)
      const useTools = Math.random() < 0.3;
      
      let toolCalls: ToolCall[] | undefined;
      
      if (useTools) {
        // Simular delay adicional para uso de ferramentas
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Simular chamadas de ferramentas
        toolCalls = [
          {
            id: uuidv4(),
            type: 'function',
            name: 'tavily_search',
            input: { query: content },
            output: { results: [{ title: 'Resultado de pesquisa simulado', url: 'https://example.com' }] },
            status: 'completed'
          }
        ];
      }
      
      // Criar resposta simulada do agente
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: `Esta é uma resposta simulada para: "${content}".\n\nEm um ambiente de produção, esta mensagem seria gerada pelo modelo de IA selecionado.`,
        created_at: new Date().toISOString(),
        tool_calls: toolCalls
      };
      
      // Adicionar resposta do agente ao estado
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || 'Erro ao enviar mensagem');
      console.error('Erro ao enviar mensagem:', err);
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  // Função para limpar o histórico de mensagens
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Função para tentar novamente a última mensagem
  const retry = useCallback(() => {
    // Verificar se há mensagens
    if (messages.length === 0) return;
    
    // Encontrar a última mensagem do usuário
    const lastUserMessageIndex = [...messages].reverse().findIndex(msg => msg.role === 'user');
    
    if (lastUserMessageIndex === -1) return;
    
    // Obter a última mensagem do usuário
    const lastUserMessage = messages[messages.length - 1 - lastUserMessageIndex];
    
    // Remover mensagens após a última mensagem do usuário
    setMessages(messages.slice(0, messages.length - lastUserMessageIndex));
    
    // Enviar a mensagem novamente
    sendMessage(lastUserMessage.content);
  }, [messages, sendMessage]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    retry,
    clearMessages
  };
}