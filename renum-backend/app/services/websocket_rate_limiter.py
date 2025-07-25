"""
Serviço de limitação de taxa para WebSocket
"""
import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Tipos de limitação de taxa"""
    GLOBAL = "global"
    USER = "user"
    IP = "ip"
    CHANNEL = "channel"

class RateLimitAction(Enum):
    """Ações para violações de rate limit"""
    THROTTLE = "throttle"
    DISCONNECT = "disconnect"
    BLOCK = "block"

@dataclass
class RateLimitRule:
    """Regra de limitação de taxa"""
    id: str
    name: str
    type: RateLimitType
    target: Optional[str]
    limit: int
    window_seconds: int
    action: RateLimitAction
    enabled: bool
    created_at: datetime
    violations_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "target": self.target,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "action": self.action.value,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "violations_count": self.violations_count
        }

@dataclass
class RateLimitViolation:
    """Violação de rate limit"""
    rule_id: str
    connection_id: str
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    action_taken: RateLimitAction

class RateLimitTracker:
    """Rastreador de rate limit para uma regra específica"""
    
    def __init__(self, rule: RateLimitRule):
        self.rule = rule
        self.requests: Dict[str, List[float]] = {}  # key -> [timestamps]
        self.blocked_until: Dict[str, float] = {}  # key -> timestamp
    
    def is_allowed(self, key: str) -> Tuple[bool, Optional[float]]:
        """
        Verifica se uma requisição é permitida
        Returns: (allowed, retry_after_seconds)
        """
        now = time.time()
        
        # Verificar se está bloqueado
        if key in self.blocked_until:
            if now < self.blocked_until[key]:
                return False, self.blocked_until[key] - now
            else:
                del self.blocked_until[key]
        
        # Limpar requisições antigas
        if key in self.requests:
            cutoff = now - self.rule.window_seconds
            self.requests[key] = [ts for ts in self.requests[key] if ts > cutoff]
        else:
            self.requests[key] = []
        
        # Verificar limite
        if len(self.requests[key]) >= self.rule.limit:
            # Aplicar ação
            if self.rule.action == RateLimitAction.BLOCK:
                # Bloquear por uma janela de tempo
                self.blocked_until[key] = now + self.rule.window_seconds
                return False, self.rule.window_seconds
            elif self.rule.action == RateLimitAction.THROTTLE:
                # Calcular tempo de retry baseado na janela
                oldest_request = min(self.requests[key])
                retry_after = (oldest_request + self.rule.window_seconds) - now
                return False, max(retry_after, 1)
            else:  # DISCONNECT
                return False, None
        
        # Registrar requisição
        self.requests[key].append(now)
        return True, None
    
    def get_current_count(self, key: str) -> int:
        """Obtém contagem atual para uma chave"""
        now = time.time()
        if key not in self.requests:
            return 0
        
        cutoff = now - self.rule.window_seconds
        valid_requests = [ts for ts in self.requests[key] if ts > cutoff]
        return len(valid_requests)
    
    def reset_key(self, key: str):
        """Reseta contadores para uma chave"""
        if key in self.requests:
            del self.requests[key]
        if key in self.blocked_until:
            del self.blocked_until[key]

class WebSocketRateLimiter:
    """Limitador de taxa para WebSocket"""
    
    def __init__(self):
        self.rules: Dict[str, RateLimitRule] = {}
        self.trackers: Dict[str, RateLimitTracker] = {}
        self.violations: List[RateLimitViolation] = []
        self.max_violations_history = 1000
        
        # Estatísticas
        self.stats = {
            "total_violations": 0,
            "violations_last_hour": 0,
            "blocked_connections": set(),
            "throttled_connections": set()
        }
    
    def add_rule(self, rule: RateLimitRule):
        """Adiciona uma regra de rate limit"""
        self.rules[rule.id] = rule
        if rule.enabled:
            self.trackers[rule.id] = RateLimitTracker(rule)
        
        logger.info(f"Rate limit rule added: {rule.name} ({rule.id})")
    
    def remove_rule(self, rule_id: str):
        """Remove uma regra de rate limit"""
        if rule_id in self.rules:
            del self.rules[rule_id]
        if rule_id in self.trackers:
            del self.trackers[rule_id]
        
        logger.info(f"Rate limit rule removed: {rule_id}")
    
    def update_rule(self, rule: RateLimitRule):
        """Atualiza uma regra de rate limit"""
        self.rules[rule.id] = rule
        
        if rule.enabled:
            self.trackers[rule.id] = RateLimitTracker(rule)
        elif rule.id in self.trackers:
            del self.trackers[rule.id]
        
        logger.info(f"Rate limit rule updated: {rule.name} ({rule.id})")
    
    def toggle_rule(self, rule_id: str, enabled: bool):
        """Ativa/desativa uma regra"""
        if rule_id not in self.rules:
            return False
        
        self.rules[rule_id].enabled = enabled
        
        if enabled:
            self.trackers[rule_id] = RateLimitTracker(self.rules[rule_id])
        elif rule_id in self.trackers:
            del self.trackers[rule_id]
        
        logger.info(f"Rate limit rule {'enabled' if enabled else 'disabled'}: {rule_id}")
        return True
    
    def check_rate_limit(
        self,
        connection_id: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Verifica rate limits para uma conexão
        Returns: (allowed, violated_rule_id, retry_after_seconds)
        """
        for rule_id, tracker in self.trackers.items():
            rule = self.rules[rule_id]
            
            # Determinar chave baseada no tipo de regra
            key = self._get_rate_limit_key(rule, connection_id, user_id, ip_address, channel)
            if key is None:
                continue
            
            allowed, retry_after = tracker.is_allowed(key)
            
            if not allowed:
                # Registrar violação
                violation = RateLimitViolation(
                    rule_id=rule_id,
                    connection_id=connection_id,
                    user_id=user_id,
                    ip_address=ip_address or "unknown",
                    timestamp=datetime.utcnow(),
                    action_taken=rule.action
                )
                
                self._record_violation(violation)
                
                logger.warning(
                    f"Rate limit violation: rule={rule.name}, connection={connection_id}, "
                    f"user={user_id}, ip={ip_address}, action={rule.action.value}"
                )
                
                return False, rule_id, retry_after
        
        return True, None, None
    
    def _get_rate_limit_key(
        self,
        rule: RateLimitRule,
        connection_id: str,
        user_id: Optional[str],
        ip_address: Optional[str],
        channel: Optional[str]
    ) -> Optional[str]:
        """Gera chave para rate limit baseada no tipo de regra"""
        if rule.type == RateLimitType.GLOBAL:
            return "global"
        elif rule.type == RateLimitType.USER:
            if rule.target:
                return f"user:{rule.target}" if user_id == rule.target else None
            else:
                return f"user:{user_id}" if user_id else None
        elif rule.type == RateLimitType.IP:
            if rule.target:
                return f"ip:{rule.target}" if ip_address == rule.target else None
            else:
                return f"ip:{ip_address}" if ip_address else None
        elif rule.type == RateLimitType.CHANNEL:
            if rule.target:
                return f"channel:{rule.target}" if channel == rule.target else None
            else:
                return f"channel:{channel}" if channel else None
        
        return None
    
    def _record_violation(self, violation: RateLimitViolation):
        """Registra uma violação"""
        self.violations.append(violation)
        
        # Limitar histórico
        if len(self.violations) > self.max_violations_history:
            self.violations = self.violations[-self.max_violations_history:]
        
        # Atualizar estatísticas
        self.stats["total_violations"] += 1
        
        # Contar violações da última hora
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        self.stats["violations_last_hour"] = len([
            v for v in self.violations 
            if v.timestamp > one_hour_ago
        ])
        
        # Atualizar contadores de ação
        if violation.action_taken == RateLimitAction.BLOCK:
            self.stats["blocked_connections"].add(violation.connection_id)
        elif violation.action_taken == RateLimitAction.THROTTLE:
            self.stats["throttled_connections"].add(violation.connection_id)
        
        # Incrementar contador da regra
        if violation.rule_id in self.rules:
            self.rules[violation.rule_id].violations_count += 1
    
    def get_rules(self) -> List[RateLimitRule]:
        """Obtém todas as regras"""
        return list(self.rules.values())
    
    def get_rule(self, rule_id: str) -> Optional[RateLimitRule]:
        """Obtém uma regra específica"""
        return self.rules.get(rule_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de rate limiting"""
        active_rules = len([r for r in self.rules.values() if r.enabled])
        
        return {
            "total_rules": len(self.rules),
            "active_rules": active_rules,
            "total_violations": self.stats["total_violations"],
            "violations_last_hour": self.stats["violations_last_hour"],
            "blocked_connections": len(self.stats["blocked_connections"]),
            "throttled_connections": len(self.stats["throttled_connections"])
        }
    
    def get_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém histórico de violações"""
        recent_violations = sorted(
            self.violations, 
            key=lambda v: v.timestamp, 
            reverse=True
        )[:limit]
        
        return [
            {
                "rule_id": v.rule_id,
                "rule_name": self.rules[v.rule_id].name if v.rule_id in self.rules else "Unknown",
                "connection_id": v.connection_id,
                "user_id": v.user_id,
                "ip_address": v.ip_address,
                "timestamp": v.timestamp.isoformat(),
                "action_taken": v.action_taken.value
            }
            for v in recent_violations
        ]
    
    def reset_connection_limits(self, connection_id: str):
        """Reseta limites para uma conexão específica"""
        for tracker in self.trackers.values():
            # Tentar resetar para diferentes tipos de chave
            tracker.reset_key(f"connection:{connection_id}")
        
        # Remover das estatísticas
        self.stats["blocked_connections"].discard(connection_id)
        self.stats["throttled_connections"].discard(connection_id)
    
    def reset_user_limits(self, user_id: str):
        """Reseta limites para um usuário específico"""
        for tracker in self.trackers.values():
            tracker.reset_key(f"user:{user_id}")
    
    def reset_ip_limits(self, ip_address: str):
        """Reseta limites para um IP específico"""
        for tracker in self.trackers.values():
            tracker.reset_key(f"ip:{ip_address}")
    
    def cleanup_old_data(self):
        """Limpa dados antigos"""
        # Limpar violações antigas (mais de 24 horas)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.violations = [v for v in self.violations if v.timestamp > cutoff]
        
        # Recalcular estatísticas
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        self.stats["violations_last_hour"] = len([
            v for v in self.violations 
            if v.timestamp > one_hour_ago
        ])
        
        logger.debug("Rate limiter cleanup completed")

# Instância global do rate limiter
rate_limiter = WebSocketRateLimiter()

def get_rate_limiter() -> WebSocketRateLimiter:
    """Obtém a instância global do rate limiter"""
    return rate_limiter