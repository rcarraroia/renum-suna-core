"""
Modelos para WebSocket.

Este módulo define os modelos de dados para WebSocket, incluindo conexões,
mensagens e notificações.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from uuid import UUID


class WebSocketConnectionStatus(str, Enum):
    """Status de uma conexão WebSocket."""
    
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    IDLE = "idle"


class WebSocketMessageType(str, Enum):
    """Tipo de mensagem WebSocket."""
    
    NOTIFICATION = "notification"
    EXECUTION_UPDATE = "execution_update"
    SYSTEM_EVENT = "system_event"
    COMMAND = "command"
    RESPONSE = "response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class WebSocketConnection(BaseModel):
    """Modelo para uma conexão WebSocket."""
    
    connection_id: str = Field(..., description="ID único da conexão")
    user_id: str = Field(..., description="ID do usuário")
    status: WebSocketConnectionStatus = Field(
        default=WebSocketConnectionStatus.CONNECTED,
        description="Status da conexão"
    )
    connected_at: datetime = Field(default_factory=datetime.now, description="Data e hora da conexão")
    last_activity: datetime = Field(default_factory=datetime.now, description="Data e hora da última atividade")
    subscribed_channels: List[str] = Field(default_factory=list, description="Canais inscritos")
    client_info: Dict[str, Any] = Field(default_factory=dict, description="Informações do cliente")


class WebSocketMessage(BaseModel):
    """Modelo para uma mensagem WebSocket."""
    
    type: WebSocketMessageType = Field(..., description="Tipo da mensagem")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Conteúdo da mensagem")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data e hora da mensagem")
    channel: Optional[str] = Field(None, description="Canal da mensagem")
    sender: Optional[str] = Field(None, description="Remetente da mensagem")
    target: Optional[Union[str, List[str]]] = Field(None, description="Destinatário(s) da mensagem")


class WebSocketNotification(BaseModel):
    """Modelo para uma notificação WebSocket."""
    
    id: str = Field(..., description="ID único da notificação")
    user_id: str = Field(..., description="ID do usuário destinatário")
    type: str = Field(..., description="Tipo da notificação")
    title: str = Field(..., description="Título da notificação")
    message: str = Field(..., description="Mensagem da notificação")
    read: bool = Field(default=False, description="Indica se a notificação foi lida")
    created_at: datetime = Field(default_factory=datetime.now, description="Data e hora de criação")
    action: Optional[Dict[str, Any]] = Field(None, description="Ação associada à notificação")


class WebSocketExecutionUpdate(BaseModel):
    """Modelo para uma atualização de execução via WebSocket."""
    
    execution_id: UUID = Field(..., description="ID da execução")
    team_id: UUID = Field(..., description="ID da equipe")
    status: str = Field(..., description="Status da execução")
    progress: float = Field(..., description="Progresso da execução (0-100)")
    current_step: Optional[str] = Field(None, description="Etapa atual da execução")
    result: Optional[Dict[str, Any]] = Field(None, description="Resultado da execução")
    error: Optional[str] = Field(None, description="Erro da execução")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data e hora da atualização")


class WebSocketCommand(BaseModel):
    """Modelo para um comando WebSocket enviado pelo cliente."""
    
    command: str = Field(..., description="Nome do comando")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros do comando")


class WebSocketResponse(BaseModel):
    """Modelo para uma resposta WebSocket enviada pelo servidor."""
    
    request_id: Optional[str] = Field(None, description="ID da requisição")
    success: bool = Field(..., description="Indica se o comando foi bem-sucedido")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados da resposta")
    error: Optional[str] = Field(None, description="Mensagem de erro")


class WebSocketStats(BaseModel):
    """Modelo para estatísticas de WebSocket."""
    
    total_connections: int = Field(..., description="Número total de conexões")
    active_users: int = Field(..., description="Número de usuários ativos")
    channels: Dict[str, int] = Field(..., description="Número de conexões por canal")
    connection_rate: float = Field(..., description="Taxa de conexões por minuto")
    message_rate: float = Field(..., description="Taxa de mensagens por minuto")
    uptime: float = Field(..., description="Tempo de atividade em segundos")