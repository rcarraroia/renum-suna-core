#!/usr/bin/env python3
"""
Script simplificado para executar diagnóstico WebSocket imediatamente
"""

# Carregar variáveis de ambiente primeiro
from dotenv import load_dotenv
load_dotenv()

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.token_diagnostic_service import TokenDiagnosticService
from services.resource_diagnostic_service import ResourceDiagnosticService
from services.connection_diagnostic_service import ConnectionDiagnosticService


async def run_diagnosis():
    """Executa diagnóstico completo de WebSocket"""
    print("🔍 DIAGNÓSTICO COMPLETO DE WEBSOCKET")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Contadores de problemas
    critical_count = 0
    high_count = 0
    medium_count = 0
    
    # === DIAGNÓSTICO DE TOKENS ===
    print("🔐 DIAGNÓSTICO DE TOKENS")
    print("-" * 30)
    
    try:
        token_service = TokenDiagnosticService()
        
        # Validar geração de tokens
        token_gen = await token_service.validate_token_generation()
        if token_gen.success:
            print("   ✅ Geração de tokens: OK")
        else:
            print("   ❌ Geração de tokens: FALHA")
            critical_count += 1
            print(f"      Problemas: {len(token_gen.issues)}")
            for issue in token_gen.issues[:3]:  # Mostrar apenas os 3 primeiros
                print(f"      - {issue.description}")
        
        # Verificar tokens vazios
        empty_tokens = await token_service.diagnose_empty_tokens()
        if empty_tokens:
            print(f"   ⚠️  Tokens vazios: {len(empty_tokens)} problemas encontrados")
            for issue in empty_tokens:
                if issue.severity.value == 'critical':
                    critical_count += 1
                elif issue.severity.value == 'high':
                    high_count += 1
                else:
                    medium_count += 1
        else:
            print("   ✅ Tokens vazios: Nenhum problema encontrado")
            
    except Exception as e:
        print(f"   ❌ Erro no diagnóstico de tokens: {e}")
        critical_count += 1
    
    print()
    
    # === DIAGNÓSTICO DE RECURSOS ===
    print("💾 DIAGNÓSTICO DE RECURSOS")
    print("-" * 30)
    
    try:
        resource_service = ResourceDiagnosticService()
        
        # Verificar limites de conexão
        conn_limits = await resource_service.check_connection_limits()
        if conn_limits.available:
            print("   ✅ Limites de conexão: OK")
        else:
            print("   ❌ Limites de conexão: ATINGIDO")
            critical_count += 1
            print(f"      Recomendações: {len(conn_limits.recommendations)}")
            for rec in conn_limits.recommendations[:2]:
                print(f"      - {rec}")
        
        # Analisar uso de memória
        memory = await resource_service.analyze_memory_usage()
        print(f"   📊 Memória: {memory.used_mb:.1f}MB / {memory.total_mb:.1f}MB ({memory.percentage:.1f}%)")
        
        if memory.percentage > 90:
            print("   ❌ Uso de memória: CRÍTICO")
            critical_count += 1
        elif memory.percentage > 80:
            print("   ⚠️  Uso de memória: ALTO")
            high_count += 1
        else:
            print("   ✅ Uso de memória: OK")
        
        print(f"   📈 Conexões estimadas máximas: {memory.estimated_max_connections}")
        
        # Verificar recursos de rede
        network = await resource_service.check_network_resources()
        if network.bandwidth_available:
            print("   ✅ Recursos de rede: OK")
        else:
            print("   ⚠️  Recursos de rede: PROBLEMAS DETECTADOS")
            high_count += 1
            
    except Exception as e:
        print(f"   ❌ Erro no diagnóstico de recursos: {e}")
        critical_count += 1
    
    print()
    
    # === DIAGNÓSTICO DE CONEXÕES ===
    print("🔌 DIAGNÓSTICO DE CONEXÕES")
    print("-" * 30)
    
    try:
        connection_service = ConnectionDiagnosticService()
        
        # Analisar falhas de handshake
        handshake_issues = await connection_service.analyze_handshake_failures()
        if handshake_issues:
            print(f"   ⚠️  Falhas de handshake: {len(handshake_issues)} problemas")
            # Considerar todas as falhas de handshake como problemas altos
            high_count += len(handshake_issues)
            for issue in handshake_issues[:3]:  # Mostrar apenas os 3 primeiros
                print(f"      - {issue.error_message} (estágio: {issue.stage})")
        else:
            print("   ✅ Falhas de handshake: Nenhum problema encontrado")
        
        # Verificar fechamentos prematuros
        closures = await connection_service.check_premature_closures()
        if closures.premature_closures > 0:
            print(f"   ⚠️  Fechamentos prematuros: {closures.premature_closures} detectados")
            high_count += 1
        else:
            print("   ✅ Fechamentos prematuros: Nenhum detectado")
        
        # Validar configuração
        config = await connection_service.validate_websocket_config()
        if config.valid:
            print("   ✅ Configuração WebSocket: VÁLIDA")
        else:
            print("   ❌ Configuração WebSocket: INVÁLIDA")
            critical_count += 1
            for issue in config.issues[:3]:
                print(f"      - {issue.description}")
            
    except Exception as e:
        print(f"   ❌ Erro no diagnóstico de conexões: {e}")
        critical_count += 1
    
    # === RESUMO FINAL ===
    print()
    print("📋 RESUMO DO DIAGNÓSTICO")
    print("=" * 50)
    
    total_issues = critical_count + high_count + medium_count
    
    if critical_count > 0:
        status = "🔴 CRÍTICO"
        exit_code = 2
    elif high_count > 0:
        status = "🟡 ATENÇÃO"
        exit_code = 1
    else:
        status = "🟢 OK"
        exit_code = 0
    
    print(f"Status Geral: {status}")
    print(f"🚨 Problemas Críticos: {critical_count}")
    print(f"⚠️  Problemas Altos: {high_count}")
    print(f"ℹ️  Problemas Médios: {medium_count}")
    print(f"📊 Total de Problemas: {total_issues}")
    
    # Recomendações baseadas nos problemas
    print()
    print("💡 RECOMENDAÇÕES IMEDIATAS:")
    
    if critical_count > 0:
        print("   1. ⚡ AÇÃO URGENTE: Reiniciar serviços WebSocket")
        print("   2. 🔧 Corrigir problemas de autenticação JWT")
        print("   3. 📈 Aumentar limites de recursos do sistema")
        print("   4. 🔍 Implementar monitoramento proativo")
    elif high_count > 0:
        print("   1. 🔧 Otimizar configurações de WebSocket")
        print("   2. 📊 Implementar monitoramento de recursos")
        print("   3. 🧪 Executar testes de carga")
        print("   4. 📝 Documentar configurações atuais")
    else:
        print("   1. ✅ Sistema funcionando adequadamente")
        print("   2. 📊 Manter monitoramento regular")
        print("   3. 🧪 Agendar testes de carga periódicos")
        print("   4. 📝 Atualizar documentação")
    
    print()
    print(f"⏰ Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    return exit_code


async def main():
    """Função principal"""
    try:
        exit_code = await run_diagnosis()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())