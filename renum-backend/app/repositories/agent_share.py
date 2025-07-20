"""
Módulo que implementa os repositórios para gerenciamento de compartilhamento de agentes da Plataforma Renum.
Este módulo contém as implementações específicas do padrão Repository para as
entidades de gerenciamento de compartilhamento de agentes.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime

from app.core.supabase_client import supabase
from app.models.agent_share import AgentShare, PermissionLevel
from app.repositories.base import SupabaseRepository

# Configurar logger
logger = logging.getLogger(__name__)

class AgentShareRepository(SupabaseRepository[AgentShare]):
    """Repositório para compartilhamento de agentes."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "renum_agent_shares")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> AgentShare:
        """Converte um dicionário de dados em uma entidade AgentShare.
        
        Args:
            data: Dicionário com os dados do compartilhamento.
            
        Returns:
            Entidade AgentShare correspondente aos dados.
        """
        return AgentShare(**data)
    
    def _map_to_dict(self, entity: AgentShare) -> Dict[str, Any]:
        """Converte uma entidade AgentShare em um dicionário de dados.
        
        Args:
            entity: Entidade AgentShare a ser convertida.
            
        Returns:
            Dicionário com os dados do compartilhamento.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_agent_id(self, agent_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[AgentShare]:
        """Recupera compartilhamentos de um agente específico.
        
        Args:
            agent_id: ID do agente.
            limit: Número máximo de compartilhamentos a serem retornados.
            offset: Número de compartilhamentos a serem pulados.
            
        Returns:
            Lista de compartilhamentos do agente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("agent_id", str(agent_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_user_id(self, user_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[AgentShare]:
        """Recupera compartilhamentos para um usuário específico.
        
        Args:
            user_id: ID do usuário.
            limit: Número máximo de compartilhamentos a serem retornados.
            offset: Número de compartilhamentos a serem pulados.
            
        Returns:
            Lista de compartilhamentos para o usuário.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("user_id", str(user_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_agent_and_user(self, agent_id: Union[str, UUID], user_id: Union[str, UUID]) -> Optional[AgentShare]:
        """Recupera um compartilhamento específico entre um agente e um usuário.
        
        Args:
            agent_id: ID do agente.
            user_id: ID do usuário.
            
        Returns:
            Compartilhamento entre o agente e o usuário, se existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("agent_id", str(agent_id)).eq("user_id", str(user_id)).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        
        return None
    
    async def update_permission_level(self, share_id: Union[str, UUID], permission_level: PermissionLevel) -> AgentShare:
        """Atualiza o nível de permissão de um compartilhamento.
        
        Args:
            share_id: ID do compartilhamento.
            permission_level: Novo nível de permissão.
            
        Returns:
            Compartilhamento atualizado.
        """
        update_data = {
            "permission_level": permission_level,
            "updated_at": datetime.now().isoformat()
        }
        
        result = await self.supabase.from_(self.table_name).update(update_data).eq("id", str(share_id)).execute()
        
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        
        raise ValueError(f"Falha ao atualizar nível de permissão do compartilhamento com ID {share_id}")
    
    async def get_shared_agents_for_user(self, user_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Recupera agentes compartilhados com um usuário específico.
        
        Args:
            user_id: ID do usuário.
            limit: Número máximo de agentes a serem retornados.
            offset: Número de agentes a serem pulados.
            
        Returns:
            Lista de agentes compartilhados com o usuário, incluindo detalhes do compartilhamento.
        """
        # Consulta com join para obter detalhes do agente e do compartilhamento
        query = f"""
        SELECT a.*, s.permission_level, s.created_at as shared_at, s.created_by as shared_by
        FROM agents a
        JOIN agent_shares s ON a.id = s.agent_id
        WHERE s.user_id = '{str(user_id)}'
        ORDER BY s.created_at DESC
        LIMIT {limit} OFFSET {offset}
        """
        
        result = await self.supabase.rpc("execute_sql", {"query": query}).execute()
        return result.data if result.data else []
    
    async def check_user_permission(self, agent_id: Union[str, UUID], user_id: Union[str, UUID], required_level: PermissionLevel) -> bool:
        """Verifica se um usuário tem o nível de permissão necessário para um agente.
        
        Args:
            agent_id: ID do agente.
            user_id: ID do usuário.
            required_level: Nível de permissão necessário.
            
        Returns:
            True se o usuário tem o nível de permissão necessário, False caso contrário.
        """
        # Primeiro, verificar se o usuário é o proprietário do agente
        agent_query = await self.supabase.from_("agents").select("client_id, created_by").eq("id", str(agent_id)).limit(1).execute()
        
        if agent_query.data and len(agent_query.data) > 0:
            agent_data = agent_query.data[0]
            
            # Se o usuário é o criador do agente, ele tem todas as permissões
            if agent_data.get("created_by") == str(user_id):
                return True
            
            # Verificar compartilhamento
            share_query = await self.supabase.from_(self.table_name).select("permission_level").eq("agent_id", str(agent_id)).eq("user_id", str(user_id)).limit(1).execute()
            
            if share_query.data and len(share_query.data) > 0:
                user_permission = PermissionLevel(share_query.data[0].get("permission_level"))
                
                # Mapear níveis de permissão para valores numéricos para comparação
                permission_values = {
                    PermissionLevel.VIEW: 1,
                    PermissionLevel.USE: 2,
                    PermissionLevel.EDIT: 3,
                    PermissionLevel.ADMIN: 4
                }
                
                return permission_values[user_permission] >= permission_values[required_level]
        
        return False


# Instância global do repositório
agent_share_repository = AgentShareRepository()
"""