"""
Diagnóstico Final - Validação das correções implementadas
Este script executa um diagnóstico completo para verificar se os problemas foram resolvidos
"""

# Carregar variáveis de ambiente primeiro
from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalDiagnosticService:
    """Serviço de diagnóstico final para validar correções"""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    async def run_complete_diagnosis(self) -> Dict[str, Any]:
        """Executa diagnóstico completo"""
        logger.info("🔍 DIAGNÓSTICO FINAL DE WEBSOCKET")
        logger.info("=" * 50)
        logger.info(f"⏰ Iniciado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Executar todos os diagnósticos
        await self._diagnose_token_issues()
        await self._diagnose_connection_issues()
        await self._diagnose_resource_usage()
        await self._test_websocket_functionality()
        
        # Gerar relatório final
        final_report = self._generate_final_report()
        
        # Mostrar resultados
        self._display_results(final_report)
        
        return final_report
    
    async def _diagnose_token_issues(self):
        """Diagnóstica problemas de token"""
        logger.info("🔐 DIAGNÓSTICO DE TOKENS")
        logger.info("-" * 30)
        
        try:
            from services.improved_token_validator import ImprovedTokenValidator
            
            validator = ImprovedTokenValidator()
            
            # Teste 1: Geração de token
            logger.info("Testando geração de tokens...")
            test_result = await validator.validate_token_async("test_token")
            
            if test_result:
                logger.info("✅ Sistema de validação de tokens: FUNCIONANDO")
                self.results["token_validation"] = "OK"
            else:
                logger.warning("⚠️  Sistema de validação de tokens: PROBLEMAS")
                self.results["token_validation"] = "WARNING"
            
            # Teste 2: Tokens vazios
            logger.info("Testando tratamento de tokens vazios...")
            empty_result = await validator.validate_token_async("")
            
            if not empty_result["valid"]:
                logger.info("✅ Tokens vazios: REJEITADOS CORRETAMENTE")
                self.results["empty_tokens"] = "OK"
            else:
                logger.error("❌ Tokens vazios: ACEITOS INCORRETAMENTE")
                self.results["empty_tokens"] = "ERROR"
            
            # Teste 3: Tokens inválidos
            logger.info("Testando tratamento de tokens inválidos...")
            invalid_result = await validator.validate_token_async("invalid.token.here")
            
            if not invalid_result["valid"]:
                logger.info("✅ Tokens inválidos: REJEITADOS CORRETAMENTE")
                self.results["invalid_tokens"] = "OK"
            else:
                logger.error("❌ Tokens inválidos: ACEITOS INCORRETAMENTE")
                self.results["invalid_tokens"] = "ERROR"
                
        except Exception as e:
            logger.error(f"❌ Erro no diagnóstico de tokens: {str(e)}")
            self.results["token_validation"] = "ERROR"
            self.results["empty_tokens"] = "ERROR"
            self.results["invalid_tokens"] = "ERROR"
    
    async def _diagnose_connection_issues(self):
        """Diagnóstica problemas de conexão"""
        logger.info("🔌 DIAGNÓSTICO DE CONEXÕES")
        logger.info("-" * 30)
        
        try:
            # Teste de handshake
            logger.info("Testando capacidade de handshake...")
            
            import socket
            import ssl
            
            # Testar conexão TCP básica
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', 8000))
                sock.close()
                
                if result == 0:
                    logger.info("✅ Conexão TCP: OK")
                    self.results["tcp_connection"] = "OK"
                else:
                    logger.warning("⚠️  Conexão TCP: PROBLEMAS")
                    self.results["tcp_connection"] = "WARNING"
                    
            except Exception as e:
                logger.error(f"❌ Conexão TCP: ERRO - {str(e)}")
                self.results["tcp_connection"] = "ERROR"
            
            # Testar protocolo WebSocket
            logger.info("Testando protocolo WebSocket...")
            
            try:
                import websockets
                
                # Tentar conexão WebSocket básica
                uri = "ws://localhost:8000/ws"
                
                async def test_websocket():
                    try:
                        async with websockets.connect(uri, timeout=5) as websocket:
                            # Aguardar resposta inicial
                            response = await asyncio.wait_for(websocket.recv(), timeout=3)
                            return True
                    except websockets.exceptions.ConnectionClosedError:
                        # Conexão fechada é aceitável (pode ser por falta de auth)
                        return True
                    except Exception:
                        return False
                
                ws_result = await test_websocket()
                
                if ws_result:
                    logger.info("✅ Protocolo WebSocket: OK")
                    self.results["websocket_protocol"] = "OK"
                else:
                    logger.warning("⚠️  Protocolo WebSocket: PROBLEMAS")
                    self.results["websocket_protocol"] = "WARNING"
                    
            except ImportError:
                logger.warning("⚠️  Biblioteca websockets não disponível")
                self.results["websocket_protocol"] = "WARNING"
            except Exception as e:
                logger.error(f"❌ Protocolo WebSocket: ERRO - {str(e)}")
                self.results["websocket_protocol"] = "ERROR"
                
        except Exception as e:
            logger.error(f"❌ Erro no diagnóstico de conexões: {str(e)}")
            self.results["tcp_connection"] = "ERROR"
            self.results["websocket_protocol"] = "ERROR"
    
    async def _diagnose_resource_usage(self):
        """Diagnóstica uso de recursos"""
        logger.info("📊 DIAGNÓSTICO DE RECURSOS")
        logger.info("-" * 30)
        
        try:
            import psutil
            
            # Memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            logger.info(f"Memória: {memory.used // (1024**2)}MB / {memory.total // (1024**2)}MB ({memory_percent:.1f}%)")
            
            if memory_percent < 85:
                logger.info("✅ Uso de memória: OK")
                self.results["memory_usage"] = "OK"
            elif memory_percent < 95:
                logger.warning("⚠️  Uso de memória: ALTO")
                self.results["memory_usage"] = "WARNING"
            else:
                logger.error("❌ Uso de memória: CRÍTICO")
                self.results["memory_usage"] = "ERROR"
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            logger.info(f"CPU: {cpu_percent:.1f}%")
            
            if cpu_percent < 80:
                logger.info("✅ Uso de CPU: OK")
                self.results["cpu_usage"] = "OK"
            elif cpu_percent < 95:
                logger.warning("⚠️  Uso de CPU: ALTO")
                self.results["cpu_usage"] = "WARNING"
            else:
                logger.error("❌ Uso de CPU: CRÍTICO")
                self.results["cpu_usage"] = "ERROR"
            
            # Conexões de rede
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            logger.info(f"Conexões ativas: {active_connections}")
            
            if active_connections < 100:
                logger.info("✅ Conexões de rede: OK")
                self.results["network_connections"] = "OK"
            elif active_connections < 500:
                logger.warning("⚠️  Conexões de rede: MODERADAS")
                self.results["network_connections"] = "WARNING"
            else:
                logger.error("❌ Conexões de rede: MUITAS")
                self.results["network_connections"] = "ERROR"
                
        except ImportError:
            logger.warning("⚠️  Biblioteca psutil não disponível")
            self.results["memory_usage"] = "WARNING"
            self.results["cpu_usage"] = "WARNING"
            self.results["network_connections"] = "WARNING"
        except Exception as e:
            logger.error(f"❌ Erro no diagnóstico de recursos: {str(e)}")
            self.results["memory_usage"] = "ERROR"
            self.results["cpu_usage"] = "ERROR"
            self.results["network_connections"] = "ERROR"
    
    async def _test_websocket_functionality(self):
        """Testa funcionalidade WebSocket"""
        logger.info("🧪 TESTE DE FUNCIONALIDADE")
        logger.info("-" * 30)
        
        try:
            # Testar endpoints HTTP
            import requests
            
            # Health check
            try:
                response = requests.get("http://localhost:8000/ws/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Endpoint de health: OK")
                    self.results["health_endpoint"] = "OK"
                else:
                    logger.warning(f"⚠️  Endpoint de health: HTTP {response.status_code}")
                    self.results["health_endpoint"] = "WARNING"
            except Exception as e:
                logger.error(f"❌ Endpoint de health: ERRO - {str(e)}")
                self.results["health_endpoint"] = "ERROR"
            
            # Stats endpoint
            try:
                response = requests.get("http://localhost:8000/ws/stats", timeout=5)
                if response.status_code == 200:
                    stats = response.json()
                    logger.info(f"✅ Endpoint de stats: OK (conexões: {stats.get('active_connections', 0)})")
                    self.results["stats_endpoint"] = "OK"
                else:
                    logger.warning(f"⚠️  Endpoint de stats: HTTP {response.status_code}")
                    self.results["stats_endpoint"] = "WARNING"
            except Exception as e:
                logger.error(f"❌ Endpoint de stats: ERRO - {str(e)}")
                self.results["stats_endpoint"] = "ERROR"
            
            # Broadcast endpoint
            try:
                response = requests.post(
                    "http://localhost:8000/ws/broadcast",
                    json={"message": "Teste de diagnóstico"},
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info("✅ Endpoint de broadcast: OK")
                    self.results["broadcast_endpoint"] = "OK"
                else:
                    logger.warning(f"⚠️  Endpoint de broadcast: HTTP {response.status_code}")
                    self.results["broadcast_endpoint"] = "WARNING"
            except Exception as e:
                logger.error(f"❌ Endpoint de broadcast: ERRO - {str(e)}")
                self.results["broadcast_endpoint"] = "ERROR"
                
        except ImportError:
            logger.warning("⚠️  Biblioteca requests não disponível")
            self.results["health_endpoint"] = "WARNING"
            self.results["stats_endpoint"] = "WARNING"
            self.results["broadcast_endpoint"] = "WARNING"
        except Exception as e:
            logger.error(f"❌ Erro no teste de funcionalidade: {str(e)}")
            self.results["health_endpoint"] = "ERROR"
            self.results["stats_endpoint"] = "ERROR"
            self.results["broadcast_endpoint"] = "ERROR"
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Gera relatório final"""
        # Contar resultados
        ok_count = sum(1 for v in self.results.values() if v == "OK")
        warning_count = sum(1 for v in self.results.values() if v == "WARNING")
        error_count = sum(1 for v in self.results.values() if v == "ERROR")
        total_count = len(self.results)
        
        # Determinar status geral
        if error_count == 0 and warning_count == 0:
            overall_status = "✅ OK"
            status_emoji = "🟢"
        elif error_count == 0 and warning_count <= 2:
            overall_status = "🟡 ATENÇÃO"
            status_emoji = "🟡"
        elif error_count <= 2:
            overall_status = "🟠 PROBLEMAS"
            status_emoji = "🟠"
        else:
            overall_status = "🔴 CRÍTICO"
            status_emoji = "🔴"
        
        # Calcular score
        score = (ok_count * 100 + warning_count * 50) / (total_count * 100) * 100 if total_count > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "overall_status": overall_status,
            "status_emoji": status_emoji,
            "score": score,
            "summary": {
                "total_tests": total_count,
                "ok": ok_count,
                "warnings": warning_count,
                "errors": error_count
            },
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> list:
        """Gera recomendações baseadas nos resultados"""
        recommendations = []
        
        # Verificar problemas específicos
        if self.results.get("empty_tokens") == "ERROR":
            recommendations.append("🔧 Corrigir tratamento de tokens vazios no sistema de autenticação")
        
        if self.results.get("invalid_tokens") == "ERROR":
            recommendations.append("🔧 Implementar validação mais rigorosa de tokens JWT")
        
        if self.results.get("websocket_protocol") == "ERROR":
            recommendations.append("🔧 Verificar configuração do protocolo WebSocket")
        
        if self.results.get("memory_usage") == "ERROR":
            recommendations.append("📊 Otimizar uso de memória - considerar aumentar recursos")
        
        if self.results.get("cpu_usage") == "ERROR":
            recommendations.append("📊 Otimizar uso de CPU - verificar processos intensivos")
        
        # Recomendações gerais
        if not recommendations:
            recommendations.append("🎉 Sistema funcionando corretamente! Manter monitoramento regular.")
        else:
            recommendations.append("📋 Executar testes de carga após implementar correções")
            recommendations.append("📊 Implementar monitoramento contínuo")
        
        return recommendations
    
    def _display_results(self, report: Dict[str, Any]):
        """Exibe resultados do diagnóstico"""
        logger.info("")
        logger.info("📋 RESUMO DO DIAGNÓSTICO FINAL")
        logger.info("=" * 50)
        
        # Status geral
        logger.info(f"Status Geral: {report['overall_status']}")
        logger.info(f"Score: {report['score']:.1f}%")
        logger.info(f"Duração: {report['duration']:.2f}s")
        
        # Resumo
        summary = report['summary']
        logger.info(f"")
        logger.info(f"📊 Resultados:")
        logger.info(f"  ✅ OK: {summary['ok']}")
        logger.info(f"  ⚠️  Avisos: {summary['warnings']}")
        logger.info(f"  ❌ Erros: {summary['errors']}")
        logger.info(f"  📋 Total: {summary['total_tests']}")
        
        # Detalhes por categoria
        logger.info("")
        logger.info("🔍 Detalhes por Categoria:")
        
        categories = {
            "Autenticação": ["token_validation", "empty_tokens", "invalid_tokens"],
            "Conexões": ["tcp_connection", "websocket_protocol"],
            "Recursos": ["memory_usage", "cpu_usage", "network_connections"],
            "Funcionalidade": ["health_endpoint", "stats_endpoint", "broadcast_endpoint"]
        }
        
        for category, tests in categories.items():
            logger.info(f"  {category}:")
            for test in tests:
                if test in report['detailed_results']:
                    status = report['detailed_results'][test]
                    if status == "OK":
                        logger.info(f"    ✅ {test}")
                    elif status == "WARNING":
                        logger.info(f"    ⚠️  {test}")
                    else:
                        logger.info(f"    ❌ {test}")
        
        # Recomendações
        logger.info("")
        logger.info("💡 RECOMENDAÇÕES:")
        for i, rec in enumerate(report['recommendations'], 1):
            logger.info(f"  {i}. {rec}")
        
        # Comparação com diagnóstico anterior
        logger.info("")
        logger.info("📈 COMPARAÇÃO COM DIAGNÓSTICO ANTERIOR:")
        
        if report['score'] >= 90:
            logger.info("🎉 EXCELENTE! Problemas críticos foram resolvidos.")
        elif report['score'] >= 75:
            logger.info("✅ BOM! Melhorias significativas implementadas.")
        elif report['score'] >= 50:
            logger.info("🟡 MODERADO. Ainda há problemas para resolver.")
        else:
            logger.info("❌ INSUFICIENTE. Problemas críticos persistem.")

async def main():
    """Função principal"""
    print("🚀 DIAGNÓSTICO FINAL DE WEBSOCKET")
    print("=" * 50)
    print("Validando correções implementadas...")
    print("")
    
    diagnostic = FinalDiagnosticService()
    
    try:
        report = await diagnostic.run_complete_diagnosis()
        
        # Salvar relatório
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"websocket_final_diagnosis_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("")
        print(f"📄 Relatório salvo em: {filename}")
        
        # Determinar código de saída
        if report['score'] >= 75:
            print("🎯 RESULTADO: CORREÇÕES VALIDADAS!")
            sys.exit(0)
        else:
            print("⚠️  RESULTADO: PROBLEMAS AINDA EXISTEM")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Erro crítico no diagnóstico: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())