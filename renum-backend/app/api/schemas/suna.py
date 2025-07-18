"""
Módulo que define os esquemas para os endpoints de proxy da Suna Core.

Este módulo contém as classes que representam os esquemas de requisição e resposta
para os endpoints de proxy da Suna Core.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

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

class HealthCheckResponse(BaseModel):
    """Esquema para resposta de verificação de saúde."""
    
    status: str = Field(..., description="Status da API")
    message: str = Field(..., description="Mensagem de status")

class ToolsResponse(BaseModel):
    """Esquema para resposta de ferramentas disponíveis."""
    
    tools: List[str] = Field(..., description="Lista de ferramentas disponíveis")

class ModelsResponse(BaseModel):
    """Esquema para resposta de modelos disponíveis."""
    
    models: List[Dict[str, Any]] = Field(..., description="Lista de modelos disponíveis")