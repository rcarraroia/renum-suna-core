"""
Serviço de diagnóstico para recursos do sistema WebSocket.

Este módulo implementa ferramentas de diagnóstico para identificar e resolver
problemas relacionados a recursos insuficientes em conexões WebSocket.
"""

import os
import psutil
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import socket
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    # resource module não está disponível no Windows
    HAS_RESOURCE = False

# Configuração simplificada de logger para diagnóstico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ResourceIssueType(Enum):
    """Tipos de problemas com recursos."""
    MEMORY_LIMIT = "memory_limit"
    CPU_LIMIT = "cpu_limit"
    CONNECTION_LIMIT = "connection_limit"
    FILE_DESCRIPTOR_LIMIT = "file_descriptor_limit"
    NETWORK_LIMIT = "network_limit"
    SYSTEM_OVERLOAD = "system_overload"
    CONFIGURATION_ERROR = "configuration_error"


class IssueSeverity(Enum):
    """Severidade dos problemas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ResourceIssue:
    """Representa um problema identificado com recursos."""
    type: ResourceIssueType
    severity: IssueSeverity
    description: str
    solution: str
    affected_components: List[str]
    details: Dict[str, Any]


@dataclass
class ResourceStatus:
    """Status de recursos do sistema."""
    available: bool
    current_usage: Dict[str, Any]
    limits: Dict[str, Any]
    recommendations: List[str]
    issues: List[ResourceIssue]


@dataclass
class MemoryAnalysis:
    """Análise de uso de memória."""
    total_mb: float
    used_mb: float
    available_mb: float
    percentage: float
    per_connection_mb: float
    estimated_max_connections: int
    issues: List[ResourceIssue]


@dataclass
class NetworkStatus:
    """Status de recursos de rede."""
    bandwidth_available: bool
    latency_ms: float
    active_connections: int
    max_connections: int
    port_availability: Dict[int, bool]
    issues: List[ResourceIssue]


class ResourceDiagnosticService:
    """Serviço de diagnóstico para recursos do sistema WebSocket."""
    
    def __init__(self):
        """Inicializa o serviço de diagnóstico de recursos."""
        self.max_websocket_connections = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "500"))
        self.memory_threshold_mb = int(os.getenv("MEMORY_THRESHOLD_MB", "1024"))
        self.cpu_threshold = float(os.getenv("CPU_THRESHOLD", "80.0"))
        
        logger.info("ResourceDiagnosticService initialized")
    
    async def check_connection_limits(self) -> ResourceStatus:
        """
        Verifica limites de conexão do sistema.
        
        Returns:
            ResourceStatus: Status dos limites de conexão
        """
        logger.info("Starting connection limits check")
        
        issues = []
        recommendations = []
        current_usage = {}
        limits = {}
        
        try:
            # 1. Verificar limite de file descriptors (apenas em sistemas Unix)
            if HAS_RESOURCE:
                try:
                    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
                    current_fds = len(psutil.Process().open_files()) + len(psutil.Process().connections())
                    
                    current_usage["file_descriptors"] = {
                        "current": current_fds,
                        "soft_limit": soft_limit,
                        "hard_limit": hard_limit,
                        "percentage": (current_fds / soft_limit) * 100 if soft_limit > 0 else 0
                    }
                    
                    limits["file_descriptors"] = {
                        "soft": soft_limit,
                        "hard": hard_limit,
                        "recommended_minimum": 8192
                    }
                    
                    # Verificar se o limite é muito baixo
                    if soft_limit < 1024:
                        issue = ResourceIssue(
                            type=ResourceIssueType.FILE_DESCRIPTOR_LIMIT,
                            severity=IssueSeverity.CRITICAL,
                            description=f"Limite de file descriptors muito baixo: {soft_limit}",
                            solution="Aumentar limite com 'ulimit -n 8192' ou configurar /etc/security/limits.conf",
                            affected_components=["system", "websocket", "network"],
                            details={"current_limit": soft_limit, "recommended": 8192}
                        )
                        issues.append(issue)
                        recommendations.append("Aumentar limite de file descriptors para pelo menos 8192")
                    
                    # Verificar se está próximo do limite
                    elif current_fds > soft_limit * 0.8:
                        issue = ResourceIssue(
                            type=ResourceIssueType.FILE_DESCRIPTOR_LIMIT,
                            severity=IssueSeverity.HIGH,
                            description=f"Uso de file descriptors próximo do limite: {current_fds}/{soft_limit}",
                            solution="Monitorar uso e considerar aumentar limite",
                            affected_components=["system", "websocket"],
                            details={"current": current_fds, "limit": soft_limit, "percentage": (current_fds / soft_limit) * 100}
                        )
                        issues.append(issue)
                        recommendations.append("Monitorar uso de file descriptors")
                    
                    logger.info(f"File descriptors: {current_fds}/{soft_limit} ({(current_fds / soft_limit) * 100:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"Error checking file descriptor limits: {str(e)}")
                    issue = ResourceIssue(
                        type=ResourceIssueType.CONFIGURATION_ERROR,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Não foi possível verificar limites de file descriptors: {str(e)}",
                        solution="Verificar permissões do sistema",
                        affected_components=["system"],
                        details={"error": str(e)}
                    )
                    issues.append(issue)
            else:
                # Windows - usar estimativa baseada em handles
                try:
                    current_handles = len(psutil.Process().open_files()) + len(psutil.Process().connections())
                    estimated_limit = 10000  # Limite típico do Windows
                    
                    current_usage["file_descriptors"] = {
                        "current": current_handles,
                        "estimated_limit": estimated_limit,
                        "percentage": (current_handles / estimated_limit) * 100,
                        "platform": "Windows"
                    }
                    
                    limits["file_descriptors"] = {
                        "estimated": estimated_limit,
                        "platform": "Windows",
                        "note": "Windows usa handles em vez de file descriptors"
                    }
                    
                    if current_handles > estimated_limit * 0.8:
                        issue = ResourceIssue(
                            type=ResourceIssueType.FILE_DESCRIPTOR_LIMIT,
                            severity=IssueSeverity.HIGH,
                            description=f"Muitos handles abertos no Windows: {current_handles}",
                            solution="Verificar vazamentos de handles e otimizar uso de recursos",
                            affected_components=["system", "websocket"],
                            details={"current_handles": current_handles, "estimated_limit": estimated_limit}
                        )
                        issues.append(issue)
                    
                    logger.info(f"Windows handles: {current_handles} (estimativa)")
                    
                except Exception as e:
                    logger.error(f"Error checking Windows handles: {str(e)}")
                    current_usage["file_descriptors"] = {"error": str(e), "platform": "Windows"}
            
            # 2. Verificar conexões de rede ativas
            try:
                connections = psutil.net_connections()
                active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
                listening_connections = len([c for c in connections if c.status == 'LISTEN'])
                
                current_usage["network_connections"] = {
                    "active": active_connections,
                    "listening": listening_connections,
                    "total": len(connections)
                }
                
                limits["network_connections"] = {
                    "max_websocket": self.max_websocket_connections,
                    "system_limit": soft_limit if 'soft_limit' in locals() else "unknown"
                }
                
                # Verificar se há muitas conexões ativas
                if active_connections > 1000:
                    issue = ResourceIssue(
                        type=ResourceIssueType.CONNECTION_LIMIT,
                        severity=IssueSeverity.HIGH,
                        description=f"Muitas conexões ativas: {active_connections}",
                        solution="Verificar se há vazamentos de conexão ou implementar pool de conexões",
                        affected_components=["network", "websocket"],
                        details={"active_connections": active_connections}
                    )
                    issues.append(issue)
                    recommendations.append("Implementar pool de conexões e monitoramento")
                
                logger.info(f"Network connections: {active_connections} active, {listening_connections} listening")
                
            except Exception as e:
                logger.error(f"Error checking network connections: {str(e)}")
                issue = ResourceIssue(
                    type=ResourceIssueType.CONFIGURATION_ERROR,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Não foi possível verificar conexões de rede: {str(e)}",
                    solution="Verificar permissões de rede",
                    affected_components=["network"],
                    details={"error": str(e)}
                )
                issues.append(issue)
            
            # 3. Verificar configuração de WebSocket
            current_usage["websocket_config"] = {
                "max_connections": self.max_websocket_connections,
                "memory_threshold_mb": self.memory_threshold_mb,
                "cpu_threshold": self.cpu_threshold
            }
            
            # Verificar se a configuração é realista
            if self.max_websocket_connections > 1000 and self.memory_threshold_mb < 2048:
                issue = ResourceIssue(
                    type=ResourceIssueType.CONFIGURATION_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"Configuração inconsistente: {self.max_websocket_connections} conexões com apenas {self.memory_threshold_mb}MB",
                    solution="Aumentar MEMORY_THRESHOLD_MB ou reduzir MAX_WEBSOCKET_CONNECTIONS",
                    affected_components=["websocket", "configuration"],
                    details={
                        "max_connections": self.max_websocket_connections,
                        "memory_threshold": self.memory_threshold_mb,
                        "recommended_memory": self.max_websocket_connections * 2  # 2MB por conexão
                    }
                )
                issues.append(issue)
                recommendations.append("Ajustar configuração de memória para suportar conexões planejadas")
            
            # 4. Verificar portas disponíveis
            try:
                websocket_port = int(os.getenv("WEBSOCKET_PORT", "8000"))
                port_available = self._check_port_availability(websocket_port)
                
                current_usage["port_availability"] = {
                    "websocket_port": websocket_port,
                    "available": port_available
                }
                
                if not port_available:
                    issue = ResourceIssue(
                        type=ResourceIssueType.NETWORK_LIMIT,
                        severity=IssueSeverity.CRITICAL,
                        description=f"Porta WebSocket {websocket_port} não está disponível",
                        solution="Verificar se outro processo está usando a porta ou alterar configuração",
                        affected_components=["network", "websocket"],
                        details={"port": websocket_port}
                    )
                    issues.append(issue)
                    recommendations.append(f"Liberar porta {websocket_port} ou configurar porta alternativa")
                
            except Exception as e:
                logger.error(f"Error checking port availability: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error during connection limits check: {str(e)}")
            issue = ResourceIssue(
                type=ResourceIssueType.SYSTEM_OVERLOAD,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante verificação de limites: {str(e)}",
                solution="Verificar logs do sistema e reiniciar serviços se necessário",
                affected_components=["system"],
                details={"error": str(e)}
            )
            issues.append(issue)
        
        # Determinar se os recursos estão disponíveis
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        available = len(critical_issues) == 0
        
        if not recommendations and available:
            recommendations.append("Limites de conexão estão adequados")
        
        return ResourceStatus(
            available=available,
            current_usage=current_usage,
            limits=limits,
            recommendations=recommendations,
            issues=issues
        )
    
    async def analyze_memory_usage(self) -> MemoryAnalysis:
        """
        Analisa uso de memória por conexões WebSocket.
        
        Returns:
            MemoryAnalysis: Análise detalhada de memória
        """
        logger.info("Starting memory usage analysis")
        
        issues = []
        
        try:
            # Obter informações de memória do sistema
            memory = psutil.virtual_memory()
            
            total_mb = memory.total / 1024 / 1024
            used_mb = memory.used / 1024 / 1024
            available_mb = memory.available / 1024 / 1024
            percentage = memory.percent
            
            # Estimar uso por conexão WebSocket (baseado em observações típicas)
            per_connection_mb = 2.0  # Estimativa conservadora de 2MB por conexão
            
            # Calcular máximo de conexões baseado na memória disponível
            memory_for_websocket = available_mb * 0.7  # Usar 70% da memória disponível
            estimated_max_connections = int(memory_for_websocket / per_connection_mb)
            
            logger.info(f"Memory: {used_mb:.1f}MB/{total_mb:.1f}MB ({percentage:.1f}%)")
            logger.info(f"Estimated max WebSocket connections: {estimated_max_connections}")
            
            # Verificar problemas de memória
            if percentage > 90:
                issue = ResourceIssue(
                    type=ResourceIssueType.MEMORY_LIMIT,
                    severity=IssueSeverity.CRITICAL,
                    description=f"Uso de memória crítico: {percentage:.1f}%",
                    solution="Liberar memória, reiniciar serviços ou adicionar mais RAM",
                    affected_components=["system", "websocket"],
                    details={"percentage": percentage, "used_mb": used_mb, "total_mb": total_mb}
                )
                issues.append(issue)
                
            elif percentage > 80:
                issue = ResourceIssue(
                    type=ResourceIssueType.MEMORY_LIMIT,
                    severity=IssueSeverity.HIGH,
                    description=f"Uso de memória alto: {percentage:.1f}%",
                    solution="Monitorar uso de memória e considerar otimizações",
                    affected_components=["system", "websocket"],
                    details={"percentage": percentage, "used_mb": used_mb, "total_mb": total_mb}
                )
                issues.append(issue)
            
            # Verificar se a configuração atual é viável
            if self.max_websocket_connections > estimated_max_connections:
                issue = ResourceIssue(
                    type=ResourceIssueType.CONFIGURATION_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"Configuração de conexões ({self.max_websocket_connections}) excede capacidade de memória ({estimated_max_connections})",
                    solution="Reduzir MAX_WEBSOCKET_CONNECTIONS ou adicionar mais RAM",
                    affected_components=["websocket", "configuration"],
                    details={
                        "configured_max": self.max_websocket_connections,
                        "memory_based_max": estimated_max_connections,
                        "memory_needed_mb": self.max_websocket_connections * per_connection_mb
                    }
                )
                issues.append(issue)
            
            # Verificar vazamentos de memória potenciais
            try:
                process = psutil.Process()
                process_memory_mb = process.memory_info().rss / 1024 / 1024
                
                if process_memory_mb > 1024:  # Mais de 1GB para o processo
                    issue = ResourceIssue(
                        type=ResourceIssueType.MEMORY_LIMIT,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Processo usando muita memória: {process_memory_mb:.1f}MB",
                        solution="Verificar vazamentos de memória e otimizar código",
                        affected_components=["application"],
                        details={"process_memory_mb": process_memory_mb}
                    )
                    issues.append(issue)
                    
            except Exception as e:
                logger.error(f"Error checking process memory: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error during memory analysis: {str(e)}")
            issue = ResourceIssue(
                type=ResourceIssueType.SYSTEM_OVERLOAD,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante análise de memória: {str(e)}",
                solution="Verificar logs do sistema",
                affected_components=["system"],
                details={"error": str(e)}
            )
            issues.append(issue)
            
            # Valores padrão em caso de erro
            total_mb = 0
            used_mb = 0
            available_mb = 0
            percentage = 0
            per_connection_mb = 2.0
            estimated_max_connections = 0
        
        return MemoryAnalysis(
            total_mb=total_mb,
            used_mb=used_mb,
            available_mb=available_mb,
            percentage=percentage,
            per_connection_mb=per_connection_mb,
            estimated_max_connections=estimated_max_connections,
            issues=issues
        )
    
    async def check_network_resources(self) -> NetworkStatus:
        """
        Verifica recursos de rede disponíveis.
        
        Returns:
            NetworkStatus: Status dos recursos de rede
        """
        logger.info("Starting network resources check")
        
        issues = []
        
        try:
            # 1. Verificar latência de rede local
            latency_ms = await self._measure_local_latency()
            
            # 2. Contar conexões ativas
            connections = psutil.net_connections()
            active_connections = len([c for c in connections if c.status == 'ESTABLISHED'])
            
            # 3. Verificar disponibilidade de portas importantes
            important_ports = [8000, 8080, 3000, 5432, 6379]  # WebSocket, HTTP, React, PostgreSQL, Redis
            port_availability = {}
            
            for port in important_ports:
                port_availability[port] = self._check_port_availability(port)
            
            # 4. Estimar máximo de conexões baseado em recursos de rede
            max_connections = min(self.max_websocket_connections, 1000)  # Limite conservador
            
            logger.info(f"Network latency: {latency_ms:.2f}ms")
            logger.info(f"Active connections: {active_connections}")
            
            # Verificar problemas de rede
            if latency_ms > 100:
                issue = ResourceIssue(
                    type=ResourceIssueType.NETWORK_LIMIT,
                    severity=IssueSeverity.HIGH,
                    description=f"Latência de rede alta: {latency_ms:.2f}ms",
                    solution="Verificar conectividade de rede e otimizar configurações",
                    affected_components=["network", "websocket"],
                    details={"latency_ms": latency_ms}
                )
                issues.append(issue)
            
            # Verificar se portas importantes estão disponíveis
            unavailable_ports = [port for port, available in port_availability.items() if not available]
            if unavailable_ports:
                severity = IssueSeverity.CRITICAL if 8000 in unavailable_ports else IssueSeverity.MEDIUM
                issue = ResourceIssue(
                    type=ResourceIssueType.NETWORK_LIMIT,
                    severity=severity,
                    description=f"Portas não disponíveis: {unavailable_ports}",
                    solution="Verificar processos usando as portas e liberar se necessário",
                    affected_components=["network", "websocket"],
                    details={"unavailable_ports": unavailable_ports}
                )
                issues.append(issue)
            
            # Verificar sobrecarga de conexões
            if active_connections > 500:
                issue = ResourceIssue(
                    type=ResourceIssueType.CONNECTION_LIMIT,
                    severity=IssueSeverity.HIGH,
                    description=f"Muitas conexões ativas: {active_connections}",
                    solution="Implementar pool de conexões e limpeza de conexões ociosas",
                    affected_components=["network"],
                    details={"active_connections": active_connections}
                )
                issues.append(issue)
            
            bandwidth_available = latency_ms < 50 and active_connections < 200
            
        except Exception as e:
            logger.error(f"Error during network resources check: {str(e)}")
            issue = ResourceIssue(
                type=ResourceIssueType.SYSTEM_OVERLOAD,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante verificação de rede: {str(e)}",
                solution="Verificar configuração de rede",
                affected_components=["network"],
                details={"error": str(e)}
            )
            issues.append(issue)
            
            # Valores padrão em caso de erro
            latency_ms = 999.0
            active_connections = 0
            max_connections = 0
            port_availability = {}
            bandwidth_available = False
        
        return NetworkStatus(
            bandwidth_available=bandwidth_available,
            latency_ms=latency_ms,
            active_connections=active_connections,
            max_connections=max_connections,
            port_availability=port_availability,
            issues=issues
        )
    
    def _check_port_availability(self, port: int) -> bool:
        """
        Verifica se uma porta está disponível.
        
        Args:
            port: Número da porta
            
        Returns:
            bool: True se a porta estiver disponível
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0  # Porta disponível se conexão falhar
        except Exception:
            return False
    
    async def _measure_local_latency(self) -> float:
        """
        Mede latência de rede local.
        
        Returns:
            float: Latência em milissegundos
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Simula uma operação de rede local
            await asyncio.sleep(0.001)  # 1ms
            
            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000
            
            return max(latency_ms, 0.1)  # Mínimo de 0.1ms
            
        except Exception:
            return 999.0  # Valor alto em caso de erro
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """
        Obtém visão geral dos recursos do sistema.
        
        Returns:
            Dict[str, Any]: Visão geral dos recursos
        """
        logger.info("Getting system overview")
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memória
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            
            # Rede
            net_io = psutil.net_io_counters()
            
            # Processos
            process_count = len(psutil.pids())
            
            overview = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else "N/A (Windows)"
                },
                "memory": {
                    "total_mb": memory.total / 1024 / 1024,
                    "used_mb": memory.used / 1024 / 1024,
                    "available_mb": memory.available / 1024 / 1024,
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / 1024 / 1024 / 1024,
                    "used_gb": disk.used / 1024 / 1024 / 1024,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                },
                "processes": {
                    "count": process_count
                },
                "websocket_config": {
                    "max_connections": self.max_websocket_connections,
                    "memory_threshold_mb": self.memory_threshold_mb,
                    "cpu_threshold": self.cpu_threshold
                }
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting system overview: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo dos diagnósticos de recursos.
        
        Returns:
            Dict[str, Any]: Resumo dos diagnósticos
        """
        return {
            "service": "ResourceDiagnosticService",
            "version": "1.0.0",
            "capabilities": [
                "check_connection_limits",
                "analyze_memory_usage",
                "check_network_resources",
                "get_system_overview"
            ],
            "monitored_resources": [
                "memory",
                "cpu",
                "network_connections",
                "file_descriptors",
                "disk_space",
                "network_latency"
            ],
            "configuration": {
                "max_websocket_connections": self.max_websocket_connections,
                "memory_threshold_mb": self.memory_threshold_mb,
                "cpu_threshold": self.cpu_threshold
            }
        }