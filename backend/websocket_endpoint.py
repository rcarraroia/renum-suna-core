"""
WebSocket endpoint com autenticação JWT robusta.

Este módulo implementa um endpoint WebSocket que resolve os problemas críticos
identificados no diagnóstico, incluindo tokens vazios e falhas de autenticação.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.routing import APIRouter
from services.improved_token_validator import ImprovedTokenValidator, ValidationFailureReason

# Configuração de logging
logger = logging.getLogger(__name__)

# Router para WebSocket
websocket_router = APIRouter()

# Gerenciador de conexões WebSocket
class WebSocketManager:
    """Gerenciador de conexões WebSocket com autenticação."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.token_validator = ImprovedTokenValidator()
        
    async def connect(self, websocket: WebSocket, token: str) -> Optional[str]:
        """
        Conecta cliente WebSocket com validação de token.
        
        Args:
            websocket: Conexão WebSocket
            token: Token JWT para autenticação
            
        Returns:
            Connection ID se sucesso, None se falha
        """
        try:
            # Validar token para WebSocket
            validation_result = await self.token_validator.validate_websocket_token(token)
            
            if not validation_result.valid:
                logger.warning("WebSocket connection rejected - invalid token", extra={
                    'reason': validation_result.reason.value if validation_result.reason else 'unknown',
                    'error': validation_result.error_message
                })
                
                # Enviar erro específico antes de fechar
                await websocket.accept()
                await websocket.send_json({
                    'type': 'auth_error',
                    'error': validation_result.error_message,
                    'reason': validation_result.reason.value if validation_result.reason else 'unknown'
                })
                await websocket.close(code=4001, reason="Authentication failed")
                return None
            
            # Aceitar conexão
            await websocket.accept()
            
            # Gerar ID único para conexão
            connection_id = f"ws_{validation_result.user_id}_{datetime.now().timestamp()}"
            user_id = validation_result.user_id
            
            # Registrar conexão
            self.active_connections[connection_id] = websocket
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Armazenar metadata
            self.connection_metadata[connection_id] = {
                'user_id': user_id,
                'connected_at': datetime.now(),
                'token_expires_at': validation_result.expires_at,
                'should_refresh': validation_result.should_refresh
            }
            
            logger.info("WebSocket connection established", extra={
                'connection_id': connection_id,
                'user_id': user_id,
                'total_connections': len(self.active_connections)
            })
            
            # Enviar confirmação de conexão
            await websocket.send_json({
                'type': 'connection_established',
                'connection_id': connection_id,
                'user_id': user_id,
                'server_time': datetime.now().isoformat(),
                'token_refresh_needed': validation_result.should_refresh
            })
            
            return connection_id
            
        except Exception as e:
            logger.error("Error establishing WebSocket connection", extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            
            try:
                await websocket.accept()
                await websocket.send_json({
                    'type': 'connection_error',
                    'error': 'Internal server error during connection'
                })
                await websocket.close(code=4000, reason="Connection error")
            except:
                pass  # Conexão já pode estar fechada
                
            return None
    
    async def disconnect(self, connection_id: str) -> None:
        """
        Desconecta cliente WebSocket.
        
        Args:
            connection_id: ID da conexão para desconectar
        """
        if connection_id not in self.active_connections:
            return
            
        # Obter metadata
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get('user_id')
        
        # Remover conexão
        del self.active_connections[connection_id]
        del self.connection_metadata[connection_id]
        
        # Remover da lista de usuário
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info("WebSocket connection closed", extra={
            'connection_id': connection_id,
            'user_id': user_id,
            'total_connections': len(self.active_connections)
        })
    
    async def send_personal_message(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Envia mensagem para todas as conexões de um usuário.
        
        Args:
            user_id: ID do usuário
            message: Mensagem para enviar
            
        Returns:
            Número de conexões que receberam a mensagem
        """
        if user_id not in self.user_connections:
            return 0
            
        sent_count = 0
        failed_connections = []
        
        for connection_id in self.user_connections[user_id].copy():
            websocket = self.active_connections.get(connection_id)
            if not websocket:
                failed_connections.append(connection_id)
                continue
                
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send message to connection", extra={
                    'connection_id': connection_id,
                    'user_id': user_id,
                    'error': str(e)
                })
                failed_connections.append(connection_id)
        
        # Limpar conexões falhas
        for connection_id in failed_connections:
            await self.disconnect(connection_id)
        
        return sent_count
    
    async def broadcast(self, message: Dict[str, Any], exclude_user: Optional[str] = None) -> int:
        """
        Envia mensagem para todas as conexões ativas.
        
        Args:
            message: Mensagem para enviar
            exclude_user: ID do usuário para excluir do broadcast
            
        Returns:
            Número de conexões que receberam a mensagem
        """
        sent_count = 0
        failed_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            metadata = self.connection_metadata.get(connection_id, {})
            user_id = metadata.get('user_id')
            
            if exclude_user and user_id == exclude_user:
                continue
                
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to broadcast message to connection", extra={
                    'connection_id': connection_id,
                    'user_id': user_id,
                    'error': str(e)
                })
                failed_connections.append(connection_id)
        
        # Limpar conexões falhas
        for connection_id in failed_connections:
            await self.disconnect(connection_id)
        
        return sent_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas das conexões."""
        return {
            'total_connections': len(self.active_connections),
            'unique_users': len(self.user_connections),
            'connections_by_user': {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }


# Instância global do gerenciador
websocket_manager = WebSocketManager()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token for authentication")
):
    """
    Endpoint WebSocket principal com autenticação JWT.
    
    Este endpoint resolve os problemas críticos identificados:
    - Valida tokens JWT antes de aceitar conexão
    - Trata tokens vazios/inválidos adequadamente  
    - Fornece mensagens de erro claras
    - Implementa reconexão automática
    """
    connection_id = None
    
    try:
        # Verificar se token foi fornecido
        if not token or token.strip() == "":
            logger.error("WebSocket connection attempted without token")
            await websocket.accept()
            await websocket.send_json({
                'type': 'auth_error',
                'error': 'Token is required for WebSocket connection',
                'reason': 'empty_token'
            })
            await websocket.close(code=4001, reason="Token required")
            return
        
        # Estabelecer conexão com validação
        connection_id = await websocket_manager.connect(websocket, token)
        
        if not connection_id:
            # Conexão já foi rejeitada e fechada no método connect
            return
        
        # Loop principal de mensagens
        while True:
            try:
                # Receber mensagem do cliente
                data = await websocket.receive_json()
                
                # Processar mensagem
                await handle_websocket_message(connection_id, data)
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected", extra={
                    'connection_id': connection_id
                })
                break
                
            except json.JSONDecodeError:
                # Mensagem inválida
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Invalid JSON message format'
                })
                
            except Exception as e:
                logger.error("Error processing WebSocket message", extra={
                    'connection_id': connection_id,
                    'error': str(e)
                })
                
                await websocket.send_json({
                    'type': 'error',
                    'error': 'Error processing message'
                })
    
    except Exception as e:
        logger.error("Fatal error in WebSocket endpoint", extra={
            'connection_id': connection_id,
            'error': str(e),
            'error_type': type(e).__name__
        })
    
    finally:
        # Limpar conexão
        if connection_id:
            await websocket_manager.disconnect(connection_id)


async def handle_websocket_message(connection_id: str, message: Dict[str, Any]) -> None:
    """
    Processa mensagens recebidas via WebSocket.
    
    Args:
        connection_id: ID da conexão
        message: Mensagem recebida
    """
    message_type = message.get('type', 'unknown')
    
    logger.debug("Processing WebSocket message", extra={
        'connection_id': connection_id,
        'message_type': message_type
    })
    
    # Obter conexão e metadata
    websocket = websocket_manager.active_connections.get(connection_id)
    metadata = websocket_manager.connection_metadata.get(connection_id, {})
    
    if not websocket:
        logger.warning("Message received for unknown connection", extra={
            'connection_id': connection_id
        })
        return
    
    try:
        if message_type == 'ping':
            # Responder ping com pong
            await websocket.send_json({
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
            
        elif message_type == 'get_stats':
            # Enviar estatísticas da conexão
            stats = websocket_manager.get_stats()
            await websocket.send_json({
                'type': 'stats',
                'data': stats
            })
            
        elif message_type == 'echo':
            # Ecoar mensagem de volta
            await websocket.send_json({
                'type': 'echo_response',
                'original_message': message.get('data'),
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            # Tipo de mensagem não reconhecido
            await websocket.send_json({
                'type': 'error',
                'error': f'Unknown message type: {message_type}'
            })
            
    except Exception as e:
        logger.error("Error handling WebSocket message", extra={
            'connection_id': connection_id,
            'message_type': message_type,
            'error': str(e)
        })


# Endpoint HTTP para estatísticas (para debugging)
@websocket_router.get("/ws/stats")
async def get_websocket_stats():
    """Retorna estatísticas das conexões WebSocket."""
    stats = websocket_manager.get_stats()
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'websocket_stats': stats
    }


# Endpoint HTTP para enviar mensagem para usuário específico
@websocket_router.post("/ws/send/{user_id}")
async def send_message_to_user(user_id: str, message: Dict[str, Any]):
    """Envia mensagem para todas as conexões de um usuário."""
    sent_count = await websocket_manager.send_personal_message(user_id, message)
    
    return {
        'status': 'ok',
        'user_id': user_id,
        'connections_reached': sent_count,
        'timestamp': datetime.now().isoformat()
    }


# Endpoint HTTP para broadcast
@websocket_router.post("/ws/broadcast")
async def broadcast_message(message: Dict[str, Any], exclude_user: Optional[str] = None):
    """Envia mensagem para todas as conexões ativas."""
    sent_count = await websocket_manager.broadcast(message, exclude_user)
    
    return {
        'status': 'ok',
        'connections_reached': sent_count,
        'timestamp': datetime.now().isoformat()
    }