"""
Rotas da API para gerenciamento de membros de equipes de agentes.

Este módulo implementa os endpoints da API para gerenciamento de membros de equipes de agentes,
incluindo adição, atualização e remoção de membros.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Body
from typing import Dict, Any, List
from uuid import UUID

from app.models.team_models import (
    TeamResponse,
    WorkflowAgent,
    AgentRole
)
from app.repositories.team_repository import TeamRepository
from app.services.suna_api_client import SunaApiClient
from app.core.dependencies import get_team_repository, get_suna_client
from app.core.auth import get_current_user_id
from app.core.validators import validate_agent_ownership
from app.core.config import get_settings

router = APIRouter(
    prefix="/teams/{team_id}/members",
    tags=["team-members"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "",
    response_model=TeamResponse,
    status_code=201,
    summary="Add member to team",
    description="Adds a new agent member to an existing team",
    responses={
        201: {"description": "Member added successfully"},
        400: {"description": "Invalid member data"},
        404: {"description": "Team not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"},
        422: {"description": "Validation error"}
    }
)
async def add_team_member(
    team_id: UUID = Path(..., description="Team ID"),
    agent_config: WorkflowAgent = Body(..., description="Agent configuration"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository),
    suna_client: SunaApiClient = Depends(get_suna_client)
):
    """
    Adds a new agent member to an existing team.
    
    This endpoint allows adding a new agent to a team with specific configuration.
    The agent will be added to the team's workflow definition.
    
    - **team_id**: Unique identifier of the team
    - **agent_config**: Configuration for the new agent member
    
    Returns the updated team details.
    """
    settings = get_settings()
    
    # Get the current team
    team = await team_repository.get_team(team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    # Check if the agent is already in the team
    if agent_config.agent_id in team.agent_ids:
        raise HTTPException(status_code=400, detail=f"Agent {agent_config.agent_id} is already a member of this team")
    
    # Check if the team has reached the maximum number of agents
    if len(team.agent_ids) >= settings.MAX_AGENTS_PER_TEAM:
        raise HTTPException(status_code=400, detail=f"Team has reached the maximum number of agents ({settings.MAX_AGENTS_PER_TEAM})")
    
    # Validate agent ownership
    try:
        await validate_agent_ownership(user_id, [agent_config.agent_id], suna_client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Add the agent to the team
    updated_agent_ids = team.agent_ids + [agent_config.agent_id]
    updated_workflow_agents = team.workflow_definition.agents + [agent_config]
    
    # Create updated workflow definition
    updated_workflow_definition = team.workflow_definition.copy(deep=True)
    updated_workflow_definition.agents = updated_workflow_agents
    
    # Update the team
    updated_team = await team_repository.update_team(
        team_id,
        user_id,
        {
            "agent_ids": updated_agent_ids,
            "workflow_definition": updated_workflow_definition
        }
    )
    
    if not updated_team:
        raise HTTPException(status_code=500, detail="Failed to update team")
    
    return updated_team


@router.put(
    "/{agent_id}",
    response_model=TeamResponse,
    summary="Update team member",
    description="Updates the configuration of an existing team member",
    responses={
        200: {"description": "Member updated successfully"},
        400: {"description": "Invalid member data"},
        404: {"description": "Team or member not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"},
        422: {"description": "Validation error"}
    }
)
async def update_team_member(
    team_id: UUID = Path(..., description="Team ID"),
    agent_id: str = Path(..., description="Agent ID"),
    agent_config: Dict[str, Any] = Body(..., description="Updated agent configuration"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository)
):
    """
    Updates the configuration of an existing team member.
    
    This endpoint allows updating the configuration of an agent that is already part of a team.
    The agent's role, execution order, input configuration, and other properties can be updated.
    
    - **team_id**: Unique identifier of the team
    - **agent_id**: ID of the agent to update
    - **agent_config**: Updated configuration for the agent
    
    Returns the updated team details.
    """
    # Get the current team
    team = await team_repository.get_team(team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    # Check if the agent is in the team
    if agent_id not in team.agent_ids:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not a member of this team")
    
    # Find the agent in the workflow definition
    updated_workflow_agents = []
    agent_found = False
    
    for agent in team.workflow_definition.agents:
        if agent.agent_id == agent_id:
            # Update the agent configuration
            updated_agent = agent.copy(deep=True)
            
            # Update fields from the request
            if "role" in agent_config:
                updated_agent.role = AgentRole(agent_config["role"])
            
            if "execution_order" in agent_config:
                updated_agent.execution_order = agent_config["execution_order"]
            
            if "input" in agent_config:
                updated_agent.input = agent_config["input"]
            
            if "conditions" in agent_config:
                updated_agent.conditions = agent_config["conditions"]
            
            if "timeout" in agent_config:
                updated_agent.timeout = agent_config["timeout"]
            
            if "retry_config" in agent_config:
                updated_agent.retry_config = agent_config["retry_config"]
            
            updated_workflow_agents.append(updated_agent)
            agent_found = True
        else:
            updated_workflow_agents.append(agent)
    
    if not agent_found:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in workflow definition")
    
    # Create updated workflow definition
    updated_workflow_definition = team.workflow_definition.copy(deep=True)
    updated_workflow_definition.agents = updated_workflow_agents
    
    # Update the team
    updated_team = await team_repository.update_team(
        team_id,
        user_id,
        {
            "workflow_definition": updated_workflow_definition
        }
    )
    
    if not updated_team:
        raise HTTPException(status_code=500, detail="Failed to update team")
    
    return updated_team


@router.delete(
    "/{agent_id}",
    response_model=TeamResponse,
    summary="Remove team member",
    description="Removes an agent from a team",
    responses={
        200: {"description": "Member removed successfully"},
        404: {"description": "Team or member not found"},
        400: {"description": "Cannot remove the last member of a team"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"}
    }
)
async def remove_team_member(
    team_id: UUID = Path(..., description="Team ID"),
    agent_id: str = Path(..., description="Agent ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository)
):
    """
    Removes an agent from a team.
    
    This endpoint allows removing an agent from a team.
    The agent will be removed from the team's agent list and workflow definition.
    
    - **team_id**: Unique identifier of the team
    - **agent_id**: ID of the agent to remove
    
    Returns the updated team details.
    """
    # Get the current team
    team = await team_repository.get_team(team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    # Check if the agent is in the team
    if agent_id not in team.agent_ids:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} is not a member of this team")
    
    # Check if this is the last agent in the team
    if len(team.agent_ids) <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last agent from a team")
    
    # Remove the agent from the team
    updated_agent_ids = [aid for aid in team.agent_ids if aid != agent_id]
    updated_workflow_agents = [agent for agent in team.workflow_definition.agents if agent.agent_id != agent_id]
    
    # Create updated workflow definition
    updated_workflow_definition = team.workflow_definition.copy(deep=True)
    updated_workflow_definition.agents = updated_workflow_agents
    
    # Update the team
    updated_team = await team_repository.update_team(
        team_id,
        user_id,
        {
            "agent_ids": updated_agent_ids,
            "workflow_definition": updated_workflow_definition
        }
    )
    
    if not updated_team:
        raise HTTPException(status_code=500, detail="Failed to update team")
    
    return updated_team