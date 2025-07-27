import { useQuery } from '@tanstack/react-query';
// import { supabase } from '../lib/supabase'; // Comentado temporariamente

export interface TypewriterPhrase {
  id: string;
  text: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const useTypewriterPhrases = () => {
  const { data: phrases, isLoading, error } = useQuery<TypewriterPhrase[]>({
    queryKey: ['typewriter-phrases'],
    queryFn: async () => {
      // Temporariamente retornando dados mock
      return [
        { id: '1', text: 'Automatize suas tarefas', display_order: 1, is_active: true, created_at: '', updated_at: '' },
        { id: '2', text: 'Otimize seus processos', display_order: 2, is_active: true, created_at: '', updated_at: '' },
        { id: '3', text: 'Acelere seu trabalho', display_order: 3, is_active: true, created_at: '', updated_at: '' }
      ];
    },
  });

  return {
    phrases: phrases || [],
    isLoading,
    error,
  };
};