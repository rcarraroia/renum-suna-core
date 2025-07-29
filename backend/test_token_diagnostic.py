#!/usr/bin/env python3
"""
Script de teste para o TokenDiagnosticService.

Este script executa diagnósticos completos dos tokens de autenticação WebSocket
para identificar problemas relacionados a tokens vazios, falhas de conexão e
outros problemas de autenticação.
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

from services.token_diagnostic_service import TokenDiagnosticService, IssueSeverity


def print_diagnostic_result(result, test_name):
    """Imprime o resultado de um diagnóstico de forma formatada."""
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: {test_name}")
    print(f"{'='*60}")
    
    print(f"✅ Sucesso: {'Sim' if result.success else 'Não'}")
    print(f"⏱️  Tempo de resposta: {result.metrics.get('response_time', 0):.2f}ms")
    print(f"📊 Testes: {result.metrics.get('tests_passed', 0)}/{result.metrics.get('tests_performed', 0)} passou")
    print(f"🕐 Timestamp: {result.timestamp}")
    
    if result.issues:
        print(f"\n🚨 PROBLEMAS ENCONTRADOS ({len(result.issues)}):")
        for i, issue in enumerate(result.issues, 1):
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
    
    if result.recommendations:
        print(f"\n💡 RECOMENDAÇÕES ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")


async def test_token_generation():
    """Testa a geração de tokens."""
    service = TokenDiagnosticService()
    result = await service.validate_token_generation()
    print_diagnostic_result(result, "Validação de Geração de Tokens")
    return result


async def test_token_transmission_empty():
    """Testa transmissão com token vazio."""
    service = TokenDiagnosticService()
    result = await service.check_token_transmission(token="")
    print_diagnostic_result(result, "Transmissão de Token Vazio")
    return result


async def test_token_transmission_null():
    """Testa transmissão com token null."""
    service = TokenDiagnosticService()
    result = await service.check_token_transmission(token=None)
    print_diagnostic_result(result, "Transmissão de Token Null")
    return result


async def test_token_transmission_invalid():
    """Testa transmissão com token inválido."""
    service = TokenDiagnosticService()
    result = await service.check_token_transmission(token="invalid.token.here")
    print_diagnostic_result(result, "Transmissão de Token Inválido")
    return result


async def test_empty_token_diagnosis():
    """Testa diagnóstico de tokens vazios."""
    service = TokenDiagnosticService()
    issues = await service.diagnose_empty_tokens()
    
    print(f"\n{'='*60}")
    print(f"DIAGNÓSTICO: Análise de Tokens Vazios")
    print(f"{'='*60}")
    
    print(f"🔍 Problemas identificados: {len(issues)}")
    
    if issues:
        for i, issue in enumerate(issues, 1):
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
    
    return issues


async def test_service_summary():
    """Testa o resumo do serviço."""
    service = TokenDiagnosticService()
    summary = service.get_diagnostic_summary()
    
    print(f"\n{'='*60}")
    print(f"RESUMO DO SERVIÇO")
    print(f"{'='*60}")
    
    print(f"📋 Serviço: {summary['service']}")
    print(f"🔢 Versão: {summary['version']}")
    print(f"⚙️  Capacidades: {', '.join(summary['capabilities'])}")
    print(f"🔐 Tipos de token suportados: {', '.join(summary['supported_token_types'])}")
    print(f"🔑 Algoritmos suportados: {', '.join(summary['supported_algorithms'])}")
    
    print(f"\n📊 CONFIGURAÇÃO:")
    for key, value in summary['configuration'].items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}: {value}")
    
    return summary


async def run_comprehensive_diagnosis():
    """Executa diagnóstico completo."""
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO DE TOKENS WEBSOCKET")
    print("="*80)
    
    # Verificar variáveis de ambiente
    print("\n🔧 VERIFICANDO CONFIGURAÇÃO:")
    jwt_secret = os.getenv("JWT_SECRET")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    
    print(f"   JWT_SECRET: {'✅ Configurado' if jwt_secret else '❌ Não configurado'}")
    print(f"   JWT_ALGORITHM: {jwt_algorithm}")
    
    if not jwt_secret:
        print("\n⚠️  AVISO: JWT_SECRET não está configurado!")
        print("   Para testar completamente, configure a variável de ambiente JWT_SECRET")
        print("   Exemplo: export JWT_SECRET='sua-chave-secreta-aqui'")
    
    # Executar todos os testes
    results = []
    
    try:
        # 1. Teste de geração de tokens
        result1 = await test_token_generation()
        results.append(("Geração de Tokens", result1))
        
        # 2. Teste de transmissão com token vazio
        result2 = await test_token_transmission_empty()
        results.append(("Token Vazio", result2))
        
        # 3. Teste de transmissão com token null
        result3 = await test_token_transmission_null()
        results.append(("Token Null", result3))
        
        # 4. Teste de transmissão com token inválido
        result4 = await test_token_transmission_invalid()
        results.append(("Token Inválido", result4))
        
        # 5. Diagnóstico de tokens vazios
        issues = await test_empty_token_diagnosis()
        
        # 6. Resumo do serviço
        summary = await test_service_summary()
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE DIAGNÓSTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Resumo final
    print(f"\n{'='*80}")
    print("📋 RESUMO FINAL DO DIAGNÓSTICO")
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
            
            status = "✅" if result.success else "❌"
            print(f"   {status} {test_name}: {test_issues} problemas ({test_critical} críticos, {test_high} altos)")
    
    print(f"\n📊 ESTATÍSTICAS GERAIS:")
    print(f"   🔍 Total de problemas encontrados: {total_issues}")
    print(f"   💀 Problemas críticos: {critical_issues}")
    print(f"   🔴 Problemas altos: {high_issues}")
    
    if critical_issues > 0:
        print(f"\n🚨 AÇÃO NECESSÁRIA: {critical_issues} problemas críticos precisam ser resolvidos imediatamente!")
    elif high_issues > 0:
        print(f"\n⚠️  ATENÇÃO: {high_issues} problemas de alta prioridade precisam ser resolvidos.")
    else:
        print(f"\n✅ SISTEMA OK: Nenhum problema crítico ou de alta prioridade encontrado.")
    
    print(f"\n🎯 PRÓXIMOS PASSOS:")
    if not jwt_secret:
        print("   1. Configure JWT_SECRET nas variáveis de ambiente")
    if critical_issues > 0:
        print("   2. Resolva os problemas críticos identificados")
    if high_issues > 0:
        print("   3. Resolva os problemas de alta prioridade")
    print("   4. Execute este diagnóstico novamente após as correções")
    print("   5. Implemente monitoramento contínuo de tokens")


if __name__ == "__main__":
    # Executa o diagnóstico completo
    asyncio.run(run_comprehensive_diagnosis())