#!/usr/bin/env python3
"""
Teste para ImprovedTokenValidator
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.improved_token_validator import ImprovedTokenValidator, ValidationFailureReason


async def test_improved_token_validator():
    """Testa o ImprovedTokenValidator"""
    print("🧪 Testando ImprovedTokenValidator...")
    
    # Configurar JWT_SECRET para teste
    os.environ['JWT_SECRET'] = 'test_secret_key_with_at_least_32_characters_for_security'
    os.environ['JWT_ISSUER'] = 'suna-test'
    os.environ['JWT_AUDIENCE'] = 'suna-test-users'
    
    validator = ImprovedTokenValidator()
    
    # Teste 1: Token vazio
    print("\n1. Testando token vazio...")
    result = await validator.validate("")
    assert not result.valid
    assert result.reason == ValidationFailureReason.EMPTY_TOKEN
    print("   ✅ Token vazio rejeitado corretamente")
    
    # Teste 2: Token None
    print("\n2. Testando token None...")
    result = await validator.validate(None)
    assert not result.valid
    assert result.reason == ValidationFailureReason.EMPTY_TOKEN
    print("   ✅ Token None rejeitado corretamente")
    
    # Teste 3: Token com formato inválido
    print("\n3. Testando token com formato inválido...")
    result = await validator.validate("invalid.token")
    assert not result.valid
    assert result.reason == ValidationFailureReason.INVALID_FORMAT
    print("   ✅ Token com formato inválido rejeitado")
    
    # Teste 4: Gerar token válido
    print("\n4. Testando geração de token...")
    token = await validator.generate_token("test_user_123")
    assert token is not None
    assert len(token.split('.')) == 3  # Formato JWT
    print(f"   ✅ Token gerado: {token[:50]}...")
    
    # Teste 5: Validar token gerado
    print("\n5. Testando validação de token válido...")
    result = await validator.validate(token)
    assert result.valid
    assert result.user_id == "test_user_123"
    assert result.payload is not None
    print(f"   ✅ Token válido aceito para usuário: {result.user_id}")
    
    # Teste 6: Cache de tokens
    print("\n6. Testando cache de tokens...")
    # Primeira validação
    result1 = await validator.validate(token)
    # Segunda validação (deve usar cache)
    result2 = await validator.validate(token)
    assert result1.valid == result2.valid
    assert result1.user_id == result2.user_id
    print("   ✅ Cache funcionando corretamente")
    
    # Teste 7: Refresh de token
    print("\n7. Testando refresh de token...")
    # Aguardar 1 segundo para garantir timestamp diferente
    await asyncio.sleep(1)
    new_token = await validator.refresh_token(token)
    assert new_token is not None
    assert new_token != token  # Deve ser diferente
    print(f"   ✅ Token renovado: {new_token[:50]}...")
    
    # Teste 8: Validação WebSocket
    print("\n8. Testando validação WebSocket...")
    ws_result = await validator.validate_websocket_token(token)
    assert ws_result.valid
    assert ws_result.user_id == "test_user_123"
    print("   ✅ Validação WebSocket funcionando")
    
    # Teste 9: WebSocket com token vazio
    print("\n9. Testando WebSocket com token vazio...")
    ws_empty = await validator.validate_websocket_token("")
    assert not ws_empty.valid
    assert ws_empty.reason == ValidationFailureReason.EMPTY_TOKEN
    print("   ✅ WebSocket rejeita token vazio")
    
    # Teste 10: Estatísticas do cache
    print("\n10. Testando estatísticas do cache...")
    stats = validator.get_cache_stats()
    assert 'size' in stats
    assert 'max_size' in stats
    print(f"   ✅ Cache stats: {stats}")
    
    print("\n✅ Todos os testes do ImprovedTokenValidator passaram!")
    return True


async def test_without_jwt_secret():
    """Testa comportamento sem JWT_SECRET"""
    print("\n🧪 Testando sem JWT_SECRET...")
    
    # Remover JWT_SECRET
    if 'JWT_SECRET' in os.environ:
        del os.environ['JWT_SECRET']
    
    validator = ImprovedTokenValidator()
    
    # Deve falhar na validação
    result = await validator.validate("any.token.here")
    assert not result.valid
    assert result.reason == ValidationFailureReason.CONFIGURATION_ERROR
    print("   ✅ Falha correta sem JWT_SECRET")
    
    # Deve falhar na geração
    token = await validator.generate_token("test_user")
    assert token is None
    print("   ✅ Geração falha sem JWT_SECRET")


async def main():
    """Função principal de teste"""
    try:
        success1 = await test_improved_token_validator()
        await test_without_jwt_secret()
        
        print("\n🎉 Todos os testes passaram com sucesso!")
        return True
        
    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)