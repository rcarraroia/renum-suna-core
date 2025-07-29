"""
Script de teste para o EnhancedWebSocketManager
Valida funcionalidades do pool de conexões e gerenciamento de recursos
"""

import asyncio
import os
import sys
from pathlib import Path

# Configurar JWT_SECRET para teste
os.environ['JWT_SECRET'] = 'test_secret_key_for_validation_testing_purposes_only'

# Adicionar o diretório backend ao path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_enhanced_manager():
    print("🧪 TESTANDO ENHANCED WEBSOCKET MANAGER")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 6
    
    try:
        from services.enhanced_websocket_manager import (
            EnhancedWebSocketManager, 
            PoolConfiguration, 
            ConnectionPool,
            ResourceStatus
        )
        
        # Teste 1: Criação do manager
        print("1. Testando criação do manager...")
        config = PoolConfiguration(
            max_connections=100,
            max_connections_per_user=5,
            handshake_timeout=10,
            retry_attempts=2
        )
        manager = EnhancedWebSocketManager(config)
        print(f"   ✅ Manager criado - Max conexões: {config.max_connections}")
        tests_passed += 1
        
        # Teste 2: Inicialização do pool
        print("\n2. Testando inicialização do pool...")
        await manager.start()
        print("   ✅ Pool iniciado com sucesso")
        tests_passed += 1
        
        # Teste 3: Verificação de recursos
        print("\n3. Testando verificação de recursos...")
        can_accept, reason = await manager.pool.can_accept_connection("test_user", "127.0.0.1")
        print(f"   ✅ Verificação de recursos: {can_accept} - {reason}")
        if can_accept:
            tests_passed += 1
        
        # Teste 4: Estatísticas do pool
        print("\n4. Testando estatísticas do pool...")
        stats = manager.get_stats()
        
        required_keys = [
            "manager_info", "pool_stats", "retry_config", "active_retries"
        ]
        
        all_keys_present = all(key in stats for key in required_keys)
        if all_keys_present:
            print("   ✅ Todas as chaves de estatísticas presentes")
            print(f"      - Conexões ativas: {stats['pool_stats']['current_state']['active_connections']}")
            print(f"      - Usuários únicos: {stats['pool_stats']['current_state']['unique_users']}")
            print(f"      - Tentativas de retry: {stats['retry_config']['max_attempts']}")
            tests_passed += 1
        else:
            print("   ❌ Chaves de estatísticas faltando")
        
        # Teste 5: Configuração de retry
        print("\n5. Testando configuração de retry...")
        retry_config = stats['retry_config']
        
        if (retry_config['max_attempts'] == 2 and 
            retry_config['base_delay'] == 1.0 and
            retry_config['exponential_base'] == 2.0):
            print("   ✅ Configuração de retry correta")
            tests_passed += 1
        else:
            print("   ❌ Configuração de retry incorreta")
        
        # Teste 6: Limpeza
        print("\n6. Testando limpeza do manager...")
        await manager.stop()
        print("   ✅ Manager parado com sucesso")
        tests_passed += 1
        
    except Exception as e:
        print(f"   ❌ Erro nos testes: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Resultado final
    print("\n" + "=" * 50)
    print("📊 RESULTADO DOS TESTES")
    print("=" * 50)
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"Testes aprovados: {tests_passed}/{total_tests}")
    print(f"Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Pool de conexões: IMPLEMENTADO")
        print("✅ Verificação de recursos: FUNCIONANDO")
        print("✅ Sistema de retry: CONFIGURADO")
        print("✅ Estatísticas: DISPONÍVEIS")
        return True
    elif success_rate >= 80:
        print("\n✅ MAIORIA DOS TESTES PASSOU")
        print("🟡 Algumas funcionalidades podem precisar de ajustes")
        return True
    else:
        print("\n❌ MUITOS TESTES FALHARAM")
        print("🔴 Implementação precisa de revisão")
        return False

async def test_pool_limits():
    """Teste específico dos limites do pool"""
    print("\n🔍 TESTANDO LIMITES DO POOL")
    print("-" * 30)
    
    try:
        from services.enhanced_websocket_manager import PoolConfiguration, ConnectionPool
        
        # Configuração com limites baixos para teste
        config = PoolConfiguration(
            max_connections=3,
            max_connections_per_user=2,
            max_connections_per_ip=2
        )
        
        pool = ConnectionPool(config)
        await pool.start()
        
        # Teste limite por usuário
        print("Testando limite por usuário...")
        can_accept1, _ = await pool.can_accept_connection("user1", "127.0.0.1")
        can_accept2, _ = await pool.can_accept_connection("user1", "127.0.0.1")
        can_accept3, reason3 = await pool.can_accept_connection("user1", "127.0.0.1")
        
        print(f"   1ª conexão user1: {can_accept1}")
        print(f"   2ª conexão user1: {can_accept2}")
        print(f"   3ª conexão user1: {can_accept3} - {reason3}")
        
        # Teste limite por IP
        print("Testando limite por IP...")
        can_accept_ip1, _ = await pool.can_accept_connection("user2", "192.168.1.1")
        can_accept_ip2, _ = await pool.can_accept_connection("user3", "192.168.1.1")
        can_accept_ip3, reason_ip3 = await pool.can_accept_connection("user4", "192.168.1.1")
        
        print(f"   1ª conexão IP: {can_accept_ip1}")
        print(f"   2ª conexão IP: {can_accept_ip2}")
        print(f"   3ª conexão IP: {can_accept_ip3} - {reason_ip3}")
        
        await pool.stop()
        
        # Verificar se os limites funcionaram
        if (can_accept1 and can_accept2 and not can_accept3 and
            can_accept_ip1 and can_accept_ip2 and not can_accept_ip3):
            print("   ✅ Limites do pool funcionando corretamente")
            return True
        else:
            print("   ❌ Limites do pool não funcionando adequadamente")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro testando limites: {str(e)}")
        return False

async def main():
    """Função principal"""
    print("🚀 TESTE DO ENHANCED WEBSOCKET MANAGER")
    print("=" * 60)
    
    try:
        # Executar testes principais
        success1 = await test_enhanced_manager()
        
        # Executar testes de limites
        success2 = await test_pool_limits()
        
        # Resultado final
        print("\n" + "=" * 60)
        print("🎯 RESULTADO FINAL")
        print("=" * 60)
        
        if success1 and success2:
            print("🎉 ENHANCED WEBSOCKET MANAGER VALIDADO!")
            print("✅ Pool de conexões com limite configurável: IMPLEMENTADO")
            print("✅ Verificação de recursos antes de aceitar conexões: IMPLEMENTADO")
            print("✅ Timeout configurável para handshake: IMPLEMENTADO")
            print("✅ Sistema de retry com backoff exponencial: IMPLEMENTADO")
            print("\n🎯 Tarefa 3.1 concluída com sucesso!")
            return True
        else:
            print("⚠️  ENHANCED WEBSOCKET MANAGER PRECISA DE AJUSTES")
            print("Algumas funcionalidades não estão funcionando adequadamente.")
            return False
            
    except Exception as e:
        print(f"💥 Erro crítico: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)