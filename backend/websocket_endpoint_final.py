"""
WebSocket Endpoint Final - Versão definitiva com sistema de fallback robusto
Resolve problemas de tokens vazios e falhas de handshake
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt

from services.improved_token_validator import ImprovedTokenValidator
from services.websocket_auth_fallback import WebSocketAuthFallback

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Gerenciador de conexões WebSocket com sistema de fallback robusto"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        self.connection_metadata: Dict[str, dict] = {}
        self.token_validator = ImprovedTokenValidator()
        self.auth_fallback = WebSocketAuthFallback()
        self.max_connections = 1000
        self.connection_timeout = 30
        self.heartbeat_interval = 30
        self.retry_attempts = 3
        self.retry_delay = 1
        
    async def connect(self, websocket: WebSocket, token: Optional[str] = None, 
                     connection_id: Optional[str] = None) -> tuple[bool, str, Optional[str]]:
        """
        Conecta um WebSocket com sistema de fallback robusto
        
        Returns:
            tuple[bool, str, Optional[str]]: (sucesso, mensagem, user_id)
        """
        try:
            # Verificar limite de conexões
            if len(self.active_connections) >= self.max_connections:
                logger.warning(f"Limite de conexões atingido: {len(self.active_connections)}")
                return False, "Limite de conexões atingido", None
            
            # Gerar ID único se não fornecido
            if not connection_id:
                connection_id = f"conn_{int(time.time() * 1000)}_{id(websocket)}"
            
            # Aceitar conexão WebSocket primeiro
            await websocket.accept()
            logger.info(f"WebSocket aceito para conexão {connection_id}")
            
            # Tentar autenticação com fallback
            auth_result = await self._authenticate_with_fallback(websocket, token, connection_id)
            
            if not auth_result["success"]:
                # Enviar erro e fechar conexão
                await self._send_error(websocket, auth_result["error"], auth_result.get("code", "AUTH_FAILED"))
                await websocket.close(code=1008, reason=auth_result["error"])
                return False, auth_result["error"], None
            
            user_id = auth_result["user_id"]
            
            # Registrar conexão
            self.active_connections[connection_id] = websocket
            
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Armazenar metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "token": token,
                "auth_method": auth_result.get("auth_method", "jwt")
            }
            
            # Enviar confirmação de conexão
            await self._send_message(websocket, {
                "type": "connection_established",
                "connection_id": connection_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Conexão estabelecida: {connection_id} para usuário {user_id}")
            return True, "Conectado com sucesso", user_id
            
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket: {str(e)}")
            try:
                await websocket.close(code=1011, reason="Erro interno do servidor")
            except:
                pass
            return False, f"Erro interno: {str(e)}", None
    
    async def _authenticate_with_fallback(self, websocket: WebSocket, token: Optional[str], 
                                        connection_id: str) -> dict:
        """Autentica com sistema de fallback robusto"""
        
        # Tentativa 1: Token JWT fornecido
        if token and token.strip():
            logger.info(f"Tentando autenticação JWT para {connection_id}")
            validation_result = await self.token_validator.validate_token_async(token)
            
            if validation_result["valid"]:
                logger.info(f"Autenticação JWT bem-sucedida para {connection_id}")
                return {
                    "success": True,
                    "user_id": validation_result["user_id"],
                    "auth_method": "jwt"
                }
            else:
                logger.warning(f"Token JWT inválido para {connection_id}: {validation_result['error']}")
        
        # Tentativa 2: Solicitar token via WebSocket
        logger.info(f"Solicitando token via WebSocket para {connection_id}")
        token_request_result = await self._request_token_via_websocket(websocket, connection_id)
        
        if token_request_result["success"]:
            return token_request_result
        
        # Tentativa 3: Autenticação de sessão/fallback
        logger.info(f"Tentando autenticação de fallback para {connection_id}")
        fallback_result = await self.auth_fallback.authenticate_fallback(websocket, connection_id)
        
        if fallback_result["success"]:
            return fallback_result
        
        # Tentativa 4: Modo guest (se habilitado)
        if self.auth_fallback.allow_guest_mode:
            logger.info(f"Permitindo modo guest para {connection_id}")
            return {
                "success": True,
                "user_id": f"guest_{connection_id}",
                "auth_method": "guest"
            }
        
        # Todas as tentativas falharam
        return {
            "success": False,
            "error": "Falha na autenticação: token inválido ou ausente",
            "code": "AUTH_FAILED"
        }
    
    async def _request_token_via_websocket(self, websocket: WebSocket, connection_id: str) -> dict:
        """Solicita token via WebSocket com timeout"""
        try:
            # Enviar solicitação de token
            await self._send_message(websocket, {
                "type": "token_required",
                "message": "Token de autenticação necessário",
                "connection_id": connection_id
            })
            
            # Aguardar resposta com timeout
            try:
                response = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
                
                if response.get("type") == "auth_token" and response.get("token"):
                    token = response["token"]
                    validation_result = await self.token_validator.validate_token_async(token)
                    
                    if validation_result["valid"]:
                        logger.info(f"Token via WebSocket válido para {connection_id}")
                        return {
                            "success": True,
                            "user_id": validation_result["user_id"],
                            "auth_method": "websocket_token"
                        }
                    else:
                        logger.warning(f"Token via WebSocket inválido para {connection_id}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout aguardando token para {connection_id}")
            
        except Exception as e:
            logger.error(f"Erro solicitando token via WebSocket: {str(e)}")
        
        return {"success": False, "error": "Token não fornecido ou inválido"}
    
    async def disconnect(self, connection_id: str):
        """Desconecta um WebSocket"""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                
                # Remover das conexões ativas
                del self.active_connections[connection_id]
                
                # Remover metadata
                metadata = self.connection_metadata.pop(connection_id, {})
                user_id = metadata.get("user_id")
                
                # Remover das conexões do usuário
                if user_id and user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                logger.info(f"Conexão {connection_id} desconectada")
                
        except Exception as e:
            logger.error(f"Erro ao desconectar {connection_id}: {str(e)}")
    
    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """Envia mensagem para todas as conexões de um usuário"""
        if user_id not in self.user_connections:
            return False
        
        success_count = 0
        connections_to_remove = []
        
        for connection_id in self.user_connections[user_id].copy():
            if connection_id in self.active_connections:
                try:
                    websocket = self.active_connections[connection_id]
                    await self._send_message(websocket, message)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Erro enviando para {connection_id}: {str(e)}")
                    connections_to_remove.append(connection_id)
        
        # Remover conexões com falha
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return success_count > 0
    
    async def broadcast(self, message: dict, exclude_user: Optional[str] = None) -> int:
        """Envia mensagem para todas as conexões ativas"""
        success_count = 0
        connections_to_remove = []
        
        for connection_id, websocket in self.active_connections.copy().items():
            try:
                metadata = self.connection_metadata.get(connection_id, {})
                user_id = metadata.get("user_id")
                
                if exclude_user and user_id == exclude_user:
                    continue
                
                await self._send_message(websocket, message)
                success_count += 1
                
            except Exception as e:
                logger.error(f"Erro no broadcast para {connection_id}: {str(e)}")
                connections_to_remove.append(connection_id)
        
        # Remover conexões com falha
        for connection_id in connections_to_remove:
            await self.disconnect(connection_id)
        
        return success_count
    
    async def _send_message(self, websocket: WebSocket, message: dict):
        """Envia mensagem via WebSocket com tratamento de erro"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Erro enviando mensagem: {str(e)}")
            raise
    
    async def _send_error(self, websocket: WebSocket, error: str, code: str = "ERROR"):
        """Envia mensagem de erro"""
        try:
            await self._send_message(websocket, {
                "type": "error",
                "error": error,
                "code": code,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # Ignorar erros ao enviar erro
    
    def get_stats(self) -> dict:
        """Retorna estatísticas das conexões"""
        return {
            "active_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "max_connections": self.max_connections,
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            },
            "uptime_stats": {
                connection_id: {
                    "user_id": metadata.get("user_id"),
                    "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                    "auth_method": metadata.get("auth_method")
                }
                for connection_id, metadata in self.connection_metadata.items()
            }
        }

# Instância global do gerenciador
manager = WebSocketManager()

# Modelos Pydantic
class SendMessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class BroadcastRequest(BaseModel):
    message: str
    exclude_user: Optional[str] = None

def setup_websocket_routes(app: FastAPI):
    """Configura as rotas WebSocket na aplicação FastAPI"""
    
    @app.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: Optional[str] = Query(None, description="JWT token para autenticação")
    ):
        """Endpoint WebSocket principal com autenticação robusta"""
        connection_id = None
        
        try:
            # Tentar extrair token da URL se não fornecido como parâmetro
            if not token:
                query_string = str(websocket.url.query)
                if "token=" in query_string:
                    parsed = parse_qs(query_string)
                    if "token" in parsed and parsed["token"]:
                        token = parsed["token"][0]
            
            # Conectar com sistema de fallback
            success, message, user_id = await manager.connect(websocket, token)
            
            if not success:
                logger.error(f"Falha na conexão WebSocket: {message}")
                return
            
            # Obter connection_id das conexões ativas
            connection_id = None
            for conn_id, ws in manager.active_connections.items():
                if ws == websocket:
                    connection_id = conn_id
                    break
            
            if not connection_id:
                logger.error("Connection ID não encontrado após conexão bem-sucedida")
                return
            
            logger.info(f"WebSocket conectado: {connection_id} (usuário: {user_id})")
            
            # Loop principal de mensagens
            try:
                while True:
                    # Receber mensagem
                    data = await websocket.receive_json()
                    
                    # Atualizar heartbeat
                    if connection_id in manager.connection_metadata:
                        manager.connection_metadata[connection_id]["last_heartbeat"] = datetime.now()
                    
                    # Processar mensagem
                    await process_websocket_message(websocket, connection_id, user_id, data)
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket desconectado normalmente: {connection_id}")
            except Exception as e:
                logger.error(f"Erro no loop WebSocket {connection_id}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Erro crítico no WebSocket: {str(e)}")
        finally:
            # Limpar conexão
            if connection_id:
                await manager.disconnect(connection_id)
    
    async def process_websocket_message(websocket: WebSocket, connection_id: str, 
                                      user_id: str, data: dict):
        """Processa mensagens recebidas via WebSocket"""
        try:
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                await manager._send_message(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "echo":
                await manager._send_message(websocket, {
                    "type": "echo_response",
                    "original_message": data.get("message", ""),
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "broadcast":
                message = data.get("message", "")
                if message:
                    broadcast_data = {
                        "type": "broadcast_message",
                        "message": message,
                        "from_user": user_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    count = await manager.broadcast(broadcast_data, exclude_user=user_id)
                    
                    await manager._send_message(websocket, {
                        "type": "broadcast_sent",
                        "recipients": count,
                        "timestamp": datetime.now().isoformat()
                    })
            
            else:
                await manager._send_message(websocket, {
                    "type": "error",
                    "error": f"Tipo de mensagem desconhecido: {message_type}",
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Erro processando mensagem: {str(e)}")
            await manager._send_message(websocket, {
                "type": "error",
                "error": "Erro interno processando mensagem",
                "timestamp": datetime.now().isoformat()
            })
    
    @app.get("/ws/stats")
    async def get_websocket_stats():
        """Retorna estatísticas das conexões WebSocket"""
        return manager.get_stats()
    
    @app.post("/ws/send/{user_id}")
    async def send_message_to_user(user_id: str, request: SendMessageRequest):
        """Envia mensagem para um usuário específico"""
        message = {
            "type": "direct_message",
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        success = await manager.send_to_user(user_id, message)
        
        if success:
            return {"status": "sent", "user_id": user_id}
        else:
            raise HTTPException(status_code=404, detail="Usuário não encontrado ou não conectado")
    
    @app.post("/ws/broadcast")
    async def broadcast_message(request: BroadcastRequest):
        """Envia mensagem para todas as conexões ativas"""
        message = {
            "type": "broadcast_message",
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        count = await manager.broadcast(message, exclude_user=request.exclude_user)
        
        return {"status": "sent", "recipients": count}
    
    @app.get("/ws/health")
    async def websocket_health():
        """Endpoint de health check para WebSocket"""
        stats = manager.get_stats()
        
        return {
            "status": "healthy",
            "active_connections": stats["active_connections"],
            "unique_users": stats["unique_users"],
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Exemplo de uso
    from fastapi import FastAPI
    
    app = FastAPI(title="WebSocket Final API")
    setup_websocket_routes(app)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)