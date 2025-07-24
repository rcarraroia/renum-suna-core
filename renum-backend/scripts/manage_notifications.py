#!/usr/bin/env python3
"""
Script para gerenciar notificações via linha de comando
"""
import asyncio
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.database import get_database_session
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService
from app.services.notification_cleanup_service import NotificationCleanupService
from app.services.websocket_manager import WebSocketManager
from app.models.notification_models import NotificationType

async def create_test_notification(args):
    """Cria uma notificação de teste"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        websocket_manager = WebSocketManager()
        notification_service = NotificationService(notification_repo, websocket_manager)
        
        notification = await notification_service.create_notification(
            user_id=args.user_id,
            title=args.title,
            message=args.message,
            notification_type=NotificationType(args.type),
            metadata=json.loads(args.metadata) if args.metadata else None
        )
        
        print(f"Notificação criada: {notification.id}")
        print(f"Título: {notification.title}")
        print(f"Mensagem: {notification.message}")
        print(f"Tipo: {notification.type}")

async def list_notifications(args):
    """Lista notificações de um usuário"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        
        notifications = await notification_repo.get_by_user(
            user_id=args.user_id,
            limit=args.limit,
            offset=args.offset
        )
        
        print(f"Encontradas {len(notifications)} notificações:")
        for notif in notifications:
            print(f"- {notif.id}: {notif.title} ({notif.status}) - {notif.created_at}")

async def cleanup_notifications(args):
    """Executa limpeza de notificações"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        cleanup_service = NotificationCleanupService(notification_repo)
        
        if args.stats_only:
            stats = await cleanup_service.get_cleanup_stats()
            print("Estatísticas de limpeza:")
            print(f"- Notificações lidas para limpeza: {stats['read_to_cleanup']}")
            print(f"- Notificações não lidas para limpeza: {stats['unread_to_cleanup']}")
            print(f"- Notificações expiradas para limpeza: {stats['expired_to_cleanup']}")
            print(f"- Total para limpeza: {stats['total_to_cleanup']}")
            print(f"- Total de notificações: {stats['total_notifications']}")
        else:
            stats = await cleanup_service.cleanup_old_notifications()
            print("Limpeza concluída:")
            print(f"- Notificações lidas removidas: {stats['read_deleted']}")
            print(f"- Notificações não lidas removidas: {stats['unread_deleted']}")
            print(f"- Notificações expiradas removidas: {stats['expired_deleted']}")
            print(f"- Total removido: {stats['total_deleted']}")
            print(f"- Erros: {stats['errors']}")

async def get_user_stats(args):
    """Obtém estatísticas de notificações de um usuário"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        
        total = await notification_repo.count_by_user(args.user_id)
        unread = await notification_repo.get_unread_count(args.user_id)
        read = total - unread
        
        print(f"Estatísticas do usuário {args.user_id}:")
        print(f"- Total de notificações: {total}")
        print(f"- Não lidas: {unread}")
        print(f"- Lidas: {read}")
        
        # Estatísticas por tipo
        by_type = await notification_repo.get_count_by_type(args.user_id)
        if by_type:
            print("- Por tipo:")
            for notification_type, count in by_type.items():
                print(f"  - {notification_type}: {count}")

async def mark_all_read(args):
    """Marca todas as notificações de um usuário como lidas"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        websocket_manager = WebSocketManager()
        notification_service = NotificationService(notification_repo, websocket_manager)
        
        count = await notification_service.mark_all_as_read(args.user_id)
        print(f"Marcadas {count} notificações como lidas para o usuário {args.user_id}")

async def delete_user_notifications(args):
    """Remove todas as notificações de um usuário"""
    async with get_database_session() as db:
        notification_repo = NotificationRepository(db)
        
        if not args.confirm:
            print("ATENÇÃO: Esta operação removerá TODAS as notificações do usuário!")
            print("Use --confirm para confirmar a operação.")
            return
        
        count = await notification_repo.delete_all_by_user(args.user_id)
        print(f"Removidas {count} notificações do usuário {args.user_id}")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Gerenciador de notificações")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando para criar notificação de teste
    create_parser = subparsers.add_parser("create", help="Criar notificação de teste")
    create_parser.add_argument("--user-id", required=True, help="ID do usuário")
    create_parser.add_argument("--title", required=True, help="Título da notificação")
    create_parser.add_argument("--message", required=True, help="Mensagem da notificação")
    create_parser.add_argument("--type", default="custom", help="Tipo da notificação")
    create_parser.add_argument("--metadata", help="Metadados em JSON")
    
    # Comando para listar notificações
    list_parser = subparsers.add_parser("list", help="Listar notificações")
    list_parser.add_argument("--user-id", required=True, help="ID do usuário")
    list_parser.add_argument("--limit", type=int, default=10, help="Limite de notificações")
    list_parser.add_argument("--offset", type=int, default=0, help="Offset para paginação")
    
    # Comando para limpeza
    cleanup_parser = subparsers.add_parser("cleanup", help="Limpar notificações antigas")
    cleanup_parser.add_argument("--stats-only", action="store_true", help="Apenas mostrar estatísticas")
    
    # Comando para estatísticas
    stats_parser = subparsers.add_parser("stats", help="Estatísticas de usuário")
    stats_parser.add_argument("--user-id", required=True, help="ID do usuário")
    
    # Comando para marcar todas como lidas
    read_parser = subparsers.add_parser("mark-read", help="Marcar todas como lidas")
    read_parser.add_argument("--user-id", required=True, help="ID do usuário")
    
    # Comando para deletar notificações
    delete_parser = subparsers.add_parser("delete", help="Deletar notificações de usuário")
    delete_parser.add_argument("--user-id", required=True, help="ID do usuário")
    delete_parser.add_argument("--confirm", action="store_true", help="Confirmar operação")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Executar comando
    if args.command == "create":
        asyncio.run(create_test_notification(args))
    elif args.command == "list":
        asyncio.run(list_notifications(args))
    elif args.command == "cleanup":
        asyncio.run(cleanup_notifications(args))
    elif args.command == "stats":
        asyncio.run(get_user_stats(args))
    elif args.command == "mark-read":
        asyncio.run(mark_all_read(args))
    elif args.command == "delete":
        asyncio.run(delete_user_notifications(args))

if __name__ == "__main__":
    main()