"""
Repositório para gerenciamento de equipes de agentes.

Este módulo implementa o repositório para operações CRUD de equipes de agentes,
incluindo criação, atualização, consulta e exclusão de equipes.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from app.models.team_models import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    PaginatedTeamResponse
)
from app.db.database import Database

logger = logging.getLogger(__name__)


class TeamRepository:
    """Repositório para gerenciamento de equipes de agentes."""
    
    def __init__(self, db: Database):
        """
        Inicializa o repositório.
        
        Args:
            db: Conexão com o banco de dados
        """
        self.db = db
    
    async def create_team(self, user_id: UUID, team_data: TeamCreate) -> TeamResponse:
        """
        Cria uma nova equipe.
        
        Args:
            user_id: ID do usuário
            team_data: Dados da equipe
            
        Returns:
            Objeto TeamResponse com os dados da equipe criada
            
        Raises:
            ValueError: Se ocorrer um erro na criação da equipe
        """
        try:
            # Valida os agentes
            await self._validate_agents(user_id, team_data.agent_ids)
            
            # Prepara os dados para inserção
            team_dict = {
                "user_id": str(user_id),
                "name": team_data.name,
                "description": team_data.description,
                "agent_ids": team_data.agent_ids,
                "workflow_definition": team_data.workflow_definition.dict(),
                "user_api_keys": team_data.user_api_keys or {},
                "team_config": team_data.team_config or {},
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "created_by": str(user_id)
            }
            
            # Insere no banco de dados
            result = await self.db.table('renum_agent_teams').insert(team_dict).execute()
            
            if not result.data:
                raise ValueError("Failed to create team")
            
            # Obtém o ID da equipe criada
            team_id = result.data[0]['team_id']
            
            # Retorna os dados da equipe
            return TeamResponse(
                team_id=team_id,
                user_id=user_id,
                name=team_data.name,
                description=team_data.description,
                agent_ids=team_data.agent_ids,
                workflow_definition=team_data.workflow_definition,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to create team: {str(e)}")
            raise ValueError(f"Failed to create team: {str(e)}")
    
    async def get_team(self, team_id: UUID, user_id: UUID) -> Optional[TeamResponse]:
        """
        Obtém os dados de uma equipe.
        
        Args:
            team_id: ID da equipe
            user_id: ID do usuário
            
        Returns:
            Objeto TeamResponse com os dados da equipe ou None se não existir
        """
        try:
            # Consulta o banco de dados
            result = await self.db.table('renum_agent_teams') \
                .select('*') \
                .eq('team_id', str(team_id)) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not result.data:
                return None
            
            team_data = result.data[0]
            
            # Converte para objeto TeamResponse
            return TeamResponse(
                team_id=team_data['team_id'],
                user_id=team_data['user_id'],
                name=team_data['name'],
                description=team_data['description'],
                agent_ids=team_data['agent_ids'],
                workflow_definition=team_data['workflow_definition'],
                is_active=team_data['is_active'],
                created_at=datetime.fromisoformat(team_data['created_at']),
                updated_at=datetime.fromisoformat(team_data['updated_at'])
            )
            
        except Exception as e:
            logger.error(f"Failed to get team {team_id}: {str(e)}")
            return None
    
    async def get_team_config(self, team_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Obtém a configuração completa de uma equipe.
        
        Args:
            team_id: ID da equipe
            user_id: ID do usuário
            
        Returns:
            Configuração da equipe ou None se não existir
        """
        try:
            # Consulta o banco de dados
            result = await self.db.table('renum_agent_teams') \
                .select('*') \
                .eq('team_id', str(team_id)) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not result.data:
                return None
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get team config {team_id}: {str(e)}")
            return None
    
    async def update_team(self, team_id: UUID, user_id: UUID, team_data: TeamUpdate) -> Optional[TeamResponse]:
        """
        Atualiza uma equipe existente.
        
        Args:
            team_id: ID da equipe
            user_id: ID do usuário
            team_data: Dados atualizados da equipe
            
        Returns:
            Objeto TeamResponse com os dados atualizados ou None se não existir
            
        Raises:
            ValueError: Se ocorrer um erro na atualização da equipe
        """
        try:
            # Verifica se a equipe existe
            team = await self.get_team(team_id, user_id)
            if not team:
                return None
            
            # Prepara os dados para atualização
            update_data = {}
            
            if team_data.name is not None:
                update_data["name"] = team_data.name
            
            if team_data.description is not None:
                update_data["description"] = team_data.description
            
            if team_data.agent_ids is not None:
                # Valida os agentes
                await self._validate_agents(user_id, team_data.agent_ids)
                update_data["agent_ids"] = team_data.agent_ids
            
            if team_data.workflow_definition is not None:
                update_data["workflow_definition"] = team_data.workflow_definition.dict()
            
            if team_data.user_api_keys is not None:
                update_data["user_api_keys"] = team_data.user_api_keys
            
            if team_data.team_config is not None:
                update_data["team_config"] = team_data.team_config
            
            if team_data.is_active is not None:
                update_data["is_active"] = team_data.is_active
            
            # Adiciona timestamp de atualização
            update_data["updated_at"] = datetime.now().isoformat()
            
            # Atualiza no banco de dados
            if update_data:
                await self.db.table('renum_agent_teams') \
                    .update(update_data) \
                    .eq('team_id', str(team_id)) \
                    .eq('user_id', str(user_id)) \
                    .execute()
            
            # Retorna os dados atualizados
            return await self.get_team(team_id, user_id)
            
        except Exception as e:
            logger.error(f"Failed to update team {team_id}: {str(e)}")
            raise ValueError(f"Failed to update team: {str(e)}")
    
    async def delete_team(self, team_id: UUID, user_id: UUID) -> bool:
        """
        Exclui uma equipe.
        
        Args:
            team_id: ID da equipe
            user_id: ID do usuário
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            # Verifica se a equipe existe
            team = await self.get_team(team_id, user_id)
            if not team:
                return False
            
            # Exclui do banco de dados
            await self.db.table('renum_agent_teams') \
                .delete() \
                .eq('team_id', str(team_id)) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete team {team_id}: {str(e)}")
            return False
    
    async def list_teams(
        self, 
        user_id: UUID, 
        page: int = 1, 
        limit: int = 10,
        name_filter: Optional[str] = None,
        active_only: bool = True
    ) -> PaginatedTeamResponse:
        """
        Lista equipes do usuário.
        
        Args:
            user_id: ID do usuário
            page: Número da página
            limit: Limite de resultados por página
            name_filter: Filtro por nome
            active_only: Incluir apenas equipes ativas
            
        Returns:
            Objeto PaginatedTeamResponse com a lista de equipes
        """
        try:
            # Calcula o offset
            offset = (page - 1) * limit
            
            # Constrói a query
            query = self.db.table('renum_agent_teams') \
                .select('*') \
                .eq('user_id', str(user_id))
            
            # Aplica filtros opcionais
            if active_only:
                query = query.eq('is_active', True)
            
            if name_filter:
                query = query.ilike('name', f'%{name_filter}%')
            
            # Conta o total de resultados
            count_query = query.count()
            count_result = await count_query.execute()
            total = count_result.count
            
            # Aplica paginação e ordenação
            query = query.order('created_at', desc=True) \
                .range(offset, offset + limit - 1)
            
            # Executa a query
            result = await query.execute()
            
            # Converte para objetos TeamResponse
            teams = []
            for team_data in result.data:
                teams.append(TeamResponse(
                    team_id=team_data['team_id'],
                    user_id=team_data['user_id'],
                    name=team_data['name'],
                    description=team_data['description'],
                    agent_ids=team_data['agent_ids'],
                    workflow_definition=team_data['workflow_definition'],
                    is_active=team_data['is_active'],
                    created_at=datetime.fromisoformat(team_data['created_at']),
                    updated_at=datetime.fromisoformat(team_data['updated_at'])
                ))
            
            # Calcula o total de páginas
            total_pages = (total + limit - 1) // limit
            
            # Retorna a resposta paginada
            return PaginatedTeamResponse(
                items=teams,
                total=total,
                page=page,
                limit=limit,
                pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to list teams: {str(e)}")
            # Retorna uma lista vazia em caso de erro
            return PaginatedTeamResponse(
                items=[],
                total=0,
                page=page,
                limit=limit,
                pages=0
            )
    
    async def _validate_agents(self, user_id: UUID, agent_ids: List[str]) -> bool:
        """
        Valida se os agentes pertencem ao usuário.
        
        Args:
            user_id: ID do usuário
            agent_ids: Lista de IDs dos agentes
            
        Returns:
            True se todos os agentes são válidos
            
        Raises:
            ValueError: Se algum agente não for válido
        """
        # Implementação simplificada - em um sistema real, verificaria no Suna Core
        if not agent_ids:
            raise ValueError("Agent IDs list cannot be empty")
        
        if len(agent_ids) > 10:
            raise ValueError("Maximum of 10 agents per team")
        
        # Aqui você implementaria a verificação real dos agentes
        # Por exemplo, consultando o Suna Core para verificar se os agentes existem
        # e pertencem ao usuário
        
        return True