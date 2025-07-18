"""
Módulo que implementa os repositórios para autenticação e autorização da Plataforma Renum.

Este módulo contém as implementações específicas do padrão Repository para as
entidades de autenticação e autorização, como usuários, clientes e sessões.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from uuid import UUID
from datetime import datetime, timedelta

from app.core.supabase_client import supabase
from app.models.auth import Client, User, Session, PasswordResetToken, UserRole, ClientStatus
from app.repositories.base import SupabaseRepository

# Configurar logger
logger = logging.getLogger(__name__)


class ClientRepository(SupabaseRepository[Client]):
    """Repositório para clientes da plataforma."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "clients")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Client:
        """Converte um dicionário de dados em uma entidade Client.
        
        Args:
            data: Dicionário com os dados do cliente.
            
        Returns:
            Entidade Client correspondente aos dados.
        """
        return Client(**data)
    
    def _map_to_dict(self, entity: Client) -> Dict[str, Any]:
        """Converte uma entidade Client em um dicionário de dados.
        
        Args:
            entity: Entidade Client a ser convertida.
            
        Returns:
            Dicionário com os dados do cliente.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_name(self, name: str) -> Optional[Client]:
        """Recupera um cliente pelo nome.
        
        Args:
            name: Nome do cliente.
            
        Returns:
            Cliente encontrado ou None se não existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("name", name).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def update_status(self, client_id: Union[str, UUID], status: ClientStatus) -> Client:
        """Atualiza o status de um cliente.
        
        Args:
            client_id: ID do cliente.
            status: Novo status do cliente.
            
        Returns:
            Cliente atualizado.
        """
        result = await self.supabase.from_(self.table_name).update({"status": status}).eq("id", str(client_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar status do cliente com ID {client_id}")


class UserRepository(SupabaseRepository[User]):
    """Repositório para usuários da plataforma."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "users")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> User:
        """Converte um dicionário de dados em uma entidade User.
        
        Args:
            data: Dicionário com os dados do usuário.
            
        Returns:
            Entidade User correspondente aos dados.
        """
        return User(**data)
    
    def _map_to_dict(self, entity: User) -> Dict[str, Any]:
        """Converte uma entidade User em um dicionário de dados.
        
        Args:
            entity: Entidade User a ser convertida.
            
        Returns:
            Dicionário com os dados do usuário.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Recupera um usuário pelo email.
        
        Args:
            email: Email do usuário.
            
        Returns:
            Usuário encontrado ou None se não existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("email", email).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def get_by_client_id(self, client_id: Union[str, UUID], limit: int = 100, offset: int = 0) -> List[User]:
        """Recupera usuários de um cliente específico.
        
        Args:
            client_id: ID do cliente.
            limit: Número máximo de usuários a serem retornados.
            offset: Número de usuários a serem pulados.
            
        Returns:
            Lista de usuários do cliente.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("client_id", str(client_id)).limit(limit).offset(offset).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def update_last_login(self, user_id: Union[str, UUID]) -> User:
        """Atualiza a data e hora do último login de um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Usuário atualizado.
        """
        result = await self.supabase.from_(self.table_name).update({"last_login": datetime.now().isoformat()}).eq("id", str(user_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar last_login do usuário com ID {user_id}")
    
    async def update_role(self, user_id: Union[str, UUID], role: UserRole) -> User:
        """Atualiza o papel de um usuário.
        
        Args:
            user_id: ID do usuário.
            role: Novo papel do usuário.
            
        Returns:
            Usuário atualizado.
        """
        result = await self.supabase.from_(self.table_name).update({"role": role}).eq("id", str(user_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar role do usuário com ID {user_id}")
    
    async def deactivate(self, user_id: Union[str, UUID]) -> User:
        """Desativa um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Usuário desativado.
        """
        result = await self.supabase.from_(self.table_name).update({"is_active": False}).eq("id", str(user_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao desativar usuário com ID {user_id}")


class SessionRepository(SupabaseRepository[Session]):
    """Repositório para sessões de usuário."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "sessions")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> Session:
        """Converte um dicionário de dados em uma entidade Session.
        
        Args:
            data: Dicionário com os dados da sessão.
            
        Returns:
            Entidade Session correspondente aos dados.
        """
        return Session(**data)
    
    def _map_to_dict(self, entity: Session) -> Dict[str, Any]:
        """Converte uma entidade Session em um dicionário de dados.
        
        Args:
            entity: Entidade Session a ser convertida.
            
        Returns:
            Dicionário com os dados da sessão.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_active_by_user_id(self, user_id: Union[str, UUID]) -> List[Session]:
        """Recupera sessões ativas de um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Lista de sessões ativas do usuário.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("user_id", str(user_id)).eq("is_active", True).execute()
        return [self._map_to_entity(item) for item in result.data]
    
    async def get_by_token(self, token: str) -> Optional[Session]:
        """Recupera uma sessão pelo token.
        
        Args:
            token: Token da sessão.
            
        Returns:
            Sessão encontrada ou None se não existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("token", token).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def invalidate(self, session_id: Union[str, UUID]) -> Session:
        """Invalida uma sessão.
        
        Args:
            session_id: ID da sessão.
            
        Returns:
            Sessão invalidada.
        """
        result = await self.supabase.from_(self.table_name).update({"is_active": False}).eq("id", str(session_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao invalidar sessão com ID {session_id}")
    
    async def invalidate_all_for_user(self, user_id: Union[str, UUID]) -> int:
        """Invalida todas as sessões de um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Número de sessões invalidadas.
        """
        result = await self.supabase.from_(self.table_name).update({"is_active": False}).eq("user_id", str(user_id)).eq("is_active", True).execute()
        return len(result.data) if result.data else 0
    
    async def update_last_activity(self, session_id: Union[str, UUID]) -> Session:
        """Atualiza a data e hora da última atividade de uma sessão.
        
        Args:
            session_id: ID da sessão.
            
        Returns:
            Sessão atualizada.
        """
        result = await self.supabase.from_(self.table_name).update({"last_activity": datetime.now().isoformat()}).eq("id", str(session_id)).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao atualizar last_activity da sessão com ID {session_id}")
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove sessões expiradas.
        
        Returns:
            Número de sessões removidas.
        """
        now = datetime.now().isoformat()
        result = await self.supabase.from_(self.table_name).update({"is_active": False}).lt("expires_at", now).eq("is_active", True).execute()
        return len(result.data) if result.data else 0


class PasswordResetTokenRepository(SupabaseRepository[PasswordResetToken]):
    """Repositório para tokens de redefinição de senha."""
    
    def __init__(self):
        """Inicializa o repositório."""
        super().__init__(supabase, "password_reset_tokens")
    
    def _map_to_entity(self, data: Dict[str, Any]) -> PasswordResetToken:
        """Converte um dicionário de dados em uma entidade PasswordResetToken.
        
        Args:
            data: Dicionário com os dados do token.
            
        Returns:
            Entidade PasswordResetToken correspondente aos dados.
        """
        return PasswordResetToken(**data)
    
    def _map_to_dict(self, entity: PasswordResetToken) -> Dict[str, Any]:
        """Converte uma entidade PasswordResetToken em um dicionário de dados.
        
        Args:
            entity: Entidade PasswordResetToken a ser convertida.
            
        Returns:
            Dicionário com os dados do token.
        """
        return entity.model_dump(exclude_unset=True)
    
    async def get_by_token(self, token: str) -> Optional[PasswordResetToken]:
        """Recupera um token de redefinição de senha pelo token.
        
        Args:
            token: Token de redefinição de senha.
            
        Returns:
            Token encontrado ou None se não existir.
        """
        result = await self.supabase.from_(self.table_name).select("*").eq("token", token).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def get_valid_by_user_id(self, user_id: Union[str, UUID]) -> Optional[PasswordResetToken]:
        """Recupera um token de redefinição de senha válido para um usuário.
        
        Args:
            user_id: ID do usuário.
            
        Returns:
            Token válido encontrado ou None se não existir.
        """
        now = datetime.now().isoformat()
        result = await self.supabase.from_(self.table_name).select("*").eq("user_id", str(user_id)).eq("is_used", False).gt("expires_at", now).execute()
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        return None
    
    async def mark_as_used(self, token_id: Union[str, UUID]) -> PasswordResetToken:
        """Marca um token como usado.
        
        Args:
            token_id: ID do token.
            
        Returns:
            Token atualizado.
        """
        result = await self.supabase.from_(self.table_name).update({
            "is_used": True,
            "used_at": datetime.now().isoformat()
        }).eq("id", str(token_id)).execute()
        
        if result.data and len(result.data) > 0:
            return self._map_to_entity(result.data[0])
        raise ValueError(f"Falha ao marcar token com ID {token_id} como usado")
    
    async def create_for_user(self, user_id: Union[str, UUID], expires_in_hours: int = 24) -> PasswordResetToken:
        """Cria um novo token de redefinição de senha para um usuário.
        
        Args:
            user_id: ID do usuário.
            expires_in_hours: Número de horas até a expiração do token.
            
        Returns:
            Token criado.
        """
        import secrets
        
        # Gerar token aleatório
        token = secrets.token_urlsafe(32)
        
        # Calcular data de expiração
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        # Criar entidade
        token_entity = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_used=False
        )
        
        # Salvar no repositório
        return await self.create(token_entity)


# Instâncias globais dos repositórios
client_repository = ClientRepository()
user_repository = UserRepository()
session_repository = SessionRepository()
password_reset_token_repository = PasswordResetTokenRepository()