"""
Módulo que implementa os endpoints REST para autenticação e autorização.

Este módulo contém os endpoints para registro, login, logout e gerenciamento de usuários e clientes.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.schemas.auth import (
    UserCreate,
    UserUpdate,
    UserResponse,
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    SessionResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResponse,
    PasswordChangeRequest,
    PasswordChangeResponse
)
from app.models.auth import User, Client, UserRole
from app.services.auth import auth_service
from app.repositories.auth import user_repository, client_repository, session_repository

# Configurar logger
logger = logging.getLogger(__name__)

# Configurar OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v2/auth/login")

# Criar router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Item não encontrado"}}
)


# Dependência para obter o usuário atual
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Obtém o usuário atual a partir do token JWT.
    
    Args:
        token: Token JWT.
        
    Returns:
        Usuário atual.
        
    Raises:
        HTTPException: Se o token for inválido ou o usuário não for encontrado.
    """
    user_data = await auth_service.validate_jwt_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return User(**user_data["user"])


# Dependência para verificar se o usuário é administrador
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verifica se o usuário atual é administrador.
    
    Args:
        current_user: Usuário atual.
        
    Returns:
        Usuário atual se for administrador.
        
    Raises:
        HTTPException: Se o usuário não for administrador.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada. Apenas administradores podem acessar este recurso."
        )
    
    return current_user


# Endpoints para autenticação

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Registra um novo usuário."""
    try:
        result = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            client_id=user_data.client_id,
            role=user_data.role,
            display_name=user_data.display_name
        )
        
        return result["user"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar usuário: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Autentica um usuário existente."""
    try:
        result = await auth_service.login(
            email=login_data.email,
            password=login_data.password
        )
        
        # Formatar resposta
        response = {
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "session_token": result["session"]["token"],
            "expires_at": result["session"]["expires_at"]
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao autenticar usuário: {str(e)}"
        )


@router.post("/login/oauth", response_model=LoginResponse)
async def login_oauth(form_data: OAuth2PasswordRequestForm = Depends()):
    """Autentica um usuário usando OAuth2."""
    try:
        result = await auth_service.login(
            email=form_data.username,
            password=form_data.password
        )
        
        # Formatar resposta
        response = {
            "user": result["user"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "session_token": result["session"]["token"],
            "expires_at": result["session"]["expires_at"]
        }
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao autenticar usuário: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(logout_data: LogoutRequest):
    """Encerra uma sessão de usuário."""
    try:
        success = await auth_service.logout(logout_data.session_token)
        
        return {
            "success": success
        }
    except Exception as e:
        logger.error(f"Erro ao encerrar sessão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao encerrar sessão: {str(e)}"
        )


@router.post("/logout/all", response_model=LogoutResponse)
async def logout_all(current_user: User = Depends(get_current_user)):
    """Encerra todas as sessões do usuário atual."""
    try:
        count = await auth_service.logout_all_sessions(current_user.id)
        
        return {
            "success": True
        }
    except Exception as e:
        logger.error(f"Erro ao encerrar todas as sessões: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao encerrar todas as sessões: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(current_user: User = Depends(get_current_user)):
    """Obtém as sessões ativas do usuário atual."""
    try:
        sessions = await auth_service.get_user_sessions(current_user.id)
        
        return sessions
    except Exception as e:
        logger.error(f"Erro ao obter sessões: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter sessões: {str(e)}"
        )


@router.post("/password/reset", response_model=PasswordResetResponse)
async def request_password_reset(reset_data: PasswordResetRequest):
    """Solicita a redefinição de senha para um usuário."""
    try:
        success = await auth_service.request_password_reset(reset_data.email)
        
        # Não revelar se o usuário existe ou não por segurança
        return {
            "success": True,
            "message": "Se o email estiver registrado, você receberá um link para redefinir sua senha."
        }
    except Exception as e:
        logger.error(f"Erro ao solicitar redefinição de senha: {str(e)}")
        # Não revelar detalhes do erro por segurança
        return {
            "success": True,
            "message": "Se o email estiver registrado, você receberá um link para redefinir sua senha."
        }


@router.post("/password/reset/confirm", response_model=PasswordResetConfirmResponse)
async def confirm_password_reset(reset_data: PasswordResetConfirmRequest):
    """Redefine a senha de um usuário."""
    try:
        success = await auth_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        return {
            "success": success,
            "message": "Senha redefinida com sucesso."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao redefinir senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao redefinir senha: {str(e)}"
        )


@router.post("/password/change", response_model=PasswordChangeResponse)
async def change_password(
    change_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Altera a senha do usuário atual."""
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=change_data.current_password,
            new_password=change_data.new_password
        )
        
        return {
            "success": success,
            "message": "Senha alterada com sucesso."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao alterar senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao alterar senha: {str(e)}"
        )


# Endpoints para gerenciamento de usuários

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    client_id: Optional[UUID] = Query(None, description="Filtrar por ID do cliente"),
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular"),
    current_user: User = Depends(get_admin_user)
):
    """Lista usuários (apenas para administradores)."""
    try:
        # Filtrar por client_id se fornecido
        filters = {}
        if client_id:
            filters["client_id"] = client_id
        
        # Buscar no repositório
        users = await user_repository.list(filters=filters, limit=limit, offset=offset)
        
        return users
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar usuários: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID = Path(..., description="ID do usuário"),
    current_user: User = Depends(get_current_user)
):
    """Obtém um usuário pelo ID."""
    try:
        # Verificar permissão
        if current_user.id != user_id and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada. Você só pode acessar seus próprios dados."
            )
        
        # Buscar no repositório
        user = await user_repository.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter usuário: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID = Path(..., description="ID do usuário"),
    user_data: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um usuário."""
    try:
        # Verificar permissão
        is_admin = current_user.role == UserRole.ADMIN
        is_self = current_user.id == user_id
        
        if not is_admin and not is_self:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada. Você só pode atualizar seus próprios dados."
            )
        
        # Verificar se o usuário existe
        existing_user = await user_repository.get_by_id(user_id)
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        
        # Verificar permissões para campos específicos
        if user_data.role is not None and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada. Apenas administradores podem alterar o papel do usuário."
            )
        
        if user_data.is_active is not None and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada. Apenas administradores podem ativar/desativar usuários."
            )
        
        # Atualizar campos
        if user_data.display_name is not None:
            existing_user.display_name = user_data.display_name
        
        if user_data.role is not None:
            existing_user.role = user_data.role
        
        if user_data.is_active is not None:
            existing_user.is_active = user_data.is_active
        
        if user_data.metadata is not None:
            existing_user.metadata = user_data.metadata
        
        # Salvar no repositório
        updated_user = await user_repository.update(user_id, existing_user)
        
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID = Path(..., description="ID do usuário"),
    current_user: User = Depends(get_admin_user)
):
    """Exclui um usuário (apenas para administradores)."""
    try:
        # Verificar se o usuário existe
        existing_user = await user_repository.get_by_id(user_id)
        
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado"
            )
        
        # Não permitir que um administrador exclua a si mesmo
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode excluir sua própria conta"
            )
        
        # Excluir do repositório
        await user_repository.delete(user_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir usuário: {str(e)}"
        )


# Endpoints para gerenciamento de clientes

@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_admin_user)
):
    """Cria um novo cliente (apenas para administradores)."""
    try:
        # Verificar se já existe um cliente com o mesmo nome
        existing_client = await client_repository.get_by_name(client_data.name)
        if existing_client:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cliente com nome '{client_data.name}' já existe"
            )
        
        # Criar objeto Client
        client = Client(
            name=client_data.name,
            status=client_data.status,
            settings=client_data.settings or {}
        )
        
        # Salvar no repositório
        created_client = await client_repository.create(client)
        
        return created_client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar cliente: {str(e)}"
        )


@router.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    limit: int = Query(100, description="Número máximo de resultados"),
    offset: int = Query(0, description="Número de resultados a pular"),
    current_user: User = Depends(get_admin_user)
):
    """Lista clientes (apenas para administradores)."""
    try:
        # Buscar no repositório
        clients = await client_repository.list(limit=limit, offset=offset)
        
        return clients
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar clientes: {str(e)}"
        )


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID = Path(..., description="ID do cliente"),
    current_user: User = Depends(get_current_user)
):
    """Obtém um cliente pelo ID."""
    try:
        # Verificar permissão
        is_admin = current_user.role == UserRole.ADMIN
        is_member = current_user.client_id == client_id
        
        if not is_admin and not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissão negada. Você só pode acessar dados do seu próprio cliente."
            )
        
        # Buscar no repositório
        client = await client_repository.get_by_id(client_id)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com ID {client_id} não encontrado"
            )
        
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter cliente: {str(e)}"
        )


@router.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID = Path(..., description="ID do cliente"),
    client_data: ClientUpdate = Body(...),
    current_user: User = Depends(get_admin_user)
):
    """Atualiza um cliente (apenas para administradores)."""
    try:
        # Verificar se o cliente existe
        existing_client = await client_repository.get_by_id(client_id)
        
        if not existing_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com ID {client_id} não encontrado"
            )
        
        # Atualizar campos
        if client_data.name is not None:
            # Verificar se já existe outro cliente com o mesmo nome
            if client_data.name != existing_client.name:
                name_exists = await client_repository.get_by_name(client_data.name)
                if name_exists:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cliente com nome '{client_data.name}' já existe"
                    )
            
            existing_client.name = client_data.name
        
        if client_data.status is not None:
            existing_client.status = client_data.status
        
        if client_data.settings is not None:
            existing_client.settings = client_data.settings
        
        # Salvar no repositório
        updated_client = await client_repository.update(client_id, existing_client)
        
        return updated_client
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar cliente: {str(e)}"
        )


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID = Path(..., description="ID do cliente"),
    current_user: User = Depends(get_admin_user)
):
    """Exclui um cliente (apenas para administradores)."""
    try:
        # Verificar se o cliente existe
        existing_client = await client_repository.get_by_id(client_id)
        
        if not existing_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com ID {client_id} não encontrado"
            )
        
        # Verificar se o cliente tem usuários
        users = await user_repository.get_by_client_id(client_id)
        if users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível excluir um cliente que possui usuários"
            )
        
        # Excluir do repositório
        await client_repository.delete(client_id)
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir cliente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir cliente: {str(e)}"
        )