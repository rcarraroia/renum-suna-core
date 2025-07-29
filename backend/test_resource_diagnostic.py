#!/usr/bin/env python3
"""
Script de teste para o ResourceDiagnosticService.

Este script executa diagnósticos completos dos recursos do sistema
para identificar problemas relacionados a "Insufficient resources".
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona o diretório backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Carrega variáveis de ambiente do arquivo .env
load_dotenv(backend_dir / '.env')

from services.resource_diagnostic_service import ResourceDiagnosticService, IssueSeverity


def print_resource_status(status, test_name):
    """Imprime o status de recursos de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"✅ Recursos disponíveis: {'Sim' if status.available else 'Não'}")
    
    if status.current_usage:
        print(f"\n📊 USO ATUAL:")
        for resource, usage in status.current_usage.items():
            print(f"   {resource}: {usage}")
    
    if status.limits:
        print(f"\n🔒 LIMITES:")
        for resource, limit in status.limits.items():
            print(f"   {resource}: {limit}")
    
    if status.issues:
        print(f"\n🚨 PROBLEMAS ENCONTRADOS ({len(status.issues)}):")
        for i, issue in enumerate(status.issues, 1):
            severity_emoji = {
                IssueSeverity.LOW: "🟡",
                IssueSeverity.MEDIUM: "🟠", 
                IssueSeverity.HIGH: "🔴",
                IssueSeverity.CRITICAL: "💀"
            }
            
            print(f"\n{i}. {severity_emoji.get(issue.severity, '❓')} {issue.severity.value.upper()}")
            print(f"   Tipo: {issue.type.value}")
            print(f"   Descrição: {issue.description}")
            print(f"   Solução: {issue.solution}")
            print(f"   Componentes afetados: {', '.join(issue.affected_components)}")
            
            if issue.details:
                print(f"   Detalhes: {issue.details}")
    
    if status.recommendations:
        print(f"\n💡 RECOMENDAÇÕES ({len(status.recommendations)}):")
        for i, rec in enumerate(status.recommendations, 1):
            print(f"{i}. {rec}")


def print_memory_analysis(analysis, test_name):
    """Imprime análise de memória de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"💾 MEMÓRIA TOTAL: {analysis.total_mb:.1f} MB")
    print(f"📈 MEMÓRIA USADA: {analysis.used_mb:.1f} MB ({analysis.percentage:.1f}%)")
    print(f"📉 MEMÓRIA DISPONÍVEL: {analysis.available_mb:.1f} MB")
    print(f"🔗 MEMÓRIA POR CONEXÃO: {analysis.per_connection_mb:.1f} MB")
    print(f"🎯 MÁXIMO DE CONEXÕES ESTIMADO: {analysis.estimated_max_connections}")
    
    if analysis.issues:
        print(f"\n🚨 PROBLEMAS ENCONTRADOS ({len(analysis.issues)}):")
        for i, issue in enumerate(analysis.issues, 1):
            severity_emoji = {
                IssueSeverity.LOW: "🟡",
                IssueSeverity.MEDIUM: "🟠", 
                IssueSeverity.HIGH: "🔴",
                IssueSeverity.CRITICAL: "💀"
            }
            
            print(f"\n{i}. {severity_emoji.get(issue.severity, '❓')} {issue.severity.value.upper()}")
            print(f"   Tipo: {issue.type.value}")
            print(f"   Descrição: {issue.description}")
            print(f"   Solução: {issue.solution}")
            print(f"   Componentes afetados: {', '.join(issue.affected_components)}")


def print_network_status(status, test_name):
    """Imprime status de rede de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"🌐 LARGURA DE BANDA DISPONÍVEL: {'Sim' if status.bandwidth_available else 'Não'}")
    print(f"⚡ LATÊNCIA: {status.latency_ms:.2f} ms")
    print(f"🔗 CONEXÕES ATIVAS: {status.active_connections}")
    print(f"🎯 MÁXIMO DE CONEXÕES: {status.max_connections}")
    
    if status.port_availability:
        print(f"\n🚪 DISPONIBILIDADE DE PORTAS:")
        for port, available in status.port_availability.items():
            status_emoji = "✅" if available else "❌"
            print(f"   {status_emoji} Porta {port}: {'Disponível' if available else 'Em uso'}")
    
    if status.issues:
        print(f"\n🚨 PROBLEMAS ENCONTRADOS ({len(status.issues)}):")
        for i, issue in enumerate(status.issues, 1):
            severity_emoji = {
                IssueSeverity.LOW: "🟡",
                IssueSeverity.MEDIUM: "🟠", 
                IssueSeverity.HIGH: "🔴",
                IssueSeverity.CRITICAL: "💀"
            }
            
            print(f"\n{i}. {severity_emoji.get(issue.severity, '❓')} {issue.severity.value.upper()}")
            print(f"   Tipo: {issue.type.value}")
            print(f"   Descrição: {issue.description}")
            print(f"   Solução: {issue.solution}")
            print(f"   Componentes afetados: {', '.join(issue.affected_components)}")


async def test_connection_limits():
    """Testa limites de conexão."""
    service = ResourceDiagnosticService()
    status = await service.check_connection_limits()
    print_resource_status(status, "Limites de Conexão")
    return status


async def test_memory_analysis():
    """Testa análise de memória."""
    service = ResourceDiagnosticService()
    analysis = await service.analyze_memory_usage()
    print_memory_analysis(analysis, "Análise de Memória")
    return analysis


async def test_network_resources():
    """Testa recursos de rede."""
    service = ResourceDiagnosticService()
    status = await service.check_network_resources()
    print_network_status(status, "Recursos de Rede")
    return status


async def test_system_overview():
    """Testa visão geral do sistema."""
    service = ResourceDiagnosticService()
    overview = await service.get_system_overview()
    
    print(f"\n{'='*60}")
    print(f"VISÃO GERAL DO SISTEMA")
    print(f"{'='*60}")
    
    if "error" in overview:
        print(f"❌ Erro: {overview['error']}")
        return overview
    
    print(f"🕐 Timestamp: {overview['timestamp']}")
    
    # CPU
    cpu = overview.get('cpu', {})
    print(f"\n🖥️  CPU:")
    print(f"   Uso: {cpu.get('percent', 0):.1f}%")
    print(f"   Núcleos: {cpu.get('count', 0)}")
    if cpu.get('load_avg'):
        print(f"   Load Average: {cpu['load_avg']}")
    
    # Memória
    memory = overview.get('memory', {})
    print(f"\n💾 MEMÓRIA:")
    print(f"   Total: {memory.get('total_mb', 0):.1f} MB")
    print(f"   Usada: {memory.get('used_mb', 0):.1f} MB ({memory.get('percent', 0):.1f}%)")
    print(f"   Disponível: {memory.get('available_mb', 0):.1f} MB")
    
    # Disco
    disk = overview.get('disk', {})
    print(f"\n💿 DISCO:")
    print(f"   Total: {disk.get('total_gb', 0):.1f} GB")
    print(f"   Usado: {disk.get('used_gb', 0):.1f} GB ({disk.get('percent', 0):.1f}%)")
    print(f"   Livre: {disk.get('free_gb', 0):.1f} GB")
    
    # Rede
    network = overview.get('network', {})
    print(f"\n🌐 REDE:")
    print(f"   Bytes enviados: {network.get('bytes_sent', 0):,}")
    print(f"   Bytes recebidos: {network.get('bytes_recv', 0):,}")
    print(f"   Pacotes enviados: {network.get('packets_sent', 0):,}")
    print(f"   Pacotes recebidos: {network.get('packets_recv', 0):,}")
    
    # Processos
    processes = overview.get('processes', {})
    print(f"\n⚙️  PROCESSOS:")
    print(f"   Total: {processes.get('count', 0)}")
    
    # Configuração WebSocket
    ws_config = overview.get('websocket_config', {})
    print(f"\n🔌 CONFIGURAÇÃO WEBSOCKET:")
    print(f"   Máximo de conexões: {ws_config.get('max_connections', 0)}")
    print(f"   Limite de memória: {ws_config.get('memory_threshold_mb', 0)} MB")
    print(f"   Limite de CPU: {ws_config.get('cpu_threshold', 0)}%")
    
    return overview


async def test_service_summary():
    """Testa resumo do serviço."""
    service = ResourceDiagnosticService()
    summary = service.get_diagnostic_summary()
    
    print(f"\n{'='*60}")
    print(f"RESUMO DO SERVIÇO")
    print(f"{'='*60}")
    
    print(f"📋 Serviço: {summary['service']}")
    print(f"🔢 Versão: {summary['version']}")
    print(f"⚙️  Capacidades: {', '.join(summary['capabilities'])}")
    print(f"📊 Recursos monitorados: {', '.join(summary['monitored_resources'])}")
    
    print(f"\n📊 CONFIGURAÇÃO:")
    for key, value in summary['configuration'].items():
        print(f"   {key}: {value}")
    
    return summary


async def run_comprehensive_diagnosis():
    """Executa diagnóstico completo de recursos."""
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE RECURSOS WEBSOCKET")
    print("="*80)
    
    # Verificar configuração
    print("\n🔧 VERIFICANDO CONFIGURAÇÃO:")
    max_connections = os.getenv("MAX_WEBSOCKET_CONNECTIONS", "500")
    memory_threshold = os.getenv("MEMORY_THRESHOLD_MB", "1024")
    cpu_threshold = os.getenv("CPU_THRESHOLD", "80.0")
    
    print(f"   MAX_WEBSOCKET_CONNECTIONS: {max_connections}")
    print(f"   MEMORY_THRESHOLD_MB: {memory_threshold}")
    print(f"   CPU_THRESHOLD: {cpu_threshold}")
    
    # Executar todos os testes
    results = []
    
    try:
        # 1. Visão geral do sistema
        overview = await test_system_overview()
        
        # 2. Teste de limites de conexão
        connection_status = await test_connection_limits()
        results.append(("Limites de Conexão", connection_status))
        
        # 3. Análise de memória
        memory_analysis = await test_memory_analysis()
        results.append(("Análise de Memória", memory_analysis))
        
        # 4. Recursos de rede
        network_status = await test_network_resources()
        results.append(("Recursos de Rede", network_status))
        
        # 5. Resumo do serviço
        summary = await test_service_summary()
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE DIAGNÓSTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL DO DIAGNÓSTICO DE RECURSOS")
    print(f"{'='*80}")
    
    total_issues = 0
    critical_issues = 0
    high_issues = 0
    
    for test_name, result in results:
        if hasattr(result, 'issues'):
            test_issues = len(result.issues)
            test_critical = len([i for i in result.issues if i.severity == IssueSeverity.CRITICAL])
            test_high = len([i for i in result.issues if i.severity == IssueSeverity.HIGH])
            
            total_issues += test_issues
            critical_issues += test_critical
            high_issues += test_high
            
            available = result.available if hasattr(result, 'available') else len(result.issues) == 0
            status = "✅" if available else "❌"
            print(f"   {status} {test_name}: {test_issues} problemas ({test_critical} críticos, {test_high} altos)")
    
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   🔍 Total de problemas encontrados: {total_issues}")
    print(f"   💀 Problemas críticos: {critical_issues}")
    print(f"   🔴 Problemas altos: {high_issues}")
    
    # Análise específica para "Insufficient resources"
    print(f"\n🔍 ANÁLISE ESPECÍFICA - 'INSUFFICIENT RESOURCES':")
    
    # Verificar se há problemas que causariam "Insufficient resources"
    insufficient_resources_causes = []
    
    if memory_analysis.percentage > 90:
        insufficient_resources_causes.append("Memória crítica (>90%)")
    
    if memory_analysis.estimated_max_connections < int(max_connections):
        insufficient_resources_causes.append(f"Memória insuficiente para {max_connections} conexões")
    
    # Verificar file descriptors
    for test_name, result in results:
        if hasattr(result, 'issues'):
            for issue in result.issues:
                if "file descriptor" in issue.description.lower():
                    insufficient_resources_causes.append("Limite de file descriptors")
                elif "conexões ativas" in issue.description.lower():
                    insufficient_resources_causes.append("Muitas conexões ativas")
    
    if insufficient_resources_causes:
        print(f"   ⚠️  CAUSAS IDENTIFICADAS:")
        for i, cause in enumerate(insufficient_resources_causes, 1):
            print(f"      {i}. {cause}")
    else:
        print(f"   ✅ Nenhuma causa óbvia de 'Insufficient resources' identificada")
    
    if critical_issues > 0:
        print(f"\n🚨 AÇÃO NECESSÁRIA: {critical_issues} problemas críticos precisam ser resolvidos imediatamente!")
    elif high_issues > 0:
        print(f"\n⚠️  ATENÇÃO: {high_issues} problemas de alta prioridade precisam ser resolvidos.")
    else:
        print(f"\n✅ RECURSOS OK: Nenhum problema crítico ou de alta prioridade encontrado.")
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    if critical_issues > 0:
        print("   1. Resolva os problemas críticos identificados")
    if high_issues > 0:
        print("   2. Resolva os problemas de alta prioridade")
    if insufficient_resources_causes:
        print("   3. Foque nas causas específicas de 'Insufficient resources'")
    print("   4. Execute este diagnóstico novamente após as correções")
    print("   5. Implemente monitoramento contínuo de recursos")


if __name__ == "__main__":
    # Executa o diagnóstico completo
    asyncio.run(run_comprehensive_diagnosis())