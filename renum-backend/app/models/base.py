"""
Módulo que define os modelos base para a Plataforma Renum.

Este módulo contém as classes base para os modelos de dados da plataforma.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict


class RenumBaseModel(BaseModel):
    """Modelo base para todos os modelos da Plataforma Renum."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    )


class Entity(RenumBaseModel):
    """Modelo base para entidades com ID."""
    
    id: Optional[UUID] = Field(default_factory=uuid4, description="Identificador único da entidade")


class TimestampedEntity(Entity):
    """Modelo base para entidades com timestamps de criação e atualização."""
    
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Data e hora de criação")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="Data e hora da última atualização")