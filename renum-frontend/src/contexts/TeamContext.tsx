/**
 * Contexto para gerenciamento de equipes
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { useTeams, useTeam, useCreateTeam, useUpdateTeam, useDeleteTeam } from '../services/api-hooks';
import { TeamResponse, TeamCreate, TeamUpdate, PaginatedTeamResponse } from '../services/api-types';
import { ApiError } from '../services/api-error';

interface TeamContextType {
  teams: TeamResponse[];
  totalTeams: number;
  currentPage: number;
  totalPages: number;
  isLoading: boolean;
  loading: boolean; // Alias para isLoading
  error: ApiError | null;
  selectedTeam: TeamResponse | null;
  fetchTeams: (page?: number, limit?: number) => void;
  fetchTeam: (teamId: string) => Promise<TeamResponse | null>;
  createTeam: (team: TeamCreate) => Promise<TeamResponse | null>;
  updateTeam: (teamId: string, team: TeamUpdate) => Promise<TeamResponse | null>;
  deleteTeam: (teamId: string) => Promise<boolean>;
  selectTeam: (team: TeamResponse | null) => void;
}

const TeamContext = createContext<TeamContextType | undefined>(undefined);

export function useTeamContext() {
  const context = useContext(TeamContext);
  if (context === undefined) {
    throw new Error('useTeamContext deve ser usado dentro de um TeamProvider');
  }
  return context;
}

interface TeamProviderProps {
  children: ReactNode;
}

export function TeamProvider({ children }: TeamProviderProps) {
  // Estado local
  const [selectedTeam, setSelectedTeam] = useState<TeamResponse | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageLimit, setPageLimit] = useState<number>(10);
  
  // Consultas React Query
  const { 
    data: teamsData,
    isLoading,
    error: teamsError,
    refetch: refetchTeams
  } = useTeams({ page: currentPage, limit: pageLimit });
  
  const createTeamMutation = useCreateTeam();
  const updateTeamMutation = useUpdateTeam(selectedTeam?.team_id || '');
  const deleteTeamMutation = useDeleteTeam();
  
  // Funções de gerenciamento de equipes
  const fetchTeams = useCallback((page: number = 1, limit: number = 10) => {
    setCurrentPage(page);
    setPageLimit(limit);
    refetchTeams();
  }, [refetchTeams]);
  
  const fetchTeam = useCallback(async (teamId: string): Promise<TeamResponse | null> => {
    try {
      // Buscar a equipe na lista já carregada primeiro
      const existingTeam = teamsData?.items.find(team => team.team_id === teamId);
      if (existingTeam) {
        setSelectedTeam(existingTeam);
        return existingTeam;
      }
      
      // Se não encontrou na lista, recarregar todas as equipes
      await refetchTeams();
      const updatedTeam = teamsData?.items.find(team => team.team_id === teamId);
      if (updatedTeam) {
        setSelectedTeam(updatedTeam);
        return updatedTeam;
      }
      
      return null;
    } catch (error) {
      console.error('Erro ao buscar equipe:', error);
      return null;
    }
  }, [teamsData, refetchTeams]);
  
  const createTeam = useCallback(async (team: TeamCreate): Promise<TeamResponse | null> => {
    try {
      const newTeam = await createTeamMutation.mutateAsync(team);
      return newTeam;
    } catch (error) {
      console.error('Erro ao criar equipe:', error);
      return null;
    }
  }, [createTeamMutation]);
  
  const updateTeam = useCallback(async (teamId: string, team: TeamUpdate): Promise<TeamResponse | null> => {
    try {
      const updatedTeam = await updateTeamMutation.mutateAsync(team);
      if (selectedTeam?.team_id === teamId) {
        setSelectedTeam(updatedTeam);
      }
      return updatedTeam;
    } catch (error) {
      console.error('Erro ao atualizar equipe:', error);
      return null;
    }
  }, [updateTeamMutation, selectedTeam]);
  
  const deleteTeam = useCallback(async (teamId: string): Promise<boolean> => {
    try {
      await deleteTeamMutation.mutateAsync(teamId);
      if (selectedTeam?.team_id === teamId) {
        setSelectedTeam(null);
      }
      return true;
    } catch (error) {
      console.error('Erro ao excluir equipe:', error);
      return false;
    }
  }, [deleteTeamMutation, selectedTeam]);
  
  const selectTeam = useCallback((team: TeamResponse | null) => {
    setSelectedTeam(team);
  }, []);
  
  // Valores do contexto
  const value: TeamContextType = {
    teams: teamsData?.items || [],
    totalTeams: teamsData?.total || 0,
    currentPage: teamsData?.page || 1,
    totalPages: teamsData?.pages || 1,
    isLoading,
    loading: isLoading, // Alias para compatibilidade
    error: teamsError as ApiError | null,
    selectedTeam,
    fetchTeams,
    fetchTeam,
    createTeam,
    updateTeam,
    deleteTeam,
    selectTeam
  };
  
  return <TeamContext.Provider value={value}>{children}</TeamContext.Provider>;
}