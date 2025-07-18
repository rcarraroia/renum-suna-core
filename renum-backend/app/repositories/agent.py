"""
Módulo que implementa os repositórios para gerenciamento de agentes da Plataforma Renum.
Este módulo contém as implementações específicas do padrão Repository para as
entidades de gerenciamento de agentes.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime

from app.core.supabase_client import supabase
from app.models.agent import Agent, AgentExecution, AgentStatus, AgentExecutionStatus
from app.repositories.base import SupabaseRepository

# Configurar logger
logger = logging.getLogger(__name__)

class AgentRepository(SupabaseRepository[Agent]):
    """Repositório para agentes."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "agents")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Agent:
        """Converte um dicionário de dados em uma entidade Agent.
        
        Args:
            data: Dicionário com os dados do agente.
            
        Returns:
            Entidade Agent correspondente aos dados.
        """
        return Agent(**data)
    
    def _map_to_dict(self, entity: Agent) -> Dict[str, Any]:
        """Converte uma entidade Agent em um dicionário de dados.
        
        Args:
            entity: Entidade Agent a ser convertida.
            
        Returns:
            Dicionário com os dados do agente.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_client_id(self, client_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[Agent]:
        """Recupera agentes de um cliente específico.
        
        Args:
            client_id: ID do cliente.
            limit: Número máximo de agentes a serem retornados.
            offset: Número de agentes a serem pulados.
            
        Returns:
            Lista de agentes do cliente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("client_id", str(client_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_status(self, status: AgentStatus, client_id: Optional[Union[str, UUID]] = None, limit: int = 100, offset: int = 0) -> List[Agent]:
        """Recupera agentes com um status específico.
        
        Args:
            status: Status dos agentes a serem recuperados.
            client_id: ID do cliente (opcional).
            limit: Número máximo de agentes a serem retornados.
            offset: Número de agentes a serem pulados.
            
        Returns:
            Lista de agentes com o status especificado.
        """
        query = self.supabase.from_(self.table_name).select("*").eq("status", status).limit(limit).offset(offset)
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        
        result = await query.execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def update_status(self, agent_id: Union[str, UUID], status: AgentStatus, updated_by: Optional[Union[str, UUID]] = None) -> Agent:
        """Atualiza o status de um agente.
        
        Args:
            agent_id: ID do agente.
            status: Novo status do agente.
            updated_by: ID do usuário que está atualizando o status.
            
        Returns:
            Agente atualizado.
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if updated_by:
            update_data["updated_by"] = str(updated_by)
        
        result = await self.supabase.from_(self.table_name).update(update_data).eq("id", str(agent_id)).execute()
        
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        
        raise ValueError(f"Falha ao atualizar status do agente com ID {agent_id}")
    
    async def get_by_knowledge_base(self, knowledge_base_id: Union[str, UUID], client_id: Optional[Union[str, UUID]] = None, limit: int = 100, offset: int = 0) -> List[Agent]:
        """Recupera agentes associados a uma base de conhecimento específica.
        
        Args:
            knowledge_base_id: ID da base de conhecimento.
            client_id: ID do cliente (opcional).
            limit: Número máximo de agentes a serem retornados.
            offset: Número de agentes a serem pulados.
            
        Returns:
            Lista de agentes associados à base de conhecimento.
        """
        # Usando a função de array do PostgreSQL para buscar em arrays
        query = self.supabase.from_(self.table_name).select("*").contains("knowledge_base_ids", [str(knowledge_base_id)]).limit(limit).offset(offset)
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        
        result = await query.execute()
        return [self._map_to_entity(item) for item in result.data]


class AgentExecutionRepository(SupabaseRepository[AgentExecution]):
    """Repositório para execuções de agentes."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "agent_executions")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> AgentExecution:
        """Converte um dicionário de dados em uma entidade AgentExecution.
        
        Args:
            data: Dicionário com os dados da execução.
            
        Returns:
            Entidade AgentExecution correspondente aos dados.
        """
        return AgentExecution(**data)
    
    def _map_to_dict(self, entity: AgentExecution) -> Dict[str, Any]:
        """Converte uma entidade AgentExecution em um dicionário de dados.
        
        Args:
            entity: Entidade AgentExecution a ser convertida.
            
        Returns:
            Dicionário com os dados da execução.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_agent_id(self, agent_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[AgentExecution]:
        """Recupera execuções de um agente específico.
        
        Args:
            agent_id: ID do agente.
            limit: Número máximo de execuções a serem retornadas.
            offset: Número de execuções a serem puladas.
            
        Returns:
            Lista de execuções do agente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("agent_id", str(agent_id)).order("started_at", desc=True).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_user_id(self, user_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[AgentExecution]:
        """Recupera execuções iniciadas por um usuário específico.
        
        Args:
            user_id: ID do usuário.
            limit: Número máximo de execuções a serem retornadas.
            offset: Número de execuções a serem puladas.
            
        Returns:
            Lista de execuções do usuário.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("user_id", str(user_id)).order("started_at", desc=True).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_client_id(self, client_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[AgentExecution]:
        """Recupera execuções de um cliente específico.
        
        Args:
            client_id: ID do cliente.
            limit: Número máximo de execuções a serem retornadas.
            offset: Número de execuções a serem puladas.
            
        Returns:
            Lista de execuções do cliente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("client_id", str(client_id)).order("started_at", desc=True).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_status(self, status: AgentExecutionStatus, client_id: Optional[Union[str, UUID]] = None, limit: int = 100, offset: int = 0) -> List[AgentExecution]:
        """Recupera execuções com um status específico.
        
        Args:
            status: Status das execuções a serem recuperadas.
            client_id: ID do cliente (opcional).
            limit: Número máximo de execuções a serem retornadas.
            offset: Número de execuções a serem puladas.
            
        Returns:
            Lista de execuções com o status especificado.
        """
        query = self.supabase.from_(self.table_name).select("*").eq("status", status).order("started_at", desc=True).limit(limit).offset(offset)
        
        if client_id:
            query = query.eq("client_id", str(client_id))
        
        result = await query.execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def update_status(self, execution_id: Union[str, UUID], status: AgentExecutionStatus, output: Optional[Dict[str, Any]] = None, error: Optional[str] = None, tokens_used: Optional[int] = None) -> AgentExecution:
        """Atualiza o status de uma execução.
        
        Args:
            execution_id: ID da execução.
            status: Novo status da execução.
            output: Saída da execução (opcional).
            error: Mensagem de erro (opcional).
            tokens_used: Número de tokens utilizados (opcional).
            
        Returns:
            Execução atualizada.
        """
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        
        if status in [AgentExecutionStatus.COMPLETED, AgentExecutionStatus.FAILED, AgentExecutionStatus.CANCELLED, AgentExecutionStatus.TIMEOUT]:
            update_data["completed_at"] = datetime.now().isoformat()
        
        if output is not None:
            update_data["output"] = output
        
        if error is not None:
            update_data["error"] = error
        
        if tokens_used is not None:
            update_data["tokens_used"] = tokens_used
        
        result = await self.supabase.from_(self.table_name).update(update_data).eq("id", str(execution_id)).execute()
        
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        
        raise ValueError(f"Falha ao atualizar status da execução com ID {execution_id}")
    
    async def get_recent_executions(self, client_id: Union[str, UUID], days: int = 30, limit: int = 100) -> List[AgentExecution]:
        """Recupera execuções recentes de um cliente.
        
        Args:
            client_id: ID do cliente.
            days: Número de dias para considerar como recente.
            limit: Número máximo de execuções a serem retornadas.
            
        Returns:
            Lista de execuções recentes do cliente.
        """
        # Calcular a data de início (hoje - dias)
        start_date = (datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        result = await self.supabase.from_(self.table_name).select("*").eq("client_id", str(client_id)).gte("started_at", start_date).order("started_at", desc=True).limit(limit).execute()
        return [self._map_to_entity(item) for item in result.data]


# Instâncias globais dos repositórios
agent_repository = AgentRepository()
agent_execution_repository = AgentExecutionRepository()
"""