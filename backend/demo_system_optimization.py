#!/usr/bin/env python3
"""
Demonstração das otimizações do sistema operacional
Executa diagnóstico, otimização e testes de validação
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from utils.system_optimizer import SystemOptimizer
from test_system_optimization import SystemOptimizationTester

async def main():
    """Demonstração completa das otimizações"""
    print("🚀 DEMONSTRAÇÃO DE OTIMIZAÇÃO DO SISTEMA PARA WEBSOCKET")
    print("=" * 70)
    
    # Fase 1: Diagnóstico inicial
    print("\n📋 FASE 1: DIAGNÓSTICO INICIAL")
    print("-" * 40)
    
    optimizer = SystemOptimizer()
    
    print("Analisando limites atuais do sistema...")
    limits = await optimizer.diagnose_system_limits()
    
    print("\nLimites encontrados:")
    for name, limit in limits.items():
        status = "✅" if limit.current_value and limit.current_value >= limit.recommended_value else "⚠️"
        if limit.critical:
            status = "❌"
        
        current_str = str(limit.current_value) if limit.current_value else "N/A"
        print(f"{status} {name}: {current_str} (recomendado: {limit.recommended_value})")
    
    # Identifica problemas críticos
    critical_issues = [name for name, limit in limits.items() if limit.critical]
    if critical_issues:
        print(f"\n❌ PROBLEMAS CRÍTICOS ENCONTRADOS: {', '.join(critical_issues)}")
    else:
        print("\n✅ Nenhum problema crítico encontrado")
    
    # Fase 2: Aplicação de otimizações
    print("\n🔧 FASE 2: APLICAÇÃO DE OTIMIZAÇÕES")
    print("-" * 40)
    
    print("Aplicando otimizações...")
    results = await optimizer.apply_optimizations(limits)
    
    successful = 0
    failed = 0
    requires_restart = []
    
    for name, result in results.items():
        if result.success:
            successful += 1
            print(f"✅ {name}: {result.message}")
        else:
            failed += 1
            print(f"❌ {name}: {result.message}")
        
        if result.requires_restart:
            requires_restart.append(name)
    
    print(f"\nResultado: {successful} sucessos, {failed} falhas")
    
    if requires_restart:
        print(f"⚠️  Requer reinicialização: {', '.join(requires_restart)}")
    
    # Fase 3: Geração de relatório
    print("\n📄 FASE 3: GERAÇÃO DE RELATÓRIO")
    print("-" * 40)
    
    report = await optimizer.generate_optimization_report(limits, results)
    
    # Salva relatório
    report_path = "backend/demo_optimization_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Relatório detalhado salvo em: {report_path}")
    
    # Cria script de monitoramento
    script_path = await optimizer.create_monitoring_script()
    print(f"Script de monitoramento criado em: {script_path}")
    
    # Fase 4: Testes de validação
    print("\n🧪 FASE 4: TESTES DE VALIDAÇÃO")
    print("-" * 40)
    
    print("Executando testes de validação...")
    tester = SystemOptimizationTester()
    
    # Executa apenas alguns testes principais para demo
    test_results = []
    
    # Teste de file descriptors
    print("  • Testando file descriptors...")
    fd_result = await tester.test_file_descriptors()
    test_results.append(("File Descriptors", fd_result))
    
    # Teste de memória
    print("  • Testando limites de memória...")
    mem_result = await tester.test_memory_limits()
    test_results.append(("Memória", mem_result))
    
    # Teste de capacidade de conexões
    print("  • Testando capacidade de conexões...")
    conn_result = await tester.test_connection_capacity()
    test_results.append(("Conexões", conn_result))
    
    # Mostra resultados dos testes
    print("\nResultados dos testes:")
    passed = 0
    for test_name, result in test_results:
        if result['success']:
            print(f"✅ {test_name}: PASSOU")
            passed += 1
        else:
            print(f"❌ {test_name}: FALHOU")
        
        # Mostra alguns detalhes
        for detail in result.get('details', [])[:2]:  # Apenas primeiros 2 detalhes
            print(f"   {detail}")
    
    print(f"\nTestes aprovados: {passed}/{len(test_results)}")
    
    # Fase 5: Demonstração de monitoramento
    print("\n📊 FASE 5: DEMONSTRAÇÃO DE MONITORAMENTO")
    print("-" * 40)
    
    print("Executando verificação única de recursos...")
    
    try:
        from monitor_websocket_resources import WebSocketResourceMonitor
        monitor = WebSocketResourceMonitor()
        metrics = await monitor.run_single_check()
        
        print("\n✅ Monitoramento executado com sucesso")
        
    except Exception as e:
        print(f"❌ Erro no monitoramento: {e}")
    
    # Resumo final
    print("\n🎯 RESUMO FINAL")
    print("=" * 40)
    
    if critical_issues:
        print("❌ Sistema possui problemas críticos que precisam ser resolvidos")
    elif failed > successful:
        print("⚠️  Algumas otimizações falharam, verifique privilégios")
    elif requires_restart:
        print("⚠️  Otimizações aplicadas, mas requer reinicialização")
    else:
        print("✅ Sistema otimizado com sucesso!")
    
    print("\nPróximos passos:")
    print("1. Revise o relatório detalhado")
    print("2. Execute o script de monitoramento para acompanhar recursos")
    print("3. Teste as conexões WebSocket em ambiente real")
    
    if not optimizer.is_root:
        print("4. Execute como administrador para aplicar todas as otimizações")
    
    if requires_restart:
        print("5. Reinicie o sistema para aplicar configurações persistentes")
    
    print("\n🏁 Demonstração concluída!")

if __name__ == "__main__":
    asyncio.run(main())