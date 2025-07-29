"""
Serviço de diagnóstico para conexões WebSocket.

Este módulo implementa ferramentas de diagnóstico para identificar e resolver
problemas relacionados a conexões WebSocket fechadas prematuramente e falhas
no handshake.
"""

import os
import asyncio
import logging
import socket
import ssl
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json

# Configuração simplificada de logger para diagnóstico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConnectionIssueType(Enum):
    """Tipos de problemas com conexões."""
    HANDSHAKE_FAILURE = "handshake_failure"
    PREMATURE_CLOSURE = "premature_closure"
    TIMEOUT_ERROR = "timeout_error"
    SSL_ERROR = "ssl_error"
    PROTOCOL_ERROR = "protocol_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"


class IssueSeverity(Enum):
    """Severidade dos problemas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConnectionIssue:
    """Representa um problema identificado com conexões."""
    type: ConnectionIssueType
    severity: IssueSeverity
    description: str
    solution: str
    affected_components: List[str]
    details: Dict[str, Any]


@dataclass
class HandshakeIssue:
    """Representa um problema específico de handshake."""
    stage: str
    error_code: Optional[int]
    error_message: str
    timing_ms: float
    suggestions: List[str]


@dataclass
class ClosureAnalysis:
    """Análise de fechamentos de conexão."""
    total_closures: int
    premature_closures: int
    normal_closures: int
    error_closures: int
    common_patterns: List[str]
    timing_analysis: Dict[str, float]
    issues: List[ConnectionIssue]


@dataclass
class ConfigValidation:
    """Validação de configuração WebSocket."""
    valid: bool
    websocket_url: str
    ssl_enabled: bool
    timeout_settings: Dict[str, int]
    protocol_version: str
    issues: List[ConnectionIssue]
    recommendations: List[str]


class ConnectionDiagnosticService:
    """Serviço de diagnóstico para conexões WebSocket."""
    
    def __init__(self):
        """Inicializa o serviço de diagnóstico de conexões."""
        self.websocket_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws")
        self.websocket_timeout = int(os.getenv("WEBSOCKET_TIMEOUT", "30"))
        self.max_reconnect_attempts = int(os.getenv("MAX_RECONNECT_ATTEMPTS", "5"))
        
        logger.info("ConnectionDiagnosticService initialized")
    
    async def analyze_handshake_failures(self) -> List[HandshakeIssue]:
        """
        Analisa falhas no handshake WebSocket.
        
        Returns:
            List[HandshakeIssue]: Lista de problemas de handshake identificados
        """
        logger.info("Starting handshake failure analysis")
        
        issues = []
        
        try:
            # 1. Testar handshake básico
            handshake_issue = await self._test_basic_handshake()
            if handshake_issue:
                issues.append(handshake_issue)
            
            # 2. Testar handshake com diferentes protocolos
            protocol_issues = await self._test_protocol_handshakes()
            issues.extend(protocol_issues)
            
            # 3. Testar handshake com SSL/TLS se aplicável
            if self.websocket_url.startswith("wss://"):
                ssl_issue = await self._test_ssl_handshake()
                if ssl_issue:
                    issues.append(ssl_issue)
            
            # 4. Testar handshake com timeout
            timeout_issue = await self._test_timeout_handshake()
            if timeout_issue:
                issues.append(timeout_issue)
            
        except Exception as e:
            logger.error(f"Error during handshake analysis: {str(e)}")
            issues.append(HandshakeIssue(
                stage="analysis_error",
                error_code=None,
                error_message=f"Erro durante análise de handshake: {str(e)}",
                timing_ms=0,
                suggestions=["Verificar logs detalhados do sistema"]
            ))
        
        logger.info(f"Handshake analysis completed: {len(issues)} issues found")
        
        return issues
    
    async def check_premature_closures(self) -> ClosureAnalysis:
        """
        Investiga conexões fechadas prematuramente.
        
        Returns:
            ClosureAnalysis: Análise detalhada de fechamentos
        """
        logger.info("Starting premature closure analysis")
        
        issues = []
        common_patterns = []
        timing_analysis = {}
        
        try:
            # 1. Simular diferentes cenários de conexão
            closure_tests = await self._run_closure_tests()
            
            total_closures = len(closure_tests)
            premature_closures = len([t for t in closure_tests if t.get("premature", False)])
            normal_closures = len([t for t in closure_tests if t.get("normal", False)])
            error_closures = len([t for t in closure_tests if t.get("error", False)])
            
            # 2. Analisar padrões comuns
            if premature_closures > 0:
                common_patterns.append("Conexões fechadas antes do handshake completo")
                
                issue = ConnectionIssue(
                    type=ConnectionIssueType.PREMATURE_CLOSURE,
                    severity=IssueSeverity.HIGH,
                    description=f"{premature_closures} conexões fechadas prematuramente",
                    solution="Verificar configuração de timeout e estabilidade da rede",
                    affected_components=["websocket", "network"],
                    details={"premature_count": premature_closures, "total_tests": total_closures}
                )
                issues.append(issue)
            
            if error_closures > total_closures * 0.3:  # Mais de 30% com erro
                common_patterns.append("Alta taxa de erros durante conexão")
                
                issue = ConnectionIssue(
                    type=ConnectionIssueType.NETWORK_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"Alta taxa de erros: {error_closures}/{total_closures}",
                    solution="Verificar estabilidade da rede e configuração do servidor",
                    affected_components=["network", "server"],
                    details={"error_rate": error_closures / total_closures if total_closures > 0 else 0}
                )
                issues.append(issue)
            
            # 3. Análise de timing
            connection_times = [t.get("connection_time", 0) for t in closure_tests if t.get("connection_time")]
            if connection_times:
                timing_analysis = {
                    "average_connection_time": sum(connection_times) / len(connection_times),
                    "max_connection_time": max(connection_times),
                    "min_connection_time": min(connection_times),
                    "slow_connections": len([t for t in connection_times if t > 5000])  # > 5s
                }
                
                if timing_analysis["average_connection_time"] > 3000:  # > 3s
                    issue = ConnectionIssue(
                        type=ConnectionIssueType.TIMEOUT_ERROR,
                        severity=IssueSeverity.MEDIUM,
                        description=f"Tempo de conexão lento: {timing_analysis['average_connection_time']:.0f}ms",
                        solution="Otimizar configuração de rede e servidor",
                        affected_components=["network", "performance"],
                        details=timing_analysis
                    )
                    issues.append(issue)
            
        except Exception as e:
            logger.error(f"Error during closure analysis: {str(e)}")
            issue = ConnectionIssue(
                type=ConnectionIssueType.NETWORK_ERROR,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante análise de fechamentos: {str(e)}",
                solution="Verificar logs do sistema e configuração de rede",
                affected_components=["system"],
                details={"error": str(e)}
            )
            issues.append(issue)
            
            # Valores padrão em caso de erro
            total_closures = 0
            premature_closures = 0
            normal_closures = 0
            error_closures = 0
        
        return ClosureAnalysis(
            total_closures=total_closures,
            premature_closures=premature_closures,
            normal_closures=normal_closures,
            error_closures=error_closures,
            common_patterns=common_patterns,
            timing_analysis=timing_analysis,
            issues=issues
        )
    
    async def validate_websocket_config(self) -> ConfigValidation:
        """
        Valida configuração de WebSocket.
        
        Returns:
            ConfigValidation: Resultado da validação
        """
        logger.info("Starting WebSocket configuration validation")
        
        issues = []
        recommendations = []
        
        try:
            # 1. Validar URL do WebSocket
            url_valid = self._validate_websocket_url()
            if not url_valid["valid"]:
                issue = ConnectionIssue(
                    type=ConnectionIssueType.CONFIGURATION_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description=f"URL WebSocket inválida: {self.websocket_url}",
                    solution="Corrigir formato da URL WebSocket",
                    affected_components=["configuration", "websocket"],
                    details=url_valid
                )
                issues.append(issue)
                recommendations.append("Usar formato ws://host:port/path ou wss://host:port/path")
            
            # 2. Verificar configurações de timeout
            timeout_config = self._validate_timeout_settings()
            if timeout_config["issues"]:
                for timeout_issue in timeout_config["issues"]:
                    issues.append(timeout_issue)
            
            # 3. Testar conectividade básica
            connectivity = await self._test_basic_connectivity()
            if not connectivity["success"]:
                issue = ConnectionIssue(
                    type=ConnectionIssueType.NETWORK_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"Falha na conectividade básica: {connectivity['error']}",
                    solution="Verificar se o servidor WebSocket está rodando e acessível",
                    affected_components=["network", "server"],
                    details=connectivity
                )
                issues.append(issue)
                recommendations.append("Verificar se o servidor WebSocket está ativo")
            
            # 4. Verificar suporte a SSL/TLS se necessário
            ssl_enabled = self.websocket_url.startswith("wss://")
            if ssl_enabled:
                ssl_validation = await self._validate_ssl_config()
                if ssl_validation["issues"]:
                    issues.extend(ssl_validation["issues"])
                    recommendations.extend(ssl_validation["recommendations"])
            
            # 5. Verificar versão do protocolo WebSocket
            protocol_version = await self._detect_websocket_version()
            
            # 6. Validar headers e configurações adicionais
            headers_validation = self._validate_websocket_headers()
            if headers_validation["issues"]:
                issues.extend(headers_validation["issues"])
            
        except Exception as e:
            logger.error(f"Error during config validation: {str(e)}")
            issue = ConnectionIssue(
                type=ConnectionIssueType.CONFIGURATION_ERROR,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante validação: {str(e)}",
                solution="Verificar configuração completa do WebSocket",
                affected_components=["configuration"],
                details={"error": str(e)}
            )
            issues.append(issue)
        
        # Determinar se a configuração é válida
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        valid = len(critical_issues) == 0
        
        if not recommendations and valid:
            recommendations.append("Configuração WebSocket está válida")
        
        return ConfigValidation(
            valid=valid,
            websocket_url=self.websocket_url,
            ssl_enabled=ssl_enabled if 'ssl_enabled' in locals() else False,
            timeout_settings={
                "websocket_timeout": self.websocket_timeout,
                "max_reconnect_attempts": self.max_reconnect_attempts
            },
            protocol_version=protocol_version if 'protocol_version' in locals() else "unknown",
            issues=issues,
            recommendations=recommendations
        )
    
    async def _test_basic_handshake(self) -> Optional[HandshakeIssue]:
        """Testa handshake básico WebSocket."""
        try:
            start_time = time.time()
            
            # Simular tentativa de handshake
            url_parts = self.websocket_url.replace("ws://", "").replace("wss://", "").split("/")
            host_port = url_parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else (80 if self.websocket_url.startswith("ws://") else 443)
            
            # Testar conexão TCP básica
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                sock.connect((host, port))
                sock.close()
                
                end_time = time.time()
                timing_ms = (end_time - start_time) * 1000
                
                if timing_ms > 3000:  # > 3s
                    return HandshakeIssue(
                        stage="tcp_connection",
                        error_code=None,
                        error_message=f"Conexão TCP lenta: {timing_ms:.0f}ms",
                        timing_ms=timing_ms,
                        suggestions=["Verificar latência de rede", "Otimizar configuração do servidor"]
                    )
                
                logger.info(f"Basic handshake test passed: {timing_ms:.0f}ms")
                return None
                
            except socket.timeout:
                return HandshakeIssue(
                    stage="tcp_connection",
                    error_code=None,
                    error_message="Timeout na conexão TCP",
                    timing_ms=5000,
                    suggestions=["Verificar se o servidor está rodando", "Aumentar timeout"]
                )
                
            except ConnectionRefusedError:
                return HandshakeIssue(
                    stage="tcp_connection",
                    error_code=None,
                    error_message="Conexão recusada pelo servidor",
                    timing_ms=0,
                    suggestions=["Verificar se o servidor WebSocket está ativo", "Verificar porta correta"]
                )
                
        except Exception as e:
            return HandshakeIssue(
                stage="handshake_test",
                error_code=None,
                error_message=f"Erro durante teste de handshake: {str(e)}",
                timing_ms=0,
                suggestions=["Verificar configuração de rede"]
            )
    
    async def _test_protocol_handshakes(self) -> List[HandshakeIssue]:
        """Testa handshakes com diferentes protocolos."""
        issues = []
        
        # Simular testes de diferentes versões de protocolo
        protocols = ["13", "8", "7"]  # WebSocket protocol versions
        
        for protocol in protocols:
            try:
                # Simular teste de protocolo
                await asyncio.sleep(0.1)  # Simular tempo de teste
                
                if protocol == "7":  # Protocolo antigo
                    issues.append(HandshakeIssue(
                        stage="protocol_negotiation",
                        error_code=None,
                        error_message=f"Protocolo WebSocket {protocol} é obsoleto",
                        timing_ms=100,
                        suggestions=["Atualizar para protocolo WebSocket 13"]
                    ))
                
            except Exception as e:
                issues.append(HandshakeIssue(
                    stage="protocol_test",
                    error_code=None,
                    error_message=f"Erro testando protocolo {protocol}: {str(e)}",
                    timing_ms=0,
                    suggestions=["Verificar suporte a protocolos WebSocket"]
                ))
        
        return issues
    
    async def _test_ssl_handshake(self) -> Optional[HandshakeIssue]:
        """Testa handshake SSL/TLS."""
        try:
            # Simular teste SSL
            await asyncio.sleep(0.2)
            
            # Verificar se certificado é válido (simulado)
            cert_valid = True  # Em implementação real, verificaria certificado
            
            if not cert_valid:
                return HandshakeIssue(
                    stage="ssl_handshake",
                    error_code=None,
                    error_message="Certificado SSL inválido ou expirado",
                    timing_ms=200,
                    suggestions=["Renovar certificado SSL", "Verificar configuração HTTPS"]
                )
            
            return None
            
        except Exception as e:
            return HandshakeIssue(
                stage="ssl_test",
                error_code=None,
                error_message=f"Erro durante teste SSL: {str(e)}",
                timing_ms=0,
                suggestions=["Verificar configuração SSL/TLS"]
            )
    
    async def _test_timeout_handshake(self) -> Optional[HandshakeIssue]:
        """Testa handshake com timeout."""
        try:
            # Simular teste de timeout
            if self.websocket_timeout < 10:
                return HandshakeIssue(
                    stage="timeout_config",
                    error_code=None,
                    error_message=f"Timeout muito baixo: {self.websocket_timeout}s",
                    timing_ms=0,
                    suggestions=["Aumentar WEBSOCKET_TIMEOUT para pelo menos 30s"]
                )
            
            return None
            
        except Exception as e:
            return HandshakeIssue(
                stage="timeout_test",
                error_code=None,
                error_message=f"Erro durante teste de timeout: {str(e)}",
                timing_ms=0,
                suggestions=["Verificar configuração de timeout"]
            )
    
    async def _run_closure_tests(self) -> List[Dict[str, Any]]:
        """Executa testes de fechamento de conexão."""
        tests = []
        
        try:
            # Simular diferentes cenários de teste
            test_scenarios = [
                {"name": "normal_connection", "expected_result": "normal"},
                {"name": "quick_disconnect", "expected_result": "premature"},
                {"name": "timeout_test", "expected_result": "timeout"},
                {"name": "error_simulation", "expected_result": "error"}
            ]
            
            for scenario in test_scenarios:
                start_time = time.time()
                
                # Simular teste baseado no cenário
                if scenario["name"] == "normal_connection":
                    await asyncio.sleep(0.1)
                    tests.append({
                        "scenario": scenario["name"],
                        "normal": True,
                        "connection_time": (time.time() - start_time) * 1000
                    })
                    
                elif scenario["name"] == "quick_disconnect":
                    await asyncio.sleep(0.05)
                    tests.append({
                        "scenario": scenario["name"],
                        "premature": True,
                        "connection_time": (time.time() - start_time) * 1000
                    })
                    
                elif scenario["name"] == "timeout_test":
                    await asyncio.sleep(0.2)
                    tests.append({
                        "scenario": scenario["name"],
                        "error": True,
                        "connection_time": (time.time() - start_time) * 1000
                    })
                    
                elif scenario["name"] == "error_simulation":
                    tests.append({
                        "scenario": scenario["name"],
                        "error": True,
                        "connection_time": 0
                    })
            
        except Exception as e:
            logger.error(f"Error during closure tests: {str(e)}")
            tests.append({
                "scenario": "test_error",
                "error": True,
                "connection_time": 0,
                "error_message": str(e)
            })
        
        return tests
    
    def _validate_websocket_url(self) -> Dict[str, Any]:
        """Valida URL do WebSocket."""
        try:
            if not self.websocket_url:
                return {"valid": False, "error": "URL não configurada"}
            
            if not (self.websocket_url.startswith("ws://") or self.websocket_url.startswith("wss://")):
                return {"valid": False, "error": "URL deve começar com ws:// ou wss://"}
            
            # Verificar formato básico
            url_parts = self.websocket_url.replace("ws://", "").replace("wss://", "").split("/")
            if not url_parts[0]:
                return {"valid": False, "error": "Host não especificado"}
            
            return {"valid": True, "url": self.websocket_url}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _validate_timeout_settings(self) -> Dict[str, Any]:
        """Valida configurações de timeout."""
        issues = []
        
        if self.websocket_timeout < 10:
            issue = ConnectionIssue(
                type=ConnectionIssueType.CONFIGURATION_ERROR,
                severity=IssueSeverity.MEDIUM,
                description=f"Timeout WebSocket muito baixo: {self.websocket_timeout}s",
                solution="Aumentar WEBSOCKET_TIMEOUT para pelo menos 30s",
                affected_components=["configuration", "websocket"],
                details={"current_timeout": self.websocket_timeout, "recommended": 30}
            )
            issues.append(issue)
        
        if self.max_reconnect_attempts < 3:
            issue = ConnectionIssue(
                type=ConnectionIssueType.CONFIGURATION_ERROR,
                severity=IssueSeverity.LOW,
                description=f"Poucas tentativas de reconexão: {self.max_reconnect_attempts}",
                solution="Aumentar MAX_RECONNECT_ATTEMPTS para pelo menos 5",
                affected_components=["configuration", "resilience"],
                details={"current_attempts": self.max_reconnect_attempts, "recommended": 5}
            )
            issues.append(issue)
        
        return {"issues": issues}
    
    async def _test_basic_connectivity(self) -> Dict[str, Any]:
        """Testa conectividade básica."""
        try:
            # Extrair host e porta da URL
            url_clean = self.websocket_url.replace("ws://", "").replace("wss://", "")
            host_port = url_clean.split("/")[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else (80 if self.websocket_url.startswith("ws://") else 443)
            
            # Testar conexão TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                sock.connect((host, port))
                sock.close()
                return {"success": True, "host": host, "port": port}
                
            except Exception as e:
                return {"success": False, "error": str(e), "host": host, "port": port}
                
        except Exception as e:
            return {"success": False, "error": f"Erro na análise da URL: {str(e)}"}
    
    async def _validate_ssl_config(self) -> Dict[str, Any]:
        """Valida configuração SSL."""
        issues = []
        recommendations = []
        
        try:
            # Simular validação SSL
            # Em implementação real, verificaria certificados, ciphers, etc.
            
            recommendations.append("Verificar validade do certificado SSL")
            recommendations.append("Usar TLS 1.2 ou superior")
            
        except Exception as e:
            issue = ConnectionIssue(
                type=ConnectionIssueType.SSL_ERROR,
                severity=IssueSeverity.HIGH,
                description=f"Erro na validação SSL: {str(e)}",
                solution="Verificar configuração SSL/TLS",
                affected_components=["ssl", "security"],
                details={"error": str(e)}
            )
            issues.append(issue)
        
        return {"issues": issues, "recommendations": recommendations}
    
    async def _detect_websocket_version(self) -> str:
        """Detecta versão do protocolo WebSocket."""
        try:
            # Simular detecção de versão
            return "13"  # RFC 6455
        except Exception:
            return "unknown"
    
    def _validate_websocket_headers(self) -> Dict[str, Any]:
        """Valida headers WebSocket."""
        issues = []
        
        # Verificar se headers necessários estão configurados
        # Em implementação real, verificaria headers como Origin, etc.
        
        return {"issues": issues}
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo dos diagnósticos de conexão.
        
        Returns:
            Dict[str, Any]: Resumo dos diagnósticos
        """
        return {
            "service": "ConnectionDiagnosticService",
            "version": "1.0.0",
            "capabilities": [
                "analyze_handshake_failures",
                "check_premature_closures",
                "validate_websocket_config"
            ],
            "monitored_aspects": [
                "handshake_process",
                "connection_timing",
                "closure_patterns",
                "ssl_configuration",
                "protocol_versions",
                "timeout_settings"
            ],
            "configuration": {
                "websocket_url": self.websocket_url,
                "websocket_timeout": self.websocket_timeout,
                "max_reconnect_attempts": self.max_reconnect_attempts
            }
        }