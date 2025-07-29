"""
Serviço de diagnóstico para tokens de autenticação WebSocket.

Este módulo implementa ferramentas de diagnóstico para identificar e resolver
problemas relacionados a tokens de autenticação em conexões WebSocket.
"""

import os
import jwt
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

# Configuração simplificada de logger para diagnóstico
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TokenIssueType(Enum):
    """Tipos de problemas com tokens."""
    EMPTY_TOKEN = "empty_token"
    INVALID_FORMAT = "invalid_format"
    EXPIRED_TOKEN = "expired_token"
    INVALID_SIGNATURE = "invalid_signature"
    MISSING_CLAIMS = "missing_claims"
    GENERATION_ERROR = "generation_error"
    TRANSMISSION_ERROR = "transmission_error"


class IssueSeverity(Enum):
    """Severidade dos problemas."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TokenIssue:
    """Representa um problema identificado com tokens."""
    type: TokenIssueType
    severity: IssueSeverity
    description: str
    solution: str
    affected_components: List[str]
    details: Dict[str, Any]


@dataclass
class DiagnosticResult:
    """Resultado de um diagnóstico."""
    success: bool
    issues: List[TokenIssue]
    recommendations: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime


class TokenDiagnosticService:
    """Serviço de diagnóstico para tokens de autenticação WebSocket."""
    
    def __init__(self):
        """Inicializa o serviço de diagnóstico."""
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.issues_found: List[TokenIssue] = []
        
        logger.info("TokenDiagnosticService initialized")
    
    async def validate_token_generation(self) -> DiagnosticResult:
        """
        Valida se tokens estão sendo gerados corretamente.
        
        Returns:
            DiagnosticResult: Resultado do diagnóstico
        """
        logger.info("Starting token generation validation")
        
        issues = []
        recommendations = []
        metrics = {
            "response_time": 0,
            "tests_performed": 0,
            "tests_passed": 0,
            "tests_failed": 0
        }
        
        start_time = datetime.now()
        
        try:
            # 1. Verificar se JWT_SECRET está configurado
            metrics["tests_performed"] += 1
            if not self.jwt_secret:
                issue = TokenIssue(
                    type=TokenIssueType.GENERATION_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description="JWT_SECRET não está configurado nas variáveis de ambiente",
                    solution="Configure a variável de ambiente JWT_SECRET com uma chave secreta segura",
                    affected_components=["backend", "authentication", "websocket"],
                    details={"env_var": "JWT_SECRET", "current_value": None}
                )
                issues.append(issue)
                metrics["tests_failed"] += 1
                
                recommendations.append("Configure JWT_SECRET imediatamente - sem isso, nenhum token pode ser gerado")
            else:
                metrics["tests_passed"] += 1
                logger.info("JWT_SECRET is configured")
            
            # 2. Verificar se a chave secreta é segura
            metrics["tests_performed"] += 1
            if self.jwt_secret and len(self.jwt_secret) < 32:
                issue = TokenIssue(
                    type=TokenIssueType.GENERATION_ERROR,
                    severity=IssueSeverity.HIGH,
                    description=f"JWT_SECRET é muito curto ({len(self.jwt_secret)} caracteres)",
                    solution="Use uma chave secreta com pelo menos 32 caracteres",
                    affected_components=["security", "authentication"],
                    details={"current_length": len(self.jwt_secret), "recommended_length": 32}
                )
                issues.append(issue)
                metrics["tests_failed"] += 1
                
                recommendations.append("Gere uma nova chave JWT_SECRET mais segura")
            else:
                metrics["tests_passed"] += 1
            
            # 3. Testar geração de token
            metrics["tests_performed"] += 1
            if self.jwt_secret:
                try:
                    test_payload = {
                        "user_id": "test_user",
                        "exp": datetime.now(timezone.utc).timestamp() + 3600,
                        "iat": datetime.now(timezone.utc).timestamp()
                    }
                    
                    test_token = jwt.encode(test_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
                    
                    if not test_token or test_token.strip() == "":
                        issue = TokenIssue(
                            type=TokenIssueType.GENERATION_ERROR,
                            severity=IssueSeverity.CRITICAL,
                            description="Geração de token JWT retorna valor vazio",
                            solution="Verificar implementação da geração de tokens",
                            affected_components=["jwt", "authentication"],
                            details={"token_result": test_token}
                        )
                        issues.append(issue)
                        metrics["tests_failed"] += 1
                    else:
                        metrics["tests_passed"] += 1
                        logger.info("Token generation test passed")
                        
                except Exception as e:
                    issue = TokenIssue(
                        type=TokenIssueType.GENERATION_ERROR,
                        severity=IssueSeverity.CRITICAL,
                        description=f"Erro ao gerar token JWT: {str(e)}",
                        solution="Verificar configuração do JWT e dependências",
                        affected_components=["jwt", "authentication"],
                        details={"error": str(e), "error_type": type(e).__name__}
                    )
                    issues.append(issue)
                    metrics["tests_failed"] += 1
            
            # 4. Testar validação de token
            metrics["tests_performed"] += 1
            if self.jwt_secret:
                try:
                    test_payload = {
                        "user_id": "test_user",
                        "exp": datetime.now(timezone.utc).timestamp() + 3600,
                        "iat": datetime.now(timezone.utc).timestamp()
                    }
                    
                    test_token = jwt.encode(test_payload, self.jwt_secret, algorithm=self.jwt_algorithm)
                    decoded_payload = jwt.decode(test_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                    
                    if decoded_payload.get("user_id") != "test_user":
                        issue = TokenIssue(
                            type=TokenIssueType.INVALID_FORMAT,
                            severity=IssueSeverity.HIGH,
                            description="Token gerado não contém os dados esperados após decodificação",
                            solution="Verificar processo de codificação/decodificação JWT",
                            affected_components=["jwt", "authentication"],
                            details={"expected": test_payload, "actual": decoded_payload}
                        )
                        issues.append(issue)
                        metrics["tests_failed"] += 1
                    else:
                        metrics["tests_passed"] += 1
                        logger.info("Token validation test passed")
                        
                except Exception as e:
                    issue = TokenIssue(
                        type=TokenIssueType.INVALID_FORMAT,
                        severity=IssueSeverity.CRITICAL,
                        description=f"Erro ao validar token JWT: {str(e)}",
                        solution="Verificar configuração do JWT e algoritmo usado",
                        affected_components=["jwt", "authentication"],
                        details={"error": str(e), "error_type": type(e).__name__}
                    )
                    issues.append(issue)
                    metrics["tests_failed"] += 1
            
            # 5. Verificar algoritmo JWT
            metrics["tests_performed"] += 1
            if self.jwt_algorithm not in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]:
                issue = TokenIssue(
                    type=TokenIssueType.GENERATION_ERROR,
                    severity=IssueSeverity.MEDIUM,
                    description=f"Algoritmo JWT não recomendado: {self.jwt_algorithm}",
                    solution="Use um algoritmo JWT seguro como HS256 ou RS256",
                    affected_components=["jwt", "security"],
                    details={"current_algorithm": self.jwt_algorithm, "recommended": ["HS256", "RS256"]}
                )
                issues.append(issue)
                metrics["tests_failed"] += 1
                
                recommendations.append("Configure JWT_ALGORITHM para HS256 ou RS256")
            else:
                metrics["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"Error during token generation validation: {str(e)}")
            issue = TokenIssue(
                type=TokenIssueType.GENERATION_ERROR,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante validação de geração de tokens: {str(e)}",
                solution="Verificar logs detalhados e configuração do sistema",
                affected_components=["system", "authentication"],
                details={"error": str(e), "error_type": type(e).__name__}
            )
            issues.append(issue)
        
        # Calcular métricas finais
        end_time = datetime.now()
        metrics["response_time"] = (end_time - start_time).total_seconds() * 1000  # em ms
        
        # Adicionar recomendações gerais
        if not recommendations:
            recommendations.append("Configuração de geração de tokens está funcionando corretamente")
        
        success = len([i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]) == 0
        
        result = DiagnosticResult(
            success=success,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now()
        )
        
        logger.info(f"Token generation validation completed: {metrics['tests_passed']}/{metrics['tests_performed']} tests passed")
        
        return result
    
    async def check_token_transmission(self, token: Optional[str] = None, headers: Optional[Dict[str, str]] = None) -> DiagnosticResult:
        """
        Verifica se tokens estão sendo transmitidos corretamente.
        
        Args:
            token: Token recebido (opcional)
            headers: Headers da requisição (opcional)
            
        Returns:
            DiagnosticResult: Resultado do diagnóstico
        """
        logger.info("Starting token transmission check")
        
        issues = []
        recommendations = []
        metrics = {
            "response_time": 0,
            "checks_performed": 0,
            "checks_passed": 0,
            "checks_failed": 0
        }
        
        start_time = datetime.now()
        
        try:
            # 1. Verificar se token foi fornecido
            metrics["checks_performed"] += 1
            if token is None:
                issue = TokenIssue(
                    type=TokenIssueType.TRANSMISSION_ERROR,
                    severity=IssueSeverity.CRITICAL,
                    description="Token não foi fornecido na requisição WebSocket",
                    solution="Verificar se o frontend está enviando o token na URL ou headers",
                    affected_components=["frontend", "websocket", "authentication"],
                    details={"token_provided": False, "token_value": None}
                )
                issues.append(issue)
                metrics["checks_failed"] += 1
                
                recommendations.append("Verificar implementação do frontend para envio de token")
            else:
                metrics["checks_passed"] += 1
            
            # 2. Verificar se token está vazio
            metrics["checks_performed"] += 1
            if token is not None and (token.strip() == "" or token == "null" or token == "undefined"):
                issue = TokenIssue(
                    type=TokenIssueType.EMPTY_TOKEN,
                    severity=IssueSeverity.CRITICAL,
                    description=f"Token está vazio ou contém valor inválido: '{token}'",
                    solution="Verificar se o token está sendo obtido corretamente do localStorage/sessionStorage",
                    affected_components=["frontend", "authentication", "storage"],
                    details={"token_value": token, "token_length": len(token) if token else 0}
                )
                issues.append(issue)
                metrics["checks_failed"] += 1
                
                recommendations.append("Verificar se o usuário está logado e o token foi salvo corretamente")
            elif token is not None:
                metrics["checks_passed"] += 1
            
            # 3. Verificar formato do token
            metrics["checks_performed"] += 1
            if token and token.strip() != "":
                # JWT deve ter 3 partes separadas por pontos
                token_parts = token.split('.')
                if len(token_parts) != 3:
                    issue = TokenIssue(
                        type=TokenIssueType.INVALID_FORMAT,
                        severity=IssueSeverity.HIGH,
                        description=f"Token JWT não tem o formato correto (3 partes): {len(token_parts)} partes encontradas",
                        solution="Verificar se o token está sendo gerado corretamente como JWT",
                        affected_components=["jwt", "authentication"],
                        details={"token_parts": len(token_parts), "expected_parts": 3, "token_preview": token[:50] + "..." if len(token) > 50 else token}
                    )
                    issues.append(issue)
                    metrics["checks_failed"] += 1
                    
                    recommendations.append("Verificar geração de token JWT no backend")
                else:
                    metrics["checks_passed"] += 1
            
            # 4. Verificar se token pode ser decodificado
            metrics["checks_performed"] += 1
            if token and token.strip() != "" and self.jwt_secret:
                try:
                    decoded = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                    
                    # Verificar claims obrigatórios
                    required_claims = ["user_id", "exp", "iat"]
                    missing_claims = [claim for claim in required_claims if claim not in decoded]
                    
                    if missing_claims:
                        issue = TokenIssue(
                            type=TokenIssueType.MISSING_CLAIMS,
                            severity=IssueSeverity.HIGH,
                            description=f"Token não contém claims obrigatórios: {missing_claims}",
                            solution="Verificar geração de token para incluir todos os claims necessários",
                            affected_components=["jwt", "authentication"],
                            details={"missing_claims": missing_claims, "present_claims": list(decoded.keys())}
                        )
                        issues.append(issue)
                        metrics["checks_failed"] += 1
                        
                        recommendations.append("Atualizar geração de token para incluir user_id, exp e iat")
                    else:
                        metrics["checks_passed"] += 1
                        logger.info("Token decoded successfully with all required claims")
                        
                except jwt.ExpiredSignatureError:
                    issue = TokenIssue(
                        type=TokenIssueType.EXPIRED_TOKEN,
                        severity=IssueSeverity.HIGH,
                        description="Token JWT está expirado",
                        solution="Implementar renovação automática de token ou solicitar novo login",
                        affected_components=["jwt", "authentication", "frontend"],
                        details={"error": "Token expired"}
                    )
                    issues.append(issue)
                    metrics["checks_failed"] += 1
                    
                    recommendations.append("Implementar renovação automática de tokens")
                    
                except jwt.InvalidSignatureError:
                    issue = TokenIssue(
                        type=TokenIssueType.INVALID_SIGNATURE,
                        severity=IssueSeverity.CRITICAL,
                        description="Assinatura do token JWT é inválida",
                        solution="Verificar se JWT_SECRET está correto em ambos frontend e backend",
                        affected_components=["jwt", "authentication", "security"],
                        details={"error": "Invalid signature"}
                    )
                    issues.append(issue)
                    metrics["checks_failed"] += 1
                    
                    recommendations.append("Verificar consistência da chave JWT_SECRET")
                    
                except jwt.InvalidTokenError as e:
                    issue = TokenIssue(
                        type=TokenIssueType.INVALID_FORMAT,
                        severity=IssueSeverity.HIGH,
                        description=f"Token JWT é inválido: {str(e)}",
                        solution="Verificar formato e geração do token",
                        affected_components=["jwt", "authentication"],
                        details={"error": str(e), "error_type": type(e).__name__}
                    )
                    issues.append(issue)
                    metrics["checks_failed"] += 1
                    
                    recommendations.append("Verificar processo de geração de token")
            
            # 5. Verificar headers de autenticação
            metrics["checks_performed"] += 1
            if headers:
                auth_header = headers.get("Authorization") or headers.get("authorization")
                if auth_header and not token:
                    # Token pode estar no header Authorization
                    if auth_header.startswith("Bearer "):
                        extracted_token = auth_header[7:]  # Remove "Bearer "
                        recommendations.append("Token encontrado no header Authorization, considere usar este em vez do parâmetro de query")
                    else:
                        issue = TokenIssue(
                            type=TokenIssueType.TRANSMISSION_ERROR,
                            severity=IssueSeverity.MEDIUM,
                            description="Header Authorization não segue formato Bearer",
                            solution="Use formato 'Bearer <token>' no header Authorization",
                            affected_components=["frontend", "authentication"],
                            details={"auth_header": auth_header[:50] + "..." if len(auth_header) > 50 else auth_header}
                        )
                        issues.append(issue)
                        metrics["checks_failed"] += 1
                else:
                    metrics["checks_passed"] += 1
            
        except Exception as e:
            logger.error(f"Error during token transmission check: {str(e)}")
            issue = TokenIssue(
                type=TokenIssueType.TRANSMISSION_ERROR,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro crítico durante verificação de transmissão: {str(e)}",
                solution="Verificar logs detalhados e configuração do sistema",
                affected_components=["system", "authentication"],
                details={"error": str(e), "error_type": type(e).__name__}
            )
            issues.append(issue)
        
        # Calcular métricas finais
        end_time = datetime.now()
        metrics["response_time"] = (end_time - start_time).total_seconds() * 1000  # em ms
        
        # Adicionar recomendações gerais
        if not recommendations and not issues:
            recommendations.append("Transmissão de token está funcionando corretamente")
        
        success = len([i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]]) == 0
        
        result = DiagnosticResult(
            success=success,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now()
        )
        
        logger.info(f"Token transmission check completed: {metrics['checks_passed']}/{metrics['checks_performed']} checks passed")
        
        return result
    
    async def diagnose_empty_tokens(self) -> List[TokenIssue]:
        """
        Identifica causas específicas de tokens vazios.
        
        Returns:
            List[TokenIssue]: Lista de problemas identificados
        """
        logger.info("Starting empty token diagnosis")
        
        issues = []
        
        try:
            # 1. Verificar configuração de autenticação
            if not self.jwt_secret:
                issues.append(TokenIssue(
                    type=TokenIssueType.EMPTY_TOKEN,
                    severity=IssueSeverity.CRITICAL,
                    description="JWT_SECRET não configurado - tokens não podem ser gerados",
                    solution="Configure JWT_SECRET nas variáveis de ambiente",
                    affected_components=["backend", "authentication"],
                    details={"config_missing": "JWT_SECRET"}
                ))
            
            # 2. Verificar se há problemas comuns de frontend
            frontend_issues = [
                {
                    "description": "localStorage pode estar sendo limpo automaticamente",
                    "solution": "Verificar se há código limpando localStorage ou se o navegador está em modo privado",
                    "details": {"storage_type": "localStorage", "common_cause": "auto_cleanup"}
                },
                {
                    "description": "Token pode estar sendo perdido durante navegação",
                    "solution": "Verificar se o token está sendo persistido corretamente entre páginas",
                    "details": {"storage_type": "state_management", "common_cause": "navigation_loss"}
                },
                {
                    "description": "Processo de login pode não estar salvando o token",
                    "solution": "Verificar se o processo de login está chamando setToken() corretamente",
                    "details": {"process": "login", "common_cause": "save_failure"}
                },
                {
                    "description": "Token pode estar expirando muito rapidamente",
                    "solution": "Verificar tempo de expiração do token e implementar renovação automática",
                    "details": {"timing": "expiration", "common_cause": "short_expiry"}
                }
            ]
            
            for frontend_issue in frontend_issues:
                issues.append(TokenIssue(
                    type=TokenIssueType.EMPTY_TOKEN,
                    severity=IssueSeverity.MEDIUM,
                    description=frontend_issue["description"],
                    solution=frontend_issue["solution"],
                    affected_components=["frontend", "authentication"],
                    details=frontend_issue["details"]
                ))
            
            # 3. Verificar problemas de sincronização
            sync_issue = TokenIssue(
                type=TokenIssueType.EMPTY_TOKEN,
                severity=IssueSeverity.MEDIUM,
                description="Possível problema de sincronização entre estado da aplicação e localStorage",
                solution="Implementar verificação de consistência entre Zustand store e localStorage",
                affected_components=["frontend", "state_management"],
                details={"sync_issue": "state_storage_mismatch"}
            )
            issues.append(sync_issue)
            
        except Exception as e:
            logger.error(f"Error during empty token diagnosis: {str(e)}")
            issues.append(TokenIssue(
                type=TokenIssueType.EMPTY_TOKEN,
                severity=IssueSeverity.CRITICAL,
                description=f"Erro durante diagnóstico de tokens vazios: {str(e)}",
                solution="Verificar logs detalhados do sistema",
                affected_components=["system"],
                details={"error": str(e), "error_type": type(e).__name__}
            ))
        
        logger.info(f"Empty token diagnosis completed: {len(issues)} issues identified")
        
        return issues
    
    def get_diagnostic_summary(self) -> Dict[str, Any]:
        """
        Retorna um resumo dos diagnósticos realizados.
        
        Returns:
            Dict[str, Any]: Resumo dos diagnósticos
        """
        return {
            "service": "TokenDiagnosticService",
            "version": "1.0.0",
            "capabilities": [
                "validate_token_generation",
                "check_token_transmission", 
                "diagnose_empty_tokens"
            ],
            "supported_token_types": ["JWT"],
            "supported_algorithms": ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"],
            "configuration": {
                "jwt_secret_configured": bool(self.jwt_secret),
                "jwt_algorithm": self.jwt_algorithm
            }
        }