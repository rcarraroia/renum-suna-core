"""
Ferramenta para acesso ao contexto compartilhado da equipe.

Este módulo implementa uma ferramenta que permite que os agentes acessem
e modifiquem o contexto compartilhado da equipe.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.services.team_context_manager import TeamContextManager

logger = logging.getLogger(__name__)


class TeamContextTool:
    """
    Ferramenta para acesso ao contexto compartilhado da equipe.
    
    Esta classe implementa uma ferramenta que permite que os agentes acessem
    e modifiquem o contexto compartilhado da equipe.
    """
    
    def __init__(
        self,
        team_context_manager: TeamContextManager,
        execution_id: UUID,
        agent_id: str
    ):
        """
        Inicializa a ferramenta de contexto compartilhado.
        
        Args:
            team_context_manager: Gerenciador de contexto compartilhado
            execution_id: ID da execução da equipe
            agent_id: ID do agente
        """
        self.team_context_manager = team_context_manager
        self.execution_id = execution_id
        self.agent_id = agent_id
    
    async def get_context(self) -> Dict[str, Any]:
        """
        Obtém o contexto compartilhado da equipe.
        
        Returns:
            Contexto compartilhado da equipe
        """
        try:
            context = await self.team_context_manager.get_context(self.execution_id)
            logger.info(f"Agente {self.agent_id} obteve contexto compartilhado da execução {self.execution_id}")
            return context
        except Exception as e:
            logger.error(f"Erro ao obter contexto compartilhado: {str(e)}")
            return {"error": f"Erro ao obter contexto compartilhado: {str(e)}"}
    
    async def get_variable(self, key: str) -> Any:
        """
        Obtém uma variável específica do contexto compartilhado.
        
        Args:
            key: Chave da variável
            
        Returns:
            Valor da variável ou None se não existir
        """
        try:
            value = await self.team_context_manager.get_variable(self.execution_id, key)
            logger.info(f"Agente {self.agent_id} obteve variável '{key}' do contexto compartilhado")
            return value
        except Exception as e:
            logger.error(f"Erro ao obter variável '{key}' do contexto compartilhado: {str(e)}")
            return None
    
    async def set_variable(self, key: str, value: Any) -> bool:
        """
        Define uma variável no contexto compartilhado.
        
        Args:
            key: Chave da variável
            value: Valor da variável
            
        Returns:
            True se a operação foi bem-sucedida
        """
        try:
            success = await self.team_context_manager.set_variable(
                self.execution_id, key, value, self.agent_id
            )
            logger.info(f"Agente {self.agent_id} definiu variável '{key}' no contexto compartilhado")
            return success
        except Exception as e:
            logger.error(f"Erro ao definir variável '{key}' no contexto compartilhado: {str(e)}")
            return False
    
    async def delete_variable(self, key: str) -> bool:
        """
        Remove uma variável do contexto compartilhado.
        
        Args:
            key: Chave da variável
            
        Returns:
            True se a operação foi bem-sucedida
        """
        try:
            success = await self.team_context_manager.delete_variable(
                self.execution_id, key, self.agent_id
            )
            logger.info(f"Agente {self.agent_id} removeu variável '{key}' do contexto compartilhado")
            return success
        except Exception as e:
            logger.error(f"Erro ao remover variável '{key}' do contexto compartilhado: {str(e)}")
            return False
    
    async def add_message_to_context(
        self,
        message_type: str,
        content: Any
    ) -> bool:
        """
        Adiciona uma mensagem ao contexto compartilhado.
        
        Args:
            message_type: Tipo da mensagem
            content: Conteúdo da mensagem
            
        Returns:
            True se a operação foi bem-sucedida
        """
        try:
            success = await self.team_context_manager.add_message_to_context(
                self.execution_id, self.agent_id, message_type, content
            )
            logger.info(f"Agente {self.agent_id} adicionou mensagem ao contexto compartilhado")
            return success
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem ao contexto compartilhado: {str(e)}")
            return False
    
    async def get_messages(
        self,
        limit: int = 10,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém mensagens do contexto compartilhado.
        
        Args:
            limit: Limite de mensagens a retornar
            agent_id: ID do agente para filtrar mensagens (opcional)
            message_type: Tipo de mensagem para filtrar (opcional)
            
        Returns:
            Lista de mensagens
        """
        try:
            messages = await self.team_context_manager.get_messages(
                self.execution_id, limit, agent_id, message_type
            )
            logger.info(f"Agente {self.agent_id} obteve mensagens do contexto compartilhado")
            return messages
        except Exception as e:
            logger.error(f"Erro ao obter mensagens do contexto compartilhado: {str(e)}")
            return []