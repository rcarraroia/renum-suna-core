"""
Configurações e fixtures para testes.

Este módulo define configurações e fixtures para os testes,
incluindo clientes de teste, mocks e dados de teste.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from uuid import UUID, uuid4

from app.main import app
from app.models.team_models import (
    TeamCreate,
    TeamResponse,
    WorkflowDefinition,
    WorkflowType,
    AgentConfig,
    AgentRole,
    InputConfig,
    InputSource
)


@pytest.fixture
def test_client():
    """
    Cliente de teste para a API.
    
    Returns:
        TestClient: Cliente de teste
    """
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """
    ID de usuário mock para testes.
    
    Returns:
        UUID: ID de usuário
    """
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_team_id():
    """
    ID de equipe mock para testes.
    
    Returns:
        UUID: ID de equipe
    """
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def mock_execution_id():
    """
    ID de execução mock para testes.
    
    Returns:
        UUID: ID de execução
    """
    return UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def mock_agent_ids():
    """
    IDs de agentes mock para testes.
    
    Returns:
        List[str]: Lista de IDs de agentes
    """
    return ["agent-123", "agent-456", "agent-789"]


@pytest.fixture
def mock_workflow_definition():
    """
    Definição de workflow mock para testes.
    
    Returns:
        WorkflowDefinition: Definição de workflow
    """
    return WorkflowDefinition(
        type=WorkflowType.SEQUENTIAL,
        agents=[
            AgentConfig(
                agent_id="agent-123",
                role=AgentRole.LEADER,
                execution_order=1,
                input=InputConfig(source=InputSource.INITIAL_PROMPT)
            ),
            AgentConfig(
                agent_id="agent-456",
                role=AgentRole.MEMBER,
                execution_order=2,
                input=InputConfig(
                    source=InputSource.AGENT_RESULT,
                    agent_id="agent-123"
                )
            ),
            AgentConfig(
                agent_id="agent-789",
                role=AgentRole.MEMBER,
                execution_order=3,
                input=InputConfig(
                    source=InputSource.COMBINED,
                    sources=[
                        {"type": "agent_result", "agent_id": "agent-123"},
                        {"type": "agent_result", "agent_id": "agent-456"}
                    ]
                )
            )
        ]
    )


@pytest.fixture
def mock_team_create(mock_agent_ids, mock_workflow_definition):
    """
    Dados de criação de equipe mock para testes.
    
    Returns:
        TeamCreate: Dados de criação de equipe
    """
    return TeamCreate(
        name="Equipe de Teste",
        description="Equipe para testes",
        agent_ids=mock_agent_ids,
        workflow_definition=mock_workflow_definition
    )


@pytest.fixture
def mock_team_response(mock_team_id, mock_user_id, mock_agent_ids, mock_workflow_definition):
    """
    Resposta de equipe mock para testes.
    
    Returns:
        TeamResponse: Resposta de equipe
    """
    return TeamResponse(
        team_id=mock_team_id,
        user_id=mock_user_id,
        name="Equipe de Teste",
        description="Equipe para testes",
        agent_ids=mock_agent_ids,
        workflow_definition=mock_workflow_definition,
        is_active=True,
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )


@pytest_asyncio.fixture
async def mock_team_repository():
    """
    Repositório de equipes mock para testes.
    
    Returns:
        AsyncMock: Repositório de equipes mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.create_team.return_value = None
    mock.get_team.return_value = None
    mock.update_team.return_value = None
    mock.delete_team.return_value = True
    mock.list_teams.return_value = None
    
    return mock


@pytest_asyncio.fixture
async def mock_team_execution_repository():
    """
    Repositório de execuções de equipe mock para testes.
    
    Returns:
        AsyncMock: Repositório de execuções de equipe mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.create_execution.return_value = None
    mock.get_execution.return_value = None
    mock.get_execution_status.return_value = None
    mock.update_execution_status.return_value = True
    mock.update_execution_plan.return_value = True
    mock.update_execution_result.return_value = True
    mock.get_execution_result.return_value = None
    mock.list_executions.return_value = []
    mock.count_executions.return_value = 0
    mock.delete_execution.return_value = True
    
    return mock


@pytest_asyncio.fixture
async def mock_suna_client():
    """
    Cliente da API do Suna Core mock para testes.
    
    Returns:
        AsyncMock: Cliente da API do Suna Core mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.initialize.return_value = None
    mock.close.return_value = None
    mock.create_thread.return_value = str(uuid4())
    mock.execute_agent.return_value = str(uuid4())
    mock.get_agent_run_status.return_value = {"status": "completed"}
    mock.get_agent_run_results.return_value = {"result": "Test result"}
    mock.stop_agent_run.return_value = True
    
    return mock


@pytest_asyncio.fixture
async def mock_redis_client():
    """
    Cliente Redis mock para testes.
    
    Returns:
        AsyncMock: Cliente Redis mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.set.return_value = True
    mock.get.return_value = None
    mock.delete.return_value = True
    mock.exists.return_value = True
    mock.hset.return_value = True
    mock.hget.return_value = b"{}"
    mock.hgetall.return_value = {b"variables": b"{}", b"metadata": b"{}", b"version": b"1"}
    mock.publish.return_value = 1
    mock.rpush.return_value = 1
    mock.lrange.return_value = []
    mock.expire.return_value = True
    
    # Configura o método pubsub
    pubsub_mock = AsyncMock()
    pubsub_mock.subscribe.return_value = None
    pubsub_mock.unsubscribe.return_value = None
    pubsub_mock.listen = AsyncMock()
    pubsub_mock.listen.return_value = []
    
    mock.pubsub.return_value = pubsub_mock
    
    return mock


@pytest_asyncio.fixture
async def mock_api_key_manager():
    """
    Gerenciador de API keys mock para testes.
    
    Returns:
        AsyncMock: Gerenciador de API keys mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.get_user_api_keys.return_value = {}
    mock.get_user_api_key.return_value = None
    mock.set_user_api_key.return_value = True
    mock.delete_user_api_key.return_value = True
    mock.list_user_api_keys.return_value = []
    mock.create_user_api_key.return_value = None
    
    return mock


@pytest_asyncio.fixture
async def mock_team_context_manager():
    """
    Gerenciador de contexto compartilhado mock para testes.
    
    Returns:
        AsyncMock: Gerenciador de contexto compartilhado mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.create_context.return_value = None
    mock.get_context.return_value = None
    mock.set_variable.return_value = True
    mock.get_variable.return_value = None
    mock.get_all_variables.return_value = {}
    mock.update_context.return_value = True
    mock.delete_variable.return_value = True
    mock.subscribe_to_changes.return_value = []
    mock.add_message_to_context.return_value = True
    
    return mock


@pytest_asyncio.fixture
async def mock_team_message_bus():
    """
    Sistema de mensagens entre agentes mock para testes.
    
    Returns:
        AsyncMock: Sistema de mensagens entre agentes mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.send_message.return_value = uuid4()
    mock.broadcast_message.return_value = uuid4()
    mock.request_response.return_value = {"text": "Test response"}
    mock.respond_to_request.return_value = uuid4()
    mock.subscribe_to_messages.return_value = []
    mock.get_messages.return_value = []
    
    return mock


@pytest_asyncio.fixture
async def mock_execution_engine():
    """
    Motor de execução mock para testes.
    
    Returns:
        AsyncMock: Motor de execução mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.create_execution_plan.return_value = None
    mock.execute_plan.return_value = True
    
    return mock


@pytest_asyncio.fixture
async def mock_team_orchestrator():
    """
    Orquestrador de equipes mock para testes.
    
    Returns:
        AsyncMock: Orquestrador de equipes mock
    """
    mock = AsyncMock()
    
    # Configura os métodos mock
    mock.execute_team.return_value = None
    mock.get_execution_status.return_value = None
    mock.get_execution_result.return_value = None
    mock.stop_execution.return_value = True
    mock.list_executions.return_value = []
    mock.count_executions.return_value = 0
    mock.delete_execution.return_value = True
    mock.subscribe_to_execution_updates.return_value = []
    mock.unsubscribe_from_execution_updates.return_value = None
    
    return mock


@pytest.fixture
def mock_auth():
    """
    Mock para autenticação.
    
    Returns:
        patch: Patch para a função get_current_user_id
    """
    with patch("app.core.auth.get_current_user_id") as mock:
        mock.return_value = UUID("00000000-0000-0000-0000-000000000001")
        yield mock


@pytest.fixture
def mock_websocket_manager():
    """
    Gerenciador de WebSockets mock para testes.
    
    Returns:
        MagicMock: Gerenciador de WebSockets mock
    """
    mock = MagicMock()
    mock.connect = AsyncMock()
    mock.disconnect = MagicMock()
    mock.broadcast = AsyncMock()
    return mock


@pytest.fixture
def mock_dependencies():
    """
    Mock para dependências.
    
    Returns:
        dict: Dicionário com patches para as dependências
    """
    patches = {}
    
    # Cria patches para as dependências
    patches["get_team_repository"] = patch("app.core.dependencies.get_team_repository")
    patches["get_team_execution_repository"] = patch("app.core.dependencies.get_team_execution_repository")
    patches["get_suna_client"] = patch("app.core.dependencies.get_suna_client")
    patches["get_redis_client"] = patch("app.core.dependencies.get_redis_client")
    patches["get_api_key_manager"] = patch("app.core.dependencies.get_api_key_manager")
    patches["get_team_context_manager"] = patch("app.core.dependencies.get_team_context_manager")
    patches["get_team_message_bus"] = patch("app.core.dependencies.get_team_message_bus")
    patches["get_execution_engine"] = patch("app.core.dependencies.get_execution_engine")
    patches["get_team_orchestrator"] = patch("app.core.dependencies.get_team_orchestrator")
    patches["get_websocket_manager"] = patch("app.core.dependencies.get_websocket_manager")
    
    # Inicia os patches
    mocks = {}
    for name, patch_obj in patches.items():
        mocks[name] = patch_obj.start()
    
    yield mocks
    
    # Para os patches
    for patch_obj in patches.values():
        patch_obj.stop()