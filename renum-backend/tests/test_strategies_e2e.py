"""
Testes end-to-end para as estratégias de execução.

Este módulo contém testes que verificam o comportamento completo das estratégias
de execução, incluindo cenários de sucesso, falha e recuperação.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
import time
from datetime import datetime

from app.services.execution_engine import ExecutionEngine
from app.services.team_orchestrator import TeamOrchestrator
from app.services.strategies.sequential_strategy import SequentialStrategy
from app.services.strategies.parallel_strategy import ParallelStrategy
from app.services.strategies.pipeline_strategy import PipelineStrategy
from app.services.strategies.conditional_strategy import ConditionalStrategy
from app.models.team_models import (
    RenumTeamConfig, 
    WorkflowDefinition, 
    WorkflowAgent, 
    ExecutionPlan,
    AgentExecutionResult,
    ExecutionStatus,
    InputConfig,
    InputSource,
    AgentCondition,
    WorkflowType
)


class TestStrategiesE2E:
    """Testes end-to-end para as estratégias de execução."""

    @pytest.fixture
    def mock_suna_client(self):
        """Mock para o cliente Suna API."""
        mock = AsyncMock()
        
        # Configura o comportamento padrão para execução de agente
        async def execute_agent(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)  # Simula algum processamento
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
            
        mock.execute_agent = AsyncMock(side_effect=execute_agent)
        mock.get_execution_status = AsyncMock(return_value={"status": "completed"})
        mock.get_execution_result = AsyncMock(return_value={"result": "Resultado do agente"})
        
        return mock
    
    @pytest.fixture
    def mock_context_manager(self):
        """Mock para o gerenciador de contexto."""
        mock = AsyncMock()
        mock.get_context = AsyncMock(return_value={"context_data": "dados de contexto"})
        mock.update_context = AsyncMock()
        mock.create_snapshot = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_message_bus(self):
        """Mock para o barramento de mensagens."""
        mock = AsyncMock()
        mock.send_message = AsyncMock()
        mock.broadcast = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_execution_repository(self):
        """Mock para o repositório de execuções."""
        mock = AsyncMock()
        mock.create_execution = AsyncMock(return_value="exec_123")
        mock.update_execution_status = AsyncMock()
        mock.update_execution_result = AsyncMock()
        mock.create_agent_execution = AsyncMock(return_value="agent_exec_123")
        mock.update_agent_execution = AsyncMock()
        return mock
    
    @pytest.fixture
    def execution_engine(self, mock_suna_client, mock_context_manager, mock_message_bus, mock_execution_repository):
        """Fixture para o motor de execução."""
        engine = ExecutionEngine(
            suna_client=mock_suna_client,
            context_manager=mock_context_manager,
            message_bus=mock_message_bus,
            execution_repository=mock_execution_repository
        )
        return engine
    
    @pytest.fixture
    def sequential_workflow(self):
        """Fixture para um workflow sequencial."""
        return WorkflowDefinition(
            type=WorkflowType.SEQUENTIAL,
            agents=[
                WorkflowAgent(
                    agent_id="agent1",
                    role="leader",
                    execution_order=1,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                WorkflowAgent(
                    agent_id="agent2",
                    role="member",
                    execution_order=2,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent1")
                ),
                WorkflowAgent(
                    agent_id="agent3",
                    role="member",
                    execution_order=3,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent2")
                )
            ]
        )
    
    @pytest.fixture
    def parallel_workflow(self):
        """Fixture para um workflow paralelo."""
        return WorkflowDefinition(
            type=WorkflowType.PARALLEL,
            agents=[
                WorkflowAgent(
                    agent_id="agent1",
                    role="member",
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                WorkflowAgent(
                    agent_id="agent2",
                    role="member",
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                WorkflowAgent(
                    agent_id="agent3",
                    role="member",
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                )
            ]
        )
    
    @pytest.fixture
    def pipeline_workflow(self):
        """Fixture para um workflow de pipeline."""
        return WorkflowDefinition(
            type=WorkflowType.PIPELINE,
            agents=[
                WorkflowAgent(
                    agent_id="agent1",
                    role="processor",
                    execution_order=1,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                WorkflowAgent(
                    agent_id="agent2",
                    role="processor",
                    execution_order=2,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent1")
                ),
                WorkflowAgent(
                    agent_id="agent3",
                    role="processor",
                    execution_order=3,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent2")
                )
            ]
        )
    
    @pytest.fixture
    def conditional_workflow(self):
        """Fixture para um workflow condicional."""
        return WorkflowDefinition(
            type=WorkflowType.CONDITIONAL,
            agents=[
                WorkflowAgent(
                    agent_id="agent1",
                    role="evaluator",
                    execution_order=1,
                    input=InputConfig(source=InputSource.INITIAL_PROMPT)
                ),
                WorkflowAgent(
                    agent_id="agent2",
                    role="processor",
                    execution_order=2,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent1"),
                    conditions=[
                        AgentCondition(
                            field="result",
                            operator="contains",
                            value="positivo"
                        )
                    ]
                ),
                WorkflowAgent(
                    agent_id="agent3",
                    role="processor",
                    execution_order=2,
                    input=InputConfig(source=InputSource.AGENT_RESULT, agent_id="agent1"),
                    conditions=[
                        AgentCondition(
                            field="result",
                            operator="contains",
                            value="negativo"
                        )
                    ]
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_sequential_strategy_success(self, execution_engine, sequential_workflow, mock_suna_client):
        """Testa a execução bem-sucedida da estratégia sequencial."""
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=sequential_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = SequentialStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se todos os agentes foram executados na ordem correta
        assert mock_suna_client.execute_agent.call_count == 3
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent2"
        assert call_args_list[2][0][0] == "agent3"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 3
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" in result.agent_results
    
    @pytest.mark.asyncio
    async def test_sequential_strategy_failure(self, execution_engine, sequential_workflow, mock_suna_client):
        """Testa a falha na estratégia sequencial."""
        # Configura o mock para falhar no segundo agente
        async def execute_agent_with_failure(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent2":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "failed",
                    "error": "Erro simulado",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 0
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_with_failure)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=sequential_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = SequentialStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se apenas os dois primeiros agentes foram executados
        assert mock_suna_client.execute_agent.call_count == 2
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent2"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.FAILED
        assert len(result.agent_results) == 2
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" not in result.agent_results
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_parallel_strategy_success(self, execution_engine, parallel_workflow, mock_suna_client):
        """Testa a execução bem-sucedida da estratégia paralela."""
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=parallel_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ParallelStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se todos os agentes foram executados
        assert mock_suna_client.execute_agent.call_count == 3
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 3
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" in result.agent_results
    
    @pytest.mark.asyncio
    async def test_parallel_strategy_partial_failure(self, execution_engine, parallel_workflow, mock_suna_client):
        """Testa a falha parcial na estratégia paralela."""
        # Configura o mock para falhar em um agente
        async def execute_agent_with_partial_failure(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent2":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "failed",
                    "error": "Erro simulado",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 0
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_with_partial_failure)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=parallel_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ParallelStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se todos os agentes foram executados
        assert mock_suna_client.execute_agent.call_count == 3
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED_WITH_ERRORS
        assert len(result.agent_results) == 3
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" in result.agent_results
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_pipeline_strategy_success(self, execution_engine, pipeline_workflow, mock_suna_client):
        """Testa a execução bem-sucedida da estratégia de pipeline."""
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=pipeline_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = PipelineStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se todos os agentes foram executados na ordem correta
        assert mock_suna_client.execute_agent.call_count == 3
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent2"
        assert call_args_list[2][0][0] == "agent3"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 3
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" in result.agent_results
    
    @pytest.mark.asyncio
    async def test_pipeline_strategy_rollback(self, execution_engine, pipeline_workflow, mock_suna_client):
        """Testa o rollback na estratégia de pipeline."""
        # Configura o mock para falhar no segundo agente
        async def execute_agent_with_failure(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent2":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "failed",
                    "error": "Erro simulado",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 0
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_with_failure)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=pipeline_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = PipelineStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se apenas os dois primeiros agentes foram executados
        assert mock_suna_client.execute_agent.call_count == 2
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent2"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.FAILED
        assert len(result.agent_results) == 2
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" not in result.agent_results
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_conditional_strategy_positive_path(self, execution_engine, conditional_workflow, mock_suna_client):
        """Testa o caminho positivo na estratégia condicional."""
        # Configura o mock para retornar um resultado positivo
        async def execute_agent_positive(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent1":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "completed",
                    "result": "Este é um resultado positivo",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 50
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_positive)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=conditional_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ConditionalStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se os agentes corretos foram executados
        assert mock_suna_client.execute_agent.call_count == 2
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent2"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 2
        assert "agent1" in result.agent_results
        assert "agent2" in result.agent_results
        assert "agent3" not in result.agent_results
    
    @pytest.mark.asyncio
    async def test_conditional_strategy_negative_path(self, execution_engine, conditional_workflow, mock_suna_client):
        """Testa o caminho negativo na estratégia condicional."""
        # Configura o mock para retornar um resultado negativo
        async def execute_agent_negative(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent1":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "completed",
                    "result": "Este é um resultado negativo",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 50
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_negative)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=conditional_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ConditionalStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se os agentes corretos foram executados
        assert mock_suna_client.execute_agent.call_count == 2
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        assert call_args_list[1][0][0] == "agent3"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 2
        assert "agent1" in result.agent_results
        assert "agent2" not in result.agent_results
        assert "agent3" in result.agent_results
    
    @pytest.mark.asyncio
    async def test_conditional_strategy_no_match(self, execution_engine, conditional_workflow, mock_suna_client):
        """Testa o caso em que nenhuma condição é satisfeita na estratégia condicional."""
        # Configura o mock para retornar um resultado que não satisfaz nenhuma condição
        async def execute_agent_no_match(agent_id, prompt, **kwargs):
            await asyncio.sleep(0.1)
            if agent_id == "agent1":
                return {
                    "execution_id": f"exec_{agent_id}_{int(time.time())}",
                    "agent_id": agent_id,
                    "status": "completed",
                    "result": "Este é um resultado neutro",
                    "cost_metrics": {
                        "cost_usd": 0.01,
                        "tokens_input": 100,
                        "tokens_output": 50
                    }
                }
            return {
                "execution_id": f"exec_{agent_id}_{int(time.time())}",
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Resultado do agente {agent_id}",
                "cost_metrics": {
                    "cost_usd": 0.01,
                    "tokens_input": 100,
                    "tokens_output": 50
                }
            }
        
        mock_suna_client.execute_agent = AsyncMock(side_effect=execute_agent_no_match)
        
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=conditional_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ConditionalStrategy(execution_engine)
        
        # Executa a estratégia
        result = await strategy.execute(execution_plan)
        
        # Verifica se apenas o primeiro agente foi executado
        assert mock_suna_client.execute_agent.call_count == 1
        call_args_list = mock_suna_client.execute_agent.call_args_list
        assert call_args_list[0][0][0] == "agent1"
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 1
        assert "agent1" in result.agent_results
        assert "agent2" not in result.agent_results
        assert "agent3" not in result.agent_results
    
    @pytest.mark.asyncio
    async def test_performance_basic(self, execution_engine, parallel_workflow, mock_suna_client):
        """Testa a performance básica das estratégias."""
        # Configura o plano de execução
        execution_plan = ExecutionPlan(
            team_id="team_123",
            execution_id="exec_123",
            workflow=parallel_workflow,
            initial_prompt="Prompt inicial para teste"
        )
        
        # Cria a estratégia
        strategy = ParallelStrategy(execution_engine)
        
        # Mede o tempo de execução
        start_time = time.time()
        result = await strategy.execute(execution_plan)
        end_time = time.time()
        
        # Verifica se a execução foi concluída em um tempo razoável
        execution_time = end_time - start_time
        assert execution_time < 0.5  # Deve ser rápido com mocks
        
        # Verifica o resultado final
        assert result.status == ExecutionStatus.COMPLETED
        assert len(result.agent_results) == 3