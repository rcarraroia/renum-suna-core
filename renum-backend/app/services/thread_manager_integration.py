"""
Integração com o ThreadManager do Suna Core.

Este módulo fornece funcionalidades para integrar o sistema de equipes de agentes
com o ThreadManager do Suna Core, permitindo o compartilhamento de contexto entre
agentes e a adição de informações de execução de equipe às mensagens.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID

from app.services.team_context_manager import TeamContextManager
from app.services.team_message_bus import TeamMessageBus

logger = logging.getLogger(__name__)


class TeamThreadManagerIntegration:
    """
    Integração com o ThreadManager do Suna Core.
    
    Esta classe fornece métodos para integrar o sistema de equipes de agentes
    com o ThreadManager do Suna Core, permitindo o compartilhamento de contexto
    entre agentes e a adição de informações de execução de equipe às mensagens.
    """
    
    def __init__(
        self,
        team_context_manager: TeamContextManager,
        team_message_bus: TeamMessageBus
    ):
        """
        Inicializa a integração com o ThreadManager.
        
        Args:
            team_context_manager: Gerenciador de contexto compartilhado
            team_message_bus: Sistema de mensagens entre agentes
        """
        self.team_context_manager = team_context_manager
        self.team_message_bus = team_message_bus
    
    async def extend_thread_manager(self, thread_manager, execution_id: UUID, agent_id: str) -> None:
        """
        Estende o ThreadManager com funcionalidades de equipe.
        
        Esta função modifica o ThreadManager para adicionar informações de execução
        de equipe às mensagens e permitir o compartilhamento de contexto entre agentes.
        
        Args:
            thread_manager: Instância do ThreadManager do Suna Core
            execution_id: ID da execução da equipe
            agent_id: ID do agente
        """
        # Armazena as referências originais para os métodos que serão substituídos
        original_add_message = thread_manager.add_message
        
        # Define o novo método add_message que adiciona informações de execução de equipe
        async def extended_add_message(
            thread_id: str,
            type: str,
            content: Union[Dict[str, Any], List[Any], str],
            is_llm_message: bool = False,
            metadata: Optional[Dict[str, Any]] = None,
            agent_id_param: Optional[str] = None,
            agent_version_id: Optional[str] = None
        ):
            # Cria ou atualiza o metadata se necessário
            if metadata is None:
                metadata = {}
            
            # Adiciona informações de execução de equipe ao metadata
            team_metadata = {
                "team_execution_id": str(execution_id),
                "team_agent_id": agent_id
            }
            
            # Mescla os metadados
            updated_metadata = {**metadata, **team_metadata}
            
            # Chama o método original com os metadados atualizados
            result = await original_add_message(
                thread_id=thread_id,
                type=type,
                content=content,
                is_llm_message=is_llm_message,
                metadata=updated_metadata,
                agent_id=agent_id_param,
                agent_version_id=agent_version_id
            )
            
            # Se a mensagem for do LLM, adiciona ao contexto compartilhado da equipe
            if is_llm_message and type == "text":
                # Adiciona a mensagem ao contexto compartilhado
                await self.team_context_manager.add_message_to_context(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    message_type="assistant",
                    content=content
                )
            
            # Se a mensagem for do usuário, adiciona ao contexto compartilhado
            elif not is_llm_message and type == "text":
                # Adiciona a mensagem ao contexto compartilhado
                await self.team_context_manager.add_message_to_context(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    message_type="user",
                    content=content
                )
            
            return result
        
        # Substitui o método original pelo método estendido
        thread_manager.add_message = extended_add_message
        
        # Adiciona atributos de equipe ao ThreadManager
        thread_manager.team_execution_id = execution_id
        thread_manager.team_agent_id = agent_id
        thread_manager.team_context_manager = self.team_context_manager
        thread_manager.team_message_bus = self.team_message_bus
        
        logger.info(f"ThreadManager estendido com funcionalidades de equipe para execução {execution_id}, agente {agent_id}")
    
    async def create_team_thread_manager(
        self,
        thread_manager_class,
        execution_id: UUID,
        agent_id: str,
        **kwargs
    ):
        """
        Cria uma instância do ThreadManager com funcionalidades de equipe.
        
        Args:
            thread_manager_class: Classe do ThreadManager do Suna Core
            execution_id: ID da execução da equipe
            agent_id: ID do agente
            **kwargs: Argumentos adicionais para o ThreadManager
            
        Returns:
            Instância do ThreadManager com funcionalidades de equipe
        """
        # Cria uma instância do ThreadManager
        thread_manager = thread_manager_class(**kwargs)
        
        # Estende o ThreadManager com funcionalidades de equipe
        await self.extend_thread_manager(thread_manager, execution_id, agent_id)
        
        return thread_manager
    
    async def get_team_context(self, execution_id: UUID) -> Dict[str, Any]:
        """
        Obtém o contexto compartilhado da equipe.
        
        Args:
            execution_id: ID da execução da equipe
            
        Returns:
            Contexto compartilhado da equipe
        """
        return await self.team_context_manager.get_context(execution_id)
    
    async def update_team_context(self, execution_id: UUID, updates: Dict[str, Any]) -> bool:
        """
        Atualiza o contexto compartilhado da equipe.
        
        Args:
            execution_id: ID da execução da equipe
            updates: Atualizações a serem aplicadas ao contexto
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        return await self.team_context_manager.update_context(execution_id, updates)
    
    async def send_team_message(
        self,
        execution_id: UUID,
        from_agent_id: str,
        to_agent_id: Optional[str],
        message_type: str,
        content: Dict[str, Any]
    ) -> UUID:
        """
        Envia uma mensagem entre agentes da equipe.
        
        Args:
            execution_id: ID da execução da equipe
            from_agent_id: ID do agente remetente
            to_agent_id: ID do agente destinatário (None para broadcast)
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            
        Returns:
            ID da mensagem
        """
        return await self.team_message_bus.send_message(
            execution_id=execution_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content
        )
    
    async def get_team_messages(
        self,
        execution_id: UUID,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtém mensagens da equipe.
        
        Args:
            execution_id: ID da execução da equipe
            agent_id: ID do agente para filtrar mensagens (opcional)
            limit: Limite de mensagens a retornar
            
        Returns:
            Lista de mensagens
        """
        return await self.team_message_bus.get_messages(
            execution_id=execution_id,
            agent_id=agent_id,
            limit=limit
        )