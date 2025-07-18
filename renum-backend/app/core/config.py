"""
Módulo de configuração para a aplicação Renum Backend.

Este módulo carrega as variáveis de ambiente e fornece uma interface
para acessá-las de forma segura e tipada.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Configurar logger
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # Configurações gerais
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    
    # Configurações do Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_DB_URL: Optional[str] = None
    
    # Configurações de APIs externas
    OPENAI_API_KEY: Optional[str] = None
    
    # Configurações do Suna Core
    SUNA_API_URL: Optional[str] = None
    SUNA_API_KEY: Optional[str] = None
    
    # Chave para criptografia de dados sensíveis (opcional)
    ENCRYPTION_KEY: Optional[str] = None
    
    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v):
        """Valida a URL do Supabase."""
        if not v.startswith("https://"):
            raise ValueError("SUPABASE_URL deve começar com https://")
        return v
    
    class Config:
        """Configurações do Pydantic."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações da aplicação.
    
    Usa cache para evitar carregar as variáveis de ambiente múltiplas vezes.
    
    Returns:
        Objeto Settings com as configurações da aplicação.
    """
    try:
        settings = Settings()
        logger.info(f"Configurações carregadas com sucesso. Ambiente: {settings.ENVIRONMENT}")
        return settings
    except Exception as e:
        logger.error(f"Erro ao carregar configurações: {str(e)}")
        raise


# Instância global das configurações
settings = get_settings()