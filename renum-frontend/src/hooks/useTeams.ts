// Hooks personalizados para equipes

import { useState, useEffect, useCallback } from 'react';
import { useTeamContext } from '../contexts/TeamContext';
import { Team, TeamCreate, TeamUpdate, WorkflowDefinition, AgentRole } from '../services/api-types';
import { ApiError } from '../services/api-error';

// Hook para gerenciar a criação de equipes
export function useCreateTeam() {
  const { createTeam, error, loading } = useTeamContext();
  const [success, setSuccess] = useState<boolean>(false);

  const handleCreateTeam = useCallback(async (teamData: TeamCreate) => {
    setSuccess(false);
    const result = await createTeam(teamData);
    if (result) {
      setSuccess(true);
      return result;
    }
    return null;
  }, [createTeam]);

  return { handleCreateTeam, success, loading, error };
}

// Hook para gerenciar a edição de equipes
export function useUpdateTeam() {
  const { updateTeam, error, loading } = useTeamContext();
  const [success, setSuccess] = useState<boolean>(false);

  const handleUpdateTeam = useCallback(async (teamId: string, teamData: TeamUpdate) => {
    setSuccess(false);
    const result = await updateTeam(teamId, teamData);
    if (result) {
      setSuccess(true);
      return result;
    }
    return null;
  }, [updateTeam]);

  return { handleUpdateTeam, success, loading, error };
}

// Hook para gerenciar a exclusão de equipes
export function useDeleteTeam() {
  const { deleteTeam, error, loading } = useTeamContext();
  const [success, setSuccess] = useState<boolean>(false);

  const handleDeleteTeam = useCallback(async (teamId: string) => {
    setSuccess(false);
    const result = await deleteTeam(teamId);
    if (result) {
      setSuccess(true);
    }
    return result;
  }, [deleteTeam]);

  return { handleDeleteTeam, success, loading, error };
}

// Hook para carregar uma equipe específica
export function useTeam(teamId: string | null) {
  const { fetchTeam, selectedTeam, loading, error } = useTeamContext();
  const [team, setTeam] = useState<Team | null>(null);

  useEffect(() => {
    if (teamId) {
      fetchTeam(teamId).then(result => {
        if (result) {
          setTeam(result);
        }
      });
    } else {
      setTeam(null);
    }
  }, [teamId, fetchTeam]);

  useEffect(() => {
    if (selectedTeam && selectedTeam.team_id === teamId) {
      setTeam(selectedTeam);
    }
  }, [selectedTeam, teamId]);

  return { team, loading, error, refetch: () => teamId ? fetchTeam(teamId) : Promise.resolve(null) };
}

// Hook para gerenciar a lista de equipes
export function useTeamsList() {
  const { teams, totalTeams, currentPage, totalPages, fetchTeams, loading, error } = useTeamContext();
  
  const loadTeams = useCallback((page: number = 1, limit: number = 10) => {
    return fetchTeams(page, limit);
  }, [fetchTeams]);

  return { 
    teams, 
    totalTeams, 
    currentPage, 
    totalPages, 
    loading, 
    error, 
    loadTeams 
  };
}

// Hook para gerenciar membros da equipe
export function useTeamMembers(team: Team | null) {
  const { updateTeam, loading, error } = useTeamContext();
  
  const addMember = useCallback(async (agentId: string, role: AgentRole, executionOrder: number) => {
    if (!team) return null;
    
    const updatedAgentIds = [...team.agent_ids, agentId];
    const updatedWorkflow = { ...team.workflow_definition };
    
    // Adiciona o agente à definição de workflow
    updatedWorkflow.agents = [
      ...updatedWorkflow.agents,
      {
        agent_id: agentId,
        role: role,
        execution_order: executionOrder,
        input: {
          source: "initial_prompt"
        }
      }
    ];
    
    return updateTeam(team.team_id, {
      agent_ids: updatedAgentIds,
      workflow_definition: updatedWorkflow
    });
  }, [team, updateTeam]);
  
  const removeMember = useCallback(async (agentId: string) => {
    if (!team) return null;
    
    const updatedAgentIds = team.agent_ids.filter(id => id !== agentId);
    const updatedWorkflow = { ...team.workflow_definition };
    
    // Remove o agente da definição de workflow
    updatedWorkflow.agents = updatedWorkflow.agents.filter(agent => agent.agent_id !== agentId);
    
    return updateTeam(team.team_id, {
      agent_ids: updatedAgentIds,
      workflow_definition: updatedWorkflow
    });
  }, [team, updateTeam]);
  
  const updateMemberRole = useCallback(async (agentId: string, role: AgentRole) => {
    if (!team) return null;
    
    const updatedWorkflow = { ...team.workflow_definition };
    
    // Atualiza o papel do agente na definição de workflow
    updatedWorkflow.agents = updatedWorkflow.agents.map(agent => 
      agent.agent_id === agentId ? { ...agent, role } : agent
    );
    
    return updateTeam(team.team_id, {
      workflow_definition: updatedWorkflow
    });
  }, [team, updateTeam]);
  
  const updateMemberOrder = useCallback(async (agentId: string, executionOrder: number) => {
    if (!team) return null;
    
    const updatedWorkflow = { ...team.workflow_definition };
    
    // Atualiza a ordem de execução do agente na definição de workflow
    updatedWorkflow.agents = updatedWorkflow.agents.map(agent => 
      agent.agent_id === agentId ? { ...agent, execution_order: executionOrder } : agent
    );
    
    return updateTeam(team.team_id, {
      workflow_definition: updatedWorkflow
    });
  }, [team, updateTeam]);
  
  return {
    members: team?.workflow_definition.agents || [],
    addMember,
    removeMember,
    updateMemberRole,
    updateMemberOrder,
    loading,
    error
  };
}

// Hook para gerenciar a definição de workflow
export function useWorkflowDefinition(team: Team | null) {
  const { updateTeam, loading, error } = useTeamContext();
  
  const updateWorkflow = useCallback(async (workflowDefinition: WorkflowDefinition) => {
    if (!team) return null;
    
    return updateTeam(team.team_id, {
      workflow_definition: workflowDefinition
    });
  }, [team, updateTeam]);
  
  return {
    workflow: team?.workflow_definition,
    updateWorkflow,
    loading,
    error
  };
}