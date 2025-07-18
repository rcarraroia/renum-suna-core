"""
Módulo que define os esquemas de requisição e resposta para os endpoints de autenticação e autorização.

Este módulo contém as classes Pydantic que definem a estrutura dos dados
que são enviados e recebidos pelos endpoints REST de autenticação e autorização.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.models.auth import UserRole, ClientStatus


class UserCreate(BaseModel):
    """Esquema para criação de usuário."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")
    client_id: UUID = Field(..., description="ID do cliente ao qual o usuário pertence")
    role: UserRole = Field(default=UserRole.USER, description="Papel do usuário")
    display_name: Optional[str] = Field(None, description="Nome de exibição do usuário")


class UserUpdate(BaseModel):
    """Esquema para atualização de usuário."""
    
    display_name: Optional[str] = Field(None, description="Nome de exibição do usuário")
    role: Optional[UserRole] = Field(None, description="Papel do usuário")
    is_active: Optional[bool] = Field(None, description="Se o usuário está ativo")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais do usuário")


class UserResponse(BaseModel):
    """Esquema para resposta de usuário."""
    
    id: UUID = Field(..., description="ID do usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    client_id: UUID = Field(..., description="ID do cliente ao qual o usuário pertence")
    role: UserRole = Field(..., description="Papel do usuário")
    display_name: Optional[str] = Field(None, description="Nome de exibição do usuário")
    avatar_url: Optional[str] = Field(None, description="URL do avatar do usuário")
    last_login: Optional[datetime] = Field(None, description="Data e hora do último login")
    is_active: bool = Field(..., description="Se o usuário está ativo")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora da última atualização")


class ClientCreate(BaseModel):
    """Esquema para criação de cliente."""
    
    name: str = Field(..., description="Nome do cliente")
    status: ClientStatus = Field(default=ClientStatus.ACTIVE, description="Status do cliente")
    settings: Optional[Dict[str, Any]] = Field(None, description="Configurações do cliente")


class ClientUpdate(BaseModel):
    """Esquema para atualização de cliente."""
    
    name: Optional[str] = Field(None, description="Nome do cliente")
    status: Optional[ClientStatus] = Field(None, description="Status do cliente")
    settings: Optional[Dict[str, Any]] = Field(None, description="Configurações do cliente")


class ClientResponse(BaseModel):
    """Esquema para resposta de cliente."""
    
    id: UUID = Field(..., description="ID do cliente")
    name: str = Field(..., description="Nome do cliente")
    status: ClientStatus = Field(..., description="Status do cliente")
    settings: Dict[str, Any] = Field(..., description="Configurações do cliente")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora da última atualização")


class LoginRequest(BaseModel):
    """Esquema para requisição de login."""
    
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., description="Senha do usuário")


class LoginResponse(BaseModel):
    """Esquema para resposta de login."""
    
    user: UserResponse = Field(..., description="Informações do usuário")
    access_token: str = Field(..., description="Token de acesso JWT")
    refresh_token: str = Field(..., description="Token de atualização JWT")
    session_token: str = Field(..., description="Token de sessão")
    expires_at: datetime = Field(..., description="Data e hora de expiração da sessão")


class LogoutRequest(BaseModel):
    """Esquema para requisição de logout."""
    
    session_token: str = Field(..., description="Token de sessão a ser encerrada")


class LogoutResponse(BaseModel):
    """Esquema para resposta de logout."""
    
    success: bool = Field(..., description="Se o logout foi bem-sucedido")


class SessionResponse(BaseModel):
    """Esquema para resposta de sessão."""
    
    id: UUID = Field(..., description="ID da sessão")
    user_id: UUID = Field(..., description="ID do usuário")
    device_info: Dict[str, Any] = Field(..., description="Informações sobre o dispositivo")
    ip_address: Optional[str] = Field(None, description="Endereço IP")
    is_active: bool = Field(..., description="Se a sessão está ativa")
    created_at: datetime = Field(..., description="Data e hora de criação")
    last_activity: datetime = Field(..., description="Data e hora da última atividade")
    expires_at: datetime = Field(..., description="Data e hora de expiração")


class PasswordResetRequest(BaseModel):
    """Esquema para requisição de redefinição de senha."""
    
    email: EmailStr = Field(..., description="Email do usuário")


class PasswordResetResponse(BaseModel):
    """Esquema para resposta de redefinição de senha."""
    
    success: bool = Field(..., description="Se a solicitação foi processada com sucesso")
    message: str = Field(..., description="Mensagem informativa")


class PasswordResetConfirmRequest(BaseModel):
    """Esquema para confirmação de redefinição de senha."""
    
    token: str = Field(..., description="Token de redefinição de senha")
    new_password: str = Field(..., description="Nova senha")


class PasswordResetConfirmResponse(BaseModel):
    """Esquema para resposta de confirmação de redefinição de senha."""
    
    success: bool = Field(..., description="Se a senha foi redefinida com sucesso")
    message: str = Field(..., description="Mensagem informativa")


class PasswordChangeRequest(BaseModel):
    """Esquema para requisição de alteração de senha."""
    
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., description="Nova senha")


class PasswordChangeResponse(BaseModel):
    """Esquema para resposta de alteração de senha."""
    
    success: bool = Field(..., description="Se a senha foi alterada com sucesso")
    message: str = Field(..., description="Mensagem informativa")