"""
Sistema de fallback robusto para autenticação WebSocket.

Este módulo implementa mecanismos de fallback para resolver problemas
de tokens vazios, conexões recusadas e protocolos obsoletos.
"""

import os
import jwt
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import time

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AuthFallbackType(Enum):
    """Tipos de fallback de autenticação."""
    TOKEN_REFRESH = "token_refresh"
    ALTERNATIVE_AUTH = "alternative_auth"
    GUEST_MODE = "guest_mode"
    RETRY_WITH_DELAY = "retry_with_delay"
    PROTOCOL_DOWNGRADE = "protocol_downgrade"


class AuthStatus(Enum):
    """Status da autenticação."""
    SUCCESS = "success"
    FAILED = "failed"
    RETRY_NEEDED = "retry_needed"
    FALLBACK_USED = "fallback_used"
    CRITICAL_ERROR = "critical_error"


@dataclass
class AuthResult:
    """Resultado de tentativa de autenticação."""
    status: AuthStatus
    token: Optional[str]
    fallback_used: Optional[AuthFallbackType]
    error_message: Optional[str]
    retry_after: Optional[int]  # segundos
    metadata: Dict[str, Any]


@dataclass
class FallbackConfig:
    """Configuração de fallback."""
    max_retries: int = 3
    retry_delay_base: int = 2  # segundos
    token_refresh_threshold: int = 300  # 5 minutos antes da expiração
    enable_guest_mode: bool = False
    enable_protocol_downgrade: bool = True
    alternative_auth_methods: List[str] = None


class WebSocketAuthFallback:
    """Sistema de fallback para autenticação WebSocket."""
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        """
        Inicializa o sistema de fallback.
        
        Args:
            config: Configuração de fallback
        """
        self.config = config or FallbackConfig()
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.retry_counts: Dict[str, int] = {}
        self.last_retry_time: Dict[str, float] = {}
        
        # Propriedade para compatibilidade com código existente
        self.allow_guest_mode = self.config.enable_guest_mode
        
        logger.info("WebSocketAuthFallback initialized")
    
    async def authenticate_with_fallback(
        self, 
        token: Optional[str], 
        user_id: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Tenta autenticar com sistema de fallback robusto.
        
        Args:
            token: Token de autenticação
            user_id: ID do usuário (para fallbacks)
            request_metadata: Metadados da requisição
            
        Returns:
            AuthResult: Resultado da autenticação
        """
        logger.info(f"Starting authentication with fallback for user: {user_id}")
        
        request_id = request_metadata.get("request_id", "unknown") if request_metadata else "unknown"
        
        # 1. Tentar autenticação normal primeiro
        if token and token.strip():
            normal_result = await self._try_normal_auth(token)
            if normal_result.status == AuthStatus.SUCCESS:
                logger.info("Normal authentication successful")
                return normal_result
            
            logger.warning(f"Normal authentication failed: {normal_result.error_message}")
        else:
            logger.warning("Empty or missing token, proceeding to fallbacks")
        
        # 2. Aplicar fallbacks em ordem de prioridade
        fallback_results = []
        
        # Fallback 1: Tentar refresh do token
        if token and user_id:
            refresh_result = await self._try_token_refresh(token, user_id)
            fallback_results.append(refresh_result)
            if refresh_result.status == AuthStatus.SUCCESS:
                logger.info("Token refresh successful")
                return refresh_result
        
        # Fallback 2: Métodos alternativos de autenticação
        if user_id and self.config.alternative_auth_methods:
            alt_result = await self._try_alternative_auth(user_id, request_metadata)
            fallback_results.append(alt_result)
            if alt_result.status == AuthStatus.SUCCESS:
                logger.info("Alternative authentication successful")
                return alt_result
        
        # Fallback 3: Retry com delay exponencial
        retry_result = await self._try_retry_with_delay(request_id, token, user_id)
        fallback_results.append(retry_result)
        if retry_result.status == AuthStatus.RETRY_NEEDED:
            logger.info(f"Retry scheduled after {retry_result.retry_after} seconds")
            return retry_result
        
        # Fallback 4: Modo guest (se habilitado)
        if self.config.enable_guest_mode:
            guest_result = await self._try_guest_mode(request_metadata)
            fallback_results.append(guest_result)
            if guest_result.status == AuthStatus.FALLBACK_USED:
                logger.info("Guest mode activated")
                return guest_result
        
        # Se todos os fallbacks falharam
        logger.error("All authentication fallbacks failed")
        return AuthResult(
            status=AuthStatus.CRITICAL_ERROR,
            token=None,
            fallback_used=None,
            error_message="Todos os métodos de autenticação falharam",
            retry_after=None,
            metadata={
                "fallback_attempts": len(fallback_results),
                "fallback_results": [r.error_message for r in fallback_results],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _try_normal_auth(self, token: str) -> AuthResult:
        """Tenta autenticação normal."""
        try:
            if not self.jwt_secret:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=None,
                    error_message="JWT_SECRET não configurado",
                    retry_after=None,
                    metadata={"auth_type": "normal", "error_type": "config_missing"}
                )
            
            # Validar token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Verificar expiração
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=None,
                    error_message="Token expirado",
                    retry_after=None,
                    metadata={"auth_type": "normal", "error_type": "expired"}
                )
            
            # Verificar claims obrigatórios
            required_claims = ["user_id", "exp", "iat"]
            missing_claims = [claim for claim in required_claims if claim not in payload]
            if missing_claims:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=None,
                    error_message=f"Claims obrigatórios ausentes: {missing_claims}",
                    retry_after=None,
                    metadata={"auth_type": "normal", "error_type": "missing_claims", "missing": missing_claims}
                )
            
            logger.info(f"Normal authentication successful for user: {payload.get('user_id')}")
            return AuthResult(
                status=AuthStatus.SUCCESS,
                token=token,
                fallback_used=None,
                error_message=None,
                retry_after=None,
                metadata={"auth_type": "normal", "user_id": payload.get("user_id"), "exp": exp}
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=None,
                error_message="Token expirado",
                retry_after=None,
                metadata={"auth_type": "normal", "error_type": "expired"}
            )
            
        except jwt.InvalidTokenError as e:
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=None,
                error_message=f"Token inválido: {str(e)}",
                retry_after=None,
                metadata={"auth_type": "normal", "error_type": "invalid", "error": str(e)}
            )
            
        except Exception as e:
            logger.error(f"Error during normal authentication: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=None,
                error_message=f"Erro na autenticação: {str(e)}",
                retry_after=None,
                metadata={"auth_type": "normal", "error_type": "system_error", "error": str(e)}
            )
    
    async def _try_token_refresh(self, old_token: str, user_id: str) -> AuthResult:
        """Tenta refresh do token."""
        try:
            logger.info(f"Attempting token refresh for user: {user_id}")
            
            if not self.jwt_secret:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.TOKEN_REFRESH,
                    error_message="JWT_SECRET não configurado para refresh",
                    retry_after=None,
                    metadata={"fallback_type": "token_refresh", "error_type": "config_missing"}
                )
            
            # Tentar decodificar token antigo (mesmo se expirado)
            try:
                old_payload = jwt.decode(old_token, self.jwt_secret, algorithms=[self.jwt_algorithm], options={"verify_exp": False})
            except jwt.InvalidTokenError:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.TOKEN_REFRESH,
                    error_message="Token antigo inválido para refresh",
                    retry_after=None,
                    metadata={"fallback_type": "token_refresh", "error_type": "invalid_old_token"}
                )
            
            # Verificar se o user_id bate
            if old_payload.get("user_id") != user_id:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.TOKEN_REFRESH,
                    error_message="User ID não confere com token",
                    retry_after=None,
                    metadata={"fallback_type": "token_refresh", "error_type": "user_mismatch"}
                )
            
            # Gerar novo token
            now = datetime.now(timezone.utc)
            new_payload = {
                "user_id": user_id,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(hours=24)).timestamp()),
                "refresh": True,
                "original_iat": old_payload.get("iat")
            }
            
            new_token = jwt.encode(new_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            logger.info(f"Token refresh successful for user: {user_id}")
            return AuthResult(
                status=AuthStatus.SUCCESS,
                token=new_token,
                fallback_used=AuthFallbackType.TOKEN_REFRESH,
                error_message=None,
                retry_after=None,
                metadata={
                    "fallback_type": "token_refresh",
                    "user_id": user_id,
                    "new_exp": new_payload["exp"],
                    "refreshed_at": now.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=AuthFallbackType.TOKEN_REFRESH,
                error_message=f"Erro no refresh do token: {str(e)}",
                retry_after=None,
                metadata={"fallback_type": "token_refresh", "error_type": "system_error", "error": str(e)}
            )
    
    async def _try_alternative_auth(self, user_id: str, request_metadata: Optional[Dict[str, Any]]) -> AuthResult:
        """Tenta métodos alternativos de autenticação."""
        try:
            logger.info(f"Attempting alternative authentication for user: {user_id}")
            
            # Método 1: Verificar se há sessão ativa no Redis/cache
            session_result = await self._check_active_session(user_id)
            if session_result:
                return session_result
            
            # Método 2: Verificar cookies de sessão
            if request_metadata and request_metadata.get("cookies"):
                cookie_result = await self._check_session_cookies(user_id, request_metadata["cookies"])
                if cookie_result:
                    return cookie_result
            
            # Método 3: Autenticação temporária baseada em IP/fingerprint
            if request_metadata:
                temp_result = await self._try_temporary_auth(user_id, request_metadata)
                if temp_result:
                    return temp_result
            
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=AuthFallbackType.ALTERNATIVE_AUTH,
                error_message="Nenhum método alternativo de autenticação disponível",
                retry_after=None,
                metadata={"fallback_type": "alternative_auth", "methods_tried": ["session", "cookies", "temporary"]}
            )
            
        except Exception as e:
            logger.error(f"Error during alternative authentication: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=AuthFallbackType.ALTERNATIVE_AUTH,
                error_message=f"Erro na autenticação alternativa: {str(e)}",
                retry_after=None,
                metadata={"fallback_type": "alternative_auth", "error": str(e)}
            )
    
    async def _try_retry_with_delay(self, request_id: str, token: Optional[str], user_id: Optional[str]) -> AuthResult:
        """Implementa retry com delay exponencial."""
        try:
            current_retries = self.retry_counts.get(request_id, 0)
            
            if current_retries >= self.config.max_retries:
                logger.warning(f"Max retries exceeded for request: {request_id}")
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.RETRY_WITH_DELAY,
                    error_message=f"Máximo de tentativas excedido ({self.config.max_retries})",
                    retry_after=None,
                    metadata={"fallback_type": "retry", "retries_used": current_retries}
                )
            
            # Calcular delay exponencial
            delay = self.config.retry_delay_base ** (current_retries + 1)
            
            # Verificar se já passou tempo suficiente desde a última tentativa
            last_retry = self.last_retry_time.get(request_id, 0)
            time_since_last = time.time() - last_retry
            
            if time_since_last < delay:
                remaining_delay = int(delay - time_since_last)
                logger.info(f"Retry scheduled for request {request_id} in {remaining_delay} seconds")
                return AuthResult(
                    status=AuthStatus.RETRY_NEEDED,
                    token=None,
                    fallback_used=AuthFallbackType.RETRY_WITH_DELAY,
                    error_message=f"Retry agendado em {remaining_delay} segundos",
                    retry_after=remaining_delay,
                    metadata={
                        "fallback_type": "retry",
                        "current_retries": current_retries,
                        "delay_seconds": remaining_delay
                    }
                )
            
            # Atualizar contadores
            self.retry_counts[request_id] = current_retries + 1
            self.last_retry_time[request_id] = time.time()
            
            logger.info(f"Retry attempt {current_retries + 1} for request: {request_id}")
            return AuthResult(
                status=AuthStatus.RETRY_NEEDED,
                token=None,
                fallback_used=AuthFallbackType.RETRY_WITH_DELAY,
                error_message="Tentativa de retry iniciada",
                retry_after=0,  # Retry imediato desta vez
                metadata={
                    "fallback_type": "retry",
                    "current_retries": current_retries + 1,
                    "immediate_retry": True
                }
            )
            
        except Exception as e:
            logger.error(f"Error during retry logic: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=AuthFallbackType.RETRY_WITH_DELAY,
                error_message=f"Erro na lógica de retry: {str(e)}",
                retry_after=None,
                metadata={"fallback_type": "retry", "error": str(e)}
            )
    
    async def _try_guest_mode(self, request_metadata: Optional[Dict[str, Any]]) -> AuthResult:
        """Tenta modo guest."""
        try:
            if not self.config.enable_guest_mode:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.GUEST_MODE,
                    error_message="Modo guest não habilitado",
                    retry_after=None,
                    metadata={"fallback_type": "guest_mode", "enabled": False}
                )
            
            logger.info("Activating guest mode")
            
            # Gerar token temporário para guest
            if self.jwt_secret:
                now = datetime.now(timezone.utc)
                guest_payload = {
                    "user_id": f"guest_{int(now.timestamp())}",
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(hours=1)).timestamp()),  # 1 hora para guest
                    "guest": True,
                    "permissions": ["read_only"]
                }
                
                guest_token = jwt.encode(guest_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
                
                return AuthResult(
                    status=AuthStatus.FALLBACK_USED,
                    token=guest_token,
                    fallback_used=AuthFallbackType.GUEST_MODE,
                    error_message=None,
                    retry_after=None,
                    metadata={
                        "fallback_type": "guest_mode",
                        "guest_user_id": guest_payload["user_id"],
                        "permissions": guest_payload["permissions"],
                        "expires_at": guest_payload["exp"]
                    }
                )
            else:
                return AuthResult(
                    status=AuthStatus.FAILED,
                    token=None,
                    fallback_used=AuthFallbackType.GUEST_MODE,
                    error_message="JWT_SECRET necessário para modo guest",
                    retry_after=None,
                    metadata={"fallback_type": "guest_mode", "error": "no_jwt_secret"}
                )
                
        except Exception as e:
            logger.error(f"Error during guest mode activation: {str(e)}")
            return AuthResult(
                status=AuthStatus.FAILED,
                token=None,
                fallback_used=AuthFallbackType.GUEST_MODE,
                error_message=f"Erro no modo guest: {str(e)}",
                retry_after=None,
                metadata={"fallback_type": "guest_mode", "error": str(e)}
            )
    
    async def _check_active_session(self, user_id: str) -> Optional[AuthResult]:
        """Verifica se há sessão ativa no cache."""
        try:
            # Em implementação real, verificaria Redis ou outro cache
            # Por enquanto, simular verificação
            await asyncio.sleep(0.1)
            
            # Simular que não há sessão ativa
            return None
            
        except Exception as e:
            logger.error(f"Error checking active session: {str(e)}")
            return None
    
    async def _check_session_cookies(self, user_id: str, cookies: Dict[str, str]) -> Optional[AuthResult]:
        """Verifica cookies de sessão."""
        try:
            session_cookie = cookies.get("session_id")
            if not session_cookie:
                return None
            
            # Em implementação real, validaria o cookie de sessão
            # Por enquanto, simular que não há cookie válido
            return None
            
        except Exception as e:
            logger.error(f"Error checking session cookies: {str(e)}")
            return None
    
    async def _try_temporary_auth(self, user_id: str, request_metadata: Dict[str, Any]) -> Optional[AuthResult]:
        """Tenta autenticação temporária."""
        try:
            # Em implementação real, usaria IP, user agent, etc. para criar auth temporária
            # Por enquanto, não implementar para manter segurança
            return None
            
        except Exception as e:
            logger.error(f"Error during temporary auth: {str(e)}")
            return None
    
    def reset_retry_count(self, request_id: str):
        """Reseta contador de retry para um request."""
        if request_id in self.retry_counts:
            del self.retry_counts[request_id]
        if request_id in self.last_retry_time:
            del self.last_retry_time[request_id]
        
        logger.info(f"Retry count reset for request: {request_id}")
    
    def get_retry_status(self, request_id: str) -> Dict[str, Any]:
        """Retorna status de retry para um request."""
        return {
            "request_id": request_id,
            "current_retries": self.retry_counts.get(request_id, 0),
            "max_retries": self.config.max_retries,
            "last_retry_time": self.last_retry_time.get(request_id),
            "can_retry": self.retry_counts.get(request_id, 0) < self.config.max_retries
        }
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos fallbacks."""
        return {
            "service": "WebSocketAuthFallback",
            "version": "1.0.0",
            "config": {
                "max_retries": self.config.max_retries,
                "retry_delay_base": self.config.retry_delay_base,
                "enable_guest_mode": self.config.enable_guest_mode,
                "enable_protocol_downgrade": self.config.enable_protocol_downgrade
            },
            "active_retries": len(self.retry_counts),
            "jwt_configured": bool(self.jwt_secret)
        }
    
    async def authenticate_fallback(self, websocket, connection_id: str) -> dict:
        """
        Método de fallback para autenticação WebSocket.
        
        Args:
            websocket: Conexão WebSocket
            connection_id: ID da conexão
            
        Returns:
            dict: Resultado da autenticação com success, user_id, auth_method
        """
        try:
            logger.info(f"Iniciando autenticação de fallback para {connection_id}")
            
            # Tentativa 1: Modo guest se habilitado
            if self.allow_guest_mode:
                logger.info(f"Permitindo modo guest para {connection_id}")
                return {
                    "success": True,
                    "user_id": f"guest_{connection_id}",
                    "auth_method": "guest"
                }
            
            # Tentativa 2: Autenticação alternativa (simulada)
            logger.info(f"Tentando autenticação alternativa para {connection_id}")
            
            # Em um ambiente real, isso poderia verificar cookies, sessões, etc.
            # Por enquanto, retorna falha para forçar tratamento adequado
            return {
                "success": False,
                "error": "Nenhum método de fallback disponível",
                "auth_method": "fallback_failed"
            }
            
        except Exception as e:
            logger.error(f"Erro na autenticação de fallback: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno no fallback: {str(e)}",
                "auth_method": "fallback_error"
            }