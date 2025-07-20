"""
Módulo que define os schemas para validação de dados de compartilhamento de agentes.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.agent_share import PermissionLevel

class AgentShareBase(BaseModel):
    """Schema base para compartilhamento de agentes."""
    permission_level: PermissionLevel = Field(
        default=PermissionLevel.VIEW,
        description="Nível de permissão concedido"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais do compartilhamento"
    )

class AgentShareCreate(AgentShareBase):
    """Schema para criação de compartilhamento de agentes."""
    user_id: UUID = Field(..., description="ID do usuário com quem compartilhar")
    days_valid: Optional[int] = Field(
        default=None,
        description="Número de dias que o compartilhamento será válido (None para sem expiração)"
    )

class AgentShareUpdate(BaseModel):
    """Schema para atualização de compartilhamento de agentes."""
    permission_level: Optional[PermissionLevel] = Field(
        default=None,
        description="Novo nível de permissão"
    )
    days_valid: Optional[int] = Field(
        default=None,
        description="Novo número de dias que o compartilhamento será válido (None para sem expiração, 0 para remover expiração)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Novos metadados adicionais do compartilhamento"
    )

class AgentShareResponse(AgentShareBase):
    """Schema para resposta de compartilhamento de agentes."""
    id: UUID = Field(..., description="ID do compartilhamento")
    agent_id: UUID = Field(..., description="ID do agente compartilhado")
    user_id: UUID = Field(..., description="ID do usuário com quem o agente é compartilhado")
    client_id: UUID = Field(..., description="ID do cliente do usuário com quem o agente é compartilhado")
    created_by: UUID = Field(..., description="ID do usuário que criou o compartilhamento")
    created_at: str = Field(..., description="Data de criação do compartilhamento")
    updated_at: str = Field(..., description="Data de última atualização do compartilhamento")
    expires_at: Optional[str] = Field(None, description="Data de expiração do compartilhamento (opcional)")
    
    class Config:
        """Configuração do schema."""
        from_attributes = True

class AgentShareList(BaseModel):
    """Schema para lista de compartilhamentos de agentes."""
    shares: List[AgentShareResponse] = Field(..., description="Lista de compartilhamentos")
    count: int = Field(..., description="Número total de compartilhamentos na lista")

class SharedAgentResponse(BaseModel):
    """Schema para resposta de agente compartilhado."""
    id: UUID = Field(..., description="ID do agente")
    name: str = Field(..., description="Nome do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    status: str = Field(..., description="Status do agente")
    permission_level: PermissionLevel = Field(..., description="Nível de permissão do usuário para este agente")
    shared_at: str = Field(..., description="Data em que o agente foi compartilhado")
    shared_by: UUID = Field(..., description="ID do usuário que compartilhou o agente")
    expires_at: Optional[str] = Field(None, description="Data de expiração do compartilhamento (opcional)")
    
    class Config:
        """Configuração do schema."""
        from_attributes = True

class SharedAgentList(BaseModel):
    """Schema para lista de agentes compartilhados."""
    agents: List[SharedAgentResponse] = Field(..., description="Lista de agentes compartilhados")
    count: int = Field(..., description="Número total de agentes compartilhados na lista")