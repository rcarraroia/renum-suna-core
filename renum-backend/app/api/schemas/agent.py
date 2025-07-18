"""
Módulo que define os esquemas para os endpoints de agentes.

Este módulo contém as classes que representam os esquemas de requisição e resposta
para os endpoints de agentes.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

class AgentBase(BaseModel):
    """Esquema base para agentes."""
    
    name: str = Field(..., description="Nome do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    configuration: Dict[str, Any] = Field(..., description="Configuração do agente")
    knowledge_base_ids: Optional[List[UUID]] = Field(None, description="IDs das bases de conhecimento associadas")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais do agente")

class AgentCreate(AgentBase):
    """Esquema para criação de agente."""
    
    pass

class AgentUpdate(BaseModel):
    """Esquema para atualização de agente."""
    
    name: Optional[str] = Field(None, description="Nome do agente")
    description: Optional[str] = Field(None, description="Descrição do agente")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Configuração do agente")
    status: Optional[str] = Field(None, description="Status do agente")
    knowledge_base_ids: Optional[List[UUID]] = Field(None, description="IDs das bases de conhecimento associadas")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais do agente")

class AgentResponse(AgentBase):
    """Esquema para resposta de agente."""
    
    id: UUID = Field(..., description="ID do agente")
    client_id: UUID = Field(..., description="ID do cliente proprietário do agente")
    status: str = Field(..., description="Status do agente")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora de atualização")
    created_by: Optional[UUID] = Field(None, description="ID do usuário que criou o agente")
    updated_by: Optional[UUID] = Field(None, description="ID do usuário que atualizou o agente pela última vez")
    
    class Config:
        """Configuração do modelo."""
        
        from_attributes = True

class AgentExecutionCreate(BaseModel):
    """Esquema para criação de execução de agente."""
    
    input: Dict[str, Any] = Field(..., description="Entrada para a execução")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais da execução")

class AgentExecutionRequest(BaseModel):
    """Esquema para requisição de execução de agente."""
    
    prompt: str = Field(..., description="Prompt para o agente")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadados adicionais")

class AgentExecutionResponse(BaseModel):
    """Esquema para resposta de execução de agente."""
    
    execution_id: UUID = Field(..., description="ID da execução")
    status: str = Field(..., description="Status da execução")
    created_at: datetime = Field(..., description="Data e hora de criação")
    message: str = Field(..., description="Mensagem de status")

class AgentExecutionStatusResponse(BaseModel):
    """Esquema para resposta de status de execução."""
    
    execution_id: UUID = Field(..., description="ID da execução")
    agent_id: UUID = Field(..., description="ID do agente")
    status: str = Field(..., description="Status da execução")
    created_at: datetime = Field(..., description="Data e hora de criação")
    started_at: datetime = Field(..., description="Data e hora de início")
    completed_at: Optional[datetime] = Field(None, description="Data e hora de conclusão")
    output: Optional[Dict[str, Any]] = Field(None, description="Saída da execução")
    error: Optional[str] = Field(None, description="Mensagem de erro")
    tokens_used: Optional[int] = Field(None, description="Número de tokens utilizados")

class ToolCallbackRequest(BaseModel):
    """Esquema para requisição de callback de ferramenta."""
    
    execution_id: UUID = Field(..., description="ID da execução")
    parameters: Dict[str, Any] = Field(..., description="Parâmetros da ferramenta")

class ToolCallbackResponse(BaseModel):
    """Esquema para resposta de callback de ferramenta."""
    
    success: bool = Field(..., description="Indicador de sucesso")
    data: Dict[str, Any] = Field(..., description="Dados da resposta")