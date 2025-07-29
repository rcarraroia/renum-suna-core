"""
Sistema de Otimização de Configurações do Sistema Operacional para WebSocket
Verifica e ajusta limites do sistema para suportar alta concorrência de conexões WebSocket
"""

import os
import sys
import platform
import subprocess
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SystemLimit:
    """Representa um limite do sistema"""
    name: str
    current_value: Optional[int]
    recommended_value: int
    description: str
    critical: bool = False

@dataclass
class OptimizationResult:
    """Resultado de uma otimização"""
    success: bool
    message: str
    before_value: Optional[int]
    after_value: Optional[int]
    requires_restart: bool = False

class SystemOptimizer:
    """Otimizador de configurações do sistema operacional"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_root = os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        self.optimizations_applied = []
        
    async def diagnose_system_limits(self) -> Dict[str, SystemLimit]:
        """Diagnostica limites atuais do sistema"""
        limits = {}
        
        try:
            # File descriptors
            limits['file_descriptors'] = await self._check_file_descriptors()
            
            # TCP settings
            limits['tcp_max_syn_backlog'] = await self._check_tcp_syn_backlog()
            limits['tcp_keepalive'] = await self._check_tcp_keepalive()
            limits['tcp_fin_timeout'] = await self._check_tcp_fin_timeout()
            
            # Memory settings
            limits['vm_max_map_count'] = await self._check_vm_max_map_count()
            limits['shared_memory'] = await self._check_shared_memory()
            
            # Network settings
            limits['net_core_somaxconn'] = await self._check_somaxconn()
            limits['net_core_netdev_max_backlog'] = await self._check_netdev_backlog()
            
        except Exception as e:
            logger.error(f"Erro ao diagnosticar limites do sistema: {e}")
            
        return limits
    
    async def _check_file_descriptors(self) -> SystemLimit:
        """Verifica limites de file descriptors"""
        try:
            if self.platform == 'windows':
                # Windows não tem conceito de file descriptors como Unix
                # Usa limite de handles do sistema
                return SystemLimit(
                    name="file_descriptors",
                    current_value=16384,  # Valor típico do Windows
                    recommended_value=65536,
                    description="Limite de handles por processo (Windows)",
                    critical=False
                )
            else:
                # Limite soft atual (Unix/Linux)
                import resource
                soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
                
                # Recomendação: pelo menos 65536 para suportar muitas conexões WebSocket
                recommended = 65536
                
                return SystemLimit(
                    name="file_descriptors",
                    current_value=soft_limit,
                    recommended_value=recommended,
                    description="Limite de file descriptors por processo",
                    critical=soft_limit < 10000
                )
        except Exception as e:
            logger.error(f"Erro ao verificar file descriptors: {e}")
            return SystemLimit(
                name="file_descriptors",
                current_value=None,
                recommended_value=65536,
                description="Limite de file descriptors por processo",
                critical=True
            )
    
    async def _check_tcp_syn_backlog(self) -> SystemLimit:
        """Verifica TCP SYN backlog"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/net/ipv4/tcp_max_syn_backlog', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="tcp_max_syn_backlog",
                current_value=current,
                recommended_value=8192,
                description="Máximo de conexões SYN em backlog",
                critical=current and current < 1024
            )
        except Exception as e:
            logger.error(f"Erro ao verificar TCP SYN backlog: {e}")
            return SystemLimit(
                name="tcp_max_syn_backlog",
                current_value=None,
                recommended_value=8192,
                description="Máximo de conexões SYN em backlog"
            )
    
    async def _check_tcp_keepalive(self) -> SystemLimit:
        """Verifica configurações de TCP keepalive"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/net/ipv4/tcp_keepalive_time', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="tcp_keepalive_time",
                current_value=current,
                recommended_value=600,  # 10 minutos
                description="Tempo antes de iniciar keepalive (segundos)",
                critical=current and current > 7200  # Mais de 2 horas é muito
            )
        except Exception as e:
            logger.error(f"Erro ao verificar TCP keepalive: {e}")
            return SystemLimit(
                name="tcp_keepalive_time",
                current_value=None,
                recommended_value=600,
                description="Tempo antes de iniciar keepalive (segundos)"
            )
    
    async def _check_tcp_fin_timeout(self) -> SystemLimit:
        """Verifica timeout de FIN"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/net/ipv4/tcp_fin_timeout', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="tcp_fin_timeout",
                current_value=current,
                recommended_value=30,
                description="Timeout para conexões em estado FIN_WAIT_2",
                critical=current and current > 60
            )
        except Exception as e:
            logger.error(f"Erro ao verificar TCP FIN timeout: {e}")
            return SystemLimit(
                name="tcp_fin_timeout",
                current_value=None,
                recommended_value=30,
                description="Timeout para conexões em estado FIN_WAIT_2"
            )
    
    async def _check_vm_max_map_count(self) -> SystemLimit:
        """Verifica vm.max_map_count"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/vm/max_map_count', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="vm_max_map_count",
                current_value=current,
                recommended_value=262144,
                description="Máximo de áreas de memória mapeadas",
                critical=current and current < 65536
            )
        except Exception as e:
            logger.error(f"Erro ao verificar vm.max_map_count: {e}")
            return SystemLimit(
                name="vm_max_map_count",
                current_value=None,
                recommended_value=262144,
                description="Máximo de áreas de memória mapeadas"
            )
    
    async def _check_shared_memory(self) -> SystemLimit:
        """Verifica configurações de memória compartilhada"""
        try:
            if self.platform == 'linux':
                # Verifica shmmax (tamanho máximo de segmento de memória compartilhada)
                result = subprocess.run(['sysctl', 'kernel.shmmax'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    current = int(result.stdout.split('=')[1].strip())
                else:
                    current = None
            else:
                current = None
                
            # Recomendação: pelo menos 1GB
            recommended = 1073741824  # 1GB
            
            return SystemLimit(
                name="shared_memory_max",
                current_value=current,
                recommended_value=recommended,
                description="Tamanho máximo de segmento de memória compartilhada",
                critical=current and current < 268435456  # Menos de 256MB
            )
        except Exception as e:
            logger.error(f"Erro ao verificar memória compartilhada: {e}")
            return SystemLimit(
                name="shared_memory_max",
                current_value=None,
                recommended_value=1073741824,
                description="Tamanho máximo de segmento de memória compartilhada"
            )
    
    async def _check_somaxconn(self) -> SystemLimit:
        """Verifica net.core.somaxconn"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/net/core/somaxconn', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="net_core_somaxconn",
                current_value=current,
                recommended_value=8192,
                description="Máximo de conexões em fila de listen()",
                critical=current and current < 1024
            )
        except Exception as e:
            logger.error(f"Erro ao verificar somaxconn: {e}")
            return SystemLimit(
                name="net_core_somaxconn",
                current_value=None,
                recommended_value=8192,
                description="Máximo de conexões em fila de listen()"
            )
    
    async def _check_netdev_backlog(self) -> SystemLimit:
        """Verifica net.core.netdev_max_backlog"""
        try:
            if self.platform == 'linux':
                with open('/proc/sys/net/core/netdev_max_backlog', 'r') as f:
                    current = int(f.read().strip())
            else:
                current = None
                
            return SystemLimit(
                name="net_core_netdev_max_backlog",
                current_value=current,
                recommended_value=5000,
                description="Máximo de pacotes em backlog de interface de rede",
                critical=current and current < 1000
            )
        except Exception as e:
            logger.error(f"Erro ao verificar netdev backlog: {e}")
            return SystemLimit(
                name="net_core_netdev_max_backlog",
                current_value=None,
                recommended_value=5000,
                description="Máximo de pacotes em backlog de interface de rede"
            )
    
    async def apply_optimizations(self, limits: Dict[str, SystemLimit]) -> Dict[str, OptimizationResult]:
        """Aplica otimizações baseadas nos limites diagnosticados"""
        results = {}
        
        for name, limit in limits.items():
            if limit.current_value is None:
                results[name] = OptimizationResult(
                    success=False,
                    message=f"Não foi possível determinar valor atual para {name}",
                    before_value=None,
                    after_value=None
                )
                continue
                
            if limit.current_value >= limit.recommended_value:
                results[name] = OptimizationResult(
                    success=True,
                    message=f"{name} já está otimizado ({limit.current_value} >= {limit.recommended_value})",
                    before_value=limit.current_value,
                    after_value=limit.current_value
                )
                continue
            
            # Aplica otimização específica
            if name == 'file_descriptors':
                results[name] = await self._optimize_file_descriptors(limit)
            elif name.startswith('tcp_'):
                results[name] = await self._optimize_tcp_setting(name, limit)
            elif name.startswith('vm_'):
                results[name] = await self._optimize_vm_setting(name, limit)
            elif name.startswith('net_'):
                results[name] = await self._optimize_network_setting(name, limit)
            else:
                results[name] = OptimizationResult(
                    success=False,
                    message=f"Otimização não implementada para {name}",
                    before_value=limit.current_value,
                    after_value=None
                )
        
        return results
    
    async def _optimize_file_descriptors(self, limit: SystemLimit) -> OptimizationResult:
        """Otimiza limites de file descriptors"""
        try:
            import resource
            
            # Tenta definir limite soft
            current_soft, current_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            new_soft = min(limit.recommended_value, current_hard)
            
            resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, current_hard))
            
            # Verifica se foi aplicado
            actual_soft, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            # Cria configuração persistente
            await self._create_limits_config(limit.recommended_value)
            
            return OptimizationResult(
                success=True,
                message=f"File descriptors otimizado de {current_soft} para {actual_soft}",
                before_value=current_soft,
                after_value=actual_soft,
                requires_restart=actual_soft < limit.recommended_value
            )
            
        except Exception as e:
            logger.error(f"Erro ao otimizar file descriptors: {e}")
            return OptimizationResult(
                success=False,
                message=f"Falha ao otimizar file descriptors: {e}",
                before_value=limit.current_value,
                after_value=None
            )
    
    async def _optimize_tcp_setting(self, name: str, limit: SystemLimit) -> OptimizationResult:
        """Otimiza configurações TCP"""
        if self.platform != 'linux':
            return OptimizationResult(
                success=False,
                message=f"Otimização TCP não suportada no {self.platform}",
                before_value=limit.current_value,
                after_value=None
            )
        
        try:
            # Mapeia nome para arquivo sysctl
            sysctl_map = {
                'tcp_max_syn_backlog': '/proc/sys/net/ipv4/tcp_max_syn_backlog',
                'tcp_keepalive_time': '/proc/sys/net/ipv4/tcp_keepalive_time',
                'tcp_fin_timeout': '/proc/sys/net/ipv4/tcp_fin_timeout'
            }
            
            if name not in sysctl_map:
                return OptimizationResult(
                    success=False,
                    message=f"Configuração TCP desconhecida: {name}",
                    before_value=limit.current_value,
                    after_value=None
                )
            
            sysctl_file = sysctl_map[name]
            
            # Aplica configuração temporária
            if self.is_root:
                with open(sysctl_file, 'w') as f:
                    f.write(str(limit.recommended_value))
                
                # Verifica se foi aplicado
                with open(sysctl_file, 'r') as f:
                    new_value = int(f.read().strip())
                
                # Cria configuração persistente
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=True,
                    message=f"{name} otimizado de {limit.current_value} para {new_value}",
                    before_value=limit.current_value,
                    after_value=new_value
                )
            else:
                # Sem privilégios root, apenas cria configuração
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=False,
                    message=f"Configuração {name} criada, mas requer privilégios root para aplicar",
                    before_value=limit.current_value,
                    after_value=None,
                    requires_restart=True
                )
                
        except Exception as e:
            logger.error(f"Erro ao otimizar {name}: {e}")
            return OptimizationResult(
                success=False,
                message=f"Falha ao otimizar {name}: {e}",
                before_value=limit.current_value,
                after_value=None
            )
    
    async def _optimize_vm_setting(self, name: str, limit: SystemLimit) -> OptimizationResult:
        """Otimiza configurações de VM"""
        if self.platform != 'linux':
            return OptimizationResult(
                success=False,
                message=f"Otimização VM não suportada no {self.platform}",
                before_value=limit.current_value,
                after_value=None
            )
        
        try:
            sysctl_file = f"/proc/sys/{name.replace('_', '/')}"
            
            if self.is_root:
                with open(sysctl_file, 'w') as f:
                    f.write(str(limit.recommended_value))
                
                with open(sysctl_file, 'r') as f:
                    new_value = int(f.read().strip())
                
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=True,
                    message=f"{name} otimizado de {limit.current_value} para {new_value}",
                    before_value=limit.current_value,
                    after_value=new_value
                )
            else:
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=False,
                    message=f"Configuração {name} criada, mas requer privilégios root para aplicar",
                    before_value=limit.current_value,
                    after_value=None,
                    requires_restart=True
                )
                
        except Exception as e:
            logger.error(f"Erro ao otimizar {name}: {e}")
            return OptimizationResult(
                success=False,
                message=f"Falha ao otimizar {name}: {e}",
                before_value=limit.current_value,
                after_value=None
            )
    
    async def _optimize_network_setting(self, name: str, limit: SystemLimit) -> OptimizationResult:
        """Otimiza configurações de rede"""
        if self.platform != 'linux':
            return OptimizationResult(
                success=False,
                message=f"Otimização de rede não suportada no {self.platform}",
                before_value=limit.current_value,
                after_value=None
            )
        
        try:
            # Mapeia nome para arquivo sysctl
            sysctl_map = {
                'net_core_somaxconn': '/proc/sys/net/core/somaxconn',
                'net_core_netdev_max_backlog': '/proc/sys/net/core/netdev_max_backlog'
            }
            
            if name not in sysctl_map:
                return OptimizationResult(
                    success=False,
                    message=f"Configuração de rede desconhecida: {name}",
                    before_value=limit.current_value,
                    after_value=None
                )
            
            sysctl_file = sysctl_map[name]
            
            if self.is_root:
                with open(sysctl_file, 'w') as f:
                    f.write(str(limit.recommended_value))
                
                with open(sysctl_file, 'r') as f:
                    new_value = int(f.read().strip())
                
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=True,
                    message=f"{name} otimizado de {limit.current_value} para {new_value}",
                    before_value=limit.current_value,
                    after_value=new_value
                )
            else:
                await self._create_sysctl_config(name, limit.recommended_value)
                
                return OptimizationResult(
                    success=False,
                    message=f"Configuração {name} criada, mas requer privilégios root para aplicar",
                    before_value=limit.current_value,
                    after_value=None,
                    requires_restart=True
                )
                
        except Exception as e:
            logger.error(f"Erro ao otimizar {name}: {e}")
            return OptimizationResult(
                success=False,
                message=f"Falha ao otimizar {name}: {e}",
                before_value=limit.current_value,
                after_value=None
            )
    
    async def _create_limits_config(self, max_files: int):
        """Cria configuração persistente para limits"""
        try:
            limits_dir = Path("/etc/security/limits.d")
            if limits_dir.exists():
                config_file = limits_dir / "99-websocket-limits.conf"
                config_content = f"""# Configuração de limites para WebSocket
# Gerado automaticamente pelo SystemOptimizer

* soft nofile {max_files}
* hard nofile {max_files}
root soft nofile {max_files}
root hard nofile {max_files}
"""
                with open(config_file, 'w') as f:
                    f.write(config_content)
                
                logger.info(f"Configuração de limits criada em {config_file}")
            else:
                logger.warning("Diretório /etc/security/limits.d não encontrado")
                
        except Exception as e:
            logger.error(f"Erro ao criar configuração de limits: {e}")
    
    async def _create_sysctl_config(self, name: str, value: int):
        """Cria configuração persistente para sysctl"""
        try:
            sysctl_dir = Path("/etc/sysctl.d")
            if sysctl_dir.exists():
                config_file = sysctl_dir / "99-websocket-optimizations.conf"
                
                # Lê configuração existente se houver
                existing_config = ""
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        existing_config = f.read()
                
                # Converte nome para formato sysctl
                sysctl_name = name.replace('_', '.')
                config_line = f"{sysctl_name} = {value}\n"
                
                # Verifica se já existe
                if sysctl_name not in existing_config:
                    if not existing_config:
                        existing_config = "# Otimizações de sistema para WebSocket\n# Gerado automaticamente pelo SystemOptimizer\n\n"
                    
                    existing_config += config_line
                    
                    with open(config_file, 'w') as f:
                        f.write(existing_config)
                    
                    logger.info(f"Configuração sysctl adicionada: {sysctl_name} = {value}")
                
        except Exception as e:
            logger.error(f"Erro ao criar configuração sysctl: {e}")
    
    async def generate_optimization_report(self, limits: Dict[str, SystemLimit], 
                                         results: Dict[str, OptimizationResult]) -> str:
        """Gera relatório de otimização"""
        report = []
        report.append("=" * 80)
        report.append("RELATÓRIO DE OTIMIZAÇÃO DO SISTEMA PARA WEBSOCKET")
        report.append("=" * 80)
        report.append(f"Sistema: {platform.system()} {platform.release()}")
        report.append(f"Privilégios root: {'Sim' if self.is_root else 'Não'}")
        report.append("")
        
        # Seção de diagnóstico
        report.append("DIAGNÓSTICO DE LIMITES:")
        report.append("-" * 40)
        
        critical_issues = []
        for name, limit in limits.items():
            status = "✓" if limit.current_value and limit.current_value >= limit.recommended_value else "⚠"
            if limit.critical:
                status = "❌"
                critical_issues.append(name)
            
            current_str = str(limit.current_value) if limit.current_value else "N/A"
            report.append(f"{status} {limit.name}:")
            report.append(f"    Atual: {current_str}")
            report.append(f"    Recomendado: {limit.recommended_value}")
            report.append(f"    Descrição: {limit.description}")
            report.append("")
        
        # Seção de otimizações aplicadas
        report.append("OTIMIZAÇÕES APLICADAS:")
        report.append("-" * 40)
        
        successful = 0
        failed = 0
        requires_restart = []
        
        for name, result in results.items():
            status = "✓" if result.success else "❌"
            if result.success:
                successful += 1
            else:
                failed += 1
            
            if result.requires_restart:
                requires_restart.append(name)
            
            report.append(f"{status} {name}: {result.message}")
            if result.before_value is not None and result.after_value is not None:
                report.append(f"    {result.before_value} → {result.after_value}")
            report.append("")
        
        # Resumo
        report.append("RESUMO:")
        report.append("-" * 40)
        report.append(f"Otimizações bem-sucedidas: {successful}")
        report.append(f"Otimizações falhadas: {failed}")
        
        if critical_issues:
            report.append(f"Problemas críticos: {', '.join(critical_issues)}")
        
        if requires_restart:
            report.append(f"Requer reinicialização: {', '.join(requires_restart)}")
        
        # Recomendações
        report.append("")
        report.append("RECOMENDAÇÕES:")
        report.append("-" * 40)
        
        if not self.is_root:
            report.append("• Execute como root para aplicar todas as otimizações")
        
        if requires_restart:
            report.append("• Reinicie o sistema para aplicar algumas configurações")
        
        if critical_issues:
            report.append("• Resolva os problemas críticos antes de colocar em produção")
        
        report.append("• Monitore o desempenho após aplicar as otimizações")
        report.append("• Execute este diagnóstico periodicamente")
        
        return "\n".join(report)
    
    async def create_monitoring_script(self) -> str:
        """Cria script de monitoramento de recursos"""
        script_content = '''#!/bin/bash
# Script de monitoramento de recursos para WebSocket
# Gerado automaticamente pelo SystemOptimizer

echo "=== MONITORAMENTO DE RECURSOS WEBSOCKET ==="
echo "Data: $(date)"
echo ""

echo "=== LIMITES DE FILE DESCRIPTORS ==="
echo "Limite atual (soft/hard): $(ulimit -Sn)/$(ulimit -Hn)"
echo "Uso atual: $(lsof | wc -l) file descriptors abertos"
echo ""

echo "=== CONEXÕES DE REDE ==="
echo "Conexões TCP ativas: $(netstat -an | grep ESTABLISHED | wc -l)"
echo "Conexões em LISTEN: $(netstat -an | grep LISTEN | wc -l)"
echo "Conexões WebSocket (porta 8000): $(netstat -an | grep :8000 | wc -l)"
echo ""

echo "=== USO DE MEMÓRIA ==="
free -h
echo ""

echo "=== USO DE CPU ==="
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\\([0-9.]*\\)%* id.*/\\1/" | awk '{print "CPU Usage: " 100 - $1 "%"}'
echo ""

echo "=== CONFIGURAÇÕES SYSCTL ==="
echo "net.core.somaxconn: $(sysctl -n net.core.somaxconn 2>/dev/null || echo 'N/A')"
echo "net.core.netdev_max_backlog: $(sysctl -n net.core.netdev_max_backlog 2>/dev/null || echo 'N/A')"
echo "net.ipv4.tcp_max_syn_backlog: $(sysctl -n net.ipv4.tcp_max_syn_backlog 2>/dev/null || echo 'N/A')"
echo "vm.max_map_count: $(sysctl -n vm.max_map_count 2>/dev/null || echo 'N/A')"
echo ""

echo "=== PROCESSOS WEBSOCKET ==="
ps aux | grep -E "(websocket|uvicorn|fastapi)" | grep -v grep
echo ""
'''
        
        script_path = "backend/monitor_websocket_resources.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Torna executável
        os.chmod(script_path, 0o755)
        
        logger.info(f"Script de monitoramento criado em {script_path}")
        return script_path


# Função utilitária para uso direto
async def optimize_system_for_websocket():
    """Função principal para otimizar sistema para WebSocket"""
    optimizer = SystemOptimizer()
    
    print("Diagnosticando limites do sistema...")
    limits = await optimizer.diagnose_system_limits()
    
    print("Aplicando otimizações...")
    results = await optimizer.apply_optimizations(limits)
    
    print("Gerando relatório...")
    report = await optimizer.generate_optimization_report(limits, results)
    
    # Salva relatório
    report_path = "backend/system_optimization_report.txt"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Relatório salvo em {report_path}")
    print("\n" + report)
    
    # Cria script de monitoramento
    script_path = await optimizer.create_monitoring_script()
    print(f"\nScript de monitoramento criado em {script_path}")
    
    return limits, results


if __name__ == "__main__":
    import asyncio
    asyncio.run(optimize_system_for_websocket())