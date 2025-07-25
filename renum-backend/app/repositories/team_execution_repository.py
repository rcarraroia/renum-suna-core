"""
Repositório para gerenciamento de execuções de equipes de agentes.

Este módulo implementa o repositório para operações relacionadas a execuções de equipes,
incluindo criação, atualização, consulta e exclusão de execuções.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime

from app.models.team_models import (
    TeamExecutionCreate,
    TeamExecutionResponse,
    TeamExecutionStatus,
    TeamExecutionResult,
    TeamAgentExecutionResponse,
    ExecutionStatus,
    ExecutionLogEntry,
    CostMetrics,
    UsageMetrics
)
from app.db.database import Database

logger = logging.getLogger(__name__)


class TeamExecutionRepository:
    """Repositório para gerenciamento de execuções de equipes de agentes."""
    
    def __init__(self, db: Database):
        """
        Inicializa o repositório.
        
        Args:
            db: Conexão com o banco de dados
        """
        self.db = db
    
    async def create_execution(
        self, 
        user_id: UUID, 
        execution_data: TeamExecutionCreate
    ) -> TeamExecutionResponse:
        """
        Cria uma nova execução de equipe.
        
        Args:
            user_id: ID do usuário
            execution_data: Dados da execução
            
        Returns:
            Objeto TeamExecutionResponse com os dados da execução criada
            
        Raises:
            ValueError: Se ocorrer um erro na criação da execução
        """
        try:
            # Gera um ID para a execução
            execution_id = uuid4()
            
            # Prepara os dados para inserção
            execution_dict = {
                "execution_id": str(execution_id),
                "team_id": str(execution_data.team_id),
                "user_id": str(user_id),
                "status": ExecutionStatus.PENDING.value,
                "initial_prompt": execution_data.initial_prompt,
                "shared_context": {},
                "cost_metrics": {},
                "usage_metrics": {},
                "api_keys_used": {},
                "created_at": datetime.now().isoformat()
            }
            
            # Insere no banco de dados
            await self.db.table('renum_team_executions').insert(execution_dict).execute()
            
            # Retorna os dados da execução
            return TeamExecutionResponse(
                execution_id=execution_id,
                team_id=execution_data.team_id,
                status=ExecutionStatus.PENDING,
                initial_prompt=execution_data.initial_prompt,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to create execution: {str(e)}")
            raise ValueError(f"Failed to create execution: {str(e)}")
    
    async def get_execution(
        self, 
        execution_id: UUID, 
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Dados da execução ou None se não existir
        """
        try:
            # Consulta o banco de dados
            result = await self.db.table('renum_team_executions') \
                .select('*') \
                .eq('execution_id', str(execution_id)) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            if not result.data:
                return None
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {str(e)}")
            return None
    
    async def get_execution_status(
        self, 
        execution_id: UUID, 
        user_id: UUID
    ) -> Optional[TeamExecutionStatus]:
        """
        Obtém o status de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Objeto TeamExecutionStatus ou None se não existir
        """
        try:
            # Obtém os dados da execução
            execution = await self.get_execution(execution_id, user_id)
            if not execution:
                return None
            
            # Obtém os status dos agentes
            agent_executions = await self.list_agent_executions(execution_id)
            agent_statuses = {
                agent_execution.agent_id: agent_execution.status
                for agent_execution in agent_executions
            }
            
            # Calcula o progresso
            total_steps = len(agent_executions)
            completed_steps = sum(
                1 for status in agent_statuses.values()
                if status in [ExecutionStatus.COMPLETED, ExecutionStatus.SKIPPED]
            )
            
            progress = 0.0
            if total_steps > 0:
                progress = (completed_steps / total_steps) * 100.0
            
            # Determina a etapa atual
            current_step = None
            for agent_execution in agent_executions:
                if agent_execution.status == ExecutionStatus.RUNNING:
                    current_step = agent_execution.step_order
                    break
            
            # Estima o tempo de conclusão
            estimated_completion = None
            if execution.get('started_at') and progress > 0:
                # Implementação simplificada - em um sistema real, seria mais sofisticado
                pass
            
            # Cria o objeto de status
            return TeamExecutionStatus(
                execution_id=execution_id,
                team_id=execution['team_id'],
                status=ExecutionStatus(execution['status']),
                agent_statuses=agent_statuses,
                progress=progress,
                current_step=current_step,
                total_steps=total_steps,
                started_at=datetime.fromisoformat(execution['started_at']) if execution.get('started_at') else None,
                estimated_completion=estimated_completion,
                error_message=execution.get('error_message'),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get execution status {execution_id}: {str(e)}")
            return None
    
    async def get_execution_result(
        self, 
        execution_id: UUID, 
        user_id: UUID
    ) -> Optional[TeamExecutionResult]:
        """
        Obtém o resultado de uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            Objeto TeamExecutionResult ou None se não existir
        """
        try:
            # Obtém os dados da execução
            execution = await self.get_execution(execution_id, user_id)
            if not execution:
                return None
            
            # Verifica se a execução foi concluída
            if execution['status'] != ExecutionStatus.COMPLETED.value:
                return None
            
            # Cria o objeto de resultado
            return TeamExecutionResult(
                execution_id=execution_id,
                team_id=execution['team_id'],
                status=ExecutionStatus(execution['status']),
                initial_prompt=execution['initial_prompt'],
                final_result=execution.get('final_result', {}),
                cost_metrics=CostMetrics(**execution.get('cost_metrics', {})) if execution.get('cost_metrics') else None,
                usage_metrics=UsageMetrics(**execution.get('usage_metrics', {})) if execution.get('usage_metrics') else None,
                started_at=datetime.fromisoformat(execution['started_at']) if execution.get('started_at') else None,
                completed_at=datetime.fromisoformat(execution['completed_at']) if execution.get('completed_at') else None,
                execution_time=(
                    (datetime.fromisoformat(execution['completed_at']) - datetime.fromisoformat(execution['started_at'])).total_seconds()
                    if execution.get('completed_at') and execution.get('started_at') else None
                )
            )
            
        except Exception as e:
            logger.error(f"Failed to get execution result {execution_id}: {str(e)}")
            return None
    
    async def update_execution_status(
        self, 
        execution_id: UUID, 
        status: ExecutionStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Atualiza o status de uma execução.
        
        Args:
            execution_id: ID da execução
            status: Novo status
            error_message: Mensagem de erro (opcional)
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Prepara os dados para atualização
            update_data = {
                "status": status.value
            }
            
            # Adiciona timestamps conforme o status
            if status == ExecutionStatus.RUNNING:
                update_data["started_at"] = datetime.now().isoformat()
            elif status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
                update_data["completed_at"] = datetime.now().isoformat()
            
            # Adiciona mensagem de erro se fornecida
            if error_message:
                update_data["error_message"] = error_message
            
            # Atualiza no banco de dados
            await self.db.table('renum_team_executions') \
                .update(update_data) \
                .eq('execution_id', str(execution_id)) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update execution status {execution_id}: {str(e)}")
            return False
    
    async def update_execution_plan(
        self, 
        execution_id: UUID, 
        execution_plan: Dict[str, Any]
    ) -> bool:
        """
        Atualiza o plano de execução.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Atualiza no banco de dados
            await self.db.table('renum_team_executions') \
                .update({"execution_plan": execution_plan}) \
                .eq('execution_id', str(execution_id)) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update execution plan {execution_id}: {str(e)}")
            return False
    
    async def update_execution_result(
        self, 
        execution_id: UUID, 
        final_result: Dict[str, Any],
        cost_metrics: Optional[CostMetrics] = None,
        usage_metrics: Optional[Dict[str, UsageMetrics]] = None
    ) -> bool:
        """
        Atualiza o resultado de uma execução.
        
        Args:
            execution_id: ID da execução
            final_result: Resultado final
            cost_metrics: Métricas de custo
            usage_metrics: Métricas de uso
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Prepara os dados para atualização
            update_data = {}
            
            if final_result:
                update_data["final_result"] = final_result
            
            if cost_metrics:
                update_data["cost_metrics"] = cost_metrics.dict()
            
            if usage_metrics:
                update_data["usage_metrics"] = {
                    agent_id: metrics.dict()
                    for agent_id, metrics in usage_metrics.items()
                }
            
            # Atualiza no banco de dados se houver dados para atualizar
            if update_data:
                await self.db.table('renum_team_executions') \
                    .update(update_data) \
                    .eq('execution_id', str(execution_id)) \
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update execution result {execution_id}: {str(e)}")
            return False
    
    async def delete_execution(self, execution_id: UUID, user_id: UUID) -> bool:
        """
        Exclui uma execução.
        
        Args:
            execution_id: ID da execução
            user_id: ID do usuário
            
        Returns:
            True se a exclusão foi bem-sucedida
        """
        try:
            # Verifica se a execução existe e pertence ao usuário
            execution = await self.get_execution(execution_id, user_id)
            if not execution:
                return False
            
            # Exclui do banco de dados
            await self.db.table('renum_team_executions') \
                .delete() \
                .eq('execution_id', str(execution_id)) \
                .eq('user_id', str(user_id)) \
                .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete execution {execution_id}: {str(e)}")
            return False
    
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
        try:
            # Constrói a query
            query = self.db.table('renum_team_executions') \
                .select('*') \
                .eq('user_id', str(user_id))
            
            # Aplica filtro por equipe se fornecido
            if team_id:
                query = query.eq('team_id', str(team_id))
            
            # Aplica ordenação e paginação
            query = query.order('created_at', desc=True) \
                .range(offset, offset + limit - 1)
            
            # Executa a query
            result = await query.execute()
            
            # Converte para objetos TeamExecutionResponse
            executions = []
            for execution_data in result.data:
                executions.append(TeamExecutionResponse(
                    execution_id=execution_data['execution_id'],
                    team_id=execution_data['team_id'],
                    status=ExecutionStatus(execution_data['status']),
                    initial_prompt=execution_data['initial_prompt'],
                    final_result=execution_data.get('final_result'),
                    error_message=execution_data.get('error_message'),
                    started_at=datetime.fromisoformat(execution_data['started_at']) if execution_data.get('started_at') else None,
                    completed_at=datetime.fromisoformat(execution_data['completed_at']) if execution_data.get('completed_at') else None,
                    created_at=datetime.fromisoformat(execution_data['created_at'])
                ))
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to list executions: {str(e)}")
            return []
    
    async def count_executions(self, user_id: UUID, team_id: Optional[UUID] = None) -> int:
        """
        Conta o número de execuções.
        
        Args:
            user_id: ID do usuário
            team_id: ID da equipe (opcional)
            
        Returns:
            Número de execuções
        """
        try:
            # Constrói a query
            query = self.db.table('renum_team_executions') \
                .select('*', count='exact') \
                .eq('user_id', str(user_id))
            
            # Aplica filtro por equipe se fornecido
            if team_id:
                query = query.eq('team_id', str(team_id))
            
            # Executa a query
            result = await query.execute()
            
            return result.count
            
        except Exception as e:
            logger.error(f"Failed to count executions: {str(e)}")
            return 0
    
    async def create_agent_execution(
        self, 
        execution_id: UUID, 
        agent_id: str,
        step_order: int
    ) -> bool:
        """
        Cria um registro de execução de agente.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            step_order: Ordem da etapa
            
        Returns:
            True se a criação foi bem-sucedida
        """
        try:
            # Prepara os dados para inserção
            agent_execution = {
                "execution_id": str(execution_id),
                "agent_id": agent_id,
                "step_order": step_order,
                "status": ExecutionStatus.PENDING.value,
                "input_data": {},
                "context_snapshot": {},
                "individual_cost_metrics": {},
                "individual_usage_metrics": {},
                "api_keys_snapshot": {}
            }
            
            # Insere no banco de dados
            await self.db.table('renum_team_agent_executions').insert(agent_execution).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create agent execution {execution_id}/{agent_id}: {str(e)}")
            return False
    
    async def update_agent_execution(
        self, 
        execution_id: UUID, 
        agent_id: str,
        status: Optional[ExecutionStatus] = None,
        suna_agent_run_id: Optional[UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        context_snapshot: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        individual_cost_metrics: Optional[Dict[str, Any]] = None,
        individual_usage_metrics: Optional[Dict[str, Any]] = None,
        api_keys_snapshot: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Atualiza um registro de execução de agente.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            status: Novo status
            suna_agent_run_id: ID da execução no Suna Core
            input_data: Dados de entrada
            output_data: Dados de saída
            context_snapshot: Snapshot do contexto
            error_message: Mensagem de erro
            individual_cost_metrics: Métricas de custo
            individual_usage_metrics: Métricas de uso
            api_keys_snapshot: Snapshot das API keys
            
        Returns:
            True se a atualização foi bem-sucedida
        """
        try:
            # Prepara os dados para atualização
            update_data = {}
            
            if status is not None:
                update_data["status"] = status.value
                
                # Adiciona timestamps conforme o status
                if status == ExecutionStatus.RUNNING:
                    update_data["started_at"] = datetime.now().isoformat()
                elif status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.SKIPPED]:
                    update_data["completed_at"] = datetime.now().isoformat()
            
            if suna_agent_run_id is not None:
                update_data["suna_agent_run_id"] = str(suna_agent_run_id)
            
            if input_data is not None:
                update_data["input_data"] = input_data
            
            if output_data is not None:
                update_data["output_data"] = output_data
            
            if context_snapshot is not None:
                update_data["context_snapshot"] = context_snapshot
            
            if error_message is not None:
                update_data["error_message"] = error_message
            
            if individual_cost_metrics is not None:
                update_data["individual_cost_metrics"] = individual_cost_metrics
            
            if individual_usage_metrics is not None:
                update_data["individual_usage_metrics"] = individual_usage_metrics
            
            if api_keys_snapshot is not None:
                update_data["api_keys_snapshot"] = api_keys_snapshot
            
            # Atualiza no banco de dados se houver dados para atualizar
            if update_data:
                await self.db.table('renum_team_agent_executions') \
                    .update(update_data) \
                    .eq('execution_id', str(execution_id)) \
                    .eq('agent_id', agent_id) \
                    .execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent execution {execution_id}/{agent_id}: {str(e)}")
            return False
    
    async def get_agent_execution(
        self, 
        execution_id: UUID, 
        agent_id: str
    ) -> Optional[TeamAgentExecutionResponse]:
        """
        Obtém os dados de uma execução de agente.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            
        Returns:
            Objeto TeamAgentExecutionResponse ou None se não existir
        """
        try:
            # Consulta o banco de dados
            result = await self.db.table('renum_team_agent_executions') \
                .select('*') \
                .eq('execution_id', str(execution_id)) \
                .eq('agent_id', agent_id) \
                .execute()
            
            if not result.data:
                return None
            
            agent_execution = result.data[0]
            
            # Converte para objeto TeamAgentExecutionResponse
            return TeamAgentExecutionResponse(
                execution_id=agent_execution['execution_id'],
                agent_id=agent_execution['agent_id'],
                suna_agent_run_id=agent_execution.get('suna_agent_run_id'),
                step_order=agent_execution['step_order'],
                status=ExecutionStatus(agent_execution['status']),
                input_data=agent_execution.get('input_data', {}),
                output_data=agent_execution.get('output_data'),
                error_message=agent_execution.get('error_message'),
                started_at=datetime.fromisoformat(agent_execution['started_at']) if agent_execution.get('started_at') else None,
                completed_at=datetime.fromisoformat(agent_execution['completed_at']) if agent_execution.get('completed_at') else None
            )
            
        except Exception as e:
            logger.error(f"Failed to get agent execution {execution_id}/{agent_id}: {str(e)}")
            return None
    
    async def list_agent_executions(
        self, 
        execution_id: UUID
    ) -> List[TeamAgentExecutionResponse]:
        """
        Lista execuções de agentes para uma execução de equipe.
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Lista de objetos TeamAgentExecutionResponse
        """
        try:
            # Consulta o banco de dados
            result = await self.db.table('renum_team_agent_executions') \
                .select('*') \
                .eq('execution_id', str(execution_id)) \
                .order('step_order') \
                .execute()
            
            # Converte para objetos TeamAgentExecutionResponse
            agent_executions = []
            for agent_execution in result.data:
                agent_executions.append(TeamAgentExecutionResponse(
                    execution_id=agent_execution['execution_id'],
                    agent_id=agent_execution['agent_id'],
                    suna_agent_run_id=agent_execution.get('suna_agent_run_id'),
                    step_order=agent_execution['step_order'],
                    status=ExecutionStatus(agent_execution['status']),
                    input_data=agent_execution.get('input_data', {}),
                    output_data=agent_execution.get('output_data'),
                    error_message=agent_execution.get('error_message'),
                    started_at=datetime.fromisoformat(agent_execution['started_at']) if agent_execution.get('started_at') else None,
                    completed_at=datetime.fromisoformat(agent_execution['completed_at']) if agent_execution.get('completed_at') else None
                ))
            
            return agent_executions
            
        except Exception as e:
            logger.error(f"Failed to list agent executions for {execution_id}: {str(e)}")
            return []
    
    async def get_execution_logs(
        self, 
        execution_id: UUID, 
        limit: int = 100,
        offset: int = 0,
        log_types: Optional[List[str]] = None,
        agent_id: Optional[str] = None
    ) -> List[ExecutionLogEntry]:
        """
        Obtém logs de execução.
        
        Args:
            execution_id: ID da execução
            limit: Limite de resultados
            offset: Deslocamento para paginação
            log_types: Tipos de log a serem incluídos
            agent_id: Filtrar por agente específico
            
        Returns:
            Lista de objetos ExecutionLogEntry
        """
        try:
            # Implementação simplificada - em um sistema real, teria uma tabela de logs
            # Aqui, simulamos logs com base nas execuções de agentes
            
            # Obtém as execuções de agentes
            agent_executions = await self.list_agent_executions(execution_id)
            
            # Filtra por agente se especificado
            if agent_id:
                agent_executions = [
                    execution for execution in agent_executions
                    if execution.agent_id == agent_id
                ]
            
            # Gera logs com base nas execuções
            logs = []
            
            for agent_execution in agent_executions:
                # Log de início
                if agent_execution.started_at:
                    logs.append(ExecutionLogEntry(
                        timestamp=agent_execution.started_at,
                        level="info",
                        agent_id=agent_execution.agent_id,
                        message=f"Agent execution started",
                        details={
                            "step_order": agent_execution.step_order,
                            "suna_agent_run_id": agent_execution.suna_agent_run_id
                        }
                    ))
                
                # Log de conclusão
                if agent_execution.completed_at:
                    if agent_execution.status == ExecutionStatus.COMPLETED:
                        logs.append(ExecutionLogEntry(
                            timestamp=agent_execution.completed_at,
                            level="info",
                            agent_id=agent_execution.agent_id,
                            message=f"Agent execution completed successfully",
                            details={
                                "step_order": agent_execution.step_order,
                                "execution_time": (agent_execution.completed_at - agent_execution.started_at).total_seconds() if agent_execution.started_at else None
                            }
                        ))
                    elif agent_execution.status == ExecutionStatus.FAILED:
                        logs.append(ExecutionLogEntry(
                            timestamp=agent_execution.completed_at,
                            level="error",
                            agent_id=agent_execution.agent_id,
                            message=f"Agent execution failed: {agent_execution.error_message}",
                            details={
                                "step_order": agent_execution.step_order,
                                "error_message": agent_execution.error_message
                            }
                        ))
                    elif agent_execution.status == ExecutionStatus.SKIPPED:
                        logs.append(ExecutionLogEntry(
                            timestamp=agent_execution.completed_at,
                            level="info",
                            agent_id=agent_execution.agent_id,
                            message=f"Agent execution skipped",
                            details={
                                "step_order": agent_execution.step_order
                            }
                        ))
                    elif agent_execution.status == ExecutionStatus.CANCELLED:
                        logs.append(ExecutionLogEntry(
                            timestamp=agent_execution.completed_at,
                            level="warning",
                            agent_id=agent_execution.agent_id,
                            message=f"Agent execution cancelled",
                            details={
                                "step_order": agent_execution.step_order
                            }
                        ))
            
            # Ordena por timestamp
            logs.sort(key=lambda log: log.timestamp)
            
            # Filtra por tipo de log se especificado
            if log_types:
                logs = [log for log in logs if log.level in log_types]
            
            # Aplica paginação
            return logs[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to get execution logs for {execution_id}: {str(e)}")
            return []