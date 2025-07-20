"""
Módulo que define os modelos de dados para compartilhamento de agentes da Plataforma Renum.
Este módulo contém as classes que representam compartilhamentos de agentes e permissões.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum
from pydantic import Field

from app.models.base import TimestampedEntity

class PermissionLevel(str, Enum):
    """Enum para níveis de permissão de compartilhamento."""
    VIEW = "view"  # Apenas visualização
    USE = "use"    # Visualização e uso do agente
    EDIT = "edit"  # Visualização, uso e edição
    ADMIN = "admin"  # Controle total, incluindo compartilhamento

class AgentShare(TimestampedEntity):
    """Modelo para compartilhamento de agentes."""
    agent_id: UUID = Field(..., description="ID do agente compartilhado")
    user_id: UUID = Field(..., description="ID do usuário com quem o agente é compartilhado")
    client_id: UUID = Field(..., description="ID do cliente do usuário com quem o agente é compartilhado")
    permission_level: PermissionLevel = Field(default=PermissionLevel.VIEW, description="Nível de permissão concedido")
    created_by: UUID = Field(..., description="ID do usuário que criou o compartilhamento")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração do compartilhamento (opcional)")
    metadata: dict = Field(default_factory=dict, description="Metadados adicionais do compartilhamento")
    
    class Config:
        """Configuração do modelo."""
        schema_extra = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "agent_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "client_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "permission_level": "view",
                "created_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "created_at": "2025-07-19T14:30:00Z",
                "updated_at": "2025-07-19T14:30:00Z",
                "expires_at": None,
                "metadata": {}
            }
        }
"""