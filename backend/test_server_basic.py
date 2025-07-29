import asyncio
import os
import sys
from pathlib import Path

# Configurar JWT_SECRET para teste
os.environ['JWT_SECRET'] = 'test_secret_key_for_validation_testing_purposes_only'

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_server_components():
    print("🧪 Testando componentes do servidor...")
    
    try:
        # Teste 1: Importar WebSocket endpoint
        print("Teste 1: Importando WebSocket endpoint...")
        from websocket_endpoint_final import WebSocketManager, setup_websocket_routes
        print("  ✅ WebSocket endpoint importado com sucesso")
        
        # Teste 2: Criar manager
        print("Teste 2: Criando WebSocket manager...")
        manager = WebSocketManager()
        print(f"  ✅ Manager criado - Max conexões: {manager.max_connections}")
        
        # Teste 3: Testar stats
        print("Teste 3: Testando stats...")
        stats = manager.get_stats()
        print(f"  ✅ Stats obtidas - Conexões ativas: {stats['active_connections']}")
        
        # Teste 4: Importar sistema de fallback
        print("Teste 4: Importando sistema de fallback...")
        from services.websocket_auth_fallback import WebSocketAuthFallback
        fallback = WebSocketAuthFallback()
        print("  ✅ Sistema de fallback importado")
        
        # Teste 5: Testar FastAPI setup
        print("Teste 5: Testando setup FastAPI...")
        from fastapi import FastAPI
        app = FastAPI()
        setup_websocket_routes(app)
        print("  ✅ Rotas WebSocket configuradas")
        
        print("\n🎉 Todos os componentes estão funcionando!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro nos componentes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_server_components())
    sys.exit(0 if success else 1)