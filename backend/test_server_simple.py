#!/usr/bin/env python3
"""
Teste simples para verificar se o servidor está funcionando
"""

# Carregar variáveis de ambiente primeiro
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.improved_token_validator import ImprovedTokenValidator


async def test_server_basic():
    """Teste básico do servidor"""
    print("🧪 Testando funcionalidades básicas...")
    
    # Testar geração de token
    validator = ImprovedTokenValidator()
    token = await validator.generate_token("test_user")
    
    if token:
        print(f"   ✅ Token gerado com sucesso: {token[:50]}...")
        
        # Testar validação
        result = await validator.validate_websocket_token(token)
        if result.valid:
            print("   ✅ Token validado com sucesso")
            
            # Gerar URL WebSocket
            websocket_url = f"ws://localhost:8000/ws?token={token}"
            print(f"   🔗 URL WebSocket: {websocket_url[:80]}...")
            
            print("\n🎉 Funcionalidades básicas funcionando!")
            print("\n📋 PRÓXIMOS PASSOS:")
            print("   1. Iniciar o servidor: python api.py")
            print("   2. Testar a conexão WebSocket com um cliente")
            print("   3. Verificar logs de conexão")
            
            return True
        else:
            print(f"   ❌ Falha na validação: {result.error_message}")
            return False
    else:
        print("   ❌ Falha na geração de token")
        return False


async def main():
    """Função principal"""
    try:
        success = await test_server_basic()
        return success
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)