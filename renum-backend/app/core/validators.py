"""
Validadores para o sistema de Equipes de Agentes.

Este módulo contém funções de validação para verificar permissões,
limites e outras restrições do sistema.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.core.config import get_settings
from app.models.team_models import TeamCreate, TeamUpdate

logger = logging.getLogger(__name__)


async def validate_agent_ownership(
    user_id: UUID,
    agent_ids: List[str],
    suna_client
) -> bool:
    """
    Valida se os agentes pertencem ao usuário.
    
    Args:
        user_id: ID do usuário
        agent_ids: Lista de IDs dos agentes
        suna_client: Cliente da API do Suna Core
        
    Returns:
        True se todos os agentes pertencem ao usuário
        
    Raises:
        ValueError: Se algum agente não pertencer ao usuário
    """
    if not agent_ids:
        return True
    
    try:
        # Verifica cada agente no Suna Core
        for agent_id in agent_ids:
            agent = await suna_client.get_agent(agent_id)
            
            # Se o agente não existir ou não pertencer ao usuário, lança uma exceção
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
            
            if str(agent.get("user_id")) != str(user_id):
                raise ValueError(f"Agent {agent_id} does not belong to the user")
        
        return True
    
    except Exception as e:
        logger.error(f"Error validating agent ownership: {str(e)}")
        raise ValueError(f"Error validating agent ownership: {str(e)}")


async def validate_team_limits(
    team_data: TeamCreate,
    user_id: UUID,
    team_repository
) -> bool:
    """
    Valida os limites de uma equipe.
    
    Args:
        team_data: Dados da equipe
        user_id: ID do usuário
        team_repository: Repositório de equipes
        
    Returns:
        True se a equipe está dentro dos limites
        
    Raises:
        ValueError: Se a equipe exceder algum limite
    """
    settings = get_settings()
    
    # Verifica o número de agentes
    if len(team_data.agent_ids) > settings.MAX_AGENTS_PER_TEAM:
        raise ValueError(f"Maximum number of agents per team is {settings.MAX_AGENTS_PER_TEAM}")
    
    # Verifica o número de equipes do usuário
    teams = await team_repository.list_teams(user_id, page=1, limit=1000)
    if teams.total >= 100:  # Limite arbitrário de 100 equipes por usuário
        raise ValueError("Maximum number of teams per user reached (100)")
    
    return True


async def validate_team_update(
    team_data: TeamUpdate,
    team_id: UUID,
    user_id: UUID,
    team_repository,
    suna_client
) -> bool:
    """
    Valida a atualização de uma equipe.
    
    Args:
        team_data: Dados atualizados da equipe
        team_id: ID da equipe
        user_id: ID do usuário
        team_repository: Repositório de equipes
        suna_client: Cliente da API do Suna Core
        
    Returns:
        True se a atualização é válida
        
    Raises:
        ValueError: Se a atualização for inválida
    """
    settings = get_settings()
    
    # Verifica se a equipe existe e pertence ao usuário
    team = await team_repository.get_team(team_id, user_id)
    if not team:
        raise ValueError(f"Team {team_id} not found")
    
    # Verifica o número de agentes
    if team_data.agent_ids and len(team_data.agent_ids) > settings.MAX_AGENTS_PER_TEAM:
        raise ValueError(f"Maximum number of agents per team is {settings.MAX_AGENTS_PER_TEAM}")
    
    # Verifica a propriedade dos agentes
    if team_data.agent_ids:
        await validate_agent_ownership(user_id, team_data.agent_ids, suna_client)
    
    return True


async def validate_execution_limits(
    user_id: UUID,
    execution_repository
) -> bool:
    """
    Valida os limites de execução para um usuário.
    
    Args:
        user_id: ID do usuário
        execution_repository: Repositório de execuções
        
    Returns:
        True se o usuário está dentro dos limites de execução
        
    Raises:
        ValueError: Se o usuário exceder o limite de execuções simultâneas
    """
    # Importa o BillingManager
    from app.services.billing_manager import BillingManager
    from app.core.dependencies import get_billing_manager
    
    # Cria uma instância do BillingManager
    billing_manager = BillingManager(execution_repository)
    
    # Verifica os limites de uso
    await billing_manager.check_usage_limits(user_id)
    
    return True