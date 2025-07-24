"""
Cliente para comunicação com a API do Suna Core.

Este módulo fornece uma interface para interagir com o Suna Core API,
permitindo a execução de agentes individuais e o gerenciamento de suas execuções.
"""

import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)


class SunaApiError(Exception):
    """Exceção para erros na comunicação com a API do Suna Core."""
    pass


class SunaApiClient:
    """Cliente para comunicação com o Suna Core API."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Inicializa o cliente de API do Suna Core.
        
        Args:
            base_url: URL base da API do Suna Core
            api_key: Chave de API para autenticação (opcional)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
        self._headers = {}
        
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"
    
    async def initialize(self):
        """Inicializa a sessão HTTP."""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self._headers)
            logger.info(f"Initialized Suna API client for {self.base_url}")
    
    async def close(self):
        """Fecha a sessão HTTP."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Closed Suna API client session")
    
    async def _ensure_session(self):
        """Garante que a sessão HTTP está inicializada."""
        if self.session is None:
            await self.initialize()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Faz uma requisição para a API do Suna Core.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (sem a URL base)
            data: Dados para enviar no corpo da requisição
            params: Parâmetros de query string
            headers: Headers adicionais
            timeout: Timeout em segundos
            
        Returns:
            Resposta da API como um dicionário
            
        Raises:
            SunaApiError: Se ocorrer um erro na comunicação com a API
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        request_headers = self._headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=timeout
            ) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Suna API error ({response.status}): {error_text}")
                    raise SunaApiError(f"Suna API returned {response.status}: {error_text}")
                
                return await response.json()
        
        except aiohttp.ClientError as e:
            logger.error(f"Suna API client error: {str(e)}")
            raise SunaApiError(f"Failed to connect to Suna API: {str(e)}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Suna API response: {str(e)}")
            raise SunaApiError(f"Failed to parse Suna API response: {str(e)}")
    
    async def create_thread(self) -> str:
        """
        Cria uma nova thread no Suna Core.
        
        Returns:
            thread_id: ID da thread criada
        """
        response = await self._make_request("POST", "/api/threads")
        return response["thread_id"]
    
    async def execute_agent(
        self, 
        agent_id: str, 
        thread_id: str, 
        prompt: str,
        user_api_keys: Optional[Dict[str, str]] = None,
        model_name: Optional[str] = None,
        enable_thinking: bool = False,
        reasoning_effort: str = 'low',
        stream: bool = False
    ) -> str:
        """
        Executa um agente individual no Suna Core.
        
        Args:
            agent_id: ID do agente no Suna Core
            thread_id: ID da thread para execução
            prompt: Prompt inicial para o agente
            user_api_keys: API keys personalizadas do usuário
            model_name: Nome do modelo a ser usado (opcional)
            enable_thinking: Habilitar modo de pensamento
            reasoning_effort: Nível de esforço de raciocínio ('low', 'medium', 'high')
            stream: Usar streaming para a resposta
            
        Returns:
            agent_run_id: ID da execução do agente
        """
        headers = {}
        if user_api_keys:
            # Adiciona headers para API keys personalizadas
            for key_name, key_value in user_api_keys.items():
                headers[f"X-API-Key-{key_name}"] = key_value
        
        payload = {
            "agent_id": agent_id,
            "enable_thinking": enable_thinking,
            "reasoning_effort": reasoning_effort,
            "stream": stream
        }
        
        if model_name:
            payload["model_name"] = model_name
        
        # Adiciona o prompt como uma mensagem do usuário
        await self.add_message(thread_id, "user", prompt)
        
        response = await self._make_request(
            "POST", 
            f"/api/thread/{thread_id}/agent/start",
            data=payload,
            headers=headers
        )
        
        return response["agent_run_id"]
    
    async def execute_agent_with_thread_manager(
        self, 
        agent_id: str, 
        thread_id: str, 
        prompt: str,
        user_api_keys: Optional[Dict[str, str]] = None,
        thread_manager: Any = None,
        model_name: Optional[str] = None,
        enable_thinking: bool = False,
        reasoning_effort: str = 'low',
        stream: bool = False
    ) -> str:
        """
        Executa um agente individual no Suna Core usando um ThreadManager personalizado.
        
        Args:
            agent_id: ID do agente no Suna Core
            thread_id: ID da thread para execução
            prompt: Prompt inicial para o agente
            user_api_keys: API keys personalizadas do usuário
            thread_manager: Instância do ThreadManager personalizado
            model_name: Nome do modelo a ser usado (opcional)
            enable_thinking: Habilitar modo de pensamento
            reasoning_effort: Nível de esforço de raciocínio ('low', 'medium', 'high')
            stream: Usar streaming para a resposta
            
        Returns:
            agent_run_id: ID da execução do agente
        """
        headers = {}
        if user_api_keys:
            # Adiciona headers para API keys personalizadas
            for key_name, key_value in user_api_keys.items():
                headers[f"X-API-Key-{key_name}"] = key_value
        
        payload = {
            "agent_id": agent_id,
            "enable_thinking": enable_thinking,
            "reasoning_effort": reasoning_effort,
            "stream": stream
        }
        
        if model_name:
            payload["model_name"] = model_name
        
        # Adiciona o prompt como uma mensagem do usuário usando o ThreadManager personalizado
        if thread_manager:
            await thread_manager.add_message(thread_id, "user", {"text": prompt})
        else:
            await self.add_message(thread_id, "user", prompt)
        
        # Executa o agente usando o ThreadManager personalizado
        if thread_manager:
            # Obtém o sistema de execução de agentes do Suna Core
            from backend.agent.workflows import execute_agent_with_thread_manager
            
            # Executa o agente com o ThreadManager personalizado
            agent_run_id = await execute_agent_with_thread_manager(
                agent_id=agent_id,
                thread_id=thread_id,
                thread_manager=thread_manager,
                enable_thinking=enable_thinking,
                reasoning_effort=reasoning_effort,
                stream=stream,
                model_name=model_name,
                user_api_keys=user_api_keys
            )
            
            return agent_run_id
        else:
            # Fallback para o método padrão se não houver ThreadManager
            response = await self._make_request(
                "POST", 
                f"/api/thread/{thread_id}/agent/start",
                data=payload,
                headers=headers
            )
            
            return response["agent_run_id"]
    
    async def add_message(
        self, 
        thread_id: str, 
        message_type: str, 
        content: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Adiciona uma mensagem a uma thread.
        
        Args:
            thread_id: ID da thread
            message_type: Tipo da mensagem ('user', 'assistant', etc.)
            content: Conteúdo da mensagem
            
        Returns:
            Dados da mensagem criada
        """
        # Formata o conteúdo conforme esperado pela API
        if isinstance(content, str):
            formatted_content = {"text": content}
        else:
            formatted_content = content
        
        payload = {
            "type": message_type,
            "content": formatted_content
        }
        
        response = await self._make_request(
            "POST",
            f"/api/thread/{thread_id}/messages",
            data=payload
        )
        
        return response
    
    async def get_agent_run_status(self, agent_run_id: str) -> Dict[str, Any]:
        """
        Obtém o status de uma execução de agente.
        
        Args:
            agent_run_id: ID da execução do agente
            
        Returns:
            Dados do status da execução
        """
        response = await self._make_request(
            "GET",
            f"/api/agent-run/{agent_run_id}"
        )
        
        return response
    
    async def get_agent_run_responses(self, agent_run_id: str) -> List[Dict[str, Any]]:
        """
        Obtém as respostas de uma execução de agente.
        
        Args:
            agent_run_id: ID da execução do agente
            
        Returns:
            Lista de respostas do agente
        """
        response = await self._make_request(
            "GET",
            f"/api/agent-run/{agent_run_id}/responses"
        )
        
        return response.get("responses", [])
    
    async def stop_agent_run(self, agent_run_id: str) -> bool:
        """
        Para uma execução de agente em andamento.
        
        Args:
            agent_run_id: ID da execução do agente
            
        Returns:
            True se a operação foi bem-sucedida
        """
        await self._make_request(
            "POST",
            f"/api/agent-run/{agent_run_id}/stop"
        )
        
        return True
    
    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de um agente.
        
        Args:
            agent_id: ID do agente
            
        Returns:
            Dados do agente
        """
        response = await self._make_request(
            "GET",
            f"/api/agents/{agent_id}"
        )
        
        return response
    
    async def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Obtém todas as mensagens de uma thread.
        
        Args:
            thread_id: ID da thread
            
        Returns:
            Lista de mensagens
        """
        response = await self._make_request(
            "GET",
            f"/api/thread/{thread_id}/messages"
        )
        
        return response.get("messages", [])
    
    async def wait_for_agent_completion(
        self, 
        agent_run_id: str, 
        polling_interval: float = 1.0,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Aguarda a conclusão de uma execução de agente.
        
        Args:
            agent_run_id: ID da execução do agente
            polling_interval: Intervalo entre verificações de status (em segundos)
            timeout: Timeout em segundos (None para aguardar indefinidamente)
            
        Returns:
            Resultado final da execução
            
        Raises:
            SunaApiError: Se ocorrer um erro na execução ou timeout
        """
        import asyncio
        start_time = datetime.now()
        
        while True:
            status_data = await self.get_agent_run_status(agent_run_id)
            status = status_data.get("status")
            
            if status == "completed":
                # Execução concluída com sucesso
                responses = await self.get_agent_run_responses(agent_run_id)
                return {
                    "status": "completed",
                    "responses": responses,
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
            
            elif status == "failed":
                # Execução falhou
                error_message = status_data.get("error", "Unknown error")
                raise SunaApiError(f"Agent execution failed: {error_message}")
            
            elif status == "stopped":
                # Execução foi interrompida
                raise SunaApiError("Agent execution was stopped")
            
            # Verifica timeout
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                await self.stop_agent_run(agent_run_id)
                raise SunaApiError(f"Agent execution timed out after {timeout} seconds")
            
            # Aguarda antes da próxima verificação
            await asyncio.sleep(polling_interval)
    
    async def get_usage_metrics(self, agent_run_id: str) -> Dict[str, Any]:
        """
        Obtém métricas de uso de uma execução de agente.
        
        Args:
            agent_run_id: ID da execução do agente
            
        Returns:
            Métricas de uso (tokens, custo, etc.)
        """
        # Esta é uma implementação simulada, pois o Suna Core pode não ter este endpoint
        # Em uma implementação real, você precisaria adaptar para a API real do Suna
        
        try:
            # Tenta obter métricas do endpoint específico (se existir)
            response = await self._make_request(
                "GET",
                f"/api/agent-run/{agent_run_id}/metrics"
            )
            return response
        except SunaApiError:
            # Fallback: estima métricas com base nas respostas
            responses = await self.get_agent_run_responses(agent_run_id)
            
            # Estimativa simples de tokens (implementação real seria mais precisa)
            total_tokens_input = 0
            total_tokens_output = 0
            model_name = "unknown"
            
            for response in responses:
                if "tokens" in response:
                    total_tokens_input += response.get("tokens", {}).get("prompt", 0)
                    total_tokens_output += response.get("tokens", {}).get("completion", 0)
                
                if "model" in response and not model_name or model_name == "unknown":
                    model_name = response.get("model")
            
            # Estimativa simples de custo (implementação real usaria preços reais)
            cost_estimate = 0.0
            if "gpt-4" in model_name.lower():
                cost_estimate = (total_tokens_input * 0.00003) + (total_tokens_output * 0.00006)
            elif "gpt-3.5" in model_name.lower():
                cost_estimate = (total_tokens_input * 0.000001) + (total_tokens_output * 0.000002)
            elif "claude" in model_name.lower():
                cost_estimate = (total_tokens_input * 0.00001) + (total_tokens_output * 0.00003)
            
            return {
                "tokens_input": total_tokens_input,
                "tokens_output": total_tokens_output,
                "model_name": model_name,
                "cost_usd": cost_estimate
            }