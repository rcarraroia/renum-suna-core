"""
Módulo que implementa as rotas de proxy para ferramentas externas na API da Plataforma Renum.

Este módulo contém os endpoints para encaminhar requisições para serviços externos,
utilizando as credenciais dos clientes de forma segura e rastreando o uso para fins de faturamento.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import HttpUrl

from app.api.schemas.proxy import (
    TavilySearchRequest, TavilySearchResponse,
    FirecrawlCrawlRequest, FirecrawlCrawlResponse,
    FirecrawlExtractRequest, FirecrawlExtractResponse
)
from app.services.proxy import proxy_service
from app.services.auth import auth_service

# Configurar logger
logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(tags=["proxy"])

# Middleware para obter o usuário atual
async def get_current_user(request: Request):
    """Obtém o usuário atual a partir do token de autenticação.
    
    Args:
        request: Requisição HTTP.
        
    Returns:
        Dados do usuário autenticado.
        
    Raises:
        HTTPException: Se o usuário não estiver autenticado.
    """
    user = request.state.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não autenticado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

@router.post("/tavily/search", response_model=TavilySearchResponse)
async def tavily_search(
    request: TavilySearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Realiza uma busca usando o Tavily.
    
    Args:
        request: Dados da requisição.
        current_user: Usuário autenticado.
        
    Returns:
        Resultados da busca.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        # Obter IDs do usuário e cliente
        user_id = current_user["id"]
        client_id = current_user["client_id"]
        
        # Realizar busca
        result = await proxy_service.tavily_search(
            client_id=client_id,
            user_id=user_id,
            query=request.query,
            search_depth=request.search_depth,
            include_domains=request.include_domains,
            exclude_domains=request.exclude_domains,
            max_results=request.max_results
        )
        
        return result
    except ValueError as e:
        logger.error(f"Erro ao realizar busca no Tavily: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro interno ao realizar busca no Tavily: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição"
        )

@router.post("/firecrawl/crawl", response_model=FirecrawlCrawlResponse)
async def firecrawl_crawl(
    request: FirecrawlCrawlRequest,
    current_user: dict = Depends(get_current_user)
):
    """Realiza um crawling usando o Firecrawl.
    
    Args:
        request: Dados da requisição.
        current_user: Usuário autenticado.
        
    Returns:
        Resultados do crawling.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        # Obter IDs do usuário e cliente
        user_id = current_user["id"]
        client_id = current_user["client_id"]
        
        # Realizar crawling
        result = await proxy_service.firecrawl_crawl(
            client_id=client_id,
            user_id=user_id,
            url=str(request.url),
            max_pages=request.max_pages,
            max_depth=request.max_depth,
            follow_links=request.follow_links,
            javascript=request.javascript
        )
        
        return result
    except ValueError as e:
        logger.error(f"Erro ao realizar crawling no Firecrawl: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro interno ao realizar crawling no Firecrawl: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição"
        )

@router.post("/firecrawl/extract", response_model=FirecrawlExtractResponse)
async def firecrawl_extract(
    request: FirecrawlExtractRequest,
    current_user: dict = Depends(get_current_user)
):
    """Extrai conteúdo de uma página usando o Firecrawl.
    
    Args:
        request: Dados da requisição.
        current_user: Usuário autenticado.
        
    Returns:
        Conteúdo extraído da página.
        
    Raises:
        HTTPException: Se ocorrer um erro na requisição.
    """
    try:
        # Obter IDs do usuário e cliente
        user_id = current_user["id"]
        client_id = current_user["client_id"]
        
        # Realizar extração
        result = await proxy_service.firecrawl_extract(
            client_id=client_id,
            user_id=user_id,
            url=str(request.url),
            javascript=request.javascript,
            extract_links=request.extract_links,
            extract_metadata=request.extract_metadata
        )
        
        return result
    except ValueError as e:
        logger.error(f"Erro ao extrair conteúdo no Firecrawl: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro interno ao extrair conteúdo no Firecrawl: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a requisição"
        )
"""