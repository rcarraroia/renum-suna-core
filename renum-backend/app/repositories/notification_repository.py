"""
Repositório para gerenciamento de notificações
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import text, and_, or_, desc, asc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.notification_models import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationFilter,
    NotificationStats,
    NotificationPreference,
    NotificationType
)


class NotificationRepository:
    """Repositório para operações de notificações"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Cria uma nova notificação"""
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # SQL para inserir notificação
        query = text("""
            INSERT INTO notifications (
                id, user_id, type, title, message, read, action, 
                created_at, expires_at, metadata
            ) VALUES (
                :id, :user_id, :type, :title, :message, :read, :action,
                :created_at, :expires_at, :metadata
            )
        """)
        
        await self.db.execute(query, {
            "id": notification_id,
            "user_id": notification_data.user_id,
            "type": notification_data.type.value,
            "title": notification_data.title,
            "message": notification_data.message,
            "read": False,
            "action": notification_data.action.dict() if notification_data.action else None,
            "created_at": created_at,
            "expires_at": notification_data.expires_at,
            "metadata": notification_data.metadata
        })
        
        await self.db.commit()
        
        return await self.get_notification(notification_id)

    async def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Busca uma notificação por ID"""
        query = text("""
            SELECT * FROM notifications WHERE id = :id
        """)
        
        result = await self.db.execute(query, {"id": notification_id})
        row = result.fetchone()
        
        if not row:
            return None
            
        return Notification(**dict(row))

    async def get_notifications(self, filters: NotificationFilter) -> List[Notification]:
        """Busca notificações com filtros"""
        conditions = []
        params = {}
        
        if filters.user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = filters.user_id
            
        if filters.type:
            conditions.append("type = :type")
            params["type"] = filters.type.value
            
        if filters.read is not None:
            conditions.append("read = :read")
            params["read"] = filters.read
            
        if filters.created_after:
            conditions.append("created_at >= :created_after")
            params["created_after"] = filters.created_after
            
        if filters.created_before:
            conditions.append("created_at <= :created_before")
            params["created_before"] = filters.created_before
        
        # Remove notificações expiradas
        conditions.append("(expires_at IS NULL OR expires_at > :now)")
        params["now"] = datetime.utcnow()
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        order_direction = "DESC" if filters.order_desc else "ASC"
        
        query = text(f"""
            SELECT * FROM notifications 
            {where_clause}
            ORDER BY {filters.order_by} {order_direction}
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": filters.limit,
            "offset": filters.offset
        })
        
        result = await self.db.execute(query, params)
        rows = result.fetchall()
        
        return [Notification(**dict(row)) for row in rows]

    async def update_notification(self, notification_id: str, update_data: NotificationUpdate) -> Optional[Notification]:
        """Atualiza uma notificação"""
        updates = []
        params = {"id": notification_id}
        
        if update_data.read is not None:
            updates.append("read = :read")
            params["read"] = update_data.read
            
        if update_data.read_at is not None:
            updates.append("read_at = :read_at")
            params["read_at"] = update_data.read_at
        elif update_data.read:
            updates.append("read_at = :read_at")
            params["read_at"] = datetime.utcnow()
            
        if not updates:
            return await self.get_notification(notification_id)
            
        query = text(f"""
            UPDATE notifications 
            SET {', '.join(updates)}
            WHERE id = :id
        """)
        
        await self.db.execute(query, params)
        await self.db.commit()
        
        return await self.get_notification(notification_id)

    async def delete_notification(self, notification_id: str) -> bool:
        """Remove uma notificação"""
        query = text("DELETE FROM notifications WHERE id = :id")
        result = await self.db.execute(query, {"id": notification_id})
        await self.db.commit()
        
        return result.rowcount > 0

    async def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Marca uma notificação como lida"""
        return await self.update_notification(
            notification_id,
            NotificationUpdate(read=True, read_at=datetime.utcnow())
        )

    async def mark_all_as_read(self, user_id: str) -> int:
        """Marca todas as notificações de um usuário como lidas"""
        query = text("""
            UPDATE notifications 
            SET read = true, read_at = :read_at
            WHERE user_id = :user_id AND read = false
        """)
        
        result = await self.db.execute(query, {
            "user_id": user_id,
            "read_at": datetime.utcnow()
        })
        await self.db.commit()
        
        return result.rowcount

    async def delete_all_notifications(self, user_id: str) -> int:
        """Remove todas as notificações de um usuário"""
        query = text("DELETE FROM notifications WHERE user_id = :user_id")
        result = await self.db.execute(query, {"user_id": user_id})
        await self.db.commit()
        
        return result.rowcount

    async def get_notification_stats(self, user_id: str) -> NotificationStats:
        """Obtém estatísticas de notificações de um usuário"""
        # Total de notificações
        total_query = text("""
            SELECT COUNT(*) as total FROM notifications 
            WHERE user_id = :user_id AND (expires_at IS NULL OR expires_at > :now)
        """)
        
        # Não lidas
        unread_query = text("""
            SELECT COUNT(*) as unread FROM notifications 
            WHERE user_id = :user_id AND read = false AND (expires_at IS NULL OR expires_at > :now)
        """)
        
        # Por tipo
        by_type_query = text("""
            SELECT type, COUNT(*) as count FROM notifications 
            WHERE user_id = :user_id AND (expires_at IS NULL OR expires_at > :now)
            GROUP BY type
        """)
        
        # Recentes (últimas 24h)
        recent_query = text("""
            SELECT COUNT(*) as recent FROM notifications 
            WHERE user_id = :user_id AND created_at >= :since AND (expires_at IS NULL OR expires_at > :now)
        """)
        
        now = datetime.utcnow()
        since = now - timedelta(hours=24)
        params = {"user_id": user_id, "now": now, "since": since}
        
        total_result = await self.db.execute(total_query, params)
        unread_result = await self.db.execute(unread_query, params)
        by_type_result = await self.db.execute(by_type_query, params)
        recent_result = await self.db.execute(recent_query, params)
        
        total = total_result.scalar() or 0
        unread = unread_result.scalar() or 0
        recent = recent_result.scalar() or 0
        
        by_type = {}
        for row in by_type_result.fetchall():
            by_type[row.type] = row.count
            
        return NotificationStats(
            total=total,
            unread=unread,
            by_type=by_type,
            recent=recent
        )

    async def cleanup_expired_notifications(self) -> int:
        """Remove notificações expiradas"""
        query = text("""
            DELETE FROM notifications 
            WHERE expires_at IS NOT NULL AND expires_at <= :now
        """)
        
        result = await self.db.execute(query, {"now": datetime.utcnow()})
        await self.db.commit()
        
        return result.rowcount

    async def get_user_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Obtém as preferências de notificação de um usuário"""
        query = text("""
            SELECT * FROM notification_preferences WHERE user_id = :user_id
        """)
        
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        
        if not row:
            return None
            
        return NotificationPreference(**dict(row))

    async def update_user_preferences(self, user_id: str, preferences: NotificationPreference) -> NotificationPreference:
        """Atualiza as preferências de notificação de um usuário"""
        # Verifica se já existem preferências
        existing = await self.get_user_preferences(user_id)
        
        if existing:
            # Atualiza
            query = text("""
                UPDATE notification_preferences 
                SET email_enabled = :email_enabled,
                    websocket_enabled = :websocket_enabled,
                    types_enabled = :types_enabled,
                    quiet_hours_start = :quiet_hours_start,
                    quiet_hours_end = :quiet_hours_end,
                    timezone = :timezone,
                    updated_at = :updated_at
                WHERE user_id = :user_id
            """)
        else:
            # Cria
            query = text("""
                INSERT INTO notification_preferences (
                    user_id, email_enabled, websocket_enabled, types_enabled,
                    quiet_hours_start, quiet_hours_end, timezone, updated_at
                ) VALUES (
                    :user_id, :email_enabled, :websocket_enabled, :types_enabled,
                    :quiet_hours_start, :quiet_hours_end, :timezone, :updated_at
                )
            """)
        
        await self.db.execute(query, {
            "user_id": user_id,
            "email_enabled": preferences.email_enabled,
            "websocket_enabled": preferences.websocket_enabled,
            "types_enabled": preferences.types_enabled,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "timezone": preferences.timezone,
            "updated_at": datetime.utcnow()
        })
        
        await self.db.commit()
        
        return await self.get_user_preferences(user_id)

    async def create_tables(self):
        """Cria as tabelas necessárias"""
        # Tabela de notificações
        notifications_table = text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(200) NOT NULL,
                message TEXT NOT NULL,
                read BOOLEAN DEFAULT FALSE,
                action JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP NULL,
                expires_at TIMESTAMP NULL,
                metadata JSON,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                INDEX idx_read (read),
                INDEX idx_expires_at (expires_at)
            )
        """)
        
        # Tabela de preferências
        preferences_table = text("""
            CREATE TABLE IF NOT EXISTS notification_preferences (
                user_id VARCHAR(255) PRIMARY KEY,
                email_enabled BOOLEAN DEFAULT TRUE,
                websocket_enabled BOOLEAN DEFAULT TRUE,
                types_enabled JSON,
                quiet_hours_start VARCHAR(5),
                quiet_hours_end VARCHAR(5),
                timezone VARCHAR(50) DEFAULT 'UTC',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.db.execute(notifications_table)
        await self.db.execute(preferences_table)
        await self.db.commit()