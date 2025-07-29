#!/usr/bin/env python3
"""
Testes para validar otimizações do sistema operacional
"""

import asyncio
import sys
import os
import time
import resource
import psutil
from pathlib import Path

# Adiciona o diretório backend ao path
sys.path.append(str(Path(__file__).parent))

from utils.system_optimizer import SystemOptimizer

class SystemOptimizationTester:
    """Testa as otimizações aplicadas no sistema"""
    
    def __init__(self):
        self.optimizer = SystemOptimizer()
        self.test_results = []
    
    async def run_all_tests(self):
        """Executa todos os testes de validação"""
        print("🧪 EXECUTANDO TESTES DE OTIMIZAÇÃO DO SISTEMA")
        print("=" * 60)
        
        tests = [
            ("File Descriptors", self.test_file_descriptors),
            ("Limites de Memória", self.test_memory_limits),
            ("Configurações TCP", self.test_tcp_settings),
            ("Configurações de Rede", self.test_network_settings),
            ("Capacidade de Conexões", self.test_connection_capacity),
            ("Performance do Sistema", self.test_system_performance)
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 Executando: {test_name}")
            print("-" * 40)
            
            try:
                result = await test_func()
                self.test_results.append((test_name, result, None))
                
                if result['success']:
                    print(f"✅ {test_name}: PASSOU")
                else:
                    print(f"❌ {test_name}: FALHOU")
                
                for detail in result.get('details', []):
                    print(f"   • {detail}")
                    
            except Exception as e:
                print(f"❌ {test_name}: ERRO - {e}")
                self.test_results.append((test_name, None, str(e)))
        
        # Gera relatório final
        await self.generate_test_report()
    
    async def test_file_descriptors(self):
        """Testa limites de file descriptors"""
        try:
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            details = [
                f"Limite soft: {soft_limit}",
                f"Limite hard: {hard_limit}"
            ]
            
            # Verifica se está otimizado
            success = soft_limit >= 10000  # Mínimo aceitável
            
            if soft_limit >= 65536:
                details.append("✅ Otimizado para alta concorrência")
            elif soft_limit >= 10000:
                details.append("⚠️  Adequado, mas pode ser melhorado")
            else:
                details.append("❌ Insuficiente para alta concorrência")
            
            return {
                'success': success,
                'details': details,
                'metrics': {
                    'soft_limit': soft_limit,
                    'hard_limit': hard_limit
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao verificar file descriptors: {e}"],
                'metrics': {}
            }
    
    async def test_memory_limits(self):
        """Testa configurações de memória"""
        try:
            # Verifica memória disponível
            memory = psutil.virtual_memory()
            
            details = [
                f"Memória total: {memory.total // (1024**3)} GB",
                f"Memória disponível: {memory.available // (1024**3)} GB",
                f"Uso atual: {memory.percent}%"
            ]
            
            # Verifica se há memória suficiente
            available_gb = memory.available // (1024**3)
            success = available_gb >= 2  # Pelo menos 2GB disponível
            
            if available_gb >= 8:
                details.append("✅ Memória abundante para WebSocket")
            elif available_gb >= 4:
                details.append("✅ Memória adequada para WebSocket")
            elif available_gb >= 2:
                details.append("⚠️  Memória limitada, monitore o uso")
            else:
                details.append("❌ Memória insuficiente")
            
            return {
                'success': success,
                'details': details,
                'metrics': {
                    'total_gb': memory.total // (1024**3),
                    'available_gb': available_gb,
                    'usage_percent': memory.percent
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao verificar memória: {e}"],
                'metrics': {}
            }
    
    async def test_tcp_settings(self):
        """Testa configurações TCP"""
        try:
            details = []
            success = True
            metrics = {}
            
            if self.optimizer.platform == 'linux':
                # Verifica configurações TCP
                tcp_settings = {
                    'tcp_max_syn_backlog': '/proc/sys/net/ipv4/tcp_max_syn_backlog',
                    'tcp_keepalive_time': '/proc/sys/net/ipv4/tcp_keepalive_time',
                    'tcp_fin_timeout': '/proc/sys/net/ipv4/tcp_fin_timeout'
                }
                
                for setting, path in tcp_settings.items():
                    try:
                        with open(path, 'r') as f:
                            value = int(f.read().strip())
                        
                        metrics[setting] = value
                        details.append(f"{setting}: {value}")
                        
                        # Verifica se está otimizado
                        if setting == 'tcp_max_syn_backlog' and value < 1024:
                            success = False
                            details.append(f"  ❌ {setting} muito baixo")
                        elif setting == 'tcp_keepalive_time' and value > 7200:
                            details.append(f"  ⚠️  {setting} muito alto")
                        elif setting == 'tcp_fin_timeout' and value > 60:
                            details.append(f"  ⚠️  {setting} muito alto")
                        else:
                            details.append(f"  ✅ {setting} adequado")
                            
                    except Exception as e:
                        details.append(f"Erro ao ler {setting}: {e}")
                        success = False
            else:
                details.append("Configurações TCP não verificáveis neste sistema")
            
            return {
                'success': success,
                'details': details,
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao verificar TCP: {e}"],
                'metrics': {}
            }
    
    async def test_network_settings(self):
        """Testa configurações de rede"""
        try:
            details = []
            success = True
            metrics = {}
            
            if self.optimizer.platform == 'linux':
                # Verifica configurações de rede
                network_settings = {
                    'somaxconn': '/proc/sys/net/core/somaxconn',
                    'netdev_max_backlog': '/proc/sys/net/core/netdev_max_backlog'
                }
                
                for setting, path in network_settings.items():
                    try:
                        with open(path, 'r') as f:
                            value = int(f.read().strip())
                        
                        metrics[setting] = value
                        details.append(f"{setting}: {value}")
                        
                        # Verifica se está otimizado
                        if setting == 'somaxconn' and value < 1024:
                            success = False
                            details.append(f"  ❌ {setting} muito baixo")
                        elif setting == 'netdev_max_backlog' and value < 1000:
                            success = False
                            details.append(f"  ❌ {setting} muito baixo")
                        else:
                            details.append(f"  ✅ {setting} adequado")
                            
                    except Exception as e:
                        details.append(f"Erro ao ler {setting}: {e}")
                        success = False
            else:
                details.append("Configurações de rede não verificáveis neste sistema")
            
            return {
                'success': success,
                'details': details,
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao verificar rede: {e}"],
                'metrics': {}
            }
    
    async def test_connection_capacity(self):
        """Testa capacidade de conexões"""
        try:
            details = []
            
            # Simula abertura de múltiplas conexões
            import socket
            sockets = []
            max_connections = 0
            
            try:
                # Tenta abrir até 1000 sockets
                for i in range(1000):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setblocking(False)
                    sockets.append(sock)
                    max_connections = i + 1
                    
                    if i % 100 == 0:
                        print(f"   Testando {i} conexões...")
                        
            except Exception as e:
                details.append(f"Limite atingido em {max_connections} conexões: {e}")
            finally:
                # Fecha todos os sockets
                for sock in sockets:
                    try:
                        sock.close()
                    except:
                        pass
            
            details.append(f"Máximo de sockets criados: {max_connections}")
            
            success = max_connections >= 500
            
            if max_connections >= 1000:
                details.append("✅ Excelente capacidade de conexões")
            elif max_connections >= 500:
                details.append("✅ Boa capacidade de conexões")
            elif max_connections >= 100:
                details.append("⚠️  Capacidade limitada")
            else:
                details.append("❌ Capacidade insuficiente")
            
            return {
                'success': success,
                'details': details,
                'metrics': {
                    'max_connections': max_connections
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao testar conexões: {e}"],
                'metrics': {}
            }
    
    async def test_system_performance(self):
        """Testa performance geral do sistema"""
        try:
            details = []
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            details.append(f"Uso de CPU: {cpu_percent}%")
            
            # Load average (apenas Linux)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                details.append(f"Load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
            
            # Processos
            process_count = len(psutil.pids())
            details.append(f"Processos ativos: {process_count}")
            
            # Conexões de rede
            try:
                connections = psutil.net_connections()
                tcp_connections = len([c for c in connections if c.type == socket.SOCK_STREAM])
                details.append(f"Conexões TCP ativas: {tcp_connections}")
            except:
                details.append("Não foi possível contar conexões TCP")
            
            # Avalia performance
            success = True
            if cpu_percent > 80:
                success = False
                details.append("❌ CPU sobrecarregada")
            elif cpu_percent > 60:
                details.append("⚠️  CPU com carga alta")
            else:
                details.append("✅ CPU com carga normal")
            
            return {
                'success': success,
                'details': details,
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'process_count': process_count
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'details': [f"Erro ao testar performance: {e}"],
                'metrics': {}
            }
    
    async def generate_test_report(self):
        """Gera relatório dos testes"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE TESTES DE OTIMIZAÇÃO DO SISTEMA")
        report.append("=" * 80)
        report.append(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Sistema: {self.optimizer.platform}")
        report.append("")
        
        passed = 0
        failed = 0
        errors = 0
        
        for test_name, result, error in self.test_results:
            if error:
                report.append(f"❌ {test_name}: ERRO")
                report.append(f"   {error}")
                errors += 1
            elif result and result['success']:
                report.append(f"✅ {test_name}: PASSOU")
                passed += 1
            else:
                report.append(f"❌ {test_name}: FALHOU")
                failed += 1
            
            if result:
                for detail in result.get('details', []):
                    report.append(f"   {detail}")
            
            report.append("")
        
        # Resumo
        report.append("RESUMO DOS TESTES:")
        report.append("-" * 40)
        report.append(f"Testes aprovados: {passed}")
        report.append(f"Testes falhados: {failed}")
        report.append(f"Testes com erro: {errors}")
        report.append(f"Total: {len(self.test_results)}")
        
        # Recomendações
        report.append("")
        report.append("RECOMENDAÇÕES:")
        report.append("-" * 40)
        
        if failed > 0 or errors > 0:
            report.append("• Execute o otimizador novamente: python3 optimize_system.py")
            report.append("• Verifique se tem privilégios adequados")
            report.append("• Considere reiniciar o sistema após otimizações")
        else:
            report.append("• Sistema otimizado com sucesso!")
            report.append("• Monitore a performance em produção")
        
        report_content = "\n".join(report)
        
        # Salva relatório
        report_path = "backend/system_optimization_test_report.txt"
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"\n📄 Relatório de testes salvo em {report_path}")
        print("\n" + "=" * 60)
        print("RESUMO FINAL:")
        print(f"✅ Aprovados: {passed}")
        print(f"❌ Falhados: {failed}")
        print(f"⚠️  Erros: {errors}")
        
        if failed == 0 and errors == 0:
            print("\n🎉 Todos os testes passaram! Sistema otimizado.")
        else:
            print("\n⚠️  Alguns testes falharam. Verifique o relatório.")


async def main():
    """Função principal"""
    tester = SystemOptimizationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    import socket
    asyncio.run(main())