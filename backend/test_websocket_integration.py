#!/usr/bin/env python3
"""
Teste de integração para verificar se o endpoint WebSocket está funcionando
com o servidor FastAPI
"""

# Carregar variáveis de ambiente primeiro
from dotenv import load_dotenv
load_dotenv()

import asyncio
import json
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.improved_token_validator import ImprovedTokenValidator


async def test_websocket_integration():
    """Testa integração WebSocket com FastAPI"""
    print("🧪 Testando integração WebSocket com FastAPI...")
    
    # Gerar token válido
    validator = ImprovedTokenValidator()
    token = await validator.generate_token("integration_test_user")
    
    if not token:
        print("   ❌ Falha ao gerar token")
        return False
    
    print(f"   ✅ Token gerado: {token[:50]}...")
    
    # Verificar se o endpoint está configurado corretamente
    try:
        from websocket_endpoint import websocket_router, websocket_manager
        print("   ✅ Endpoint WebSocket importado com sucesso")
        
        # Verificar se o router tem as rotas corretas
        routes = [route.path for route in websocket_router.routes]
        print(f"   📡 Rotas WebSocket disponíveis: {routes}")
        
        if "/ws" in routes:
            print("   ✅ Rota /ws encontrada")
        else:
            print("   ❌ Rota /ws não encontrada")
            return False
        
        # Verificar estatísticas iniciais
        stats = websocket_manager.get_stats()
        print(f"   📊 Estatísticas iniciais: {stats}")
        
        # Testar URL completa
        websocket_url = f"ws://localhost:8000/ws?token={token}"
        print(f"   🔗 URL WebSocket completa: {websocket_url[:80]}...")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro ao importar endpoint WebSocket: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        return False


async def test_api_integration():
    """Testa se o endpoint foi integrado ao FastAPI"""
    print("\n🧪 Testando integração com FastAPI...")
    
    try:
        # Importar o app FastAPI
        from api import app
        print("   ✅ App FastAPI importado com sucesso")
        
        # Verificar se as rotas WebSocket estão registradas
        websocket_routes = []
        for route in app.routes:
            if hasattr(route, 'routes'):  # APIRouter
                for subroute in route.routes:
                    if hasattr(subroute, 'path') and 'ws' in subroute.path:
                        websocket_routes.append(subroute.path)
        
        print(f"   📡 Rotas WebSocket encontradas: {websocket_routes}")
        
        if websocket_routes:
            print("   ✅ Rotas WebSocket integradas ao FastAPI")
            return True
        else:
            print("   ⚠️  Nenhuma rota WebSocket encontrada no FastAPI")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar integração FastAPI: {e}")
        return False


async def test_token_validation_flow():
    """Testa o fluxo completo de validação de token"""
    print("\n🧪 Testando fluxo completo de validação...")
    
    validator = ImprovedTokenValidator()
    
    # Teste 1: Token válido
    valid_token = await validator.generate_token("flow_test_user")
    validation_result = await validator.validate_websocket_token(valid_token)
    
    if validation_result.valid:
        print("   ✅ Token válido aceito")
    else:
        print(f"   ❌ Token válido rejeitado: {validation_result.error_message}")
        return False
    
    # Teste 2: Token vazio
    empty_result = await validator.validate_websocket_token("")
    if not empty_result.valid:
        print("   ✅ Token vazio rejeitado corretamente")
    else:
        print("   ❌ Token vazio foi aceito incorretamente")
        return False
    
    # Teste 3: Token malformado
    malformed_result = await validator.validate_websocket_token("invalid.token")
    if not malformed_result.valid:
        print("   ✅ Token malformado rejeitado corretamente")
    else:
        print("   ❌ Token malformado foi aceito incorretamente")
        return False
    
    return True


async def generate_test_urls():
    """Gera URLs de teste para diferentes cenários"""
    print("\n🔗 Gerando URLs de teste...")
    
    validator = ImprovedTokenValidator()
    
    # URL com token válido
    valid_token = await validator.generate_token("manual_test_user")
    valid_url = f"ws://localhost:8000/ws?token={valid_token}"
    
    print(f"   ✅ URL com token válido:")
    print(f"      {valid_url}")
    
    # URL sem token
    empty_url = "ws://localhost:8000/ws"
    print(f"   ❌ URL sem token (deve falhar):")
    print(f"      {empty_url}")
    
    # URL com token inválido
    invalid_url = "ws://localhost:8000/ws?token=invalid.token.here"
    print(f"   ❌ URL com token inválido (deve falhar):")
    print(f"      {invalid_url}")
    
    return valid_url


async def main():
    """Função principal de teste"""
    try:
        print("🚀 TESTE DE INTEGRAÇÃO WEBSOCKET")
        print("=" * 50)
        
        # Executar testes
        test1 = await test_websocket_integration()
        test2 = await test_api_integration()
        test3 = await test_token_validation_flow()
        
        # Gerar URLs de teste
        test_url = await generate_test_urls()
        
        # Resumo
        print("\n📋 RESUMO DOS TESTES:")
        print(f"   {'✅' if test1 else '❌'} Integração WebSocket")
        print(f"   {'✅' if test2 else '❌'} Integração FastAPI")
        print(f"   {'✅' if test3 else '❌'} Fluxo de validação")
        
        all_passed = test1 and test2 and test3
        
        if all_passed:
            print("\n🎉 Todos os testes de integração passaram!")
            print("\n🚀 PRÓXIMOS PASSOS:")
            print("   1. Iniciar o servidor FastAPI: python api.py")
            print("   2. Testar a URL WebSocket em um cliente")
            print("   3. Verificar logs de conexão")
            print(f"\n🔗 URL para teste manual:")
            print(f"   {test_url}")
        else:
            print("\n❌ Alguns testes falharam")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)