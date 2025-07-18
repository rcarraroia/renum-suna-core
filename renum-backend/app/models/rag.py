"""
Módulo que define os modelos de dados para o módulo RAG da Plataforma Renum.

Este módulo contém as classes que representam as entidades do módulo RAG,
como bases de conhecimento, coleções, documentos e chunks.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from pydantic import Field, field_validator

from app.models.base import TimestampedEntity


class KnowledgeBase(TimestampedEntity):
    """Modelo para bases de conhecimento."""
    
    client_id: UUID = Field(..., description="ID do cliente proprietário da base de conhecimento")
    name: str = Field(..., description="Nome da base de conhecimento")
    description: Optional[str] = Field(None, description="Descrição da base de conhecimento")


class KnowledgeCollection(TimestampedEntity):
    """Modelo para coleções dentro de bases de conhecimento."""
    
    knowledge_base_id: UUID = Field(..., description="ID da base de conhecimento")
    name: str = Field(..., description="Nome da coleção")
    description: Optional[str] = Field(None, description="Descrição da coleção")


class Document(TimestampedEntity):
    """Modelo para documentos em coleções."""
    
    collection_id: UUID = Field(..., description="ID da coleção")
    name: str = Field(..., description="Nome do documento")
    source_type: str = Field(..., description="Tipo de fonte do documento (arquivo, URL, texto)")
    source_url: Optional[str] = Field(None, description="URL de origem do documento, se aplicável")
    file_type: Optional[str] = Field(None, description="Tipo de arquivo do documento")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")
    status: str = Field("pending", description="Status do processamento do documento")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Valida o status do documento."""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}")
        return v


class DocumentChunk(TimestampedEntity):
    """Modelo para chunks de documentos."""
    
    document_id: UUID = Field(..., description="ID do documento")
    content: str = Field(..., description="Conteúdo do chunk")
    chunk_index: int = Field(..., description="Índice do chunk no documento")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados do chunk")
    embedding_id: Optional[str] = Field(None, description="ID do embedding no banco vetorial")
    embedding: Optional[List[float]] = Field(None, description="Vetor de embedding do chunk")


class DocumentVersion(TimestampedEntity):
    """Modelo para versões de documentos."""
    
    document_id: UUID = Field(..., description="ID do documento")
    version_number: int = Field(..., description="Número da versão")
    change_type: str = Field(..., description="Tipo de alteração (criação, atualização, exclusão)")
    changed_by: Optional[UUID] = Field(None, description="ID do usuário que fez a alteração")
    change_description: Optional[str] = Field(None, description="Descrição da alteração")


class DocumentUsageStats(TimestampedEntity):
    """Modelo para estatísticas de uso de documentos."""
    
    document_id: UUID = Field(..., description="ID do documento")
    chunk_id: Optional[UUID] = Field(None, description="ID do chunk, se aplicável")
    agent_id: Optional[UUID] = Field(None, description="ID do agente que utilizou o documento")
    client_id: UUID = Field(..., description="ID do cliente")
    usage_count: int = Field(1, description="Contador de uso")
    last_used_at: datetime = Field(default_factory=datetime.now, description="Data e hora do último uso")
    first_used_at: datetime = Field(default_factory=datetime.now, description="Data e hora do primeiro uso")


class RetrievalFeedback(TimestampedEntity):
    """Modelo para feedback sobre relevância de recuperação."""
    
    document_id: UUID = Field(..., description="ID do documento")
    chunk_id: UUID = Field(..., description="ID do chunk")
    agent_id: Optional[UUID] = Field(None, description="ID do agente que utilizou o documento")
    client_id: UUID = Field(..., description="ID do cliente")
    query: str = Field(..., description="Consulta que gerou a recuperação")
    relevance_score: float = Field(..., description="Pontuação de relevância (0-1)")
    feedback_source: str = Field("user", description="Fonte do feedback (user, system, agent)")
    
    @field_validator("relevance_score")
    @classmethod
    def validate_relevance_score(cls, v):
        """Valida a pontuação de relevância."""
        if v < 0 or v > 1:
            raise ValueError("Pontuação de relevância deve estar entre 0 e 1")
        return v


class ProcessingJob(TimestampedEntity):
    """Modelo para jobs de processamento."""
    
    document_id: UUID = Field(..., description="ID do documento")
    job_type: str = Field(..., description="Tipo de job (chunking, embedding, indexing)")
    status: str = Field("pending", description="Status do job")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    completed_at: Optional[datetime] = Field(None, description="Data e hora de conclusão")
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Valida o status do job."""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"Status inválido. Valores permitidos: {', '.join(valid_statuses)}")
        return v
    
    @field_validator("job_type")
    @classmethod
    def validate_job_type(cls, v):
        """Valida o tipo de job."""
        valid_types = ["chunking", "embedding", "indexing"]
        if v not in valid_types:
            raise ValueError(f"Tipo de job inválido. Valores permitidos: {', '.join(valid_types)}")
        return v