"""
Motor de execução para equipes de agentes.

Este módulo implementa o motor de execução para equipes de agentes,
responsável por criar e executar planos de execução com base nas definições de workflow.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
from datetime import datetime

from app.models.team_models import (
    TeamConfig,
    WorkflowType,
    ExecutionPlan,
    ExecutionStep,
    InputSource,
    AgentCondition,
    ExecutionStatus
)
# from app.repositories.team_execution_repository import TeamExecutionRepository
from app.services.suna_api_client import SunaApiClient
from app.services.team_context_manager import TeamContextManager
from app.services.team_message_bus import TeamMessageBus
from app.services.api_key_manager import ApiKeyManager
from app.services.websocket_manager import WebSocketManager
# from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Motor de execução para equipes de agentes."""
    
    def __init__(
        self,
        # execution_repository: TeamExecutionRepository,
        suna_client: SunaApiClient,
        context_manager: TeamContextManager,
        message_bus: TeamMessageBus,
        api_key_manager: ApiKeyManager,
        websocket_manager: WebSocketManager = None
    ):
        """
        Inicializa o motor de execução.
        
        Args:
            execution_repository: Repositório de execuções
            suna_client: Cliente da API do Suna Core
            context_manager: Gerenciador de contexto compartilhado
            message_bus: Sistema de mensagens entre agentes
            api_key_manager: Gerenciador de API keys
            websocket_manager: Gerenciador de WebSocket para eventos em tempo real
        """
        self.execution_repository = execution_repository
        self.suna_client = suna_client
        self.context_manager = context_manager
        self.message_bus = message_bus
        self.api_key_manager = api_key_manager
        self.websocket_manager = websocket_manager
    
    async def create_execution_plan(
        self, 
        team_config: TeamConfig,
        execution_id: UUID
    ) -> ExecutionPlan:
        """
        Cria um plano de execução com base na configuração da equipe.
        
        Args:
            team_config: Configuração da equipe
            execution_id: ID da execução
            
        Returns:
            Plano de execução
        """
        workflow_def = team_config.workflow_definition
        workflow_type = workflow_def.type
        
        # Cria os passos de execução
        steps = []
        dependencies = {}
        
        # Processa os agentes conforme o tipo de workflow
        if workflow_type == WorkflowType.SEQUENTIAL:
            # Ordena os agentes por ordem de execução
            sorted_agents = sorted(workflow_def.agents, key=lambda a: a.execution_order or 0)
            
            for i, agent_config in enumerate(sorted_agents):
                step = ExecutionStep(
                    agent_id=agent_config.agent_id,
                    step_order=i,
                    input_config=agent_config.input,
                    dependencies=[sorted_agents[i-1].agent_id] if i > 0 else []
                )
                steps.append(step)
                
                # Registra dependências
                if i > 0:
                    dependencies[agent_config.agent_id] = [sorted_agents[i-1].agent_id]
        
        elif workflow_type == WorkflowType.PARALLEL:
            # Todos os agentes executam simultaneamente
            for i, agent_config in enumerate(workflow_def.agents):
                step = ExecutionStep(
                    agent_id=agent_config.agent_id,
                    step_order=i,
                    input_config=agent_config.input,
                    dependencies=[]
                )
                steps.append(step)
                
                # Sem dependências
                dependencies[agent_config.agent_id] = []
        
        elif workflow_type == WorkflowType.CONDITIONAL:
            # Agentes executam com base em condições
            for i, agent_config in enumerate(workflow_def.agents):
                step = ExecutionStep(
                    agent_id=agent_config.agent_id,
                    step_order=i,
                    input_config=agent_config.input,
                    conditions=agent_config.conditions,
                    dependencies=[]  # Dependências são determinadas em tempo de execução
                )
                steps.append(step)
        
        elif workflow_type == WorkflowType.PIPELINE:
            # Saída de um agente é entrada do próximo
            sorted_agents = sorted(workflow_def.agents, key=lambda a: a.execution_order or 0)
            
            for i, agent_config in enumerate(sorted_agents):
                # Configura a entrada para usar a saída do agente anterior
                # TODO: Implementar InputConfig quando disponível
                input_config = agent_config.input
                
                step = ExecutionStep(
                    agent_id=agent_config.agent_id,
                    step_order=i,
                    input_config=input_config,
                    dependencies=[sorted_agents[i-1].agent_id] if i > 0 else []
                )
                steps.append(step)
                
                # Registra dependências
                if i > 0:
                    dependencies[agent_config.agent_id] = [sorted_agents[i-1].agent_id]
        
        # Cria o plano de execução
        execution_plan = ExecutionPlan(
            execution_id=execution_id,
            team_id=team_config.team_id,
            workflow_type=workflow_type,
            steps=steps,
            dependencies=dependencies,
            estimated_duration=self._estimate_duration(workflow_type, len(steps))
        )
        
        # Salva o plano no banco de dados
        await self.execution_repository.update_execution_plan(execution_id, execution_plan.dict())
        
        return execution_plan
    
    async def execute_plan(
        self, 
        execution_id: UUID,
        team_config: TeamConfig,
        initial_prompt: str
    ) -> bool:
        """
        Executa um plano de execução.
        
        Args:
            execution_id: ID da execução
            team_config: Configuração da equipe
            initial_prompt: Prompt inicial
            
        Returns:
            True se a execução foi bem-sucedida
        """
        # Atualiza o status da execução para "running"
        await self.execution_repository.update_execution_status(execution_id, ExecutionStatus.RUNNING)
        
        # Emite evento de início de execução
        await self._emit_execution_event(
            execution_id,
            "execution_started",
            {
                "status": "running",
                "team_id": str(team_config.team_id),
                "workflow_type": team_config.workflow_definition.type.value,
                "message": "Execução iniciada"
            },
            team_config.user_id
        )
        
        try:
            # Cria o plano de execução
            execution_plan = await self.create_execution_plan(team_config, execution_id)
            
            # Emite evento de plano criado
            await self._emit_execution_event(
                execution_id,
                "plan_created",
                {
                    "status": "running",
                    "total_steps": len(execution_plan.steps),
                    "estimated_duration": execution_plan.estimated_duration,
                    "message": f"Plano de execução criado com {len(execution_plan.steps)} passos"
                }
            )
            
            # Inicializa o contexto compartilhado
            await self.context_manager.create_context(execution_id, {
                "initial_prompt": initial_prompt,
                "team_id": str(team_config.team_id),
                "execution_id": str(execution_id),
                "workflow_type": execution_plan.workflow_type.value
            })
            
            # Obtém as API keys do usuário
            user_api_keys = await self.api_key_manager.get_user_api_keys(team_config.user_id)
            
            # Executa o plano conforme o tipo de workflow
            if execution_plan.workflow_type == WorkflowType.SEQUENTIAL:
                success = await self._execute_sequential_plan(execution_id, execution_plan, initial_prompt, user_api_keys, team_config.user_id)
            elif execution_plan.workflow_type == WorkflowType.PARALLEL:
                success = await self._execute_parallel_plan(execution_id, execution_plan, initial_prompt, user_api_keys, team_config.user_id)
            elif execution_plan.workflow_type == WorkflowType.CONDITIONAL:
                success = await self._execute_conditional_plan(execution_id, execution_plan, initial_prompt, user_api_keys, team_config.user_id)
            elif execution_plan.workflow_type == WorkflowType.PIPELINE:
                success = await self._execute_pipeline_plan(execution_id, execution_plan, initial_prompt, user_api_keys, team_config.user_id)
            else:
                raise ValueError(f"Unsupported workflow type: {execution_plan.workflow_type}")
            
            # Atualiza o status da execução
            final_status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED
            await self.execution_repository.update_execution_status(
                execution_id, 
                final_status,
                error_message=None if success else "Execution failed"
            )
            
            # Consolida os resultados
            if success:
                await self._consolidate_results(execution_id, execution_plan)
            
            # Emite evento de conclusão
            await self._emit_execution_event(
                execution_id,
                "execution_completed" if success else "execution_failed",
                {
                    "status": final_status.value,
                    "message": "Execução concluída com sucesso" if success else "Execução falhou",
                    "progress": 100 if success else 0
                },
                team_config.user_id
            )
            
            return success
        
        except Exception as e:
            logger.error(f"Error executing plan: {str(e)}", exc_info=True)
            
            # Atualiza o status da execução para "failed"
            await self.execution_repository.update_execution_status(
                execution_id, 
                ExecutionStatus.FAILED,
                error_message=f"Error executing plan: {str(e)}"
            )
            
            # Emite evento de erro
            await self._emit_execution_event(
                execution_id,
                "execution_failed",
                {
                    "status": "failed",
                    "error": str(e),
                    "message": f"Erro na execução: {str(e)}"
                },
                team_config.user_id
            )
            
            return False    
   
    async def _execute_sequential_plan(
        self, 
        execution_id: UUID,
        execution_plan: ExecutionPlan,
        initial_prompt: str,
        user_api_keys: Dict[str, str],
        user_id: str
    ) -> bool:
        """
        Executa um plano sequencial.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
            initial_prompt: Prompt inicial
            user_api_keys: API keys do usuário
            
        Returns:
            True se a execução foi bem-sucedida
        """
        logger.info(f"Executing sequential plan for execution {execution_id}")
        
        # Ordena os passos por ordem de execução
        steps = sorted(execution_plan.steps, key=lambda s: s.step_order)
        total_steps = len(steps)
        
        # Executa cada passo sequencialmente
        for i, step in enumerate(steps):
            # Emite evento de progresso
            progress = int((i / total_steps) * 100)
            await self._emit_execution_event(
                execution_id,
                "execution_progress",
                {
                    "status": "running",
                    "progress": progress,
                    "current_step": f"Executando agente {step.agent_id}",
                    "step_number": i + 1,
                    "total_steps": total_steps
                }
            )
            
            success = await self._execute_step(execution_id, step, initial_prompt, user_api_keys)
            
            if not success:
                logger.error(f"Step {step.step_id} (agent {step.agent_id}) failed, aborting execution {execution_id}")
                return False
        
        return True
    
    async def _execute_parallel_plan(
        self, 
        execution_id: UUID,
        execution_plan: ExecutionPlan,
        initial_prompt: str,
        user_api_keys: Dict[str, str],
        user_id: str
    ) -> bool:
        """
        Executa um plano paralelo.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
            initial_prompt: Prompt inicial
            user_api_keys: API keys do usuário
            
        Returns:
            True se a execução foi bem-sucedida
        """
        logger.info(f"Executing parallel plan for execution {execution_id}")
        
        # Cria tasks para todos os passos
        tasks = []
        for step in execution_plan.steps:
            task = asyncio.create_task(
                self._execute_step(execution_id, step, initial_prompt, user_api_keys)
            )
            tasks.append(task)
        
        # Aguarda a conclusão de todas as tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verifica se houve falhas
        failures = [i for i, result in enumerate(results) if isinstance(result, Exception) or not result]
        
        if failures:
            logger.error(f"Parallel execution {execution_id} had {len(failures)} failures")
            return False
        
        return True
    
    async def _execute_conditional_plan(
        self, 
        execution_id: UUID,
        execution_plan: ExecutionPlan,
        initial_prompt: str,
        user_api_keys: Dict[str, str],
        user_id: str
    ) -> bool:
        """
        Executa um plano condicional.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
            initial_prompt: Prompt inicial
            user_api_keys: API keys do usuário
            
        Returns:
            True se a execução foi bem-sucedida
        """
        logger.info(f"Executing conditional plan for execution {execution_id}")
        
        # Encontra o primeiro agente (sem condições)
        first_steps = [step for step in execution_plan.steps if not step.conditions]
        
        if not first_steps:
            logger.error(f"No initial step found for conditional execution {execution_id}")
            return False
        
        # Executa o primeiro agente
        first_step = min(first_steps, key=lambda s: s.step_order)
        success = await self._execute_step(execution_id, first_step, initial_prompt, user_api_keys)
        
        if not success:
            logger.error(f"Initial step {first_step.step_id} (agent {first_step.agent_id}) failed, aborting execution {execution_id}")
            return False
        
        # Obtém o contexto atual
        context = await self.context_manager.get_all_variables(execution_id)
        
        # Executa os agentes condicionais
        conditional_steps = [step for step in execution_plan.steps if step.conditions and step.agent_id != first_step.agent_id]
        
        for step in conditional_steps:
            # Avalia as condições
            should_execute = await self._evaluate_conditions(step.conditions, context)
            
            if should_execute:
                # Executa o agente
                success = await self._execute_step(execution_id, step, initial_prompt, user_api_keys)
                
                if not success:
                    logger.error(f"Conditional step {step.step_id} (agent {step.agent_id}) failed in execution {execution_id}")
                    # Não aborta a execução, continua com os próximos agentes
            else:
                # Marca o agente como pulado
                await self.execution_repository.update_agent_execution(
                    execution_id,
                    step.agent_id,
                    status=ExecutionStatus.SKIPPED
                )
                
                logger.info(f"Skipped conditional step {step.step_id} (agent {step.agent_id}) in execution {execution_id}")
        
        return True
    
    async def _execute_pipeline_plan(
        self, 
        execution_id: UUID,
        execution_plan: ExecutionPlan,
        initial_prompt: str,
        user_api_keys: Dict[str, str],
        user_id: str
    ) -> bool:
        """
        Executa um plano em pipeline.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
            initial_prompt: Prompt inicial
            user_api_keys: API keys do usuário
            
        Returns:
            True se a execução foi bem-sucedida
        """
        logger.info(f"Executing pipeline plan for execution {execution_id}")
        
        # Ordena os passos por ordem de execução
        steps = sorted(execution_plan.steps, key=lambda s: s.step_order)
        
        # Executa cada passo sequencialmente, passando a saída para o próximo
        previous_output = initial_prompt
        
        for step in steps:
            # Configura a entrada para usar a saída do agente anterior
            if step.step_order > 0:
                # Atualiza o contexto com a saída do agente anterior
                await self.context_manager.set_variable(
                    execution_id,
                    f"pipeline_input",
                    previous_output,
                    "system"
                )
            
            # Executa o agente
            success = await self._execute_step(execution_id, step, previous_output, user_api_keys)
            
            if not success:
                logger.error(f"Pipeline step {step.step_id} (agent {step.agent_id}) failed, aborting execution {execution_id}")
                return False
            
            # Obtém a saída do agente para o próximo passo
            agent_execution = await self.execution_repository.get_agent_execution(execution_id, step.agent_id)
            if agent_execution and agent_execution.output_data:
                previous_output = agent_execution.output_data.get("result", previous_output)
        
        return True
    
    async def _execute_step(
        self, 
        execution_id: UUID,
        step: ExecutionStep,
        initial_prompt: str,
        user_api_keys: Dict[str, str]
    ) -> bool:
        """
        Executa um passo do plano.
        
        Args:
            execution_id: ID da execução
            step: Passo a ser executado
            initial_prompt: Prompt inicial
            user_api_keys: API keys do usuário
            
        Returns:
            True se a execução foi bem-sucedida
        """
        agent_id = step.agent_id
        logger.info(f"Executing step for agent {agent_id} in execution {execution_id}")
        
        try:
            # Registra o início da execução do agente
            await self.execution_repository.create_agent_execution(
                execution_id,
                agent_id,
                step.step_order
            )
            
            # Atualiza o status para "running"
            await self.execution_repository.update_agent_execution(
                execution_id,
                agent_id,
                status=ExecutionStatus.RUNNING
            )
            
            # Emite evento de início do passo
            await self._emit_step_event(
                execution_id,
                agent_id,
                "step_started",
                {
                    "status": "running",
                    "step_order": step.step_order,
                    "message": f"Iniciando execução do agente {agent_id}"
                }
            )
            
            # Prepara o prompt para o agente
            prompt = await self._prepare_agent_prompt(execution_id, step, initial_prompt)
            
            # Cria uma thread no Suna Core
            thread_id = await self.suna_client.create_thread()
            
            # Importa a integração com o ThreadManager
            from app.services.thread_manager_integration import TeamThreadManagerIntegration
            from app.core.dependencies import get_team_context_manager, get_team_message_bus
            
            # Cria a integração com o ThreadManager
            context_manager = await get_team_context_manager()
            message_bus = await get_team_message_bus()
            thread_manager_integration = TeamThreadManagerIntegration(context_manager, message_bus)
            
            # Obtém o ThreadManager do Suna Core
            from agentpress.thread_manager import ThreadManager
            
            # Cria um ThreadManager estendido com funcionalidades de equipe
            thread_manager = await thread_manager_integration.create_team_thread_manager(
                ThreadManager,
                execution_id,
                agent_id
            )
            
            # Executa o agente no Suna Core com o ThreadManager estendido
            suna_agent_run_id = await self.suna_client.execute_agent_with_thread_manager(
                agent_id,
                thread_id,
                prompt,
                user_api_keys,
                thread_manager
            )
            
            # Atualiza o ID da execução no Suna Core
            await self.execution_repository.update_agent_execution(
                execution_id,
                agent_id,
                suna_agent_run_id=UUID(suna_agent_run_id)
            )
            
            # Aguarda a conclusão do agente
            result = await self.suna_client.wait_for_agent_completion(suna_agent_run_id)
            
            # Atualiza o resultado da execução do agente
            await self.execution_repository.update_agent_execution(
                execution_id,
                agent_id,
                status=ExecutionStatus.COMPLETED,
                output_data=result
            )
            
            # Atualiza o contexto compartilhado com o resultado
            await self.context_manager.set_variable(
                execution_id,
                f"agent_{agent_id}_result",
                result,
                agent_id
            )
            
            # Emite evento de conclusão do passo
            await self._emit_step_event(
                execution_id,
                agent_id,
                "step_completed",
                {
                    "status": "completed",
                    "step_order": step.step_order,
                    "result": result,
                    "message": f"Agente {agent_id} executado com sucesso"
                }
            )
            
            logger.info(f"Successfully executed agent {agent_id} in execution {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing agent {agent_id} in execution {execution_id}: {str(e)}", exc_info=True)
            
            # Atualiza o status para "failed"
            await self.execution_repository.update_agent_execution(
                execution_id,
                agent_id,
                status=ExecutionStatus.FAILED,
                error_message=str(e)
            )
            
            # Emite evento de falha do passo
            await self._emit_step_event(
                execution_id,
                agent_id,
                "step_failed",
                {
                    "status": "failed",
                    "step_order": step.step_order,
                    "error": str(e),
                    "message": f"Falha na execução do agente {agent_id}: {str(e)}"
                }
            )
            
            return False
    
    async def _prepare_agent_prompt(
        self, 
        execution_id: UUID,
        step: ExecutionStep,
        initial_prompt: str
    ) -> str:
        """
        Prepara o prompt para um agente com base na configuração de entrada.
        
        Args:
            execution_id: ID da execução
            step: Passo a ser executado
            initial_prompt: Prompt inicial
            
        Returns:
            Prompt para o agente
        """
        input_config = step.input_config
        source = input_config.source
        
        if source == InputSource.INITIAL_PROMPT:
            return initial_prompt
        
        elif source == InputSource.AGENT_RESULT:
            # Obtém o resultado do agente especificado
            agent_id = input_config.agent_id
            if not agent_id:
                raise ValueError(f"agent_id is required for input source {source}")
            
            result = await self.context_manager.get_variable(execution_id, f"agent_{agent_id}_result")
            if not result:
                raise ValueError(f"Result for agent {agent_id} not found in context")
            
            # Extrai o resultado do agente
            if isinstance(result, dict) and "result" in result:
                return result["result"]
            else:
                return str(result)
        
        elif source == InputSource.COMBINED:
            # Combina resultados de múltiplos agentes
            sources = input_config.sources
            if not sources:
                raise ValueError(f"sources is required for input source {source}")
            
            combined_results = []
            
            for source_info in sources:
                source_type = source_info.get("type")
                source_agent_id = source_info.get("agent_id")
                
                if source_type == "agent_result" and source_agent_id:
                    result = await self.context_manager.get_variable(execution_id, f"agent_{source_agent_id}_result")
                    if result:
                        if isinstance(result, dict) and "result" in result:
                            combined_results.append(result["result"])
                        else:
                            combined_results.append(str(result))
            
            # Combina os resultados
            return "\n\n".join(combined_results)
        
        elif source == InputSource.CONTEXT_VARIABLE:
            # Obtém uma variável específica do contexto
            variable_name = input_config.variable_name
            if not variable_name:
                raise ValueError(f"variable_name is required for input source {source}")
            
            value = await self.context_manager.get_variable(execution_id, variable_name)
            if value is None:
                raise ValueError(f"Variable {variable_name} not found in context")
            
            return str(value)
        
        else:
            raise ValueError(f"Unsupported input source: {source}")
    
    async def _evaluate_conditions(
        self, 
        conditions: List[AgentCondition],
        context: Dict[str, Any]
    ) -> bool:
        """
        Avalia condições para execução condicional.
        
        Args:
            conditions: Lista de condições
            context: Contexto atual
            
        Returns:
            True se todas as condições forem satisfeitas
        """
        if not conditions:
            return True
        
        for condition in conditions:
            field = condition.field
            operator = condition.operator
            value = condition.value
            
            # Obtém o valor do campo do contexto
            field_parts = field.split('.')
            field_value = context
            
            try:
                for part in field_parts:
                    field_value = field_value.get(part)
                    if field_value is None:
                        return False
            except (AttributeError, TypeError):
                return False
            
            # Avalia a condição
            if operator == "equals":
                if field_value != value:
                    return False
            
            elif operator == "not_equals":
                if field_value == value:
                    return False
            
            elif operator == "contains":
                if isinstance(field_value, (str, list, dict)):
                    if value not in field_value:
                        return False
                else:
                    return False
            
            elif operator == "not_contains":
                if isinstance(field_value, (str, list, dict)):
                    if value in field_value:
                        return False
                else:
                    return True
            
            elif operator == "greater_than":
                if not isinstance(field_value, (int, float)) or not isinstance(value, (int, float)):
                    return False
                if field_value <= value:
                    return False
            
            elif operator == "less_than":
                if not isinstance(field_value, (int, float)) or not isinstance(value, (int, float)):
                    return False
                if field_value >= value:
                    return False
            
            elif operator == "exists":
                # Já verificamos a existência acima
                pass
            
            elif operator == "not_exists":
                return False
        
        return True
    
    async def _consolidate_results(self, execution_id: UUID, execution_plan: ExecutionPlan):
        """
        Consolida os resultados de uma execução.
        
        Args:
            execution_id: ID da execução
            execution_plan: Plano de execução
        """
        # Obtém os resultados de todos os agentes
        agent_executions = await self.execution_repository.list_agent_executions(execution_id)
        
        # Organiza os resultados por agente
        agent_results = {}
        for agent_execution in agent_executions:
            if agent_execution.output_data:
                agent_results[agent_execution.agent_id] = agent_execution.output_data
        
        # Determina o resultado final com base no tipo de workflow
        final_result = {}
        
        if execution_plan.workflow_type == WorkflowType.SEQUENTIAL:
            # O resultado final é o resultado do último agente
            last_step = max(execution_plan.steps, key=lambda s: s.step_order)
            if last_step.agent_id in agent_results:
                final_result = agent_results[last_step.agent_id]
        
        elif execution_plan.workflow_type == WorkflowType.PARALLEL:
            # O resultado final é a combinação dos resultados de todos os agentes
            final_result = {
                "agent_results": agent_results,
                "summary": "Parallel execution completed"
            }
        
        elif execution_plan.workflow_type == WorkflowType.CONDITIONAL:
            # O resultado final é a combinação dos resultados dos agentes executados
            executed_agents = [
                agent_execution.agent_id for agent_execution in agent_executions
                if agent_execution.status == ExecutionStatus.COMPLETED
            ]
            
            final_result = {
                "executed_agents": executed_agents,
                "agent_results": {
                    agent_id: agent_results[agent_id]
                    for agent_id in executed_agents
                    if agent_id in agent_results
                },
                "summary": "Conditional execution completed"
            }
        
        elif execution_plan.workflow_type == WorkflowType.PIPELINE:
            # O resultado final é o resultado do último agente
            last_step = max(execution_plan.steps, key=lambda s: s.step_order)
            if last_step.agent_id in agent_results:
                final_result = agent_results[last_step.agent_id]
        
        # Atualiza o resultado final da execução
        await self.execution_repository.update_execution_result(execution_id, final_result)
    
    async def _emit_execution_event(
        self,
        execution_id: UUID,
        event_type: str,
        data: Dict[str, Any],
        user_id: str = None
    ):
        """
        Emite um evento de execução via WebSocket.
        
        Args:
            execution_id: ID da execução
            event_type: Tipo do evento
            data: Dados do evento
            user_id: ID do usuário (opcional)
        """
        if not self.websocket_manager:
            return
            
        try:
            # Cria a mensagem do evento
            event_message = {
                "type": "execution_update",
                "execution_id": str(execution_id),
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Envia para o canal específico da execução
            await self.websocket_manager.broadcast_execution_update(
                execution_id,
                event_message
            )
            
            # Se temos o user_id, envia notificação personalizada
            if user_id and event_type in ["execution_completed", "execution_failed"]:
                await notification_service.send_execution_notification(
                    user_id,
                    str(execution_id),
                    data.get("status", "unknown"),
                    data.get("message")
                )
                
        except Exception as e:
            logger.error(f"Error emitting execution event: {str(e)}")

    async def _emit_step_event(
        self,
        execution_id: UUID,
        agent_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Emite um evento de passo de execução via WebSocket.
        
        Args:
            execution_id: ID da execução
            agent_id: ID do agente
            event_type: Tipo do evento
            data: Dados do evento
        """
        if not self.websocket_manager:
            return
            
        try:
            # Cria a mensagem do evento
            event_message = {
                "type": "step_update",
                "execution_id": str(execution_id),
                "agent_id": agent_id,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Envia para o canal específico da execução
            await self.websocket_manager.broadcast_execution_update(
                execution_id,
                event_message
            )
                
        except Exception as e:
            logger.error(f"Error emitting step event: {str(e)}")

    def _estimate_duration(self, workflow_type: WorkflowType, num_agents: int) -> int:
        """
        Estima a duração de uma execução em segundos.
        
        Args:
            workflow_type: Tipo de workflow
            num_agents: Número de agentes
            
        Returns:
            Duração estimada em segundos
        """
        # Tempo base por agente (em segundos)
        base_time_per_agent = 30
        
        if workflow_type == WorkflowType.SEQUENTIAL or workflow_type == WorkflowType.PIPELINE:
            # Execução sequencial: tempo total = soma dos tempos individuais
            return num_agents * base_time_per_agent
        
        elif workflow_type == WorkflowType.PARALLEL:
            # Execução paralela: tempo total = tempo do agente mais lento
            return base_time_per_agent
        
        elif workflow_type == WorkflowType.CONDITIONAL:
            # Execução condicional: estimativa conservadora
            return int(num_agents * base_time_per_agent * 0.7)
        
        else:
            return num_agents * base_time_per_agent
    
    def estimate_duration(self, workflow_type: WorkflowType, num_steps: int) -> int:
        """
        Estima a duração de uma execução em segundos.
        
        Args:
            workflow_type: Tipo de workflow
            num_steps: Número de passos
            
        Returns:
            Duração estimada em segundos
        """
        # Tempo médio por agente (em segundos)
        avg_agent_time = 60
        
        if workflow_type == WorkflowType.SEQUENTIAL or workflow_type == WorkflowType.PIPELINE:
            # Tempo total é a soma dos tempos de cada agente
            return avg_agent_time * num_steps
        
        elif workflow_type == WorkflowType.PARALLEL:
            # Tempo total é o tempo do agente mais lento
            return avg_agent_time
        
        elif workflow_type == WorkflowType.CONDITIONAL:
            # Tempo total é uma estimativa baseada no número de agentes
            # Assumindo que em média 70% dos agentes serão executados
            return avg_agent_time * int(num_steps * 0.7)
        
        return avg_agent_time * num_steps