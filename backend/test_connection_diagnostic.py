#!/usr/bin/env python3
"""
Script de teste para o ConnectionDiagnosticService.

Este script executa diagnósticos completos das conexões WebSocket
para identificar problemas relacionados a conexões fechadas prematuramente
e falhas no handshake.
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

from services.connection_diagnostic_service import ConnectionDiagnosticService, IssueSeverity


def print_handshake_issues(issues, test_name):
    """Imprime problemas de handshake de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"🔍 Problemas de handshake encontrados: {len(issues)}")
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"\n{i}. 🔗 ESTÁGIO: {issue.stage}")
            print(f"   ⏱️  Tempo: {issue.timing_ms:.0f}ms")
            print(f"   ❌ Erro: {issue.error_message}")
            if issue.error_code:
                print(f"   🔢 Código: {issue.error_code}")
            
            if issue.suggestions:
                print(f"   💡 Sugestões:")
                for j, suggestion in enumerate(issue.suggestions, 1):
                    print(f"      {j}. {suggestion}")
    else:
        print("✅ Nenhum problema de handshake identificado")


def print_closure_analysis(analysis, test_name):
    """Imprime análise de fechamentos de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"📊 ESTATÍSTICAS DE FECHAMENTO:")
    print(f"   Total de fechamentos: {analysis.total_closures}")
    print(f"   Fechamentos prematuros: {analysis.premature_closures}")
    print(f"   Fechamentos normais: {analysis.normal_closures}")
    print(f"   Fechamentos com erro: {analysis.error_closures}")
    
    if analysis.timing_analysis:
        print(f"\n⏱️  ANÁLISE DE TIMING:")
        for metric, value in analysis.timing_analysis.items():
            if isinstance(value, float):
                print(f"   {metric}: {value:.0f}ms")
            else:
                print(f"   {metric}: {value}")
    
    if analysis.common_patterns:
        print(f"\n🔍 PADRÕES COMUNS IDENTIFICADOS:")
        for i, pattern in enumerate(analysis.common_patterns, 1):
            print(f"   {i}. {pattern}")
    
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


def print_config_validation(validation, test_name):
    """Imprime validação de configuração de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"✅ Configuração válida: {'Sim' if validation.valid else 'Não'}")
    print(f"🌐 URL WebSocket: {validation.websocket_url}")
    print(f"🔒 SSL habilitado: {'Sim' if validation.ssl_enabled else 'Não'}")
    print(f"📋 Versão do protocolo: {validation.protocol_version}")
    
    print(f"\n⚙️  CONFIGURAÇÕES DE TIMEOUT:")
    for setting, value in validation.timeout_settings.items():
        print(f"   {setting}: {value}")
    
    if validation.issues:
        print(f"\n🚨 PROBLEMAS ENCONTRADOS ({len(validation.issues)}):")
        for i, issue in enumerate(validation.issues, 1):
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
    
    if validation.recommendations:
        print(f"\n💡 RECOMENDAÇÕES ({len(validation.recommendations)}):")
        for i, rec in enumerate(validation.recommendations, 1):
            print(f"{i}. {rec}")


async def test_handshake_failures():
    """Testa análise de falhas de handshake."""
    service = ConnectionDiagnosticService()
    issues = await service.analyze_handshake_failures()
    print_handshake_issues(issues, "Análise de Falhas de Handshake")
    return issues


async def test_premature_closures():
    """Testa análise de fechamentos prematuros."""
    service = ConnectionDiagnosticService()
    analysis = await service.check_premature_closures()
    print_closure_analysis(analysis, "Análise de Fechamentos Prematuros")
    return analysis


async def test_config_validation():
    """Testa validação de configuração."""
    service = ConnectionDiagnosticService()
    validation = await service.validate_websocket_config()
    print_config_validation(validation, "Validação de Configuração WebSocket")
    return validation


async def test_service_summary():
    """Testa resumo do serviço."""
    service = ConnectionDiagnosticService()
    summary = service.get_diagnostic_summary()
    
    print(f"\n{'='*60}")
    print(f"RESUMO DO SERVIÇO")
    print(f"{'='*60}")
    
    print(f"📋 Serviço: {summary['service']}")
    print(f"🔢 Versão: {summary['version']}")
    print(f"⚙️  Capacidades: {', '.join(summary['capabilities'])}")
    print(f"📊 Aspectos monitorados: {', '.join(summary['monitored_aspects'])}")
    
    print(f"\n📊 CONFIGURAÇÃO:")
    for key, value in summary['configuration'].items():
        print(f"   {key}: {value}")
    
    return summary


async def run_comprehensive_diagnosis():
    """Executa diagnóstico completo de conexões."""
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE CONEXÕES WEBSOCKET")
    print("="*80)
    
    # Verificar configuração
    print("\n🔧 VERIFICANDO CONFIGURAÇÃO:")
    websocket_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws")
    websocket_timeout = os.getenv("WEBSOCKET_TIMEOUT", "30")
    max_reconnect = os.getenv("MAX_RECONNECT_ATTEMPTS", "5")
    
    print(f"   WEBSOCKET_URL: {websocket_url}")
    print(f"   WEBSOCKET_TIMEOUT: {websocket_timeout}s")
    print(f"   MAX_RECONNECT_ATTEMPTS: {max_reconnect}")
    
    # Executar todos os testes
    results = []
    
    try:
        # 1. Teste de validação de configuração
        config_validation = await test_config_validation()
        results.append(("Validação de Configuração", config_validation))
        
        # 2. Análise de falhas de handshake
        handshake_issues = await test_handshake_failures()
        results.append(("Falhas de Handshake", handshake_issues))
        
        # 3. Análise de fechamentos prematuros
        closure_analysis = await test_premature_closures()
        results.append(("Fechamentos Prematuros", closure_analysis))
        
        # 4. Resumo do serviço
        summary = await test_service_summary()
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE DIAGNÓSTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL DO DIAGNÓSTICO DE CONEXÕES")
    print(f"{'='*80}")
    
    total_issues = 0
    critical_issues = 0
    high_issues = 0
    
    # Analisar resultados
    config_valid = config_validation.valid if hasattr(config_validation, 'valid') else True
    handshake_problems = len(handshake_issues) if isinstance(handshake_issues, list) else 0
    closure_problems = len(closure_analysis.issues) if hasattr(closure_analysis, 'issues') else 0
    
    print(f"   {'✅' if config_valid else '❌'} Configuração WebSocket: {'Válida' if config_valid else 'Inválida'}")
    print(f"   {'✅' if handshake_problems == 0 else '❌'} Handshake: {handshake_problems} problemas")
    print(f"   {'✅' if closure_problems == 0 else '❌'} Fechamentos: {closure_problems} problemas")
    
    # Contar problemas por severidade
    for test_name, result in results:
        if hasattr(result, 'issues'):
            for issue in result.issues:
                total_issues += 1
                if issue.severity == IssueSeverity.CRITICAL:
                    critical_issues += 1
                elif issue.severity == IssueSeverity.HIGH:
                    high_issues += 1
    
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   🔍 Total de problemas encontrados: {total_issues}")
    print(f"   💀 Problemas críticos: {critical_issues}")
    print(f"   🔴 Problemas altos: {high_issues}")
    
    # Análise específica para "WebSocket is closed before the connection is established"
    print(f"\n🔍 ANÁLISE ESPECÍFICA - 'WEBSOCKET CLOSED BEFORE CONNECTION':")
    
    connection_closed_causes = []
    
    # Verificar problemas de handshake
    if handshake_problems > 0:
        connection_closed_causes.append("Falhas no processo de handshake")
    
    # Verificar fechamentos prematuros
    if hasattr(closure_analysis, 'premature_closures') and closure_analysis.premature_closures > 0:
        connection_closed_causes.append(f"{closure_analysis.premature_closures} conexões fechadas prematuramente")
    
    # Verificar problemas de configuração
    if not config_valid:
        connection_closed_causes.append("Configuração WebSocket inválida")
    
    # Verificar problemas de timeout
    if hasattr(closure_analysis, 'timing_analysis'):
        timing = closure_analysis.timing_analysis
        if timing.get('average_connection_time', 0) > 3000:
            connection_closed_causes.append("Tempo de conexão muito lento")
    
    if connection_closed_causes:
        print(f"   ⚠️  CAUSAS IDENTIFICADAS:")
        for i, cause in enumerate(connection_closed_causes, 1):
            print(f"      {i}. {cause}")
    else:
        print(f"   ✅ Nenhuma causa óbvia de conexões fechadas prematuramente identificada")
    
    # Recomendações específicas
    print(f"\n🎯 RECOMENDAÇÕES ESPECÍFICAS:")
    
    if critical_issues > 0:
        print("   1. 🚨 CRÍTICO: Resolver problemas críticos imediatamente")
        
    if not config_valid:
        print("   2. ⚙️  Corrigir configuração WebSocket inválida")
        
    if handshake_problems > 0:
        print("   3. 🤝 Investigar e corrigir falhas de handshake")
        
    if hasattr(closure_analysis, 'premature_closures') and closure_analysis.premature_closures > 0:
        print("   4. ⏰ Otimizar timing de conexões para evitar fechamentos prematuros")
        
    print("   5. 📊 Implementar monitoramento contínuo de conexões")
    print("   6. 🔄 Testar reconexão automática em cenários de falha")
    
    if critical_issues > 0:
        print(f"\n🚨 AÇÃO NECESSÁRIA: {critical_issues} problemas críticos precisam ser resolvidos imediatamente!")
    elif high_issues > 0:
        print(f"\n⚠️  ATENÇÃO: {high_issues} problemas de alta prioridade precisam ser resolvidos.")
    else:
        print(f"\n✅ CONEXÕES OK: Nenhum problema crítico ou de alta prioridade encontrado.")


if __name__ == "__main__":
    # Executa o diagnóstico completo
    asyncio.run(run_comprehensive_diagnosis())