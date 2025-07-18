"""
Módulo que define os modelos de dados para agentes da Plataforma Renum.
Este módulo contém as classes que representam agentes e suas execuções.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum
from pydantic import Field

from app.models.base import TimestampedEntity

class AgentStatus(str, Enum):
    """Enum para status de agentes."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"

class AgentExecutionStatus(str, Enum):
    """Enum para status de execuções de agentes."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class Agent(TimestampedEntity):
    """Modelo para agentes."""
    name: str = Field(..., description="Nome do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    client_id: UUID = Field(..., description="ID do cliente proprietário do agente")
    configuration: Dict[str, Any] = Field(..., description="Configuração do agente")
    status: AgentStatus = Field(default=AgentStatus.DRAFT, description="Status do agente")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais do agente")
    knowledge_base_ids: Optional[List[UUID]] = Field(default=None, description="IDs das bases de conhecimento associadas")
    created_by: Optional[UUID] = Field(None, description="ID do usuário que criou o agente")
    updated_by: Optional[UUID] = Field(None, description="ID do usuário que atualizou o agente pela última vez")

class AgentExecution(TimestampedEntity):
    """Modelo para execuções de agentes."""
    agent_id: UUID = Field(..., description="ID do agente executado")
    user_id: UUID = Field(..., description="ID do usuário que iniciou a execução")
    client_id: UUID = Field(..., description="ID do cliente")
    status: AgentExecutionStatus = Field(default=AgentExecutionStatus.PENDING, description="Status da execução")
    input: Dict[str, Any] = Field(..., description="Entrada para a execução")
    output: Optional[Dict[str, Any]] = Field(None, description="Saída da execução")
    error: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    tokens_used: Optional[int] = Field(None, description="Número de tokens utilizados")
    started_at: datetime = Field(default_factory=datetime.now, description="Data e hora de início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data e hora de conclusão da execução")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais da execução")
    context_used: Optional[Dict[str, Any]] = Field(None, description="Contexto utilizado na execução")
    tools_used: Optional[List[str]] = Field(None, description="Ferramentas utilizadas na execução")
"""