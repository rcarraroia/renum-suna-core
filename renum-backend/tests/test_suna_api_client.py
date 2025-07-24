"""
Testes para o cliente da API do Suna Core.

Este módulo contém testes para o cliente da API do Suna Core,
verificando a comunicação com o Suna Core para execução de agentes.
"""

import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.suna_api_client import SunaApiClient, SunaApiError


@pytest.mark.asyncio
async def test_initialize():
    """Testa a inicialização do cliente."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    
    # Mock para aiohttp.ClientSession
    with patch("aiohttp.ClientSession", return_value=AsyncMock()) as mock_session:
        # Act
        await client.initialize()
        
        # Assert
        assert client.session is not None
        mock_session.assert_called_once()


@pytest.mark.asyncio
async def test_close():
    """Testa o fechamento do cliente."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    client.session = AsyncMock()
    
    # Act
    await client.close()
    
    # Assert
    client.session.close.assert_called_once()


@pytest.mark.asyncio
async def test_make_request_success():
    """Testa uma requisição bem-sucedida."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    client.session = AsyncMock()
    
    # Mock para a resposta
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"result": "success"}
    
    # Mock para o método HTTP
    client.session.get = AsyncMock(return_value=mock_response)
    
    # Act
    result = await client._make_request("GET", "/test")
    
    # Assert
    assert result == {"result": "success"}
    client.session.get.assert_called_once_with(
        "http://localhost:8000/test",
        json=None,
        params=None,
        headers={}
    )


@pytest.mark.asyncio
async def test_make_request_error():
    """Testa uma requisição com erro."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    client.session = AsyncMock()
    
    # Mock para a resposta
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text.return_value = "Bad request"
    
    # Mock para o método HTTP
    client.session.get = AsyncMock(return_value=mock_response)
    
    # Act & Assert
    with pytest.raises(SunaApiError):
        await client._make_request("GET", "/test")


@pytest.mark.asyncio
async def test_create_thread():
    """Testa a criação de uma thread."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    
    # Mock para _make_request
    client._make_request = AsyncMock(return_value={"thread_id": "test-thread-id"})
    
    # Act
    result = await client.create_thread()
    
    # Assert
    assert result == "test-thread-id"
    client._make_request.assert_called_once_with("POST", "/api/threads")


@pytest.mark.asyncio
async def test_execute_agent():
    """Testa a execução de um agente."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    
    # Mock para add_message
    client.add_message = AsyncMock()
    
    # Mock para _make_request
    client._make_request = AsyncMock(return_value={"agent_run_id": "test-run-id"})
    
    # Act
    result = await client.execute_agent(
        "test-agent-id",
        "test-thread-id",
        "Test prompt",
        {"openai": "test-key"}
    )
    
    # Assert
    assert result == "test-run-id"
    client.add_message.assert_called_once()
    client._make_request.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_agent_completion_success():
    """Testa a espera pela conclusão de um agente com sucesso."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    
    # Mock para get_agent_run_status
    client.get_agent_run_status = AsyncMock(return_value={"status": "completed"})
    
    # Mock para get_agent_run_results
    client.get_agent_run_results = AsyncMock(return_value={"result": "success"})
    
    # Act
    result = await client.wait_for_agent_completion("test-run-id")
    
    # Assert
    assert result == {"result": "success"}
    client.get_agent_run_status.assert_called_once()
    client.get_agent_run_results.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_agent_completion_failure():
    """Testa a espera pela conclusão de um agente com falha."""
    # Arrange
    client = SunaApiClient("http://localhost:8000")
    
    # Mock para get_agent_run_status
    client.get_agent_run_status = AsyncMock(return_value={"status": "failed", "error": "Test error"})
    
    # Act & Assert
    with pytest.raises(SunaApiError):
        await client.wait_for_agent_completion("test-run-id")
    
    client.get_agent_run_status.assert_called_once()