#!/usr/bin/env python3
"""
Teste para o endpoint WebSocket com autenticação JWT
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

# Configurar variáveis de ambiente para teste
os.environ['JWT_SECRET'] = 'renum-websocket-jwt-secret-key-2025-very-secure-random-string-for-authentication'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['JWT_ISSUER'] = 'suna-app'
os.environ['JWT_AUDIENCE'] = 'suna-users'

from services.improved_token_validator import ImprovedTokenValidator
from websocket_endpoint import websocket_manager


async def test_websocket_authentication():
    """Testa autenticação WebSocket"""
    print("🧪 Testando autenticação WebSocket...")
    
    # Criar validador de token
    validator = ImprovedTokenValidator()
    
    # Gerar token válido
    token = await validator.generate_token("test_user_websocket")
    assert token is not None
    print(f"   ✅ Token gerado: {token[:50]}...")
    
    # Testar validação WebSocket
    result = await validator.validate_websocket_token(token)
    assert result.valid
    assert result.user_id == "test_user_websocket"
    print("   ✅ Token válido para WebSocket")
    
    # Testar token vazio
    empty_result = await validator.validate_websocket_token("")
    assert not empty_result.valid
    print("   ✅ Token vazio rejeitado")
    
    # Testar token inválido
    invalid_result = await validator.validate_websocket_token("invalid.token.here")
    assert not invalid_result.valid
    print("   ✅ Token inválido rejeitado")
    
    return token


async def test_websocket_manager():
    """Testa o gerenciador WebSocket"""
    print("\n🧪 Testando WebSocketManager...")
    
    # Criar mock WebSocket
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            self.closed = False
            self.close_code = None
            self.close_reason = None
            
        async def accept(self):
            pass
            
        async def send_json(self, data):
            self.messages.append(data)
            
        async def close(self, code=None, reason=None):
            self.closed = True
            self.close_code = code
            self.close_reason = reason
            
        async def receive_json(self):
            # Simular mensagem ping
            return {'type': 'ping'}
    
    # Gerar token válido
    validator = ImprovedTokenValidator()
    token = await validator.generate_token("test_user_manager")
    
    # Testar conexão com token válido
    mock_ws = MockWebSocket()
    connection_id = await websocket_manager.connect(mock_ws, token)
    
    assert connection_id is not None
    assert not mock_ws.closed
    assert len(mock_ws.messages) == 1
    assert mock_ws.messages[0]['type'] == 'connection_established'
    print("   ✅ Conexão estabelecida com token válido")
    
    # Testar estatísticas
    stats = websocket_manager.get_stats()
    assert stats['total_connections'] >= 1
    assert stats['unique_users'] >= 1
    print(f"   ✅ Estatísticas: {stats}")
    
    # Testar envio de mensagem pessoal
    test_message = {'type': 'test', 'data': 'Hello WebSocket!'}
    sent_count = await websocket_manager.send_personal_message("test_user_manager", test_message)
    assert sent_count >= 1
    print("   ✅ Mensagem pessoal enviada")
    
    # Testar broadcast
    broadcast_message = {'type': 'broadcast', 'data': 'Hello everyone!'}
    broadcast_count = await websocket_manager.broadcast(broadcast_message)
    assert broadcast_count >= 1
    print("   ✅ Broadcast enviado")
    
    # Testar desconexão
    await websocket_manager.disconnect(connection_id)
    stats_after = websocket_manager.get_stats()
    assert stats_after['total_connections'] < stats['total_connections']
    print("   ✅ Desconexão funcionando")
    
    # Testar conexão com token vazio
    mock_ws_empty = MockWebSocket()
    connection_id_empty = await websocket_manager.connect(mock_ws_empty, "")
    
    assert connection_id_empty is None
    assert mock_ws_empty.closed
    assert mock_ws_empty.close_code == 4001
    print("   ✅ Token vazio rejeitado corretamente")


async def test_websocket_url_format():
    """Testa formato da URL WebSocket"""
    print("\n🧪 Testando formato da URL WebSocket...")
    
    # Gerar token
    validator = ImprovedTokenValidator()
    token = await validator.generate_token("test_user_url")
    
    # Simular URL WebSocket
    websocket_url = f"ws://localhost:8000/ws?token={token}"
    print(f"   📡 URL WebSocket: {websocket_url[:80]}...")
    
    # Extrair token da URL
    import urllib.parse
    parsed_url = urllib.parse.urlparse(websocket_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    extracted_token = query_params.get('token', [''])[0]
    
    assert extracted_token == token
    print("   ✅ Token extraído da URL corretamente")
    
    # Validar token extraído
    result = await validator.validate_websocket_token(extracted_token)
    assert result.valid
    assert result.user_id == "test_user_url"
    print("   ✅ Token da URL validado com sucesso")


async def main():
    """Função principal de teste"""
    try:
        print("🚀 INICIANDO TESTES DO ENDPOINT WEBSOCKET")
        print("=" * 50)
        
        # Executar testes
        token = await test_websocket_authentication()
        await test_websocket_manager()
        await test_websocket_url_format()
        
        print("\n🎉 Todos os testes do WebSocket passaram!")
        print("\n📋 RESUMO:")
        print("   ✅ Autenticação JWT funcionando")
        print("   ✅ Gerenciador de conexões funcionando")
        print("   ✅ Validação de tokens vazios/inválidos")
        print("   ✅ Envio de mensagens pessoais")
        print("   ✅ Sistema de broadcast")
        print("   ✅ Formato de URL WebSocket")
        
        print(f"\n🔗 Para testar manualmente:")
        print(f"   URL: ws://localhost:8000/ws?token={token}")
        print(f"   Ou use um cliente WebSocket com o token acima")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)