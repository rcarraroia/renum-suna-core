"""
Módulo que define as rotas da API para gerenciamento de compartilhamento de agentes.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from datetime import datetime, timedelta

from app.api.dependencies.auth import get_current_user
from app.api.schemas.agent_share import (
    AgentShareCreate, 
    AgentShareResponse, 
    AgentShareUpdate,
    AgentShareList
)
from app.models.agent_share import PermissionLevel
from app.repositories.agent_share import agent_share_repository
from app.repositories.agent import agent_repository
from app.models.auth import User
from app.core.logger import logger

router = APIRouter(tags=["agent-shares"])

@router.post("/{agent_id}/share", response_model=AgentShareResponse, status_code=201)
async def share_agent(
    agent_id: UUID = Path(..., description="ID do agente a ser compartilhado"),
    share_data: AgentShareCreate = Body(..., description="Dados do compartilhamento"),
    current_user: User = Depends(get_current_user)
):
    """
    Compartilha um agente com outro usuário.
    
    Args:
        agent_id: ID do agente a ser compartilhado.
        share_data: Dados do compartilhamento.
        current_user: Usuário autenticado.
        
    Returns:
        Detalhes do compartilhamento criado.
        
    Raises:
        HTTPException: Se o agente não existir, se o usuário não tiver permissão para compartilhar,
                      ou se o compartilhamento já existir.
    """
    # Verificar se o agente existe
    agent = await agent_repository.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Verificar se o usuário atual tem permissão para compartilhar o agente
    has_permission = await agent_share_repository.check_user_permission(
        agent_id=agent_id,
        user_id=current_user.id,
        required_level=PermissionLevel.ADMIN
    )
    
    # Se não for admin, verificar se é o criador do agente
    if not has_permission:
        agent_details = await agent_repository.get_by_id(agent_id)
        if not agent_details or str(agent_details.created_by) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para compartilhar este agente"
            )
    
    # Verificar se já existe um compartilhamento para este usuário
    existing_share = await agent_share_repository.get_by_agent_and_user(
        agent_id=agent_id,
        user_id=share_data.user_id
    )
    
    if existing_share:
        raise HTTPException(
            status_code=409,
            detail="Este agente já está compartilhado com este usuário"
        )
    
    # Calcular data de expiração se days_valid for fornecido
    expires_at = None
    if share_data.days_valid:
        expires_at = datetime.now() + timedelta(days=share_data.days_valid)
    
    # Criar o compartilhamento
    share = await agent_share_repository.create({
        "agent_id": str(agent_id),
        "user_id": str(share_data.user_id),
        "client_id": str(agent.client_id),
        "permission_level": share_data.permission_level,
        "created_by": str(current_user.id),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "metadata": share_data.metadata or {}
    })
    
    logger.info(
        f"Agente {agent_id} compartilhado com usuário {share_data.user_id} "
        f"por {current_user.id} com nível de permissão {share_data.permission_level}"
    )
    
    return share

@router.get("/{agent_id}/shares", response_model=AgentShareList)
async def list_agent_shares(
    agent_id: UUID = Path(..., description="ID do agente"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de compartilhamentos a retornar"),
    offset: int = Query(0, ge=0, description="Número de compartilhamentos a pular"),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os compartilhamentos de um agente.
    
    Args:
        agent_id: ID do agente.
        limit: Número máximo de compartilhamentos a retornar.
        offset: Número de compartilhamentos a pular.
        current_user: Usuário autenticado.
        
    Returns:
        Lista de compartilhamentos do agente.
        
    Raises:
        HTTPException: Se o agente não existir ou se o usuário não tiver permissão para ver os compartilhamentos.
    """
    # Verificar se o agente existe
    agent = await agent_repository.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    
    # Verificar se o usuário atual tem permissão para ver os compartilhamentos
    has_permission = await agent_share_repository.check_user_permission(
        agent_id=agent_id,
        user_id=current_user.id,
        required_level=PermissionLevel.ADMIN
    )
    
    # Se não for admin, verificar se é o criador do agente
    if not has_permission:
        if str(agent.created_by) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para ver os compartilhamentos deste agente"
            )
    
    # Obter os compartilhamentos
    shares = await agent_share_repository.get_by_agent_id(
        agent_id=agent_id,
        limit=limit,
        offset=offset
    )
    
    return {"shares": shares, "count": len(shares)}

@router.delete("/{agent_id}/shares/{share_id}", status_code=204)
async def remove_agent_share(
    agent_id: UUID = Path(..., description="ID do agente"),
    share_id: UUID = Path(..., description="ID do compartilhamento"),
    current_user: User = Depends(get_current_user)
):
    """
    Remove um compartilhamento de agente.
    
    Args:
        agent_id: ID do agente.
        share_id: ID do compartilhamento.
        current_user: Usuário autenticado.
        
    Raises:
        HTTPException: Se o compartilhamento não existir ou se o usuário não tiver permissão para removê-lo.
    """
    # Verificar se o compartilhamento existe
    share = await agent_share_repository.get_by_id(share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")
    
    # Verificar se o compartilhamento pertence ao agente especificado
    if str(share.agent_id) != str(agent_id):
        raise HTTPException(
            status_code=400,
            detail="O compartilhamento não pertence ao agente especificado"
        )
    
    # Verificar se o usuário atual tem permissão para remover o compartilhamento
    has_permission = await agent_share_repository.check_user_permission(
        agent_id=agent_id,
        user_id=current_user.id,
        required_level=PermissionLevel.ADMIN
    )
    
    # Se não for admin, verificar se é o criador do agente ou do compartilhamento
    if not has_permission:
        agent = await agent_repository.get_by_id(agent_id)
        if (str(agent.created_by) != str(current_user.id) and 
            str(share.created_by) != str(current_user.id)):
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para remover este compartilhamento"
            )
    
    # Remover o compartilhamento
    await agent_share_repository.delete(share_id)
    
    logger.info(
        f"Compartilhamento {share_id} do agente {agent_id} removido por {current_user.id}"
    )

@router.put("/{agent_id}/shares/{share_id}", response_model=AgentShareResponse)
async def update_agent_share(
    agent_id: UUID = Path(..., description="ID do agente"),
    share_id: UUID = Path(..., description="ID do compartilhamento"),
    update_data: AgentShareUpdate = Body(..., description="Dados de atualização do compartilhamento"),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um compartilhamento de agente.
    
    Args:
        agent_id: ID do agente.
        share_id: ID do compartilhamento.
        update_data: Dados de atualização do compartilhamento.
        current_user: Usuário autenticado.
        
    Returns:
        Compartilhamento atualizado.
        
    Raises:
        HTTPException: Se o compartilhamento não existir ou se o usuário não tiver permissão para atualizá-lo.
    """
    # Verificar se o compartilhamento existe
    share = await agent_share_repository.get_by_id(share_id)
    if not share:
        raise HTTPException(status_code=404, detail="Compartilhamento não encontrado")
    
    # Verificar se o compartilhamento pertence ao agente especificado
    if str(share.agent_id) != str(agent_id):
        raise HTTPException(
            status_code=400,
            detail="O compartilhamento não pertence ao agente especificado"
        )
    
    # Verificar se o usuário atual tem permissão para atualizar o compartilhamento
    has_permission = await agent_share_repository.check_user_permission(
        agent_id=agent_id,
        user_id=current_user.id,
        required_level=PermissionLevel.ADMIN
    )
    
    # Se não for admin, verificar se é o criador do agente
    if not has_permission:
        agent = await agent_repository.get_by_id(agent_id)
        if str(agent.created_by) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para atualizar este compartilhamento"
            )
    
    # Preparar dados para atualização
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Calcular nova data de expiração se days_valid for fornecido
    if update_data.days_valid is not None:
        if update_data.days_valid > 0:
            update_dict["expires_at"] = (datetime.now() + timedelta(days=update_data.days_valid)).isoformat()
        else:
            update_dict["expires_at"] = None
        
        # Remover days_valid do dicionário de atualização
        update_dict.pop("days_valid", None)
    
    # Atualizar o compartilhamento
    updated_share = await agent_share_repository.update(share_id, update_dict)
    
    logger.info(
        f"Compartilhamento {share_id} do agente {agent_id} atualizado por {current_user.id}"
    )
    
    return updated_share

@router.get("/shared-with-me", response_model=List[AgentShareResponse])
async def list_agents_shared_with_me(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de compartilhamentos a retornar"),
    offset: int = Query(0, ge=0, description="Número de compartilhamentos a pular"),
    current_user: User = Depends(get_current_user)
):
    """
    Lista todos os agentes compartilhados com o usuário atual.
    
    Args:
        limit: Número máximo de compartilhamentos a retornar.
        offset: Número de compartilhamentos a pular.
        current_user: Usuário autenticado.
        
    Returns:
        Lista de compartilhamentos de agentes com o usuário atual.
    """
    shares = await agent_share_repository.get_by_user_id(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    # Filtrar compartilhamentos expirados
    now = datetime.now()
    valid_shares = [
        share for share in shares
        if not share.expires_at or share.expires_at > now
    ]
    
    return valid_shares