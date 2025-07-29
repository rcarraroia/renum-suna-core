#!/usr/bin/env python3
"""
Teste simples para verificar se o diagnóstico está funcionando
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.token_diagnostic_service import TokenDiagnosticService
from services.resource_diagnostic_service import ResourceDiagnosticService
from services.connection_diagnostic_service import ConnectionDiagnosticService


async def test_services():
    """Testa cada serviço individualmente"""
    print("🧪 Testando serviços de diagnóstico...")
    
    try:
        # Testar TokenDiagnosticService
        print("\n🔐 Testando TokenDiagnosticService...")
        token_service = TokenDiagnosticService()
        token_result = await token_service.validate_token_generation()
        print(f"   ✓ Token generation: {token_result.success}")
        
        # Testar ResourceDiagnosticService
        print("\n💾 Testando ResourceDiagnosticService...")
        resource_service = ResourceDiagnosticService()
        resource_result = await resource_service.check_connection_limits()
        print(f"   ✓ Connection limits: {'OK' if resource_result.available else 'LIMIT_REACHED'}")
        
        # Testar ConnectionDiagnosticService
        print("\n🔌 Testando ConnectionDiagnosticService...")
        connection_service = ConnectionDiagnosticService()
        connection_result = await connection_service.validate_websocket_config()
        print(f"   ✓ WebSocket config: {connection_result.valid}")
        
        print("\n✅ Todos os serviços testados com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Função principal"""
    success = await test_services()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())