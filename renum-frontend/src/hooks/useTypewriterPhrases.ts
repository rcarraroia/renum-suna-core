import { useQuery } from '@tanstack/react-query';
import { supabase } from '../lib/supabase';

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
      try {
        const { data, error } = await supabase
          .from('renum_homepage_phrases')
          .select('*')
          .eq('is_active', true)
          .order('display_order', { ascending: true });

        if (error) throw error;
        return data || [];
      } catch (error) {
        console.error('Error fetching typewriter phrases:', error);
        return [];
      }
    },
  });

  return {
    phrases: phrases || [],
    isLoading,
    error,
  };
};