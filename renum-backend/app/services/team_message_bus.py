"""
Sistema de mensagens entre agentes de uma equipe.

Este módulo fornece funcionalidades para comunicação entre agentes de uma equipe,
incluindo envio de mensagens, broadcast e sistema de request/response.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator, Union
from datetime import datetime
from uuid import UUID, uuid4

from app.models.team_models import TeamMessage, TeamMessageDB

logger = logging.getLogger(__name__)


class MessageTimeoutError(Exception):
    """Exceção para timeout em mensagens que requerem resposta."""
    pass


class TeamMessageBus:
    """Sistema de mensagens entre agentes de uma equipe."""
    
    def __init__(self, redis_client, db_client=None):
        """
        Inicializa o sistema de mensagens.
        
        Args:
            redis_client: Cliente Redis para comunicação em tempo real
            db_client: Cliente de banco de dados para persistência (opcional)
        """
        self.redis = redis_client
        self.db = db_client
        self.message_channel_prefix = "team_messages:"
        self.response_futures: Dict[str, asyncio.Future] = {}
    
    async def send_message(
        self, 
        execution_id: str,
        from_agent: str,
        to_agent: str,
        message: Union[TeamMessage, Dict[str, Any], str]
    ) -> str:
        """
        Envia uma mensagem para um agente específico.
        
        Args:
            execution_id: ID da execução
            from_agent: ID do agente remetente
            to_agent: ID do agente destinatário
            message: Mensagem a ser enviada (objeto TeamMessage, dict ou string)
            
        Returns:
            ID da mensagem enviada
        """
        # Converte a mensagem para objeto TeamMessage se necessário
        if isinstance(message, str):
            message = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type="info",
                content={"text": message}
            )
        elif isinstance(message, dict):
            if "message_type" not in message:
                message["message_type"] = "info"
            message = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                **message
            )
        
        # Garante que os campos de remetente e destinatário estão corretos
        message.from_agent = from_agent
        message.to_agent = to_agent
        message.execution_id = execution_id
        
        # Gera ID se não tiver
        if not message.message_id:
            message.message_id = uuid4()
        
        # Converte para formato de armazenamento
        message_db = TeamMessageDB(
            message_id=message.message_id,
            execution_id=execution_id,
            from_agent_id=from_agent,
            to_agent_id=to_agent,
            message_type=message.message_type,
            content=message.content,
            requires_response=message.requires_response,
            response_timeout=message.response_timeout,
            created_at=message.timestamp
        )
        
        # Publica no canal do destinatário
        channel = f"{self.message_channel_prefix}{execution_id}:{to_agent}"
        await self.redis.publish(channel, json.dumps(message.dict()))
        
        # Armazena no banco de dados se disponível
        if self.db:
            try:
                await self.db.table('renum_team_messages').insert(message_db.dict()).execute()
            except Exception as e:
                logger.error(f"Failed to store message in database: {str(e)}")
        
        logger.debug(f"Sent message from {from_agent} to {to_agent} in execution {execution_id}")
        
        return str(message.message_id)
    
    async def broadcast_message(
        self, 
        execution_id: str,
        from_agent: str,
        message: Union[TeamMessage, Dict[str, Any], str],
        exclude_agents: List[str] = None
    ) -> str:
        """
        Envia uma mensagem para todos os agentes da equipe.
        
        Args:
            execution_id: ID da execução
            from_agent: ID do agente remetente
            message: Mensagem a ser enviada
            exclude_agents: Lista de agentes a serem excluídos do broadcast
            
        Returns:
            ID da mensagem enviada
        """
        # Converte a mensagem para objeto TeamMessage se necessário
        if isinstance(message, str):
            message = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=None,  # None indica broadcast
                message_type="info",
                content={"text": message}
            )
        elif isinstance(message, dict):
            if "message_type" not in message:
                message["message_type"] = "info"
            message = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=None,  # None indica broadcast
                **message
            )
        
        # Garante que os campos estão corretos
        message.from_agent = from_agent
        message.to_agent = None  # None indica broadcast
        message.execution_id = execution_id
        
        # Gera ID se não tiver
        if not message.message_id:
            message.message_id = uuid4()
        
        # Converte para formato de armazenamento
        message_db = TeamMessageDB(
            message_id=message.message_id,
            execution_id=execution_id,
            from_agent_id=from_agent,
            to_agent_id=None,  # None indica broadcast
            message_type=message.message_type,
            content=message.content,
            requires_response=message.requires_response,
            response_timeout=message.response_timeout,
            created_at=message.timestamp
        )
        
        # Publica no canal de broadcast
        channel = f"{self.message_channel_prefix}{execution_id}:broadcast"
        await self.redis.publish(channel, json.dumps(message.dict()))
        
        # Armazena no banco de dados se disponível
        if self.db:
            try:
                await self.db.table('renum_team_messages').insert(message_db.dict()).execute()
            except Exception as e:
                logger.error(f"Failed to store broadcast message in database: {str(e)}")
        
        logger.debug(f"Broadcast message from {from_agent} in execution {execution_id}")
        
        return str(message.message_id)
    
    async def request_response(
        self, 
        execution_id: str,
        from_agent: str,
        to_agent: str,
        request: Union[TeamMessage, Dict[str, Any], str],
        timeout: int = 30
    ) -> TeamMessage:
        """
        Solicita uma resposta de um agente específico.
        
        Args:
            execution_id: ID da execução
            from_agent: ID do agente solicitante
            to_agent: ID do agente que deve responder
            request: Mensagem de solicitação
            timeout: Timeout em segundos
            
        Returns:
            Mensagem de resposta
            
        Raises:
            MessageTimeoutError: Se o timeout for atingido
            ValueError: Se ocorrer um erro na solicitação
        """
        # Converte a mensagem para objeto TeamMessage se necessário
        if isinstance(request, str):
            request = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type="request",
                content={"text": request},
                requires_response=True,
                response_timeout=timeout
            )
        elif isinstance(request, dict):
            request = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type="request",
                requires_response=True,
                response_timeout=timeout,
                **request
            )
        
        # Garante que os campos estão corretos
        request.from_agent = from_agent
        request.to_agent = to_agent
        request.execution_id = execution_id
        request.message_type = "request"
        request.requires_response = True
        request.response_timeout = timeout
        
        # Gera ID se não tiver
        if not request.message_id:
            request.message_id = uuid4()
        
        # Cria future para aguardar resposta
        response_future = asyncio.Future()
        response_key = f"{execution_id}:{request.message_id}"
        self.response_futures[response_key] = response_future
        
        # Envia a solicitação
        await self.send_message(execution_id, from_agent, to_agent, request)
        
        try:
            # Aguarda a resposta com timeout
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            # Remove o future
            self.response_futures.pop(response_key, None)
            raise MessageTimeoutError(f"Timeout waiting for response from {to_agent}")
        except Exception as e:
            # Remove o future
            self.response_futures.pop(response_key, None)
            raise ValueError(f"Error waiting for response: {str(e)}")
    
    async def respond_to_request(
        self, 
        execution_id: str,
        from_agent: str,
        to_agent: str,
        request_id: str,
        response: Union[TeamMessage, Dict[str, Any], str]
    ) -> str:
        """
        Responde a uma solicitação.
        
        Args:
            execution_id: ID da execução
            from_agent: ID do agente que está respondendo
            to_agent: ID do agente que fez a solicitação
            request_id: ID da mensagem de solicitação
            response: Mensagem de resposta
            
        Returns:
            ID da mensagem de resposta
        """
        # Converte a mensagem para objeto TeamMessage se necessário
        if isinstance(response, str):
            response = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type="response",
                content={"text": response}
            )
        elif isinstance(response, dict):
            response = TeamMessage(
                execution_id=execution_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type="response",
                **response
            )
        
        # Garante que os campos estão corretos
        response.from_agent = from_agent
        response.to_agent = to_agent
        response.execution_id = execution_id
        response.message_type = "response"
        
        # Gera ID se não tiver
        if not response.message_id:
            response.message_id = uuid4()
        
        # Converte para formato de armazenamento
        response_db = TeamMessageDB(
            message_id=response.message_id,
            execution_id=execution_id,
            from_agent_id=from_agent,
            to_agent_id=to_agent,
            message_type="response",
            content=response.content,
            requires_response=False,
            response_message_id=request_id,
            created_at=response.timestamp
        )
        
        # Envia a resposta
        channel = f"{self.message_channel_prefix}{execution_id}:{to_agent}"
        await self.redis.publish(channel, json.dumps(response.dict()))
        
        # Armazena no banco de dados se disponível
        if self.db:
            try:
                # Insere a resposta
                await self.db.table('renum_team_messages').insert(response_db.dict()).execute()
                
                # Atualiza a mensagem original com o ID da resposta
                await self.db.table('renum_team_messages') \
                    .update({"response_message_id": str(response.message_id)}) \
                    .eq('message_id', request_id) \
                    .execute()
            except Exception as e:
                logger.error(f"Failed to store response in database: {str(e)}")
        
        logger.debug(f"Sent response from {from_agent} to {to_agent} for request {request_id}")
        
        return str(response.message_id)
    
    async def subscribe_to_messages(
        self, 
        execution_id: str, 
        agent_id: str
    ) -> AsyncIterator[TeamMessage]:
        """
        Inscreve um agente para receber mensagens.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            
        Yields:
            Mensagens destinadas ao agente
        """
        # Inscreve nos canais específicos para o agente e broadcast
        agent_channel = f"{self.message_channel_prefix}{execution_id}:{agent_id}"
        broadcast_channel = f"{self.message_channel_prefix}{execution_id}:broadcast"
        
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(agent_channel, broadcast_channel)
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Converte a mensagem para objeto TeamMessage
                        message_dict = json.loads(message['data'])
                        team_message = TeamMessage(**message_dict)
                        
                        # Verifica se é uma resposta a uma solicitação
                        if team_message.message_type == "response":
                            # Procura o future correspondente
                            response_key = f"{execution_id}:{team_message.in_reply_to}"
                            future = self.response_futures.get(response_key)
                            if future and not future.done():
                                future.set_result(team_message)
                                # Não yield a mensagem, pois ela será retornada pelo request_response
                                continue
                        
                        # Entrega a mensagem
                        yield team_message
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
        finally:
            # Cancela a inscrição
            await pubsub.unsubscribe(agent_channel, broadcast_channel)
    
    async def get_messages(
        self, 
        execution_id: str, 
        agent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        message_type: Optional[str] = None
    ) -> List[TeamMessageDB]:
        """
        Obtém mensagens do banco de dados.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente (opcional, para filtrar mensagens)
            limit: Limite de mensagens
            offset: Offset para paginação
            message_type: Tipo de mensagem para filtrar
            
        Returns:
            Lista de mensagens
        """
        if not self.db:
            return []
        
        try:
            # Constrói a query
            query = self.db.table('renum_team_messages') \
                .select('*') \
                .eq('execution_id', str(execution_id))
            
            # Aplica filtros opcionais
            if agent_id:
                query = query.or_(f"to_agent_id.eq.{agent_id},from_agent_id.eq.{agent_id}")
            
            if message_type:
                query = query.eq('message_type', message_type)
            
            # Aplica ordenação e paginação
            result = await query.order('created_at', desc=True) \
                .range(offset, offset + limit - 1) \
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Failed to get messages from database: {str(e)}")
            return []
    
    async def process_incoming_message(self, message: TeamMessage) -> None:
        """
        Processa uma mensagem recebida.
        
        Este método é usado para processar mensagens recebidas de fontes externas,
        como o Suna Core, e encaminhá-las para o sistema de mensagens.
        
        Args:
            message: Mensagem recebida
        """
        # Verifica se é uma resposta a uma solicitação
        if message.message_type == "response" and message.in_reply_to:
            # Procura o future correspondente
            response_key = f"{message.execution_id}:{message.in_reply_to}"
            future = self.response_futures.get(response_key)
            if future and not future.done():
                future.set_result(message)
                return
        
        # Encaminha a mensagem para o destinatário
        if message.to_agent:
            # Mensagem para um agente específico
            await self.send_message(
                message.execution_id,
                message.from_agent,
                message.to_agent,
                message
            )
        else:
            # Mensagem de broadcast
            await self.broadcast_message(
                message.execution_id,
                message.from_agent,
                message
            )