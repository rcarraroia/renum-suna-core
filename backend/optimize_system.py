#!/usr/bin/env python3
"""
Script para otimizar configurações do sistema operacional para WebSocket
Executa diagnóstico e aplica otimizações automaticamente
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from utils.system_optimizer import SystemOptimizer, optimize_system_for_websocket

async def main():
    """Função principal"""
    print("🔧 OTIMIZADOR DE SISTEMA PARA WEBSOCKET")
    print("=" * 50)
    
    try:
        # Verifica se está rodando como root
        is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        if not is_root:
            print("⚠️  AVISO: Executando sem privilégios de root")
            print("   Algumas otimizações podem não ser aplicadas imediatamente")
            print("   Para aplicar todas as otimizações, execute como root:")
            print("   sudo python3 optimize_system.py")
            print()
        
        # Executa otimização
        limits, results = await optimize_system_for_websocket()
        
        # Verifica se há problemas críticos
        critical_issues = [name for name, limit in limits.items() if limit.critical]
        if critical_issues:
            print("\n❌ PROBLEMAS CRÍTICOS ENCONTRADOS:")
            for issue in critical_issues:
                limit = limits[issue]
                print(f"   • {issue}: {limit.current_value} (recomendado: {limit.recommended_value})")
            print("\n   Estes problemas podem causar falhas de conexão WebSocket!")
        
        # Verifica se precisa reiniciar
        restart_needed = [name for name, result in results.items() if result.requires_restart]
        if restart_needed:
            print("\n🔄 REINICIALIZAÇÃO NECESSÁRIA:")
            print("   As seguintes configurações requerem reinicialização do sistema:")
            for item in restart_needed:
                print(f"   • {item}")
        
        # Instruções finais
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Revise o relatório gerado em 'backend/system_optimization_report.txt'")
        print("2. Execute o script de monitoramento: './backend/monitor_websocket_resources.sh'")
        print("3. Teste as conexões WebSocket após aplicar as otimizações")
        
        if not is_root:
            print("4. Execute novamente como root para aplicar todas as otimizações")
        
        if restart_needed:
            print("5. Reinicie o sistema para aplicar configurações persistentes")
        
        print("\n✅ Otimização concluída!")
        
    except Exception as e:
        print(f"\n❌ Erro durante otimização: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())