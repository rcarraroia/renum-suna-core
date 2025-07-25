"""
Rotas da API para notificações
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.models.notification_models import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationFilter,
    NotificationStats,
    NotificationBatch,
    NotificationPreference,
    NotificationType
)
from app.services.notification_service import notification_service
from app.core.auth import get_current_user
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])
security = HTTPBearer()


@router.post("/", response_model=Notification)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Cria uma nova notificação"""
    try:
        # Verifica se o usuário pode criar notificações para outros usuários
        if notification_data.user_id != current_user["id"] and not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Cannot create notifications for other users")
        
        notification = await notification_service.create_notification(notification_data)
        return notification
        
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.post("/batch", response_model=List[Notification])
async def create_batch_notifications(
    batch: NotificationBatch,
    current_user: dict = Depends(get_current_user)
):
    """Cria múltiplas notificações em lote"""
    try:
        # Verifica permissões para cada notificação
        if not current_user.get("is_admin", False):
            for notification_data in batch.notifications:
                if notification_data.user_id != current_user["id"]:
                    raise HTTPException(status_code=403, detail="Cannot create notifications for other users")
        
        notifications = await notification_service.create_batch_notifications(batch)
        return notifications
        
    except Exception as e:
        logger.error(f"Error creating batch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create batch notifications")


@router.get("/", response_model=List[Notification])
async def get_notifications(
    type: Optional[NotificationType] = Query(None, description="Filtrar por tipo"),
    read: Optional[bool] = Query(None, description="Filtrar por status de leitura"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: dict = Depends(get_current_user)
):
    """Lista notificações do usuário atual"""
    try:
        filters = NotificationFilter(
            user_id=current_user["id"],
            type=type,
            read=read,
            limit=limit,
            offset=offset
        )
        
        notifications = await notification_service.get_user_notifications(current_user["id"], filters)
        return notifications
        
    except Exception as e:
        logger.error(f"Error getting notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notifications")


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: dict = Depends(get_current_user)
):
    """Obtém estatísticas de notificações do usuário"""
    try:
        stats = await notification_service.get_notification_stats(current_user["id"])
        return stats
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Busca uma notificação específica"""
    try:
        notification = await notification_service.get_notification(notification_id, current_user["id"])
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification")


@router.patch("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: str,
    update_data: NotificationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza uma notificação"""
    try:
        # Verifica se a notificação existe e pertence ao usuário
        existing = await notification_service.get_notification(notification_id, current_user["id"])
        if not existing:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = await notification_service.repository.update_notification(notification_id, update_data)
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification")


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marca uma notificação como lida"""
    try:
        notification = await notification_service.mark_as_read(notification_id, current_user["id"])
        
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")


@router.post("/read-all")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user)
):
    """Marca todas as notificações como lidas"""
    try:
        count = await notification_service.mark_all_as_read(current_user["id"])
        return {"message": f"Marked {count} notifications as read"}
        
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to mark all notifications as read")


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove uma notificação"""
    try:
        success = await notification_service.delete_notification(notification_id, current_user["id"])
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.delete("/")
async def clear_all_notifications(
    current_user: dict = Depends(get_current_user)
):
    """Remove todas as notificações do usuário"""
    try:
        count = await notification_service.clear_all_notifications(current_user["id"])
        return {"message": f"Deleted {count} notifications"}
        
    except Exception as e:
        logger.error(f"Error clearing all notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear all notifications")


@router.get("/preferences/", response_model=NotificationPreference)
async def get_notification_preferences(
    current_user: dict = Depends(get_current_user)
):
    """Obtém as preferências de notificação do usuário"""
    try:
        preferences = await notification_service.get_user_preferences(current_user["id"])
        return preferences
        
    except Exception as e:
        logger.error(f"Error getting notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get notification preferences")


@router.put("/preferences/", response_model=NotificationPreference)
async def update_notification_preferences(
    preferences: NotificationPreference,
    current_user: dict = Depends(get_current_user)
):
    """Atualiza as preferências de notificação do usuário"""
    try:
        updated_preferences = await notification_service.update_user_preferences(current_user["id"], preferences)
        return updated_preferences
        
    except Exception as e:
        logger.error(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update notification preferences")


# Rotas administrativas
@router.post("/admin/system", response_model=List[Notification])
async def send_system_notification(
    user_ids: List[str],
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    current_user: dict = Depends(get_current_user)
):
    """Envia notificação do sistema para múltiplos usuários (apenas admin)"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        notifications = await notification_service.send_system_notification(
            user_ids, title, message, type
        )
        
        return notifications
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending system notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send system notification")


@router.post("/admin/cleanup")
async def cleanup_expired_notifications(
    current_user: dict = Depends(get_current_user)
):
    """Remove notificações expiradas (apenas admin)"""
    try:
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        count = await notification_service.repository.cleanup_expired_notifications()
        return {"message": f"Cleaned up {count} expired notifications"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup notifications")