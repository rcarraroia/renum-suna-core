#!/usr/bin/env python3
"""
Teste para o script de diagnóstico completo de WebSocket
"""

import asyncio
import json
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from run_complete_websocket_diagnosis import WebSocketDiagnosticRunner


async def test_complete_diagnosis():
    """Testa o diagnóstico completo"""
    print("🧪 Testando diagnóstico completo de WebSocket...")
    
    try:
        # Criar runner de diagnóstico
        runner = WebSocketDiagnosticRunner()
        
        # Executar diagnóstico
        report = await runner.run_complete_diagnosis()
        
        # Validar estrutura do relatório
        assert 'timestamp' in report
        assert 'health_score' in report
        assert 'status' in report
        assert 'summary' in report
        assert 'issues' in report
        assert 'recommendations' in report
        assert 'detailed_results' in report
        assert 'next_steps' in report
        
        print("✅ Estrutura do relatório validada")
        
        # Validar summary
        summary = report['summary']
        assert 'critical_issues' in summary
        assert 'high_issues' in summary
        assert 'medium_issues' in summary
        assert 'total_issues' in summary
        
        print("✅ Resumo do relatório validado")
        
        # Validar issues
        issues = report['issues']
        assert 'critical' in issues
        assert 'high' in issues
        assert 'medium' in issues
        
        print("✅ Categorização de problemas validada")
        
        # Imprimir resumo do teste
        runner.print_summary(report)
        
        print("\n✅ Teste de diagnóstico completo passou!")
        return True
        
    except Exception as e:
        print(f"\n❌ Teste falhou: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def main():
    """Função principal de teste"""
    success = await test_complete_diagnosis()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())