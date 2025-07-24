"""
Configurações da aplicação.

Este módulo define as configurações da aplicação, incluindo variáveis de ambiente,
configurações de segurança e outras configurações globais.
"""

import os
from typing import Optional, Dict, Any, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import validator
except ImportError:
    from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # API
    API_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Renum Backend"
    VERSION: str = "0.1.0"
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    WORKERS: int = 4
    
    # Segurança
    SECRET_KEY: str = "development-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Banco de dados
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Suna Core
    SUNA_API_URL: str = "http://localhost:8000"
    SUNA_API_KEY: Optional[str] = None
    
    # Limites
    MAX_CONCURRENT_EXECUTIONS: int = 5
    MAX_AGENTS_PER_TEAM: int = 10
    
    # Criptografia
    ENCRYPTION_KEY: Optional[str] = None
    API_KEY_ENCRYPTION_KEY: Optional[str] = None
    
    @validator("API_KEY_ENCRYPTION_KEY", pre=True)
    def validate_encryption_key(cls, v: Optional[str]) -> Optional[str]:
        """Valida a chave de criptografia."""
        if v is None:
            # Em ambiente de desenvolvimento, gera uma chave aleatória
            if os.environ.get("ENV") == "development":
                try:
                    from cryptography.fernet import Fernet
                    return Fernet.generate_key().decode()
                except ImportError:
                    # Se cryptography não estiver disponível, usa uma chave padrão
                    return "development-key-not-secure"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Obtém as configurações da aplicação.
    
    Returns:
        Objeto Settings com as configurações
    """
    return Settings()


def is_feature_enabled(feature_name: str) -> bool:
    """
    Verifica se uma funcionalidade está habilitada.
    
    Args:
        feature_name: Nome da funcionalidade a ser verificada
        
    Returns:
        True se a funcionalidade estiver habilitada, False caso contrário
    """
    # Mapeamento de funcionalidades habilitadas
    enabled_features = {
        "rag_module": True,  # Módulo RAG sempre habilitado
        "websocket": True,   # WebSocket sempre habilitado
        "notifications": True,  # Notificações sempre habilitadas
        "team_orchestration": True,  # Orquestração de equipes sempre habilitada
    }
    
    return enabled_features.get(feature_name, False)