"""
ImprovedTokenValidator - Validador de tokens JWT robusto com cache e logs detalhados.

Este módulo implementa um sistema de validação de tokens JWT melhorado para resolver
os problemas críticos identificados no diagnóstico WebSocket.
"""

import os
import jwt
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

# Configuração de logging estruturado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationFailureReason(Enum):
    """Razões para falha na validação de token."""
    EMPTY_TOKEN = "empty_token"
    INVALID_FORMAT = "invalid_format"
    EXPIRED = "expired"
    INVALID_SIGNATURE = "invalid_signature"
    MISSING_CLAIMS = "missing_claims"
    INVALID_ISSUER = "invalid_issuer"
    INVALID_AUDIENCE = "invalid_audience"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass
class ValidationResult:
    """Resultado da validação de token."""
    valid: bool
    reason: Optional[ValidationFailureReason] = None
    payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    error_message: Optional[str] = None
    should_refresh: bool = False


class TokenCache:
    """Cache TTL para tokens validados."""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        self.cache: Dict[str, ValidationResult] = {}
        self.timestamps: Dict[str, datetime] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
    def _generate_key(self, token: str) -> str:
        """Gera chave de cache usando hash do token."""
        return hashlib.sha256(token.encode()).hexdigest()[:16]
    
    def get(self, token: str) -> Optional[ValidationResult]:
        """Recupera resultado do cache se válido."""
        key = self._generate_key(token)
        
        if key not in self.cache:
            return None
            
        # Verificar se expirou
        if datetime.now() - self.timestamps[key] > timedelta(seconds=self.ttl_seconds):
            self._remove(key)
            return None
            
        return self.cache[key]
    
    def set(self, token: str, result: ValidationResult) -> None:
        """Armazena resultado no cache."""
        key = self._generate_key(token)
        
        # Limpar cache se atingiu limite
        if len(self.cache) >= self.max_size:
            self._cleanup_old_entries()
            
        self.cache[key] = result
        self.timestamps[key] = datetime.now()
    
    def _remove(self, key: str) -> None:
        """Remove entrada do cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def _cleanup_old_entries(self) -> None:
        """Remove entradas antigas do cache."""
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self.timestamps.items()
            if now - timestamp > timedelta(seconds=self.ttl_seconds)
        ]
        
        for key in expired_keys:
            self._remove(key)
        
        # Se ainda está cheio, remove as mais antigas
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(
                self.timestamps.items(),
                key=lambda x: x[1]
            )
            
            # Remove 20% das entradas mais antigas
            remove_count = max(1, len(sorted_keys) // 5)
            for key, _ in sorted_keys[:remove_count]:
                self._remove(key)
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        self.cache.clear()
        self.timestamps.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'hit_rate': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
        }


class ImprovedTokenValidator:
    """Validador de tokens JWT robusto com cache e logs detalhados."""
    
    def __init__(self):
        self.jwt_secret = self._load_jwt_secret()
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "suna-app")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "suna-users")
        self.cache = TokenCache()
        
        # Configurações de validação
        self.require_exp = os.getenv("JWT_REQUIRE_EXP", "true").lower() == "true"
        self.require_iat = os.getenv("JWT_REQUIRE_IAT", "true").lower() == "true"
        self.leeway_seconds = int(os.getenv("JWT_LEEWAY_SECONDS", "30"))
        
        logger.info("ImprovedTokenValidator initialized", extra={
            'algorithm': self.jwt_algorithm,
            'issuer': self.jwt_issuer,
            'require_exp': self.require_exp,
            'cache_enabled': True
        })
    
    def _load_jwt_secret(self) -> Optional[str]:
        """Carrega JWT_SECRET das variáveis de ambiente."""
        secret = os.getenv("JWT_SECRET")
        
        if not secret:
            logger.error("JWT_SECRET not found in environment variables")
            return None
            
        if len(secret) < 32:
            logger.warning("JWT_SECRET is shorter than recommended 32 characters", extra={
                'length': len(secret)
            })
            
        return secret
    
    async def validate(self, token: str) -> ValidationResult:
        """
        Valida token JWT com cache e logs detalhados.
        
        Args:
            token: Token JWT para validar
            
        Returns:
            ValidationResult com detalhes da validação
        """
        start_time = datetime.now()
        
        try:
            # Verificar se token está vazio
            if not token or not token.strip():
                logger.warning("Empty or whitespace-only token received", extra={
                    'token_length': len(token or ""),
                    'token_type': type(token).__name__
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.EMPTY_TOKEN,
                    error_message="Token is empty or contains only whitespace"
                )
            
            # Verificar cache primeiro
            cached_result = self.cache.get(token)
            if cached_result:
                logger.debug("Token validation cache hit", extra={
                    'cache_stats': self.cache.stats()
                })
                return cached_result
            
            # Verificar se JWT_SECRET está configurado
            if not self.jwt_secret:
                logger.error("JWT_SECRET not configured - cannot validate tokens")
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.CONFIGURATION_ERROR,
                    error_message="JWT_SECRET not configured in environment"
                )
            
            # Validar formato básico do token
            if not self._is_valid_jwt_format(token):
                logger.warning("Invalid JWT format", extra={
                    'token_preview': token[:20] + "..." if len(token) > 20 else token
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.INVALID_FORMAT,
                    error_message="Token does not have valid JWT format (header.payload.signature)"
                )
            
            # Decodificar e validar token
            try:
                payload = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=[self.jwt_algorithm],
                    issuer=self.jwt_issuer if self.jwt_issuer else None,
                    audience=self.jwt_audience if self.jwt_audience else None,
                    options={
                        'require_exp': self.require_exp,
                        'require_iat': self.require_iat,
                        'verify_signature': True,
                        'verify_exp': True,
                        'verify_iat': True
                    },
                    leeway=self.leeway_seconds
                )
                
                # Extrair informações do payload
                user_id = payload.get('sub') or payload.get('user_id')
                expires_at = None
                issued_at = None
                
                if 'exp' in payload:
                    expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
                    
                if 'iat' in payload:
                    issued_at = datetime.fromtimestamp(payload['iat'], tz=timezone.utc)
                
                # Verificar se token expira em breve (próximos 5 minutos)
                should_refresh = False
                if expires_at:
                    time_to_expiry = expires_at - datetime.now(timezone.utc)
                    should_refresh = time_to_expiry < timedelta(minutes=5)
                
                result = ValidationResult(
                    valid=True,
                    payload=payload,
                    user_id=user_id,
                    expires_at=expires_at,
                    issued_at=issued_at,
                    should_refresh=should_refresh
                )
                
                # Armazenar no cache
                self.cache.set(token, result)
                
                validation_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.info("Token validation successful", extra={
                    'user_id': user_id,
                    'expires_at': expires_at.isoformat() if expires_at else None,
                    'should_refresh': should_refresh,
                    'validation_time_ms': validation_time
                })
                
                return result
                
            except jwt.ExpiredSignatureError:
                logger.warning("Token has expired", extra={
                    'token_preview': token[:20] + "..."
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.EXPIRED,
                    error_message="Token has expired"
                )
                
            except jwt.InvalidSignatureError:
                logger.error("Token has invalid signature", extra={
                    'token_preview': token[:20] + "..."
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.INVALID_SIGNATURE,
                    error_message="Token signature is invalid"
                )
                
            except jwt.InvalidIssuerError:
                logger.warning("Token has invalid issuer", extra={
                    'expected_issuer': self.jwt_issuer
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.INVALID_ISSUER,
                    error_message=f"Token issuer is invalid. Expected: {self.jwt_issuer}"
                )
                
            except jwt.InvalidAudienceError:
                logger.warning("Token has invalid audience", extra={
                    'expected_audience': self.jwt_audience
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.INVALID_AUDIENCE,
                    error_message=f"Token audience is invalid. Expected: {self.jwt_audience}"
                )
                
            except jwt.MissingRequiredClaimError as e:
                logger.warning("Token missing required claim", extra={
                    'missing_claim': str(e)
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.MISSING_CLAIMS,
                    error_message=f"Token missing required claim: {e}"
                )
                
            except jwt.InvalidTokenError as e:
                logger.error("Invalid token error", extra={
                    'error': str(e),
                    'token_preview': token[:20] + "..."
                })
                return ValidationResult(
                    valid=False,
                    reason=ValidationFailureReason.INVALID_FORMAT,
                    error_message=f"Invalid token: {e}"
                )
                
        except Exception as e:
            logger.error("Unexpected error during token validation", extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return ValidationResult(
                valid=False,
                reason=ValidationFailureReason.CONFIGURATION_ERROR,
                error_message=f"Unexpected validation error: {e}"
            )
    
    def _is_valid_jwt_format(self, token: str) -> bool:
        """Verifica se token tem formato JWT válido (header.payload.signature)."""
        parts = token.split('.')
        return len(parts) == 3 and all(part for part in parts)
    
    async def generate_token(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Gera novo token JWT para usuário.
        
        Args:
            user_id: ID do usuário
            additional_claims: Claims adicionais para incluir no token
            
        Returns:
            Token JWT ou None se erro
        """
        if not self.jwt_secret:
            logger.error("Cannot generate token - JWT_SECRET not configured")
            return None
            
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=24)  # Token válido por 24 horas
            
            payload = {
                'sub': user_id,
                'iat': int(now.timestamp()),
                'exp': int(expires_at.timestamp()),
                'iss': self.jwt_issuer,
                'aud': self.jwt_audience
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            logger.info("Token generated successfully", extra={
                'user_id': user_id,
                'expires_at': expires_at.isoformat(),
                'additional_claims': list(additional_claims.keys()) if additional_claims else []
            })
            
            return token
            
        except Exception as e:
            logger.error("Error generating token", extra={
                'user_id': user_id,
                'error': str(e)
            })
            return None
    
    async def refresh_token(self, old_token: str) -> Optional[str]:
        """
        Renova token expirado ou próximo do vencimento.
        
        Args:
            old_token: Token atual para renovar
            
        Returns:
            Novo token ou None se erro
        """
        if not self.jwt_secret:
            logger.error("Cannot refresh token - JWT_SECRET not configured")
            return None
            
        try:
            # Validar token atual (mesmo que expirado)
            payload = jwt.decode(
                old_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={
                    'verify_exp': False,  # Ignorar expiração para refresh
                    'verify_signature': True,
                    'verify_iss': False,  # Ignorar issuer para refresh
                    'verify_aud': False   # Ignorar audience para refresh
                }
            )
            
            user_id = payload.get('sub') or payload.get('user_id')
            if not user_id:
                logger.warning("Cannot refresh token - no user ID found")
                return None
            
            # Gerar novo token
            new_token = await self.generate_token(user_id)
            
            if new_token:
                logger.info("Token refreshed successfully", extra={
                    'user_id': user_id
                })
            
            return new_token
            
        except Exception as e:
            logger.error("Error refreshing token", extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        return self.cache.stats()
    
    def clear_cache(self) -> None:
        """Limpa cache de tokens."""
        self.cache.clear()
        logger.info("Token cache cleared")
    
    async def validate_websocket_token(self, token_param: str) -> ValidationResult:
        """
        Valida token especificamente para conexões WebSocket.
        
        Args:
            token_param: Parâmetro token da URL WebSocket
            
        Returns:
            ValidationResult com validação específica para WebSocket
        """
        logger.info("Validating WebSocket token", extra={
            'token_present': bool(token_param),
            'token_length': len(token_param or "")
        })
        
        # Validação específica para WebSocket
        if not token_param:
            logger.error("WebSocket token parameter is missing or empty")
            return ValidationResult(
                valid=False,
                reason=ValidationFailureReason.EMPTY_TOKEN,
                error_message="WebSocket connection requires token parameter in URL"
            )
        
        # Decodificar URL se necessário
        import urllib.parse
        decoded_token = urllib.parse.unquote(token_param)
        
        # Validar token decodificado
        result = await self.validate(decoded_token)
        
        if result.valid:
            logger.info("WebSocket token validation successful", extra={
                'user_id': result.user_id
            })
        else:
            logger.warning("WebSocket token validation failed", extra={
                'reason': result.reason.value if result.reason else 'unknown',
                'error': result.error_message
            })
        
        return result    

    async def validate_token_async(self, token: str) -> Dict[str, Any]:
        """
        Método de compatibilidade para validate_token_async.
        Retorna dicionário para compatibilidade com código existente.
        
        Args:
            token: Token JWT para validar
            
        Returns:
            Dict com detalhes da validação
        """
        result = await self.validate(token)
        
        # Converter ValidationResult para dicionário para compatibilidade
        return {
            "valid": result.valid,
            "user_id": result.user_id,
            "payload": result.payload,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            "issued_at": result.issued_at.isoformat() if result.issued_at else None,
            "error_message": result.error_message,
            "should_refresh": result.should_refresh,
            "reason": result.reason.value if result.reason else None,
            "error": result.error_message  # Alias para compatibilidade
        }