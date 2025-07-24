"""
Ferramenta para comunicação entre agentes da equipe.

Este módulo implementa uma ferramenta que permite que os agentes se comuniquem
entre si através do sistema de mensagens da equipe.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.services.team_message_bus import TeamMessageBus

logger = logging.getLogger(__name__)


class TeamMessageTool:
    """
    Ferramenta para comunicação entre agentes da equipe.
    
    Esta classe implementa uma ferramenta que permite que os agentes se comuniquem
    entre si através do sistema de mensagens da equipe.
    """
    
    def __init__(
        self,
        team_message_bus: TeamMessageBus,
        execution_id: UUID,
        agent_id: str
    ):
        """
        Inicializa a ferramenta de mensagens da equipe.
        
        Args:
            team_message_bus: Sistema de mensagens entre agentes
            execution_id: ID da execução da equipe
            agent_id: ID do agente
        """
        self.team_message_bus = team_message_bus
        self.execution_id = execution_id
        self.agent_id = agent_id
    
    async def send_message(
        self,
        to_agent_id: str,
        message_type: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Envia uma mensagem para outro agente da equipe.
        
        Args:
            to_agent_id: ID do agente destinatário
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            
        Returns:
            ID da mensagem
        """
        try:
            message_id = await self.team_message_bus.send_message(
                execution_id=self.execution_id,
                from_agent_id=self.agent_id,
                to_agent_id=to_agent_id,
                message_type=message_type,
                content=content
            )
            logger.info(f"Agente {self.agent_id} enviou mensagem para agente {to_agent_id}")
            return str(message_id)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para agente {to_agent_id}: {str(e)}")
            return f"Erro: {str(e)}"
    
    async def broadcast_message(
        self,
        message_type: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Envia uma mensagem para todos os agentes da equipe.
        
        Args:
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            
        Returns:
            ID da mensagem
        """
        try:
            message_id = await self.team_message_bus.broadcast_message(
                execution_id=self.execution_id,
                from_agent_id=self.agent_id,
                message_type=message_type,
                content=content
            )
            logger.info(f"Agente {self.agent_id} enviou mensagem para todos os agentes")
            return str(message_id)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para todos os agentes: {str(e)}")
            return f"Erro: {str(e)}"
    
    async def request_response(
        self,
        to_agent_id: str,
        message_type: str,
        content: Dict[str, Any],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem e aguarda resposta de outro agente.
        
        Args:
            to_agent_id: ID do agente destinatário
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            timeout: Tempo limite em segundos para aguardar resposta
            
        Returns:
            Resposta do agente ou dicionário com erro
        """
        try:
            response = await self.team_message_bus.request_response(
                execution_id=self.execution_id,
                from_agent_id=self.agent_id,
                to_agent_id=to_agent_id,
                message_type=message_type,
                content=content,
                timeout=timeout
            )
            logger.info(f"Agente {self.agent_id} recebeu resposta do agente {to_agent_id}")
            return response
        except Exception as e:
            logger.error(f"Erro ao solicitar resposta do agente {to_agent_id}: {str(e)}")
            return {"error": str(e)}
    
    async def get_messages(
        self,
        limit: int = 10,
        from_agent_id: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém mensagens recebidas pelo agente.
        
        Args:
            limit: Limite de mensagens a retornar
            from_agent_id: ID do agente remetente para filtrar mensagens (opcional)
            message_type: Tipo de mensagem para filtrar (opcional)
            
        Returns:
            Lista de mensagens
        """
        try:
            messages = await self.team_message_bus.get_messages(
                execution_id=self.execution_id,
                agent_id=self.agent_id,
                limit=limit,
                from_agent_id=from_agent_id,
                message_type=message_type
            )
            logger.info(f"Agente {self.agent_id} obteve mensagens")
            return messages
        except Exception as e:
            logger.error(f"Erro ao obter mensagens: {str(e)}")
            return []
    
    async def respond_to_request(
        self,
        request_message_id: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Responde a uma solicitação de outro agente.
        
        Args:
            request_message_id: ID da mensagem de solicitação
            content: Conteúdo da resposta
            
        Returns:
            ID da mensagem de resposta
        """
        try:
            message_id = await self.team_message_bus.respond_to_request(
                execution_id=self.execution_id,
                request_message_id=UUID(request_message_id),
                from_agent_id=self.agent_id,
                content=content
            )
            logger.info(f"Agente {self.agent_id} respondeu à solicitação {request_message_id}")
            return str(message_id)
        except Exception as e:
            logger.error(f"Erro ao responder à solicitação {request_message_id}: {str(e)}")
            return f"Erro: {str(e)}"