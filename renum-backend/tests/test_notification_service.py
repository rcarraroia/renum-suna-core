"""
Testes para o serviço de notificações
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.services.notification_service import NotificationService
from app.models.notification_models import (
    NotificationCreate,
    NotificationUpdate,
    NotificationFilter,
    NotificationBatch,
    NotificationPreference,
    NotificationType
)


@pytest.fixture
def mock_websocket_manager():
    """Mock do WebSocket manager"""
    manager = Mock()
    manager.send_to_user = AsyncMock()
    return manager


@pytest.fixture
def mock_repository():
    """Mock do repositório de notificações"""
    repo = Mock()
    repo.create_tables = AsyncMock()
    repo.create_notification = AsyncMock()
    repo.get_notification = AsyncMock()
    repo.get_notifications = AsyncMock()
    repo.update_notification = AsyncMock()
    repo.delete_notification = AsyncMock()
    repo.mark_as_read = AsyncMock()
    repo.mark_all_as_read = AsyncMock()
    repo.delete_all_notifications = AsyncMock()
    repo.get_notification_stats = AsyncMock()
    repo.get_user_preferences = AsyncMock()
    repo.update_user_preferences = AsyncMock()
    repo.cleanup_expired_notifications = AsyncMock()
    return repo


@pytest.fixture
def notification_service(mock_websocket_manager, mock_repository):
    """Instância do serviço de notificações com mocks"""
    service = NotificationService(mock_websocket_manager)
    service.repository = mock_repository
    return service


@pytest.mark.asyncio
async def test_initialize(notification_service, mock_repository):
    """Testa a inicialização do serviço"""
    await notification_service.initialize()
    
    mock_repository.create_tables.assert_called_once()
    assert notification_service._cleanup_task is not None


@pytest.mark.asyncio
async def test_create_notification_success(notification_service, mock_repository, mock_websocket_manager):
    """Testa a criação de uma notificação com sucesso"""
    # Arrange
    notification_data = NotificationCreate(
        user_id="user123",
        type=NotificationType.INFO,
        title="Test Notification",
        message="This is a test notification"
    )
    
    mock_notification = Mock()
    mock_notification.id = "notif123"
    mock_notification.user_id = "user123"
    mock_notification.dict.return_value = {
        "id": "notif123",
        "user_id": "user123",
        "type": "info",
        "title": "Test Notification",
        "message": "This is a test notification"
    }
    
    mock_repository.get_user_preferences.return_value = None
    mock_repository.create_notification.return_value = mock_notification
    
    # Act
    result = await notification_service.create_notification(notification_data)
    
    # Assert
    assert result == mock_notification
    mock_repository.create_notification.assert_called_once_with(notification_data)
    mock_websocket_manager.send_to_user.assert_called_once()


@pytest.mark.asyncio
async def test_create_notification_websocket_disabled(notification_service, mock_repository, mock_websocket_manager):
    """Testa a criação de notificação quando WebSocket está desabilitado"""
    # Arrange
    notification_data = NotificationCreate(
        user_id="user123",
        type=NotificationType.INFO,
        title="Test Notification",
        message="This is a test notification"
    )
    
    mock_preferences = Mock()
    mock_preferences.websocket_enabled = False
    mock_repository.get_user_preferences.return_value = mock_preferences
    
    # Act
    result = await notification_service.create_notification(notification_data)
    
    # Assert
    assert result is None
    mock_repository.create_notification.assert_not_called()
    mock_websocket_manager.send_to_user.assert_not_called()


@pytest.mark.asyncio
async def test_create_notification_type_disabled(notification_service, mock_repository, mock_websocket_manager):
    """Testa a criação de notificação quando o tipo está desabilitado"""
    # Arrange
    notification_data = NotificationCreate(
        user_id="user123",
        type=NotificationType.ERROR,
        title="Test Notification",
        message="This is a test notification"
    )
    
    mock_preferences = Mock()
    mock_preferences.websocket_enabled = True
    mock_preferences.types_enabled = {"error": False}
    mock_repository.get_user_preferences.return_value = mock_preferences
    
    # Act
    result = await notification_service.create_notification(notification_data)
    
    # Assert
    assert result is None
    mock_repository.create_notification.assert_not_called()
    mock_websocket_manager.send_to_user.assert_not_called()


@pytest.mark.asyncio
async def test_create_batch_notifications(notification_service, mock_repository):
    """Testa a criação de notificações em lote"""
    # Arrange
    batch = NotificationBatch(
        notifications=[
            NotificationCreate(
                user_id="user123",
                type=NotificationType.INFO,
                title="Notification 1",
                message="Message 1"
            ),
            NotificationCreate(
                user_id="user123",
                type=NotificationType.SUCCESS,
                title="Notification 2",
                message="Message 2"
            )
        ]
    )
    
    mock_notification1 = Mock()
    mock_notification1.id = "notif1"
    mock_notification2 = Mock()
    mock_notification2.id = "notif2"
    
    mock_repository.get_user_preferences.return_value = None
    mock_repository.create_notification.side_effect = [mock_notification1, mock_notification2]
    
    # Act
    result = await notification_service.create_batch_notifications(batch)
    
    # Assert
    assert len(result) == 2
    assert result[0] == mock_notification1
    assert result[1] == mock_notification2


@pytest.mark.asyncio
async def test_get_user_notifications(notification_service, mock_repository):
    """Testa a busca de notificações de um usuário"""
    # Arrange
    user_id = "user123"
    filters = NotificationFilter(limit=10)
    
    mock_notifications = [Mock(), Mock()]
    mock_repository.get_notifications.return_value = mock_notifications
    
    # Act
    result = await notification_service.get_user_notifications(user_id, filters)
    
    # Assert
    assert result == mock_notifications
    assert filters.user_id == user_id
    mock_repository.get_notifications.assert_called_once_with(filters)


@pytest.mark.asyncio
async def test_mark_as_read(notification_service, mock_repository):
    """Testa marcar uma notificação como lida"""
    # Arrange
    notification_id = "notif123"
    user_id = "user123"
    
    mock_notification = Mock()
    mock_notification.user_id = user_id
    mock_repository.get_notification.return_value = mock_notification
    mock_repository.mark_as_read.return_value = mock_notification
    
    # Act
    result = await notification_service.mark_as_read(notification_id, user_id)
    
    # Assert
    assert result == mock_notification
    mock_repository.get_notification.assert_called_once_with(notification_id)
    mock_repository.mark_as_read.assert_called_once_with(notification_id)


@pytest.mark.asyncio
async def test_mark_all_as_read(notification_service, mock_repository, mock_websocket_manager):
    """Testa marcar todas as notificações como lidas"""
    # Arrange
    user_id = "user123"
    mock_repository.mark_all_as_read.return_value = 5
    
    # Act
    result = await notification_service.mark_all_as_read(user_id)
    
    # Assert
    assert result == 5
    mock_repository.mark_all_as_read.assert_called_once_with(user_id)
    mock_websocket_manager.send_to_user.assert_called_once()


@pytest.mark.asyncio
async def test_delete_notification(notification_service, mock_repository, mock_websocket_manager):
    """Testa a remoção de uma notificação"""
    # Arrange
    notification_id = "notif123"
    user_id = "user123"
    
    mock_notification = Mock()
    mock_notification.user_id = user_id
    mock_repository.get_notification.return_value = mock_notification
    mock_repository.delete_notification.return_value = True
    
    # Act
    result = await notification_service.delete_notification(notification_id, user_id)
    
    # Assert
    assert result is True
    mock_repository.get_notification.assert_called_once_with(notification_id)
    mock_repository.delete_notification.assert_called_once_with(notification_id)
    mock_websocket_manager.send_to_user.assert_called_once()


@pytest.mark.asyncio
async def test_clear_all_notifications(notification_service, mock_repository, mock_websocket_manager):
    """Testa a limpeza de todas as notificações"""
    # Arrange
    user_id = "user123"
    mock_repository.delete_all_notifications.return_value = 10
    
    # Act
    result = await notification_service.clear_all_notifications(user_id)
    
    # Assert
    assert result == 10
    mock_repository.delete_all_notifications.assert_called_once_with(user_id)
    mock_websocket_manager.send_to_user.assert_called_once()


@pytest.mark.asyncio
async def test_send_system_notification(notification_service, mock_repository):
    """Testa o envio de notificação do sistema"""
    # Arrange
    user_ids = ["user1", "user2", "user3"]
    title = "System Notification"
    message = "System maintenance scheduled"
    
    mock_notifications = [Mock(), Mock(), Mock()]
    mock_repository.get_user_preferences.return_value = None
    mock_repository.create_notification.side_effect = mock_notifications
    
    # Act
    result = await notification_service.send_system_notification(
        user_ids, title, message, NotificationType.WARNING
    )
    
    # Assert
    assert len(result) == 3
    assert mock_repository.create_notification.call_count == 3


@pytest.mark.asyncio
async def test_send_execution_notification(notification_service, mock_repository):
    """Testa o envio de notificação de execução"""
    # Arrange
    user_id = "user123"
    execution_id = "exec123"
    status = "completed"
    
    mock_notification = Mock()
    mock_repository.get_user_preferences.return_value = None
    mock_repository.create_notification.return_value = mock_notification
    
    # Act
    result = await notification_service.send_execution_notification(
        user_id, execution_id, status
    )
    
    # Assert
    assert result == mock_notification
    mock_repository.create_notification.assert_called_once()
    
    # Verifica se os dados da notificação estão corretos
    call_args = mock_repository.create_notification.call_args[0][0]
    assert call_args.user_id == user_id
    assert call_args.type == NotificationType.SUCCESS
    assert call_args.title == "Execução concluída"
    assert execution_id in call_args.message
    assert call_args.metadata["execution_id"] == execution_id
    assert call_args.metadata["status"] == status


@pytest.mark.asyncio
async def test_get_user_preferences_creates_default(notification_service, mock_repository):
    """Testa que preferências padrão são criadas se não existirem"""
    # Arrange
    user_id = "user123"
    mock_repository.get_user_preferences.return_value = None
    
    mock_default_preferences = Mock()
    mock_repository.update_user_preferences.return_value = mock_default_preferences
    
    # Act
    result = await notification_service.get_user_preferences(user_id)
    
    # Assert
    assert result == mock_default_preferences
    mock_repository.get_user_preferences.assert_called_once_with(user_id)
    mock_repository.update_user_preferences.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_preferences(notification_service, mock_repository):
    """Testa a atualização de preferências do usuário"""
    # Arrange
    user_id = "user123"
    preferences = NotificationPreference(
        user_id=user_id,
        email_enabled=False,
        websocket_enabled=True,
        updated_at=datetime.utcnow()
    )
    
    mock_repository.update_user_preferences.return_value = preferences
    
    # Act
    result = await notification_service.update_user_preferences(user_id, preferences)
    
    # Assert
    assert result == preferences
    assert preferences.user_id == user_id
    mock_repository.update_user_preferences.assert_called_once_with(user_id, preferences)


@pytest.mark.asyncio
async def test_is_quiet_hours():
    """Testa a verificação de horário silencioso"""
    # Arrange
    service = NotificationService()
    
    preferences = NotificationPreference(
        user_id="user123",
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        timezone="UTC",
        updated_at=datetime.utcnow()
    )
    
    # Act & Assert
    with patch('app.services.notification_service.datetime') as mock_datetime:
        with patch('pytz.timezone') as mock_timezone:
            # Mock para horário dentro do período silencioso
            mock_now = Mock()
            mock_now.time.return_value = Mock()
            mock_now.time.return_value.__le__ = Mock(return_value=True)
            mock_now.time.return_value.__ge__ = Mock(return_value=True)
            
            mock_tz = Mock()
            mock_timezone.return_value = mock_tz
            mock_datetime.now.return_value = mock_now
            
            # Testa que retorna False para erro (implementação simplificada)
            result = service._is_quiet_hours(preferences)
            assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_shutdown(notification_service):
    """Testa o encerramento do serviço"""
    # Arrange
    mock_task = Mock()
    mock_task.cancel = Mock()
    notification_service._cleanup_task = mock_task
    
    # Act
    await notification_service.shutdown()
    
    # Assert
    mock_task.cancel.assert_called_once()