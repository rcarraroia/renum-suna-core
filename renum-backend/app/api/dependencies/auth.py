"""
Módulo que define as dependências de autenticação para os endpoints da API.

Este módulo fornece funções para autenticação e autorização de usuários e clientes.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings

# Configurar logger
logger = logging.getLogger(__name__)

# Configurar OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Obtém o usuário autenticado a partir do token JWT.
    
    Args:
        token: Token JWT.
        
    Returns:
        Dados do usuário autenticado.
        
    Raises:
        HTTPException: Se o token for inválido ou expirado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar o token JWT
        # TODO: Implementar decodificação real do token
        # Por enquanto, retornar um usuário fictício para desenvolvimento
        
        # Em produção, você deve decodificar o token JWT e verificar a assinatura
        # payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        # user_id = payload.get("sub")
        # if user_id is None:
        #     raise credentials_exception
        
        # Usuário fictício para desenvolvimento
        user = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "email": "user@example.com",
            "name": "Usuário de Teste",
            "role": "user"
        }
        
        return user
    except JWTError:
        logger.error("Erro ao decodificar token JWT")
        raise credentials_exception

async def get_current_client(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Obtém o cliente autenticado a partir do token JWT.
    
    Args:
        token: Token JWT.
        
    Returns:
        Dados do cliente autenticado.
        
    Raises:
        HTTPException: Se o token for inválido ou expirado.
    """
    # Obter usuário autenticado
    user = await get_current_user(token)
    
    # TODO: Implementar lógica para obter cliente a partir do usuário
    # Por enquanto, retornar um cliente fictício para desenvolvimento
    
    client = {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "name": "Cliente de Teste",
        "plan": "basic"
    }
    
    return client

async def get_current_admin(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Obtém o administrador autenticado a partir do token JWT.
    
    Args:
        token: Token JWT.
        
    Returns:
        Dados do administrador autenticado.
        
    Raises:
        HTTPException: Se o token for inválido ou expirado, ou se o usuário não for administrador.
    """
    # Obter usuário autenticado
    user = await get_current_user(token)
    
    # Verificar se o usuário é administrador
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Permissão de administrador necessária."
        )
    
    return user