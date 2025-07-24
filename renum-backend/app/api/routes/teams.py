"""
Rotas da API para gerenciamento de equipes de agentes.

Este módulo implementa os endpoints da API para gerenciamento de equipes de agentes,
incluindo criação, atualização, consulta e exclusão de equipes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from uuid import UUID

from app.models.team_models import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    PaginatedTeamResponse,
    UserAPIKeyCreate,
    UserAPIKeyResponse
)
from app.repositories.team_repository import TeamRepository
from app.services.api_key_manager import ApiKeyManager
from app.services.suna_api_client import SunaApiClient
from app.core.dependencies import get_team_repository, get_api_key_manager, get_suna_client
from app.core.auth import get_current_user_id
from app.core.validators import validate_agent_ownership, validate_team_limits, validate_team_update

router = APIRouter(
    prefix="/teams",
    tags=["teams"],
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
    summary="Create a new team",
    description="Creates a new agent team with the specified configuration",
    responses={
        201: {"description": "Team created successfully"},
        400: {"description": "Invalid team data"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"}
    }
)
async def create_team(
    team_data: TeamCreate,
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository),
    suna_client: SunaApiClient = Depends(get_suna_client)
):
    """
    Creates a new agent team.
    
    This endpoint allows users to create a new team of agents with a specific workflow definition.
    The workflow defines how agents will interact and execute tasks.
    
    - **name**: Name of the team
    - **description**: Optional description of the team
    - **agent_ids**: List of agent IDs that will be part of the team
    - **workflow_definition**: Definition of the workflow (sequential, parallel, etc.)
    - **user_api_keys**: Optional API keys for external services
    - **team_config**: Optional additional configuration
    
    Returns the created team with its assigned ID.
    """
    try:
        # Valida a propriedade dos agentes
        await validate_agent_ownership(user_id, team_data.agent_ids, suna_client)
        
        # Valida os limites da equipe
        await validate_team_limits(team_data, user_id, team_repository)
        
        # Cria a equipe
        return await team_repository.create_team(user_id, team_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.get(
    "",
    response_model=PaginatedTeamResponse,
    summary="List user teams",
    description="Returns a paginated list of teams owned by the authenticated user",
    responses={
        200: {"description": "List of teams"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"}
    }
)
async def list_teams(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    name_filter: Optional[str] = Query(None, description="Filter teams by name"),
    active_only: bool = Query(True, description="Include only active teams"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository)
):
    """
    Lists teams owned by the authenticated user.
    
    This endpoint returns a paginated list of teams that belong to the current user.
    The results can be filtered by name and active status.
    
    - **page**: Page number for pagination (starts at 1)
    - **limit**: Number of items per page (max 100)
    - **name_filter**: Optional filter to search teams by name
    - **active_only**: If true, only returns active teams
    
    Returns a paginated response with teams and metadata.
    """
    try:
        return await team_repository.list_teams(user_id, page, limit, name_filter, active_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team details",
    description="Returns detailed information about a specific team",
    responses={
        200: {"description": "Team details"},
        404: {"description": "Team not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"}
    }
)
async def get_team(
    team_id: UUID = Path(..., description="Team ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository)
):
    """
    Gets detailed information about a specific team.
    
    This endpoint returns all details about a team, including its configuration,
    workflow definition, and member agents.
    
    - **team_id**: Unique identifier of the team
    
    Returns the team details if the team exists and belongs to the authenticated user.
    """
    team = await team_repository.get_team(team_id, user_id)
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    return team


@router.put(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    description="Updates an existing team with new configuration",
    responses={
        200: {"description": "Team updated successfully"},
        400: {"description": "Invalid team data"},
        404: {"description": "Team not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"},
        422: {"description": "Validation error"}
    }
)
async def update_team(
    team_data: TeamUpdate,
    team_id: UUID = Path(..., description="Team ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository),
    suna_client: SunaApiClient = Depends(get_suna_client)
):
    """
    Updates an existing team.
    
    This endpoint allows updating various aspects of a team, including its name,
    description, member agents, workflow definition, and configuration.
    All fields are optional - only the provided fields will be updated.
    
    - **team_id**: Unique identifier of the team to update
    - **team_data**: Updated team data (all fields are optional)
    
    Returns the updated team details.
    """
    try:
        # Valida a atualização da equipe
        await validate_team_update(team_data, team_id, user_id, team_repository, suna_client)
        
        # Atualiza a equipe
        updated_team = await team_repository.update_team(team_id, user_id, team_data)
        if not updated_team:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        
        return updated_team
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")


@router.delete(
    "/{team_id}",
    response_model=dict,
    summary="Delete team",
    description="Deletes an existing team",
    responses={
        200: {"description": "Team deleted successfully"},
        404: {"description": "Team not found"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - user does not have access to this team"}
    }
)
async def delete_team(
    team_id: UUID = Path(..., description="Team ID"),
    user_id: UUID = Depends(get_current_user_id),
    team_repository: TeamRepository = Depends(get_team_repository)
):
    """
    Deletes an existing team.
    
    This endpoint permanently removes a team and all its associated data.
    This action cannot be undone.
    
    - **team_id**: Unique identifier of the team to delete
    
    Returns a success message if the team was deleted successfully.
    """
    success = await team_repository.delete_team(team_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    
    return {"status": "success", "message": f"Team {team_id} deleted"}


@router.post(
    "/api-keys",
    response_model=UserAPIKeyResponse,
    status_code=201,
    summary="Create API key",
    description="Creates a new API key for external services",
    responses={
        201: {"description": "API key created successfully"},
        400: {"description": "Invalid API key data"},
        401: {"description": "Unauthorized"},
        422: {"description": "Validation error"}
    }
)
async def create_api_key(
    key_data: UserAPIKeyCreate,
    user_id: UUID = Depends(get_current_user_id),
    api_key_manager: ApiKeyManager = Depends(get_api_key_manager)
):
    """
    Creates a new API key for external services.
    
    This endpoint allows users to store API keys for external services like OpenAI, Anthropic, etc.
    These keys are encrypted and stored securely, and can be used by teams during execution.
    
    - **service_name**: Name of the service (e.g., "openai", "anthropic")
    - **api_key**: The API key to store
    
    Returns the created API key entry (without the actual key value).
    """
    try:
        return await api_key_manager.create_user_api_key(user_id, key_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")


@router.get(
    "/api-keys",
    response_model=List[UserAPIKeyResponse],
    summary="List API keys",
    description="Lists all API keys stored for the authenticated user",
    responses={
        200: {"description": "List of API keys"},
        401: {"description": "Unauthorized"}
    }
)
async def list_api_keys(
    user_id: UUID = Depends(get_current_user_id),
    api_key_manager: ApiKeyManager = Depends(get_api_key_manager)
):
    """
    Lists all API keys stored for the authenticated user.
    
    This endpoint returns a list of all API keys that the user has stored for external services.
    For security reasons, the actual key values are not returned, only metadata about each key.
    
    Returns a list of API key entries.
    """
    try:
        return await api_key_manager.list_user_api_keys(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list API keys: {str(e)}")


@router.delete(
    "/api-keys/{service_name}",
    response_model=dict,
    summary="Delete API key",
    description="Deletes an API key for a specific service",
    responses={
        200: {"description": "API key deleted successfully"},
        404: {"description": "API key not found"},
        401: {"description": "Unauthorized"}
    }
)
async def delete_api_key(
    service_name: str = Path(..., description="Service name (e.g., 'openai', 'anthropic')"),
    user_id: UUID = Depends(get_current_user_id),
    api_key_manager: ApiKeyManager = Depends(get_api_key_manager)
):
    """
    Deletes an API key for a specific service.
    
    This endpoint removes a stored API key for an external service.
    This action cannot be undone.
    
    - **service_name**: Name of the service whose API key should be deleted
    
    Returns a success message if the API key was deleted successfully.
    """
    success = await api_key_manager.delete_user_api_key(user_id, service_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"API key for service {service_name} not found")
    
    return {"status": "success", "message": f"API key for service {service_name} deleted"}