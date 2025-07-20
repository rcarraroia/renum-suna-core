"""
Módulo que implementa a integração com o Suna Core.

Este módulo fornece funcionalidades para orquestrar a execução de agentes
na Suna Core, enriquecendo prompts com contexto RAG e gerenciando o ciclo de vida
das execuções.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from uuid import UUID

from app.models.agent import Agent, AgentExecution, AgentStatus, AgentExecutionStatus
from app.repositories.agent import agent_repository, agent_execution_repository
from app.services.suna_client import suna_client
from app.services.tool_proxy import tool_proxy
from app.services.semantic_search import semantic_search_service

# Configurar logger
logger = logging.getLogger(__name__)

class SunaIntegrationService:
    """Serviço de integração com o Suna Core."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de integração."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de integração."""
        logger.info("Serviço de integração com Suna inicializado")
    
    async def _enrich_prompt_with_rag(
        self,
        prompt: str,
        knowledge_base_ids: Optional[List[Union[str, UUID]]] = None,
        max_tokens: int = 1500
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Enriquece um prompt com contexto RAG.
        
        Args:
            prompt: Prompt original.
            knowledge_base_ids: IDs das bases de conhecimento a serem consultadas.
            max_tokens: Número máximo de tokens para o contexto.
            
        Returns:
            Tupla com o prompt enriquecido e a lista de chunks usados.
        """
        if not knowledge_base_ids:
            return prompt, []
        
        try:
            # Converter knowledge_base_ids para lista de UUIDs
            kb_ids = [UUID(str(kb_id)) for kb_id in knowledge_base_ids]
            
            # Obter coleções das bases de conhecimento
            collection_ids = []
            # TODO: Implementar obtenção de coleções das bases de conhecimento
            
            # Gerar contexto
            context_text, context_chunks = await semantic_search_service.generate_context(
                query=prompt,
                collection_ids=collection_ids,
                max_tokens=max_tokens
            )
            
            # Enriquecer prompt com contexto
            enriched_prompt = f"""Contexto:
{context_text}

Pergunta:
{prompt}"""
            
            return enriched_prompt, context_chunks
        except Exception as e:
            logger.error(f"Erro ao enriquecer prompt com RAG: {str(e)}")
            # Em caso de erro, retornar o prompt original
            return prompt, []
    
    async def _prepare_agent_config(
        self,
        agent: Agent,
        client_id: Union[str, UUID]
    ) -> Dict[str, Any]:
        """Prepara a configuração do agente para execução na Suna Core.
        
        Args:
            agent: Agente a ser executado.
            client_id: ID do cliente.
            
        Returns:
            Configuração do agente para a Suna Core.
        """
        # Obter configuração base do agente
        config = agent.configuration.copy()
        
        # Verificar ferramentas disponíveis para o cliente
        if "tools" in config:
            available_tools = await tool_proxy.get_available_tools(client_id)
            
            # Filtrar ferramentas que o cliente tem acesso
            filtered_tools = []
            for tool in config["tools"]:
                tool_name = tool.get("name")
                if tool_name in available_tools:
                    # Adicionar URL de callback para a ferramenta
                    tool["callback_url"] = f"/api/proxy/tool/{tool_name}"
                    filtered_tools.append(tool)
            
            config["tools"] = filtered_tools
        
        return config
    
    async def execute_agent(
        self,
        agent_id: Union[str, UUID],
        user_id: Union[str, UUID],
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentExecution:
        """Executa um agente na Suna Core.
        
        Args:
            agent_id: ID do agente a ser executado.
            user_id: ID do usuário que está iniciando a execução.
            prompt: Prompt para o agente.
            metadata: Metadados adicionais da execução.
            
        Returns:
            Execução criada.
            
        Raises:
            ValueError: Se o agente não for encontrado ou não estiver ativo.
            Exception: Se ocorrer um erro na execução.
        """
        try:
            # Recuperar agente
            agent = await agent_repository.get_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agente com ID {agent_id} não encontrado")
            
            # Verificar se o agente está ativo
            if agent.status != AgentStatus.ACTIVE:
                raise ValueError(f"Agente com ID {agent_id} não está ativo (status atual: {agent.status})")
            
            # Criar objeto AgentExecution
            execution = AgentExecution(
                agent_id=agent_id,
                user_id=user_id,
                client_id=agent.client_id,
                status=AgentExecutionStatus.PENDING,
                input={"prompt": prompt},
                metadata=metadata or {}
            )
            
            # Salvar no repositório
            execution = await agent_execution_repository.create(execution)
            
            # Atualizar status para RUNNING
            execution = await agent_execution_repository.update_status(
                execution.id, 
                AgentExecutionStatus.RUNNING
            )
            
            # Enriquecer prompt com contexto RAG
            enriched_prompt, context_chunks = await self._enrich_prompt_with_rag(
                prompt=prompt,
                knowledge_base_ids=agent.knowledge_base_ids
            )
            
            # Preparar configuração do agente
            agent_config = await self._prepare_agent_config(agent, agent.client_id)
            
            # Preparar contexto adicional
            context = {
                "execution_id": str(execution.id),
                "agent_id": str(agent_id),
                "user_id": str(user_id),
                "client_id": str(agent.client_id)
            }
            
            # Executar agente na Suna Core
            suna_response = await suna_client.execute_agent(
                prompt=enriched_prompt,
                agent_config=agent_config,
                context=context,
                metadata=metadata
            )
            
            # Atualizar execução com informações da resposta
            execution = await agent_execution_repository.update_status(
                execution.id,
                AgentExecutionStatus.COMPLETED,
                output=suna_response,
                tokens_used=suna_response.get("tokens_used")
            )
            
            # Atualizar contexto usado
            if context_chunks:
                execution.context_used = {
                    "chunks": [
                        {
                            "id": str(chunk.get("id")),
                            "content": chunk.get("content"),
                            "document_id": str(chunk.get("document_id")),
                            "similarity": chunk.get("similarity")
                        }
                        for chunk in context_chunks
                    ]
                }
                await agent_execution_repository.update(execution.id, execution)
            
            return execution
        except Exception as e:
            logger.error(f"Erro ao executar agente: {str(e)}")
            
            # Em caso de erro, atualizar status da execução
            if 'execution' in locals():
                await agent_execution_repository.update_status(
                    execution.id,
                    AgentExecutionStatus.FAILED,
                    error=str(e)
                )
            
            raise
    
    async def get_execution_status(self, execution_id: Union[str, UUID]) -> AgentExecution:
        """Obtém o status de uma execução.
        
        Args:
            execution_id: ID da execução.
            
        Returns:
            Execução atualizada.
            
        Raises:
            ValueError: Se a execução não for encontrada.
            Exception: Se ocorrer um erro na requisição.
        """
        try:
            # Recuperar execução
            execution = await agent_execution_repository.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execução com ID {execution_id} não encontrada")
            
            # Se a execução já estiver concluída, retornar diretamente
            if execution.status in [
                AgentExecutionStatus.COMPLETED,
                AgentExecutionStatus.FAILED,
                AgentExecutionStatus.CANCELLED,
                AgentExecutionStatus.TIMEOUT
            ]:
                return execution
            
            # Obter status da execução na Suna Core
            suna_status = await suna_client.get_execution_status(execution_id)
            
            # Mapear status da Suna Core para status da Renum
            status_mapping = {
                "pending": AgentExecutionStatus.PENDING,
                "running": AgentExecutionStatus.RUNNING,
                "completed": AgentExecutionStatus.COMPLETED,
                "failed": AgentExecutionStatus.FAILED,
                "cancelled": AgentExecutionStatus.CANCELLED,
                "timeout": AgentExecutionStatus.TIMEOUT
            }
            
            suna_status_str = suna_status.get("status", "").lower()
            new_status = status_mapping.get(suna_status_str, execution.status)
            
            # Atualizar execução com informações da resposta
            if new_status != execution.status:
                execution = await agent_execution_repository.update_status(
                    execution_id,
                    new_status,
                    output=suna_status.get("output"),
                    error=suna_status.get("error"),
                    tokens_used=suna_status.get("tokens_used")
                )
            
            return execution
        except Exception as e:
            logger.error(f"Erro ao obter status da execução: {str(e)}")
            raise
    
    async def cancel_execution(self, execution_id: Union[str, UUID]) -> AgentExecution:
        """Cancela uma execução em andamento.
        
        Args:
            execution_id: ID da execução.
            
        Returns:
            Execução atualizada.
            
        Raises:
            ValueError: Se a execução não for encontrada.
            Exception: Se ocorrer um erro na requisição.
        """
        try:
            # Recuperar execução
            execution = await agent_execution_repository.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execução com ID {execution_id} não encontrada")
            
            # Verificar se a execução pode ser cancelada
            if execution.status not in [AgentExecutionStatus.PENDING, AgentExecutionStatus.RUNNING]:
                raise ValueError(f"Execução com ID {execution_id} não pode ser cancelada (status atual: {execution.status})")
            
            # Cancelar execução na Suna Core
            await suna_client.cancel_execution(execution_id)
            
            # Atualizar status para CANCELLED
            execution = await agent_execution_repository.update_status(
                execution_id,
                AgentExecutionStatus.CANCELLED,
                error="Execução cancelada pelo usuário"
            )
            
            return execution
        except Exception as e:
            logger.error(f"Erro ao cancelar execução: {str(e)}")
            raise
    
    async def handle_tool_callback(
        self,
        tool_name: str,
        execution_id: Union[str, UUID],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Manipula um callback de ferramenta da Suna Core.
        
        Args:
            tool_name: Nome da ferramenta.
            execution_id: ID da execução.
            parameters: Parâmetros da ferramenta.
            
        Returns:
            Resultado da chamada da ferramenta.
            
        Raises:
            ValueError: Se a execução não for encontrada.
            Exception: Se ocorrer um erro na chamada da ferramenta.
        """
        try:
            # Recuperar execução
            execution = await agent_execution_repository.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execução com ID {execution_id} não encontrada")
            
            # Recuperar agente
            agent = await agent_repository.get_by_id(execution.agent_id)
            if not agent:
                raise ValueError(f"Agente com ID {execution.agent_id} não encontrado")
            
            # Fazer proxy da chamada da ferramenta
            result = await tool_proxy.proxy_tool_call(
                client_id=agent.client_id,
                tool_name=tool_name,
                action=parameters.get("action", "default"),
                parameters=parameters.get("parameters", {})
            )
            
            # Registrar ferramenta usada na execução
            if not execution.tools_used:
                execution.tools_used = []
            
            if tool_name not in execution.tools_used:
                execution.tools_used.append(tool_name)
                await agent_execution_repository.update(execution.id, execution)
            
            return result
        except Exception as e:
            logger.error(f"Erro ao manipular callback de ferramenta: {str(e)}")
            raise


# Instância global do serviço de integração
suna_integration_service = SunaIntegrationService.get_instance()