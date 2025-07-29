#!/usr/bin/env python3
"""
Script consolidado para diagnóstico completo de problemas WebSocket
Executa todos os serviços de diagnóstico e gera relatório detalhado
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from services.token_diagnostic_service import TokenDiagnosticService
from services.resource_diagnostic_service import ResourceDiagnosticService
from services.connection_diagnostic_service import ConnectionDiagnosticService


class WebSocketDiagnosticRunner:
    """Executor consolidado de diagnósticos WebSocket"""
    
    def __init__(self):
        self.token_service = TokenDiagnosticService()
        self.resource_service = ResourceDiagnosticService()
        self.connection_service = ConnectionDiagnosticService()
        self.results = {}
        
    async def run_complete_diagnosis(self) -> Dict[str, Any]:
        """Executa diagnóstico completo e retorna resultados"""
        print("🔍 Iniciando diagnóstico completo de WebSocket...")
        print("=" * 60)
        
        # Executar todos os diagnósticos
        await self._run_token_diagnostics()
        await self._run_resource_diagnostics()
        await self._run_connection_diagnostics()
        
        # Gerar relatório consolidado
        report = self._generate_consolidated_report()
        
        # Salvar relatório em arquivo
        await self._save_report(report)
        
        return report
    
    async def _run_token_diagnostics(self):
        """Executa diagnósticos relacionados a tokens"""
        print("\n🔐 Executando diagnósticos de token...")
        
        try:
            # Validar geração de tokens
            token_generation = await self.token_service.validate_token_generation()
            self.results['token_generation'] = token_generation
            print(f"   ✓ Geração de tokens: {'OK' if token_generation.success else 'FALHA'}")
            
            # Verificar transmissão de tokens (simulado)
            token_transmission = await self.token_service.check_token_transmission(None)
            self.results['token_transmission'] = token_transmission
            print(f"   ✓ Transmissão de tokens: {'OK' if token_transmission.success else 'FALHA'}")
            
            # Diagnosticar tokens vazios
            empty_tokens = await self.token_service.diagnose_empty_tokens()
            self.results['empty_tokens'] = empty_tokens
            print(f"   ✓ Análise de tokens vazios: {len(empty_tokens)} problemas encontrados")
            
        except Exception as e:
            print(f"   ❌ Erro no diagnóstico de tokens: {e}")
            self.results['token_error'] = str(e)
    
    async def _run_resource_diagnostics(self):
        """Executa diagnósticos relacionados a recursos"""
        print("\n💾 Executando diagnósticos de recursos...")
        
        try:
            # Verificar limites de conexão
            connection_limits = await self.resource_service.check_connection_limits()
            self.results['connection_limits'] = connection_limits
            print(f"   ✓ Limites de conexão: {'OK' if connection_limits.available else 'LIMIT_REACHED'}")
            
            # Analisar uso de memória
            memory_analysis = await self.resource_service.analyze_memory_usage()
            self.results['memory_analysis'] = memory_analysis
            print(f"   ✓ Uso de memória: {memory_analysis.used_mb:.1f}MB de {memory_analysis.total_mb:.1f}MB ({memory_analysis.percentage:.1f}%)")
            
            # Verificar recursos de rede
            network_status = await self.resource_service.check_network_resources()
            self.results['network_status'] = network_status
            print(f"   ✓ Recursos de rede: {'OK' if network_status.available else 'ISSUES_FOUND'}")
            
        except Exception as e:
            print(f"   ❌ Erro no diagnóstico de recursos: {e}")
            self.results['resource_error'] = str(e)
    
    async def _run_connection_diagnostics(self):
        """Executa diagnósticos relacionados a conexões"""
        print("\n🔌 Executando diagnósticos de conexão...")
        
        try:
            # Analisar falhas de handshake
            handshake_issues = await self.connection_service.analyze_handshake_failures()
            self.results['handshake_issues'] = handshake_issues
            print(f"   ✓ Falhas de handshake: {len(handshake_issues)} problemas encontrados")
            
            # Verificar fechamentos prematuros
            closure_analysis = await self.connection_service.check_premature_closures()
            self.results['closure_analysis'] = closure_analysis
            print(f"   ✓ Fechamentos prematuros: {closure_analysis.premature_closures} detectados")
            
            # Validar configuração WebSocket
            config_validation = await self.connection_service.validate_websocket_config()
            self.results['config_validation'] = config_validation
            print(f"   ✓ Configuração WebSocket: {'VÁLIDA' if config_validation.valid else 'INVÁLIDA'}")
            
        except Exception as e:
            print(f"   ❌ Erro no diagnóstico de conexão: {e}")
            self.results['connection_error'] = str(e)
    
    def _generate_consolidated_report(self) -> Dict[str, Any]:
        """Gera relatório consolidado com análise e recomendações"""
        print("\n📊 Gerando relatório consolidado...")
        
        # Análise de criticidade
        critical_issues = []
        high_issues = []
        medium_issues = []
        recommendations = []
        
        # Analisar resultados de tokens
        if 'token_generation' in self.results:
            token_gen = self.results['token_generation']
            if not token_gen.success:
                critical_issues.extend([{
                    'type': 'token',
                    'description': 'Falha na geração de tokens JWT',
                    'severity': 'critical'
                }])
                recommendations.extend(token_gen.recommendations)
        
        if 'empty_tokens' in self.results:
            empty_tokens = self.results['empty_tokens']
            if empty_tokens:
                for issue in empty_tokens:
                    if issue.severity.value == 'critical':
                        critical_issues.append({
                            'type': issue.issue_type.value,
                            'description': issue.description,
                            'severity': issue.severity.value
                        })
                    elif issue.severity.value == 'high':
                        high_issues.append({
                            'type': issue.issue_type.value,
                            'description': issue.description,
                            'severity': issue.severity.value
                        })
        
        # Analisar resultados de recursos
        if 'connection_limits' in self.results:
            conn_limits = self.results['connection_limits']
            if not conn_limits.available:
                critical_issues.append({
                    'type': 'resource',
                    'description': f"Limite de conexões atingido",
                    'severity': 'critical'
                })
                recommendations.extend(conn_limits.recommendations)
        
        if 'memory_analysis' in self.results:
            memory = self.results['memory_analysis']
            if memory.percentage > 90:
                critical_issues.append({
                    'type': 'resource',
                    'description': f"Uso crítico de memória: {memory.used_mb:.1f}MB ({memory.percentage:.1f}%)",
                    'severity': 'critical'
                })
            elif memory.percentage > 80:
                high_issues.append({
                    'type': 'resource',
                    'description': f"Uso alto de memória: {memory.used_mb:.1f}MB ({memory.percentage:.1f}%)",
                    'severity': 'high'
                })
        
        # Analisar resultados de conexão
        if 'handshake_issues' in self.results:
            handshake_issues = self.results['handshake_issues']
            for issue in handshake_issues:
                if issue.severity.value == 'critical':
                    critical_issues.append({
                        'type': issue.issue_type.value,
                        'description': issue.description,
                        'severity': issue.severity.value
                    })
                elif issue.severity.value == 'high':
                    high_issues.append({
                        'type': issue.issue_type.value,
                        'description': issue.description,
                        'severity': issue.severity.value
                    })
        
        if 'config_validation' in self.results:
            config = self.results['config_validation']
            if not config.valid:
                for issue in config.issues:
                    critical_issues.append({
                        'type': issue.issue_type.value,
                        'description': issue.description,
                        'severity': issue.severity.value
                    })
        
        # Gerar recomendações baseadas nos problemas encontrados
        if critical_issues:
            recommendations.extend([
                "AÇÃO IMEDIATA: Reiniciar serviços WebSocket para liberar recursos",
                "Verificar e corrigir configurações de autenticação JWT",
                "Aumentar limites de conexão e memória do sistema",
                "Implementar monitoramento proativo de recursos"
            ])
        
        # Calcular score de saúde geral
        total_issues = len(critical_issues) + len(high_issues) + len(medium_issues)
        health_score = max(0, 100 - (len(critical_issues) * 30 + len(high_issues) * 15 + len(medium_issues) * 5))
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'status': 'CRITICAL' if critical_issues else 'WARNING' if high_issues else 'OK',
            'summary': {
                'critical_issues': len(critical_issues),
                'high_issues': len(high_issues),
                'medium_issues': len(medium_issues),
                'total_issues': total_issues
            },
            'issues': {
                'critical': critical_issues,
                'high': high_issues,
                'medium': medium_issues
            },
            'recommendations': recommendations,
            'detailed_results': self.results,
            'next_steps': self._generate_next_steps(critical_issues, high_issues)
        }
        
        return report
    
    def _generate_next_steps(self, critical_issues: List, high_issues: List) -> List[str]:
        """Gera próximos passos baseados nos problemas encontrados"""
        next_steps = []
        
        if critical_issues:
            next_steps.extend([
                "1. URGENTE: Executar correções críticas imediatamente",
                "2. Implementar ImprovedTokenValidator para corrigir problemas de autenticação",
                "3. Otimizar ResourceMonitor para gerenciar recursos adequadamente",
                "4. Reiniciar serviços WebSocket com configurações corrigidas"
            ])
        elif high_issues:
            next_steps.extend([
                "1. Implementar EnhancedWebSocketManager com pool de conexões",
                "2. Configurar monitoramento proativo de recursos",
                "3. Otimizar configurações do sistema operacional",
                "4. Executar testes de carga para validar correções"
            ])
        else:
            next_steps.extend([
                "1. Implementar monitoramento contínuo",
                "2. Configurar alertas proativos",
                "3. Documentar configurações atuais",
                "4. Agendar testes de carga regulares"
            ])
        
        return next_steps
    
    async def _save_report(self, report: Dict[str, Any]):
        """Salva relatório em arquivo JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"websocket_diagnosis_report_{timestamp}.json"
        filepath = Path("logs") / filename
        
        # Criar diretório de logs se não existir
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Relatório salvo em: {filepath}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprime resumo do relatório"""
        print("\n" + "=" * 60)
        print("📋 RESUMO DO DIAGNÓSTICO WEBSOCKET")
        print("=" * 60)
        
        # Status geral
        status_emoji = "🔴" if report['status'] == 'CRITICAL' else "🟡" if report['status'] == 'WARNING' else "🟢"
        print(f"\n{status_emoji} Status Geral: {report['status']}")
        print(f"📊 Score de Saúde: {report['health_score']}/100")
        
        # Resumo de problemas
        summary = report['summary']
        print(f"\n🚨 Problemas Críticos: {summary['critical_issues']}")
        print(f"⚠️  Problemas Altos: {summary['high_issues']}")
        print(f"ℹ️  Problemas Médios: {summary['medium_issues']}")
        print(f"📈 Total de Problemas: {summary['total_issues']}")
        
        # Principais recomendações
        if report['recommendations']:
            print(f"\n💡 Principais Recomendações:")
            for i, rec in enumerate(report['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
        # Próximos passos
        if report['next_steps']:
            print(f"\n🎯 Próximos Passos:")
            for step in report['next_steps'][:4]:
                print(f"   {step}")
        
        print("\n" + "=" * 60)


async def main():
    """Função principal"""
    try:
        # Criar e executar diagnóstico
        runner = WebSocketDiagnosticRunner()
        report = await runner.run_complete_diagnosis()
        
        # Imprimir resumo
        runner.print_summary(report)
        
        # Retornar código de saída baseado na criticidade
        if report['status'] == 'CRITICAL':
            sys.exit(2)  # Código para problemas críticos
        elif report['status'] == 'WARNING':
            sys.exit(1)  # Código para warnings
        else:
            sys.exit(0)  # Sucesso
            
    except Exception as e:
        print(f"\n❌ Erro fatal durante diagnóstico: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(3)  # Código para erro fatal


if __name__ == "__main__":
    asyncio.run(main())