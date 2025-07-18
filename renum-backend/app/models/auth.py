"""
Módulo que define os modelos de dados para autenticação e autorização da Plataforma Renum.

Este módulo contém as classes que representam usuários, clientes e sessões.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from pydantic import Field, EmailStr

from app.models.base import TimestampedEntity


class UserRole(str, Enum):
    """Enum para papéis de usuário."""
    
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class ClientStatus(str, Enum):
    """Enum para status de cliente."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class Client(TimestampedEntity):
    """Modelo para clientes da plataforma (organizações)."""
    
    name: str = Field(..., description="Nome do cliente")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE, description="Status do cliente")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Configurações do cliente")


class User(TimestampedEntity):
    """Modelo para usuários da plataforma."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    client_id: UUID = Field(..., description="ID do cliente ao qual o usuário pertence")
    role: UserRole = Field(default=UserRole.USER, description="Papel do usuário")
    display_name: Optional[str] = Field(None, description="Nome de exibição do usuário")
    avatar_url: Optional[str] = Field(None, description="URL do avatar do usuário")
    last_login: Optional[datetime] = Field(None, description="Data e hora do último login")
    is_active: bool = Field(default=True, description="Se o usuário está ativo")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais do usuário")


class Session(TimestampedEntity):
    """Modelo para sessões de usuário."""
    
    user_id: UUID = Field(..., description="ID do usuário")
    token: str = Field(..., description="Token de sessão")
    expires_at: datetime = Field(..., description="Data e hora de expiração da sessão")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Informações sobre o dispositivo")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    is_active: bool = Field(default=True, description="Se a sessão está ativa")
    last_activity: datetime = Field(default_factory=datetime.now, description="Data e hora da última atividade")


class PasswordResetToken(TimestampedEntity):
    """Modelo para tokens de redefinição de senha."""
    
    user_id: UUID = Field(..., description="ID do usuário")
    token: str = Field(..., description="Token de redefinição de senha")
    expires_at: datetime = Field(..., description="Data e hora de expiração do token")
    is_used: bool = Field(default=False, description="Se o token já foi usado")
    used_at: Optional[datetime] = Field(None, description="Data e hora em que o token foi usado")