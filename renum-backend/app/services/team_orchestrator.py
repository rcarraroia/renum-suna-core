"""
Orquestrador de equipes de agentes.

Este módulo implementa o orquestrador de equipes de agentes, responsável por
coordenar a execução de equipes, gerenciar o ciclo de vida das execuções e
coletar métricas de uso e custo.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, AsyncIterator
from uuid import UUID
from datetime import datetime

from app.services.websocket_manager import websocket_manager

from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    ExecutionStatusResponse,
    CostMetrics,
    UsageMetrics,
    ExecutionStatus
)
# from app.repositories.team_repository import TeamRepository
# from app.repositories.team_execution_repository import TeamExecutionRepository
from app.services.execution_engine import ExecutionEngine
from app.services.suna_api_client import SunaApiClient
from app.services.team_context_manager import TeamContextManager
from app.services.team_message_bus import TeamMessageBus
from app.services.api_key_manager import ApiKeyManager
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TeamOrchestrator:
    """Orquestrador de equipes de agentes."""
    
    def __init__(
        self,
        # team_repository: TeamRepository,
        # execution_repository: TeamExecutionRepository,
        execution_engine: ExecutionEngine,
        suna_client: SunaApiClient,
        context_manager: TeamContextManager,
        message_bus: TeamMessageBus,
        api_key_manager: ApiKeyManager
    ):
        """
        Inicializa o orquestrador de equipes.
        
        Args:
            team_repository: Repositório de equipes
            execution_repository: Repositório de execuções
            execution_engine: Motor de execução
            suna_client: Cliente da API do Suna Core
            context_manager: Gerenciador de contexto compartilhado
            message_bus: Sistema de mensagens entre agentes
            api_key_manager: Gerenciador de API keys
        """
        self.team_repository = team_repository
        self.execution_repository = execution_repository
        self.execution_engine = execution_engine
        self.suna_client = suna_client
        self.context_manager = context_manager
        self.message_bus = message_bus
        self.api_key_manager = api_key_manager
        self.settings = get_settings()
        
        # Dicionário para rastrear execuções ativas
        self.active_executions = {}
    
    async def execute_team(
        self, 
        user_id: UUID, 
        execution_data: TeamExecutionCreate
    ) -> TeamExecutionResponse:
        """
        Inicia a execução de uma equipe.
        
        Args:
            user_id: ID do usuário
            execution_data: Dados da execução
            
        Returns:
            Objeto TeamExecutionResponse com os dados da execução criada
            
        Raises:
            ValueError: Se a equipe não existir ou o usuário não tiver acesso
        """
        # Verifica o limite de execuções concorrentes
        active_count = await self._count_active_executions(user_id)
        if active_count >= self.settings.MAX_CONCURRENT_EXECUTIONS:
            raise ValueError(f"Maximum number of concurrent executions ({self.settings.MAX_CONCURRENT_EXECUTIONS}) reached")
        
        # Cria a execução
        execution_response = await self.execution_repository.create_execution(user_id, execution_data)
        execution_id = execution_response.execution_id
        
        # Obtém a configuração da equipe
        team_config = await self.team_repository.get_team_config(execution_data.team_id, user_id)
        if not team_config:
            raise ValueError(f"Team {execution_data.team_id} not found or access denied")
        
        # Inicia a execução em background
        asyncio.create_task(self._execute_team_background(
            execution_id,
            team_config,
            execution_data.initial_prompt
        ))
        
        return execution_response
    
    async def _execute_team_background(
        self, 
        execution_id: UUID,
        team_config: Any,
        initial_prompt: str
    ):
        """
        Executa uma equipe em background.
        
        Args:
            execution_id: ID da execução
            team_config: Configuração da equipe
            initial_prompt: Prompt inicial
        """
        # Registra a execução como ativa
        self.active_executions[str(execution_id)] = {
            "team_id": str(team_config.team_id),
            "user_id": str(team_config.user_id),
            "started_at": datetime.now().isoformat()
        }
        
        # Atualiza o status da execução para "running"
        await self.execution_repository.update_execution_status(
            execution_id, 
            ExecutionStatus.RUNNING
        )
        
        # Publica atualização de status via WebSocket
        status = await self.execution_repository.get_execution_status(execution_id, team_config.user_id)
        if status:
            await websocket_manager.broadcast(
                execution_id,
                {
                    "type": "status_update",
                    "data": status.dict()
                }
            )
        
        try:
            # Executa a equipe
            await self.execution_engine.execute_plan(execution_id, team_config, initial_prompt)
            
            # Coleta métricas de uso e custo
            await self._collect_metrics(execution_id)
            
            # Atualiza o status da execução para "completed"
            await self.execution_repository.update_execution_status(
                execution_id, 
                ExecutionStatus.COMPLETED
            )
            
            # Publica atualização de status via WebSocket
            status = await self.execution_repository.get_execution_status(execution_id, team_config.user_id)
            if status:
                await websocket_manager.broadcast(
                    execution_id,
                    {
                        "type": "status_update",
                        "data": status.dict()
                    }
                )
            
        except Exception as e:
            logger.error(f"Error executing team {team_config.team_id} (execution {execution_id}): {str(e)}", exc_info=True)
            
            # Atualiza o status da execução para "failed"
            await self.execution_repository.update_execution_status(
                execution_id, 
                ExecutionStatus.FAILED,
                error_message=f"Error executing team: {str(e)}"
            )
            
            # Publica atualização de status via WebSocket
            status = await self.execution_repository.get_execution_status(execution_id, team_config.user_id)
            if status:
                await websocket_manager.broadcast(
                    execution_id,
                    {
                        "type": "status_update",
                        "data": status.dict()
                    }
                )
        
        finally:
            # Remove a execução da lista de ativas
            self.active_executions.pop(str(execution_id), None)
    
    async def get_execution_status(
        self, 
        execution_id: UUID, 
        user_id: UUID
    ) -> Optional[ExecutionStatusResponse]:
        """
        Obtém o status de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Objeto ExecutionStatusResponse ou None se não existir
        """
        return await self.execution_repository.get_execution_status(execution_id, user_id)
    
    async def get_execution_result(
        self, 
        execution_id: UUID, 
        user_id: UUID
    ) -> Optional[TeamExecutionResponse]:
        """
        Obtém o resultado de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Objeto TeamExecutionResponse ou None se não existir
        """
        return await self.execution_repository.get_execution_result(execution_id, user_id)
    
    async def stop_execution(self, execution_id: UUID, user_id: UUID) -> bool:
        """
        Para uma execução em andamento.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            True se a execução foi parada com sucesso
        """
        # Verifica se a execução existe e pertence ao usuário
        execution = await self.execution_repository.get_execution(execution_id, user_id)
        if not execution:
            return False
        
        # Verifica se a execução está em andamento
        if execution['status'] != ExecutionStatus.RUNNING.value:
            return False
        
        # Obtém as execuções de agentes em andamento
        agent_executions = await self.execution_repository.list_agent_executions(execution_id)
        running_executions = [
            agent_execution for agent_execution in agent_executions
            if agent_execution.status == ExecutionStatus.RUNNING
        ]
        
        # Para as execuções de agentes em andamento
        for agent_execution in running_executions:
            if agent_execution.suna_agent_run_id:
                try:
                    await self.suna_client.stop_agent_run(str(agent_execution.suna_agent_run_id))
                except Exception as e:
                    logger.error(f"Error stopping agent run {agent_execution.suna_agent_run_id}: {str(e)}")
                
                # Atualiza o status da execução do agente
                await self.execution_repository.update_agent_execution(
                    execution_id,
                    agent_execution.agent_id,
                    status=ExecutionStatus.CANCELLED
                )
                
                # Publica atualização de status do agente via WebSocket
                await websocket_manager.broadcast(
                    execution_id,
                    {
                        "type": "agent_status_update",
                        "data": {
                            "agent_id": agent_execution.agent_id,
                            "status": ExecutionStatus.CANCELLED.value
                        }
                    }
                )
        
        # Atualiza o status da execução
        await self.execution_repository.update_execution_status(
            execution_id, 
            ExecutionStatus.CANCELLED,
            error_message="Execution cancelled by user"
        )
        
        # Publica atualização de status via WebSocket
        status = await self.execution_repository.get_execution_status(execution_id, user_id)
        if status:
            await websocket_manager.broadcast(
                execution_id,
                {
                    "type": "status_update",
                    "data": status.dict()
                }
            )
        
        # Remove a execução da lista de ativas
        self.active_executions.pop(str(execution_id), None)
        
        return True
    
    async def list_executions(
        self, 
        user_id: UUID, 
        team_id: Optional[UUID] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[TeamExecutionResponse]:
        """
        Lista execuções de equipe.
        
        Args:
            user_id: ID do usuário
            team_id: ID da equipe (opcional)
            limit: Limite de resultados
            offset: Deslocamento para paginação
            
        Returns:
            Lista de objetos TeamExecutionResponse
        """
        return await self.execution_repository.list_executions(user_id, team_id, limit, offset)
    
    async def count_executions(self, user_id: UUID, team_id: Optional[UUID] = None) -> int:
        """
        Conta o número de execuções.
        
        Args:
            user_id: ID do usuário
            team_id: ID da equipe (opcional)
            
        Returns:
            Número de execuções
        """
        return await self.execution_repository.count_executions(user_id, team_id)
    
    async def delete_execution(self, execution_id: UUID, user_id: UUID) -> bool:
        """
        Exclui uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        # Verifica se a execução está ativa
        if str(execution_id) in self.active_executions:
            # Para a execução antes de excluí-la
            await self.stop_execution(execution_id, user_id)
        
        return await self.execution_repository.delete_execution(execution_id, user_id)
    
    async def subscribe_to_execution_updates(
        self, 
        execution_id: UUID
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Inscreve-se para receber atualizações de uma execução.
        
        Args:
            execution_id: ID da execução
            
        Yields:
            Dicionários com atualizações da execução
        """
        # Cria um canal de pubsub para atualizações de execução
        pubsub = self.message_bus.redis.pubsub()
        
        # Inscreve-se no canal de atualizações
        channel = f"team_execution_updates:{execution_id}"
        await pubsub.subscribe(channel)
        
        try:
            # Processa mensagens
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Decodifica a mensagem
                    yield message["data"]
        finally:
            # Cancela a inscrição
            await pubsub.unsubscribe(channel)
    
    async def unsubscribe_from_execution_updates(self, execution_id: UUID):
        """
        Cancela a inscrição para atualizações de uma execução.
        
        Args:
            execution_id: ID da execução
        """
        # Não é necessário fazer nada aqui, a limpeza é feita no método subscribe_to_execution_updates
        pass
    
    async def _count_active_executions(self, user_id: UUID) -> int:
        """
        Conta o número de execuções ativas do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Número de execuções ativas
        """
        user_id_str = str(user_id)
        return sum(1 for execution in self.active_executions.values() if execution["user_id"] == user_id_str)
    
    async def _collect_metrics(self, execution_id: UUID):
        """
        Coleta métricas de uso e custo de uma execução.
        
        Args:
            execution_id: ID da execução
        """
        # Importa o BillingManager
        from app.services.billing_manager import BillingManager
        
        # Cria uma instância do BillingManager
        billing_manager = BillingManager(self.execution_repository)
        
        # Obtém as execuções de agentes
        agent_executions = await self.execution_repository.list_agent_executions(execution_id)
        
        # Coleta métricas de uso por agente
        usage_metrics = {}
        total_tokens_input = 0
        total_tokens_output = 0
        
        for agent_execution in agent_executions:
            if agent_execution.status == ExecutionStatus.COMPLETED:
                # Obtém métricas de uso do Suna Core
                if agent_execution.suna_agent_run_id:
                    try:
                        metrics = await self.suna_client.get_usage_metrics(str(agent_execution.suna_agent_run_id))
                        
                        # Cria o objeto UsageMetrics
                        agent_metrics = UsageMetrics(
                            model_provider=metrics.get("model_provider", "unknown"),
                            model_name=metrics.get("model_name", "unknown"),
                            api_key_type=metrics.get("api_key_type", "renum_native"),
                            tokens_input=metrics.get("tokens_input", 0),
                            tokens_output=metrics.get("tokens_output", 0),
                            request_count=metrics.get("request_count", 1)
                        )
                        
                        # Registra o uso no BillingManager
                        await billing_manager.register_usage(
                            execution_id,
                            agent_execution.agent_id,
                            agent_metrics
                        )
                        
                        # Adiciona às métricas totais
                        usage_metrics[agent_execution.agent_id] = agent_metrics
                        total_tokens_input += agent_metrics.tokens_input
                        total_tokens_output += agent_metrics.tokens_output
                    
                    except Exception as e:
                        logger.error(f"Error collecting metrics for agent {agent_execution.agent_id}: {str(e)}")
        
        # Calcula o custo total da execução
        cost_metrics = await billing_manager.calculate_execution_cost(execution_id, user_id=None)
        
        # Atualiza as métricas na execução
        await self.execution_repository.update_execution_result(
            execution_id,
            {},  # Não atualiza o resultado final
            cost_metrics=cost_metrics,
            usage_metrics=usage_metrics
        )