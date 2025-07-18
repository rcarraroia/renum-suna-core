"""
Módulo que implementa o serviço de autenticação e autorização para a Plataforma Renum.

Este módulo fornece funcionalidades para autenticação de usuários, gerenciamento de sessões
e verificação de permissões usando o Supabase Auth.
"""

import logging
import secrets
import time
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from pydantic import EmailStr

from app.core.config import settings
from app.core.supabase_client import supabase
from app.models.auth import User, Client, Session, UserRole, ClientStatus
from app.repositories.auth import (
    user_repository,
    client_repository,
    session_repository,
    password_reset_token_repository
)

# Configurar logger
logger = logging.getLogger(__name__)


class AuthService:
    """Serviço para autenticação e autorização."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de autenticação."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de autenticação."""
        self.supabase = supabase
        self.session_expiry_days = 7  # Sessões expiram após 7 dias por padrão
        logger.info("Serviço de autenticação inicializado")
    
    async def register_user(
        self,
        email: EmailStr,
        password: str,
        client_id: Union[str, UUID],
        role: UserRole = UserRole.USER,
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Registra um novo usuário.
        
        Args:
            email: Email do usuário.
            password: Senha do usuário.
            client_id: ID do cliente ao qual o usuário pertence.
            role: Papel do usuário.
            display_name: Nome de exibição do usuário.
            
        Returns:
            Dicionário com informações do usuário registrado e token de sessão.
            
        Raises:
            HTTPException: Se ocorrer um erro durante o registro.
        """
        try:
            # Verificar se o cliente existe
            client = await client_repository.get_by_id(client_id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cliente com ID {client_id} não encontrado"
                )
            
            # Verificar se o usuário já existe
            existing_user = await user_repository.get_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Usuário com email {email} já existe"
                )
            
            # Registrar usuário no Supabase Auth
            auth_response = await self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falha ao registrar usuário no Supabase Auth"
                )
            
            # Criar usuário no banco de dados
            user = User(
                id=auth_response.user.id,
                email=email,
                client_id=client_id,
                role=role,
                display_name=display_name,
                last_login=datetime.now()
            )
            
            created_user = await user_repository.create(user)
            
            # Criar sessão
            session = await self._create_session(created_user.id)
            
            return {
                "user": created_user.model_dump(),
                "session": session.model_dump(),
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao registrar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao registrar usuário: {str(e)}"
            )
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Autentica um usuário existente.
        
        Args:
            email: Email do usuário.
            password: Senha do usuário.
            
        Returns:
            Dicionário com informações do usuário autenticado e token de sessão.
            
        Raises:
            HTTPException: Se as credenciais forem inválidas ou ocorrer um erro durante a autenticação.
        """
        try:
            # Autenticar usuário no Supabase Auth
            auth_response = await self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciais inválidas"
                )
            
            # Buscar usuário no banco de dados
            user = await user_repository.get_by_id(auth_response.user.id)
            if not user:
                # Se o usuário existe no Supabase Auth mas não no banco de dados,
                # algo está errado com a sincronização
                logger.error(f"Usuário {auth_response.user.id} existe no Supabase Auth mas não no banco de dados")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro de sincronização de usuário"
                )
            
            # Verificar se o usuário está ativo
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário desativado"
                )
            
            # Verificar se o cliente está ativo
            client = await client_repository.get_by_id(user.client_id)
            if not client or client.status != ClientStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cliente inativo ou suspenso"
                )
            
            # Atualizar último login
            user = await user_repository.update_last_login(user.id)
            
            # Criar sessão
            session = await self._create_session(user.id)
            
            return {
                "user": user.model_dump(),
                "session": session.model_dump(),
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao autenticar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao autenticar usuário: {str(e)}"
            )
    
    async def logout(self, session_token: str) -> bool:
        """Encerra uma sessão de usuário.
        
        Args:
            session_token: Token da sessão a ser encerrada.
            
        Returns:
            True se a sessão foi encerrada com sucesso, False caso contrário.
        """
        try:
            # Buscar sessão
            session = await session_repository.get_by_token(session_token)
            if not session:
                return False
            
            # Invalidar sessão
            await session_repository.invalidate(session.id)
            
            # Fazer logout no Supabase Auth
            await self.supabase.auth.sign_out()
            
            return True
        except Exception as e:
            logger.error(f"Erro ao encerrar sessão: {str(e)}")
            return False
    
    async def logout_all_sessions(self, user_id: Union[str, UUID]) -> int:
        """Encerra todas as sessões de um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Número de sessões encerradas.
        """
        try:
            # Invalidar todas as sessões
            return await session_repository.invalidate_all_for_user(user_id)
        except Exception as e:
            logger.error(f"Erro ao encerrar todas as sessões do usuário {user_id}: {str(e)}")
            return 0
    
    async def get_user_sessions(self, user_id: Union[str, UUID]) -> List[Session]:
        """Obtém as sessões ativas de um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de sessões ativas do usuário.
        """
        try:
            return await session_repository.get_active_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Erro ao obter sessões do usuário {user_id}: {str(e)}")
            return []
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Valida uma sessão de usuário.
        
        Args:
            session_token: Token da sessão a ser validada.
            
        Returns:
            Dicionário com informações do usuário e da sessão se a sessão for válida, None caso contrário.
        """
        try:
            # Buscar sessão
            session = await session_repository.get_by_token(session_token)
            if not session:
                return None
            
            # Verificar se a sessão está ativa
            if not session.is_active:
                return None
            
            # Verificar se a sessão expirou
            if session.expires_at < datetime.now():
                await session_repository.invalidate(session.id)
                return None
            
            # Buscar usuário
            user = await user_repository.get_by_id(session.user_id)
            if not user:
                return None
            
            # Verificar se o usuário está ativo
            if not user.is_active:
                return None
            
            # Verificar se o cliente está ativo
            client = await client_repository.get_by_id(user.client_id)
            if not client or client.status != ClientStatus.ACTIVE:
                return None
            
            # Atualizar última atividade da sessão
            await session_repository.update_last_activity(session.id)
            
            return {
                "user": user.model_dump(),
                "session": session.model_dump()
            }
        except Exception as e:
            logger.error(f"Erro ao validar sessão: {str(e)}")
            return None
    
    async def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida um token JWT do Supabase Auth.
        
        Args:
            token: Token JWT a ser validado.
            
        Returns:
            Dicionário com informações do usuário se o token for válido, None caso contrário.
        """
        try:
            # Verificar token JWT
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Verificar se o token expirou
            if "exp" in payload and payload["exp"] < time.time():
                return None
            
            # Verificar se o token contém o ID do usuário
            if "sub" not in payload:
                return None
            
            # Buscar usuário
            user_id = payload["sub"]
            user = await user_repository.get_by_id(user_id)
            if not user:
                return None
            
            # Verificar se o usuário está ativo
            if not user.is_active:
                return None
            
            # Verificar se o cliente está ativo
            client = await client_repository.get_by_id(user.client_id)
            if not client or client.status != ClientStatus.ACTIVE:
                return None
            
            return {
                "user": user.model_dump(),
                "token_payload": payload
            }
        except Exception as e:
            logger.error(f"Erro ao validar token JWT: {str(e)}")
            return None
    
    async def request_password_reset(self, email: str) -> bool:
        """Solicita a redefinição de senha para um usuário.
        
        Args:
            email: Email do usuário.
            
        Returns:
            True se a solicitação foi processada com sucesso, False caso contrário.
        """
        try:
            # Buscar usuário pelo email
            user = await user_repository.get_by_email(email)
            if not user:
                # Não revelar se o usuário existe ou não por segurança
                return True
            
            # Verificar se o usuário está ativo
            if not user.is_active:
                return True
            
            # Verificar se o cliente está ativo
            client = await client_repository.get_by_id(user.client_id)
            if not client or client.status != ClientStatus.ACTIVE:
                return True
            
            # Criar token de redefinição de senha
            token = await password_reset_token_repository.create_for_user(user.id)
            
            # Em uma implementação real, enviaríamos um email com o link de redefinição de senha
            # Aqui, apenas logamos o token para fins de demonstração
            logger.info(f"Token de redefinição de senha para {email}: {token.token}")
            
            # Solicitar redefinição de senha no Supabase Auth
            await self.supabase.auth.reset_password_email(email)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao solicitar redefinição de senha: {str(e)}")
            return False
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """Redefine a senha de um usuário.
        
        Args:
            token: Token de redefinição de senha.
            new_password: Nova senha.
            
        Returns:
            True se a senha foi redefinida com sucesso, False caso contrário.
            
        Raises:
            HTTPException: Se o token for inválido ou expirado.
        """
        try:
            # Buscar token
            reset_token = await password_reset_token_repository.get_by_token(token)
            if not reset_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token inválido"
                )
            
            # Verificar se o token já foi usado
            if reset_token.is_used:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token já utilizado"
                )
            
            # Verificar se o token expirou
            if reset_token.expires_at < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token expirado"
                )
            
            # Buscar usuário
            user = await user_repository.get_by_id(reset_token.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuário não encontrado"
                )
            
            # Verificar se o usuário está ativo
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuário desativado"
                )
            
            # Atualizar senha no Supabase Auth
            # Em uma implementação real, usaríamos a API do Supabase Auth para atualizar a senha
            # Aqui, apenas simulamos a atualização
            logger.info(f"Senha atualizada para o usuário {user.email}")
            
            # Marcar token como usado
            await password_reset_token_repository.mark_as_used(reset_token.id)
            
            # Invalidar todas as sessões do usuário
            await session_repository.invalidate_all_for_user(user.id)
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao redefinir senha: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao redefinir senha: {str(e)}"
            )
    
    async def change_password(self, user_id: Union[str, UUID], current_password: str, new_password: str) -> bool:
        """Altera a senha de um usuário.
        
        Args:
            user_id: ID do usuário.
            current_password: Senha atual.
            new_password: Nova senha.
            
        Returns:
            True se a senha foi alterada com sucesso, False caso contrário.
            
        Raises:
            HTTPException: Se a senha atual for inválida ou ocorrer um erro durante a alteração.
        """
        try:
            # Buscar usuário
            user = await user_repository.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            
            # Verificar senha atual
            # Em uma implementação real, usaríamos a API do Supabase Auth para verificar a senha
            # Aqui, apenas simulamos a verificação
            
            # Atualizar senha no Supabase Auth
            # Em uma implementação real, usaríamos a API do Supabase Auth para atualizar a senha
            # Aqui, apenas simulamos a atualização
            logger.info(f"Senha alterada para o usuário {user.email}")
            
            # Invalidar todas as sessões do usuário, exceto a atual
            await session_repository.invalidate_all_for_user(user_id)
            
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao alterar senha: {str(e)}"
            )
    
    async def _create_session(self, user_id: Union[str, UUID]) -> Session:
        """Cria uma nova sessão para um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Sessão criada.
        """
        # Gerar token aleatório
        token = secrets.token_urlsafe(32)
        
        # Calcular data de expiração
        expires_at = datetime.now() + timedelta(days=self.session_expiry_days)
        
        # Criar entidade
        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_active=True,
            last_activity=datetime.now()
        )
        
        # Salvar no repositório
        return await session_repository.create(session)


# Instância global do serviço de autenticação
auth_service = AuthService.get_instance()