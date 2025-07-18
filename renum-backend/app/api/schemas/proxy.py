"""
Módulo que define os schemas para os endpoints de proxy da API da Plataforma Renum.

Este módulo contém as classes Pydantic que definem a estrutura de dados
para as requisições e respostas dos endpoints de proxy.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl

# Schemas para Tavily

class TavilySearchRequest(BaseModel):
    """Schema para requisição de busca no Tavily."""
    
    query: str = Field(..., description="Consulta de busca")
    search_depth: str = Field(default="basic", description="Profundidade da busca ('basic' ou 'advanced')")
    include_domains: Optional[List[str]] = Field(default=None, description="Lista de domínios a serem incluídos")
    exclude_domains: Optional[List[str]] = Field(default=None, description="Lista de domínios a serem excluídos")
    max_results: int = Field(default=5, description="Número máximo de resultados")

class TavilySearchResult(BaseModel):
    """Schema para um resultado de busca do Tavily."""
    
    url: HttpUrl = Field(..., description="URL do resultado")
    title: str = Field(..., description="Título do resultado")
    content: str = Field(..., description="Conteúdo do resultado")
    score: float = Field(..., description="Pontuação de relevância")
    published_date: Optional[str] = Field(default=None, description="Data de publicação")

class TavilySearchResponse(BaseModel):
    """Schema para resposta de busca do Tavily."""
    
    results: List[TavilySearchResult] = Field(..., description="Lista de resultados")
    query: str = Field(..., description="Consulta original")
    search_depth: str = Field(..., description="Profundidade da busca utilizada")
    search_id: str = Field(..., description="ID da busca")

# Schemas para Firecrawl

class FirecrawlCrawlRequest(BaseModel):
    """Schema para requisição de crawling no Firecrawl."""
    
    url: HttpUrl = Field(..., description="URL a ser crawleada")
    max_pages: int = Field(default=10, description="Número máximo de páginas")
    max_depth: int = Field(default=2, description="Profundidade máxima do crawling")
    follow_links: bool = Field(default=True, description="Se deve seguir links")
    javascript: bool = Field(default=True, description="Se deve executar JavaScript")

class FirecrawlPage(BaseModel):
    """Schema para uma página crawleada pelo Firecrawl."""
    
    url: HttpUrl = Field(..., description="URL da página")
    title: str = Field(..., description="Título da página")
    content: str = Field(..., description="Conteúdo da página")
    links: List[str] = Field(..., description="Links encontrados na página")
    depth: int = Field(..., description="Profundidade da página no crawling")

class FirecrawlCrawlResponse(BaseModel):
    """Schema para resposta de crawling do Firecrawl."""
    
    pages: List[FirecrawlPage] = Field(..., description="Lista de páginas crawleadas")
    start_url: HttpUrl = Field(..., description="URL inicial")
    total_pages: int = Field(..., description="Total de páginas crawleadas")
    crawl_id: str = Field(..., description="ID do crawling")

class FirecrawlExtractRequest(BaseModel):
    """Schema para requisição de extração no Firecrawl."""
    
    url: HttpUrl = Field(..., description="URL da página")
    javascript: bool = Field(default=True, description="Se deve executar JavaScript")
    extract_links: bool = Field(default=True, description="Se deve extrair links")
    extract_metadata: bool = Field(default=True, description="Se deve extrair metadados")

class FirecrawlExtractResponse(BaseModel):
    """Schema para resposta de extração do Firecrawl."""
    
    url: HttpUrl = Field(..., description="URL da página")
    title: str = Field(..., description="Título da página")
    content: str = Field(..., description="Conteúdo da página")
    links: Optional[List[str]] = Field(default=None, description="Links encontrados na página")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadados da página")
"""