"""
Módulo que define os esquemas para os endpoints do módulo RAG.

Este módulo contém as classes que representam os esquemas de requisição e resposta
para os endpoints do módulo RAG.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

class KnowledgeBaseBase(BaseModel):
    """Esquema base para bases de conhecimento."""
    
    name: str = Field(..., description="Nome da base de conhecimento")
    description: Optional[str] = Field(None, description="Descrição da base de conhecimento")

class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Esquema para criação de base de conhecimento."""
    
    pass

class KnowledgeBaseUpdate(BaseModel):
    """Esquema para atualização de base de conhecimento."""
    
    name: Optional[str] = Field(None, description="Nome da base de conhecimento")
    description: Optional[str] = Field(None, description="Descrição da base de conhecimento")

class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Esquema para resposta de base de conhecimento."""
    
    id: UUID = Field(..., description="ID da base de conhecimento")
    client_id: UUID = Field(..., description="ID do cliente proprietário da base de conhecimento")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora de atualização")
    
    class Config:
        """Configuração do modelo."""
        
        from_attributes = True

class KnowledgeCollectionBase(BaseModel):
    """Esquema base para coleções de conhecimento."""
    
    name: str = Field(..., description="Nome da coleção")
    description: Optional[str] = Field(None, description="Descrição da coleção")

class KnowledgeCollectionCreate(KnowledgeCollectionBase):
    """Esquema para criação de coleção de conhecimento."""
    
    knowledge_base_id: UUID = Field(..., description="ID da base de conhecimento")

class KnowledgeCollectionUpdate(BaseModel):
    """Esquema para atualização de coleção de conhecimento."""
    
    name: Optional[str] = Field(None, description="Nome da coleção")
    description: Optional[str] = Field(None, description="Descrição da coleção")

class KnowledgeCollectionResponse(KnowledgeCollectionBase):
    """Esquema para resposta de coleção de conhecimento."""
    
    id: UUID = Field(..., description="ID da coleção")
    knowledge_base_id: UUID = Field(..., description="ID da base de conhecimento")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora de atualização")
    
    class Config:
        """Configuração do modelo."""
        
        from_attributes = True

class DocumentBase(BaseModel):
    """Esquema base para documentos."""
    
    name: str = Field(..., description="Nome do documento")
    source_type: str = Field(..., description="Tipo de fonte do documento (arquivo, URL, texto)")
    source_url: Optional[str] = Field(None, description="URL de origem do documento, se aplicável")
    file_type: Optional[str] = Field(None, description="Tipo de arquivo do documento")
    file_size: Optional[int] = Field(None, description="Tamanho do arquivo em bytes")

class DocumentCreate(DocumentBase):
    """Esquema para criação de documento."""
    
    collection_id: UUID = Field(..., description="ID da coleção")
    content: Optional[str] = Field(None, description="Conteúdo do documento, se for do tipo texto")

class DocumentUpdate(BaseModel):
    """Esquema para atualização de documento."""
    
    name: Optional[str] = Field(None, description="Nome do documento")
    status: Optional[str] = Field(None, description="Status do processamento do documento")

class DocumentResponse(DocumentBase):
    """Esquema para resposta de documento."""
    
    id: UUID = Field(..., description="ID do documento")
    collection_id: UUID = Field(..., description="ID da coleção")
    status: str = Field(..., description="Status do processamento do documento")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora de atualização")
    
    class Config:
        """Configuração do modelo."""
        
        from_attributes = True

class DocumentChunkResponse(BaseModel):
    """Esquema para resposta de chunk de documento."""
    
    id: UUID = Field(..., description="ID do chunk")
    document_id: UUID = Field(..., description="ID do documento")
    content: str = Field(..., description="Conteúdo do chunk")
    chunk_index: int = Field(..., description="Índice do chunk no documento")
    metadata: Dict[str, Any] = Field(..., description="Metadados do chunk")
    created_at: datetime = Field(..., description="Data e hora de criação")
    updated_at: datetime = Field(..., description="Data e hora de atualização")
    
    class Config:
        """Configuração do modelo."""
        
        from_attributes = True

class SearchQuery(BaseModel):
    """Esquema para consulta de busca."""
    
    query: str = Field(..., description="Texto da consulta")
    collection_ids: Optional[List[UUID]] = Field(None, description="IDs das coleções para filtrar a busca")
    similarity_threshold: Optional[float] = Field(0.7, description="Limiar mínimo de similaridade (0-1)")
    max_results: Optional[int] = Field(5, description="Número máximo de resultados")

class SearchResponse(BaseModel):
    """Esquema para resposta de busca."""
    
    results: List[Dict[str, Any]] = Field(..., description="Resultados da busca")
    query: str = Field(..., description="Texto da consulta original")
    total: int = Field(..., description="Número total de resultados")