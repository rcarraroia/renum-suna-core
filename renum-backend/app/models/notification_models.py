"""
Modelos de dados para notificações
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NotificationType(str, Enum):
    """Tipos de notificação"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationAction(BaseModel):
    """Ação associada a uma notificação"""
    type: str = Field(..., description="Tipo da ação (url, callback, etc.)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Dados da ação")


class NotificationCreate(BaseModel):
    """Modelo para criação de notificação"""
    user_id: str = Field(..., description="ID do usuário")
    type: NotificationType = Field(default=NotificationType.INFO, description="Tipo da notificação")
    title: str = Field(..., max_length=200, description="Título da notificação")
    message: str = Field(..., max_length=1000, description="Mensagem da notificação")
    action: Optional[NotificationAction] = Field(None, description="Ação associada")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")


class NotificationUpdate(BaseModel):
    """Modelo para atualização de notificação"""
    read: Optional[bool] = Field(None, description="Status de leitura")
    read_at: Optional[datetime] = Field(None, description="Data de leitura")


class Notification(BaseModel):
    """Modelo de notificação"""
    id: str = Field(..., description="ID único da notificação")
    user_id: str = Field(..., description="ID do usuário")
    type: NotificationType = Field(..., description="Tipo da notificação")
    title: str = Field(..., description="Título da notificação")
    message: str = Field(..., description="Mensagem da notificação")
    read: bool = Field(default=False, description="Status de leitura")
    action: Optional[NotificationAction] = Field(None, description="Ação associada")
    created_at: datetime = Field(..., description="Data de criação")
    read_at: Optional[datetime] = Field(None, description="Data de leitura")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais")

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Estatísticas de notificações"""
    total: int = Field(..., description="Total de notificações")
    unread: int = Field(..., description="Notificações não lidas")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Contagem por tipo")
    recent: int = Field(..., description="Notificações recentes (últimas 24h)")


class NotificationFilter(BaseModel):
    """Filtros para busca de notificações"""
    user_id: Optional[str] = None
    type: Optional[NotificationType] = None
    read: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    order_by: str = Field(default="created_at")
    order_desc: bool = Field(default=True)


class NotificationBatch(BaseModel):
    """Lote de notificações para operações em massa"""
    notifications: list[NotificationCreate] = Field(..., description="Lista de notificações")
    send_immediately: bool = Field(default=True, description="Enviar imediatamente via WebSocket")


class NotificationTemplate(BaseModel):
    """Template de notificação"""
    id: str = Field(..., description="ID do template")
    name: str = Field(..., description="Nome do template")
    type: NotificationType = Field(..., description="Tipo padrão")
    title_template: str = Field(..., description="Template do título")
    message_template: str = Field(..., description="Template da mensagem")
    default_action: Optional[NotificationAction] = Field(None, description="Ação padrão")
    variables: list[str] = Field(default_factory=list, description="Variáveis disponíveis")
    created_at: datetime = Field(..., description="Data de criação")
    updated_at: datetime = Field(..., description="Data de atualização")


class NotificationPreference(BaseModel):
    """Preferências de notificação do usuário"""
    user_id: str = Field(..., description="ID do usuário")
    email_enabled: bool = Field(default=True, description="Notificações por email")
    websocket_enabled: bool = Field(default=True, description="Notificações via WebSocket")
    types_enabled: Dict[str, bool] = Field(
        default_factory=lambda: {
            NotificationType.INFO: True,
            NotificationType.SUCCESS: True,
            NotificationType.WARNING: True,
            NotificationType.ERROR: True,
        },
        description="Tipos de notificação habilitados"
    )
    quiet_hours_start: Optional[str] = Field(None, description="Início do período silencioso (HH:MM)")
    quiet_hours_end: Optional[str] = Field(None, description="Fim do período silencioso (HH:MM)")
    timezone: str = Field(default="UTC", description="Fuso horário do usuário")
    updated_at: datetime = Field(..., description="Data de atualização")