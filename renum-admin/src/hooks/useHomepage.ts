import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { TypewriterPhrase, TypewriterPhraseFormData } from '../types/homepage';

export const useHomepage = () => {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  // Fetch all typewriter phrases
  const {
    data: phrases,
    isLoading: isLoadingPhrases,
    error: phrasesError,
    refetch: refetchPhrases,
  } = useQuery<TypewriterPhrase[]>({
    queryKey: ['typewriter-phrases'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/admin/homepage/phrases');
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Error fetching phrases');
        throw error;
      }
    },
  });

  // Fetch a specific phrase
  const getPhrase = async (id: string) => {
    try {
      const response = await apiClient.get(`/admin/homepage/phrases/${id}`);
      return response.data;
    } catch (error: any) {
      setError(error.response?.data?.message || 'Error fetching phrase');
      throw error;
    }
  };

  // Create a new phrase
  const createPhraseMutation = useMutation({
    mutationFn: async (data: TypewriterPhraseFormData) => {
      try {
        const response = await apiClient.post('/admin/homepage/phrases', data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Error creating phrase');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['typewriter-phrases'] });
    },
  });

  // Update an existing phrase
  const updatePhraseMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TypewriterPhraseFormData }) => {
      try {
        const response = await apiClient.put(`/admin/homepage/phrases/${id}`, data);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Error updating phrase');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['typewriter-phrases'] });
    },
  });

  // Delete a phrase
  const deletePhraseMutation = useMutation({
    mutationFn: async (id: string) => {
      try {
        const response = await apiClient.delete(`/admin/homepage/phrases/${id}`);
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Error deleting phrase');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['typewriter-phrases'] });
    },
  });

  // Toggle phrase status (active/inactive)
  const togglePhraseStatusMutation = useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      try {
        const response = await apiClient.patch(`/admin/homepage/phrases/${id}/status`, {
          is_active: isActive,
        });
        return response.data;
      } catch (error: any) {
        setError(
          error.response?.data?.message ||
            `Error ${isActive ? 'activating' : 'deactivating'} phrase`
        );
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['typewriter-phrases'] });
    },
  });

  // Reorder phrases
  const reorderPhrasesMutation = useMutation({
    mutationFn: async (phraseIds: string[]) => {
      try {
        const response = await apiClient.post('/admin/homepage/phrases/reorder', {
          phrase_ids: phraseIds,
        });
        return response.data;
      } catch (error: any) {
        setError(error.response?.data?.message || 'Error reordering phrases');
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['typewriter-phrases'] });
    },
  });

  return {
    phrases,
    isLoadingPhrases,
    error,
    setError,
    refetchPhrases,
    getPhrase,
    createPhrase: createPhraseMutation.mutate,
    isCreatingPhrase: createPhraseMutation.isPending,
    updatePhrase: updatePhraseMutation.mutate,
    isUpdatingPhrase: updatePhraseMutation.isPending,
    deletePhrase: deletePhraseMutation.mutate,
    isDeletingPhrase: deletePhraseMutation.isPending,
    togglePhraseStatus: togglePhraseStatusMutation.mutate,
    isTogglingPhraseStatus: togglePhraseStatusMutation.isPending,
    reorderPhrases: reorderPhrasesMutation.mutate,
    isReorderingPhrases: reorderPhrasesMutation.isPending,
  };
};