"""
Gerenciador de billing para equipes de agentes.

Este módulo implementa o gerenciador de billing para equipes de agentes,
responsável por verificar limites de uso, calcular custos e registrar métricas de uso.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from app.repositories.team_execution_repository import TeamExecutionRepository
from app.models.team_models import CostMetrics, UsageMetrics

logger = logging.getLogger(__name__)


class BillingManager:
    """Gerenciador de billing para equipes de agentes."""
    
    def __init__(self, execution_repository: TeamExecutionRepository):
        """
        Inicializa o gerenciador de billing.
        
        Args:
            execution_repository: Repositório de execuções
        """
        self.execution_repository = execution_repository
    
    async def check_usage_limits(self, user_id: UUID) -> bool:
        """
        Verifica se o usuário está dentro dos limites de uso.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            True se o usuário está dentro dos limites
            
        Raises:
            ValueError: Se o usuário excedeu algum limite
        """
        # Verifica o número de execuções ativas
        active_executions = await self.execution_repository.count_active_executions(user_id)
        if active_executions >= 5:  # Limite de 5 execuções ativas
            raise ValueError(f"Maximum number of concurrent executions reached (5)")
        
        # Verifica o uso mensal
        monthly_usage = await self.get_monthly_usage(user_id)
        if monthly_usage.get("total_cost_usd", 0) >= 100:  # Limite de $100 por mês
            raise ValueError(f"Monthly usage limit reached ($100)")
        
        return True
    
    async def get_monthly_usage(self, user_id: UUID) -> Dict[str, Any]:
        """
        Obtém o uso mensal do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Uso mensal (tokens, custo, etc.)
        """
        # Obtém o primeiro dia do mês atual
        today = datetime.now()
        first_day = datetime(today.year, today.month, 1).isoformat()
        
        # Obtém todas as execuções do usuário no mês atual
        executions = await self.execution_repository.list_executions_by_date(
            user_id, start_date=first_day
        )
        
        # Calcula o uso total
        total_tokens_input = 0
        total_tokens_output = 0
        total_cost_usd = 0
        
        for execution in executions:
            # Obtém as métricas de uso da execução
            if execution.get("usage_metrics"):
                usage = execution["usage_metrics"]
                total_tokens_input += usage.get("tokens_input", 0)
                total_tokens_output += usage.get("tokens_output", 0)
            
            # Obtém as métricas de custo da execução
            if execution.get("cost_metrics"):
                cost = execution["cost_metrics"]
                total_cost_usd += cost.get("cost_usd", 0)
        
        return {
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_tokens": total_tokens_input + total_tokens_output,
            "total_cost_usd": total_cost_usd,
            "month": today.month,
            "year": today.year
        }
    
    async def calculate_execution_cost(
        self, 
        execution_id: UUID,
        user_id: UUID
    ) -> CostMetrics:
        """
        Calcula o custo de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Métricas de custo
        """
        # Obtém as execuções de agentes
        agent_executions = await self.execution_repository.list_agent_executions(execution_id)
        
        # Calcula o custo total
        total_cost_usd = 0
        cost_breakdown = {}
        
        for agent_execution in agent_executions:
            # Obtém as métricas de custo do agente
            if agent_execution.individual_cost_metrics:
                cost = agent_execution.individual_cost_metrics.get("cost_usd", 0)
                total_cost_usd += cost
                cost_breakdown[agent_execution.agent_id] = cost
        
        # Cria as métricas de custo
        cost_metrics = CostMetrics(
            cost_usd=total_cost_usd,
            cost_breakdown=cost_breakdown
        )
        
        # Atualiza as métricas de custo na execução
        await self.execution_repository.update_execution_result(
            execution_id,
            final_result=None,  # Não atualiza o resultado final
            cost_metrics=cost_metrics
        )
        
        return cost_metrics
    
    async def calculate_agent_cost(
        self, 
        usage_metrics: UsageMetrics
    ) -> float:
        """
        Calcula o custo de um agente com base nas métricas de uso.
        
        Args:
            usage_metrics: Métricas de uso
            
        Returns:
            Custo em USD
        """
        model_name = usage_metrics.model_name.lower()
        tokens_input = usage_metrics.tokens_input
        tokens_output = usage_metrics.tokens_output
        
        # Preços por 1K tokens (valores aproximados)
        if "gpt-4" in model_name:
            if "o" in model_name:  # gpt-4o
                input_price = 0.005  # $0.005 por 1K tokens de entrada
                output_price = 0.015  # $0.015 por 1K tokens de saída
            else:  # gpt-4
                input_price = 0.03  # $0.03 por 1K tokens de entrada
                output_price = 0.06  # $0.06 por 1K tokens de saída
        elif "gpt-3.5" in model_name:
            input_price = 0.001  # $0.001 por 1K tokens de entrada
            output_price = 0.002  # $0.002 por 1K tokens de saída
        elif "claude" in model_name:
            if "opus" in model_name:
                input_price = 0.015  # $0.015 por 1K tokens de entrada
                output_price = 0.075  # $0.075 por 1K tokens de saída
            elif "sonnet" in model_name:
                input_price = 0.003  # $0.003 por 1K tokens de entrada
                output_price = 0.015  # $0.015 por 1K tokens de saída
            else:  # claude-instant
                input_price = 0.0008  # $0.0008 por 1K tokens de entrada
                output_price = 0.0024  # $0.0024 por 1K tokens de saída
        else:
            # Preço padrão para modelos desconhecidos
            input_price = 0.01  # $0.01 por 1K tokens de entrada
            output_price = 0.03  # $0.03 por 1K tokens de saída
        
        # Calcula o custo
        input_cost = (tokens_input / 1000) * input_price
        output_cost = (tokens_output / 1000) * output_price
        total_cost = input_cost + output_cost
        
        return total_cost
    
    async def register_usage(
        self, 
        execution_id: UUID,
        agent_id: str,
        usage_metrics: UsageMetrics
    ) -> bool:
        """
        Registra o uso de um agente.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            usage_metrics: Métricas de uso
            
        Returns:
            True se o registro foi bem-sucedido
        """
        try:
            # Calcula o custo com base nas métricas de uso
            cost = await self.calculate_agent_cost(usage_metrics)
            
            # Cria as métricas de custo
            cost_metrics = {
                "cost_usd": cost,
                "cost_breakdown": {
                    "input_tokens": (usage_metrics.tokens_input / 1000) * 0.01,
                    "output_tokens": (usage_metrics.tokens_output / 1000) * 0.03
                }
            }
            
            # Atualiza as métricas de uso e custo na execução do agente
            await self.execution_repository.update_agent_execution(
                execution_id,
                agent_id,
                individual_usage_metrics=usage_metrics.dict(),
                individual_cost_metrics=cost_metrics
            )
            
            # Registra o uso no banco de dados
            await self.execution_repository.register_usage(
                execution_id,
                agent_id,
                usage_metrics.dict(),
                cost_metrics
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error registering usage: {str(e)}")
            return False