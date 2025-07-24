"""
Gerenciador de API keys para usuários.

Este módulo fornece funcionalidades para armazenar, recuperar e gerenciar
chaves de API de usuários de forma segura.
"""

import base64
import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class ApiKeyManager:
    """Gerenciador de API keys para usuários."""
    
    def __init__(self, db_client, encryption_key=None):
        """
        Inicializa o gerenciador de API keys.
        
        Args:
            db_client: Cliente de banco de dados
            encryption_key: Chave para criptografia (opcional, gera uma se não fornecida)
        """
        self.db = db_client
        
        # Inicializa a chave de criptografia
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # Usa a variável de ambiente ou gera uma chave
            self.encryption_key = os.environ.get('API_KEY_ENCRYPTION_KEY')
            if not self.encryption_key:
                # Gera uma chave aleatória (apenas para desenvolvimento)
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                self.encryption_key = base64.urlsafe_b64encode(kdf.derive(b"renum_api_key_manager"))
        
        # Inicializa o Fernet para criptografia
        self.cipher = Fernet(self.encryption_key)
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """
        Criptografa uma API key.
        
        Args:
            api_key: Chave de API a ser criptografada
            
        Returns:
            Chave criptografada em formato base64
        """
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Descriptografa uma API key.
        
        Args:
            encrypted_key: Chave criptografada em formato base64
            
        Returns:
            Chave original
        """
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    async def set_user_api_key(self, user_id: str, service_name: str, api_key: str) -> bool:
        """
        Define uma API key para um usuário.
        
        Args:
            user_id: ID do usuário
            service_name: Nome do serviço (openai, anthropic, etc.)
            api_key: Chave de API
            
        Returns:
            True se a operação foi bem-sucedida
        """
        try:
            # Criptografa a chave
            encrypted_key = self._encrypt_api_key(api_key)
            
            # Verifica se já existe uma chave para este serviço
            result = await self.db.table('renum_user_api_keys') \
                .select('key_id') \
                .eq('user_id', str(user_id)) \
                .eq('service_name', service_name) \
                .execute()
            
            if result.data:
                # Atualiza a chave existente
                await self.db.table('renum_user_api_keys') \
                    .update({
                        'encrypted_key': encrypted_key,
                        'is_active': True,
                        'updated_at': datetime.now().isoformat()
                    }) \
                    .eq('key_id', result.data[0]['key_id']) \
                    .execute()
            else:
                # Insere uma nova chave
                await self.db.table('renum_user_api_keys') \
                    .insert({
                        'key_id': str(uuid4()),
                        'user_id': str(user_id),
                        'service_name': service_name,
                        'encrypted_key': encrypted_key,
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }) \
                    .execute()
            
            logger.info(f"Set API key for user {user_id} and service {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set API key: {str(e)}")
            return False
    
    async def get_user_api_key(self, user_id: str, service_name: str) -> Optional[str]:
        """
        Obtém uma API key de um usuário.
        
        Args:
            user_id: ID do usuário
            service_name: Nome do serviço
            
        Returns:
            Chave de API ou None se não existir
        """
        try:
            result = await self.db.table('renum_user_api_keys') \
                .select('encrypted_key', 'is_active') \
                .eq('user_id', str(user_id)) \
                .eq('service_name', service_name) \
                .execute()
            
            if not result.data:
                return None
            
            key_data = result.data[0]
            
            # Verifica se a chave está ativa
            if not key_data['is_active']:
                return None
            
            # Descriptografa a chave
            return self._decrypt_api_key(key_data['encrypted_key'])
            
        except Exception as e:
            logger.error(f"Failed to get API key: {str(e)}")
            return None
    
    async def get_user_api_keys(self, user_id: str) -> Dict[str, str]:
        """
        Obtém todas as API keys de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Dicionário com as chaves (service_name -> api_key)
        """
        try:
            result = await self.db.table('renum_user_api_keys') \
                .select('service_name', 'encrypted_key', 'is_active') \
                .eq('user_id', str(user_id)) \
                .eq('is_active', True) \
                .execute()
            
            api_keys = {}
            for key_data in result.data:
                # Descriptografa a chave
                api_keys[key_data['service_name']] = self._decrypt_api_key(key_data['encrypted_key'])
            
            return api_keys
            
        except Exception as e:
            logger.error(f"Failed to get API keys: {str(e)}")
            return {}
    
    async def delete_user_api_key(self, user_id: str, service_name: str) -> bool:
        """
        Remove uma API key de um usuário.
        
        Args:
            user_id: ID do usuário
            service_name: Nome do serviço
            
        Returns:
            True se a operação foi bem-sucedida
        """
        try:
            # Marca a chave como inativa (não exclui para manter histórico)
            await self.db.table('renum_user_api_keys') \
                .update({
                    'is_active': False,
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq('user_id', str(user_id)) \
                .eq('service_name', service_name) \
                .execute()
            
            logger.info(f"Deleted API key for user {user_id} and service {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {str(e)}")
            return False
    
    async def list_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Lista as API keys de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de informações sobre as chaves (sem as chaves em si)
        """
        try:
            result = await self.db.table('renum_user_api_keys') \
                .select('key_id', 'service_name', 'is_active', 'created_at', 'updated_at') \
                .eq('user_id', str(user_id)) \
                .execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {str(e)}")
            return []
    
    async def validate_api_key(self, user_id: str, service_name: str, api_key: str) -> bool:
        """
        Valida uma API key com o serviço correspondente.
        
        Args:
            user_id: ID do usuário
            service_name: Nome do serviço
            api_key: Chave de API a ser validada
            
        Returns:
            True se a chave é válida
        """
        # Implementação básica - apenas verifica se a chave não está vazia
        if not api_key:
            return False
        
        # Aqui você pode adicionar validação real com os serviços
        # Por exemplo, fazer uma chamada de teste para a API do serviço
        
        if service_name == "openai":
            # Validação com OpenAI
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                models = client.models.list()
                return True
            except Exception as e:
                logger.error(f"Failed to validate OpenAI API key: {str(e)}")
                return False
        
        elif service_name == "anthropic":
            # Validação com Anthropic
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                models = client.models.list()
                return True
            except Exception as e:
                logger.error(f"Failed to validate Anthropic API key: {str(e)}")
                return False
        
        # Para outros serviços, implementar validação específica
        
        # Por padrão, assume que a chave é válida
        return True
    
    async def get_api_keys_for_execution(
        self, 
        user_id: str, 
        execution_id: str, 
        custom_keys: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Obtém as API keys para uma execução específica.
        
        Combina as chaves padrão do usuário com chaves personalizadas para a execução.
        
        Args:
            user_id: ID do usuário
            execution_id: ID da execução
            custom_keys: Chaves personalizadas para esta execução
            
        Returns:
            Dicionário com as chaves a serem usadas
        """
        # Obtém as chaves padrão do usuário
        user_keys = await self.get_user_api_keys(user_id)
        
        # Se não há chaves personalizadas, retorna as chaves do usuário
        if not custom_keys:
            return user_keys
        
        # Combina as chaves, dando prioridade às personalizadas
        combined_keys = {**user_keys, **custom_keys}
        
        # Registra as chaves usadas para esta execução
        try:
            # Não armazena as chaves em si, apenas os serviços
            services_used = {service: True for service in combined_keys.keys()}
            
            await self.db.table('renum_team_executions') \
                .update({
                    'api_keys_used': services_used
                }) \
                .eq('execution_id', str(execution_id)) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to record API keys used: {str(e)}")
        
        return combined_keys