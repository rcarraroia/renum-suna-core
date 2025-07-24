"""
Autenticação e autorização para a API.

Este módulo implementa funções para autenticação e autorização de usuários,
incluindo validação de tokens JWT e obtenção do ID do usuário autenticado.
"""

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID

from app.core.config import get_settings

# Esquema de segurança para autenticação via token Bearer
security = HTTPBearer()


def decode_token(token: str) -> Optional[dict]:
    """
    Decodifica um token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Payload do token ou None se o token for inválido
    """
    settings = get_settings()
    
    try:
        # Decodifica o token JWT
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_signature": bool(settings.SUPABASE_JWT_SECRET)}
        )
        
        return payload
    
    except (jwt.PyJWTError, ValueError):
        return None


async def get_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Obtém o ID do usuário a partir de um token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        ID do usuário ou None se o token for inválido
    """
    payload = decode_token(token)
    
    if not payload:
        return None
    
    # Obtém o ID do usuário do payload
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    try:
        return UUID(user_id)
    except ValueError:
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UUID:
    """
    Obtém o ID do usuário autenticado.
    
    Args:
        credentials: Credenciais de autenticação
        
    Returns:
        ID do usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    token = credentials.credentials
    user_id = await get_user_id_from_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_id


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security, scopes=["optional"])
) -> Optional[UUID]:
    """
    Obtém o ID do usuário autenticado, se disponível.
    
    Args:
        credentials: Credenciais de autenticação (opcional)
        
    Returns:
        ID do usuário autenticado ou None se não houver autenticação
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return await get_user_id_from_token(token)