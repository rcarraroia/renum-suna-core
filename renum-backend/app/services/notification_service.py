"""
Serviço de notificações em tempo real
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

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
from app.repositories.notification_repository import NotificationRepository
from app.services.websocket_manager import WebSocketManager
from app.core.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Serviço para gerenciamento de notificações"""

    def __init__(self, websocket_manager: WebSocketManager = None):
        self.repository = NotificationRepository()
        self.websocket_manager = websocket_manager
        self._cleanup_task = None

    async def initialize(self):
        """Inicializa o serviço"""
        await self.repository.create_tables()
        
        # Inicia tarefa de limpeza automática
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Notification service initialized")

    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Cria uma nova notificação"""
        try:
            # Verifica preferências do usuário
            preferences = await self.repository.get_user_preferences(notification_data.user_id)
            
            if preferences and not preferences.websocket_enabled:
                logger.debug(f"WebSocket notifications disabled for user {notification_data.user_id}")
                return None
                
            if preferences and not preferences.types_enabled.get(notification_data.type.value, True):
                logger.debug(f"Notification type {notification_data.type} disabled for user {notification_data.user_id}")
                return None
            
            # Verifica horário silencioso
            if preferences and self._is_quiet_hours(preferences):
                logger.debug(f"Quiet hours active for user {notification_data.user_id}")
                # Ainda cria a notificação, mas não envia via WebSocket
                notification = await self.repository.create_notification(notification_data)
                return notification
            
            # Cria a notificação
            notification = await self.repository.create_notification(notification_data)
            
            # Envia via WebSocket se disponível
            if self.websocket_manager and preferences and preferences.websocket_enabled:
                await self._send_websocket_notification(notification)
            
            logger.info(f"Notification created: {notification.id} for user {notification.user_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create notification")

    async def create_batch_notifications(self, batch: NotificationBatch) -> List[Notification]:
        """Cria múltiplas notificações em lote"""
        notifications = []
        
        for notification_data in batch.notifications:
            try:
                notification = await self.create_notification(notification_data)
                if notification:
                    notifications.append(notification)
            except Exception as e:
                logger.error(f"Error creating notification in batch: {str(e)}")
                continue
        
        logger.info(f"Created {len(notifications)} notifications in batch")
        return notifications

    async def get_notification(self, notification_id: str, user_id: str = None) -> Optional[Notification]:
        """Busca uma notificação por ID"""
        notification = await self.repository.get_notification(notification_id)
        
        if not notification:
            return None
            
        # Verifica se o usuário tem permissão para ver a notificação
        if user_id and notification.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return notification

    async def get_user_notifications(self, user_id: str, filters: NotificationFilter = None) -> List[Notification]:
        """Busca notificações de um usuário"""
        if not filters:
            filters = NotificationFilter()
            
        filters.user_id = user_id
        
        return await self.repository.get_notifications(filters)

    async def mark_as_read(self, notification_id: str, user_id: str = None) -> Optional[Notification]:
        """Marca uma notificação como lida"""
        # Verifica se a notificação existe e pertence ao usuário
        notification = await self.get_notification(notification_id, user_id)
        if not notification:
            return None
            
        return await self.repository.mark_as_read(notification_id)

    async def mark_all_as_read(self, user_id: str) -> int:
        """Marca todas as notificações de um usuário como lidas"""
        count = await self.repository.mark_all_as_read(user_id)
        
        # Notifica via WebSocket sobre a atualização
        if self.websocket_manager and count > 0:
            await self._send_websocket_update(user_id, {
                "type": "notifications_marked_read",
                "count": count
            })
        
        return count

    async def delete_notification(self, notification_id: str, user_id: str = None) -> bool:
        """Remove uma notificação"""
        # Verifica se a notificação existe e pertence ao usuário
        notification = await self.get_notification(notification_id, user_id)
        if not notification:
            return False
            
        success = await self.repository.delete_notification(notification_id)
        
        if success and self.websocket_manager:
            await self._send_websocket_update(user_id, {
                "type": "notification_deleted",
                "notification_id": notification_id
            })
        
        return success

    async def clear_all_notifications(self, user_id: str) -> int:
        """Remove todas as notificações de um usuário"""
        count = await self.repository.delete_all_notifications(user_id)
        
        # Notifica via WebSocket sobre a limpeza
        if self.websocket_manager and count > 0:
            await self._send_websocket_update(user_id, {
                "type": "notifications_cleared",
                "count": count
            })
        
        return count

    async def get_notification_stats(self, user_id: str) -> NotificationStats:
        """Obtém estatísticas de notificações de um usuário"""
        return await self.repository.get_notification_stats(user_id)

    async def get_user_preferences(self, user_id: str) -> NotificationPreference:
        """Obtém as preferências de notificação de um usuário"""
        preferences = await self.repository.get_user_preferences(user_id)
        
        if not preferences:
            # Cria preferências padrão
            preferences = NotificationPreference(
                user_id=user_id,
                updated_at=datetime.utcnow()
            )
            await self.repository.update_user_preferences(user_id, preferences)
        
        return preferences

    async def update_user_preferences(self, user_id: str, preferences: NotificationPreference) -> NotificationPreference:
        """Atualiza as preferências de notificação de um usuário"""
        preferences.user_id = user_id
        return await self.repository.update_user_preferences(user_id, preferences)

    async def send_system_notification(self, user_ids: List[str], title: str, message: str, 
                                     notification_type: NotificationType = NotificationType.INFO,
                                     action: Dict[str, Any] = None) -> List[Notification]:
        """Envia uma notificação do sistema para múltiplos usuários"""
        notifications = []
        
        for user_id in user_ids:
            notification_data = NotificationCreate(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                action=action
            )
            
            try:
                notification = await self.create_notification(notification_data)
                if notification:
                    notifications.append(notification)
            except Exception as e:
                logger.error(f"Error sending system notification to user {user_id}: {str(e)}")
                continue
        
        return notifications

    async def send_execution_notification(self, user_id: str, execution_id: str, 
                                        status: str, message: str = None) -> Optional[Notification]:
        """Envia notificação sobre execução de equipe"""
        title_map = {
            "completed": "Execução concluída",
            "failed": "Execução falhou",
            "started": "Execução iniciada",
            "queued": "Execução na fila"
        }
        
        type_map = {
            "completed": NotificationType.SUCCESS,
            "failed": NotificationType.ERROR,
            "started": NotificationType.INFO,
            "queued": NotificationType.INFO
        }
        
        title = title_map.get(status, "Atualização de execução")
        notification_type = type_map.get(status, NotificationType.INFO)
        
        if not message:
            message = f"A execução {execution_id} foi {status}"
        
        notification_data = NotificationCreate(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            action={
                "type": "url",
                "payload": f"/executions/{execution_id}"
            },
            metadata={
                "execution_id": execution_id,
                "status": status
            }
        )
        
        return await self.create_notification(notification_data)

    async def _send_websocket_notification(self, notification: Notification):
        """Envia notificação via WebSocket"""
        if not self.websocket_manager:
            return
            
        try:
            message = {
                "type": "notification",
                "data": notification.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_to_user(
                notification.user_id,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")

    async def _send_websocket_update(self, user_id: str, data: Dict[str, Any]):
        """Envia atualização via WebSocket"""
        if not self.websocket_manager:
            return
            
        try:
            message = {
                **data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.send_to_user(
                user_id,
                json.dumps(message)
            )
            
        except Exception as e:
            logger.error(f"Error sending WebSocket update: {str(e)}")

    def _is_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Verifica se está no horário silencioso"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False
            
        try:
            from datetime import time
            import pytz
            
            # Obtém o horário atual no fuso horário do usuário
            tz = pytz.timezone(preferences.timezone)
            now = datetime.now(tz).time()
            
            start_time = time.fromisoformat(preferences.quiet_hours_start)
            end_time = time.fromisoformat(preferences.quiet_hours_end)
            
            if start_time <= end_time:
                # Mesmo dia
                return start_time <= now <= end_time
            else:
                # Atravessa meia-noite
                return now >= start_time or now <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {str(e)}")
            return False

    async def _cleanup_loop(self):
        """Loop de limpeza automática de notificações expiradas"""
        while True:
            try:
                await asyncio.sleep(3600)  # Executa a cada hora
                
                count = await self.repository.cleanup_expired_notifications()
                if count > 0:
                    logger.info(f"Cleaned up {count} expired notifications")
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                await asyncio.sleep(60)  # Espera 1 minuto antes de tentar novamente

    async def shutdown(self):
        """Finaliza o serviço"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Notification service shutdown")


# Instância global do serviço
notification_service = NotificationService()