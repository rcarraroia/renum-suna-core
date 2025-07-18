"""
Módulo que implementa o serviço de gerenciamento de agentes para a Plataforma Renum.
Este módulo fornece funcionalidades para criar, configurar, executar e monitorar agentes.
"""

import logging
import json
from typing import Optional, Dict, Any, List, Union
from uuid import UUID, uuid4
from datetime import datetime

from app.models.agent import Agent, AgentExecution, AgentStatus, AgentExecutionStatus
from app.repositories.agent import agent_repository, agent_execution_repository
from app.services.credentials import credential_service

# Configurar logger
logger = logging.getLogger(__name__)

class AgentService:
    """Serviço para gerenciamento de agentes."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Implementação de Singleton para o serviço de agentes."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de agentes."""
        logger.info("Serviço de agentes inicializado")
    
    async def create_agent(
        self,
        name: str,
        client_id: Union[str, UUID],
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        knowledge_base_ids: Optional[List[Union[str, UUID]]] = None,
        created_by: Optional[Union[str, UUID]] = None,
        status: AgentStatus = AgentStatus.DRAFT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Cria um novo agente.
        
        Args:
            name: Nome do agente.
            client_id: ID do cliente proprietário do agente.
            configuration: Configuração do agente.
            description: Descrição do agente (opcional).
            knowledge_base_ids: IDs das bases de conhecimento associadas (opcional).
            created_by: ID do usuário que está criando o agente (opcional).
            status: Status inicial do agente.
            metadata: Metadados adicionais do agente (opcional).
            
        Returns:
            O agente criado.
        """
        try:
            # Validar configuração do agente
            self._validate_agent_configuration(configuration)
            
            # Converter UUIDs para strings
            if knowledge_base_ids:
                knowledge_base_ids = [str(kb_id) for kb_id in knowledge_base_ids]
            
            # Criar objeto Agent
            agent = Agent(
                name=name,
                description=description,
                client_id=client_id,
                configuration=configuration,
                status=status,
                knowledge_base_ids=knowledge_base_ids,
                created_by=created_by,
                updated_by=created_by,
                metadata=metadata or {}
            )
            
            # Salvar no repositório
            return await agent_repository.create(agent)
        except Exception as e:
            logger.error(f"Erro ao criar agente: {str(e)}")
            raise
    
    async def update_agent(
        self,
        agent_id: Union[str, UUID],
        name: Optional[str] = None,
        description: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        status: Optional[AgentStatus] = None,
        knowledge_base_ids: Optional[List[Union[str, UUID]]] = None,
        updated_by: Optional[Union[str, UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Atualiza um agente existente.
        
        Args:
            agent_id: ID do agente a ser atualizado.
            name: Novo nome do agente (opcional).
            description: Nova descrição do agente (opcional).
            configuration: Nova configuração do agente (opcional).
            status: Novo status do agente (opcional).
            knowledge_base_ids: Novos IDs das bases de conhecimento associadas (opcional).
            updated_by: ID do usuário que está atualizando o agente (opcional).
            metadata: Novos metadados adicionais do agente (opcional).
            
        Returns:
            O agente atualizado.
        """
        try:
            # Recuperar agente existente
            agent = await agent_repository.get_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agente com ID {agent_id} não encontrado")
            
            # Atualizar campos
            if name is not None:
                agent.name = name
            
            if description is not None:
                agent.description = description
            
            if configuration is not None:
                # Validar nova configuração
                self._validate_agent_configuration(configuration)
                agent.configuration = configuration
            
            if status is not None:
                agent.status = status
            
            if knowledge_base_ids is not None:
                # Converter UUIDs para strings
                agent.knowledge_base_ids = [str(kb_id) for kb_id in knowledge_base_ids]
            
            if metadata is not None:
                agent.metadata = metadata
            
            # Atualizar campos de controle
            agent.updated_at = datetime.now()
            if updated_by:
                agent.updated_by = updated_by
            
            # Salvar no repositório
            return await agent_repository.update(agent_id, agent)
        except Exception as e:
            logger.error(f"Erro ao atualizar agente: {str(e)}")
            raise
    
    async def delete_agent(self, agent_id: Union[str, UUID]) -> bool:
        """Exclui um agente.
        
        Args:
            agent_id: ID do agente a ser excluído.
            
        Returns:
            True se o agente foi excluído com sucesso, False caso contrário.
        """
        try:
            # Verificar se o agente existe
            agent = await agent_repository.get_by_id(agent_id)
            if not agent:
                raise ValueError(f"Agente com ID {agent_id} não encontrado")
            
            # Excluir do repositório
            return await agent_repository.delete(agent_id)
        except Exception as e:
            logger.error(f"Erro ao excluir agente: {str(e)}")
            raise
    
    async def get_agent(self, agent_id: Union[str, UUID]) -> Optional[Agent]:
        """Recupera um agente pelo ID.
        
        Args:
            agent_id: ID do agente.
            
        Returns:
            O agente encontrado ou None se não existir.
        """
        try:
            return await agent_repository.get_by_id(agent_id)
        except Exception as e:
            logger.error(f"Erro ao recuperar agente: {str(e)}")
            raise
    
    async def list_agents(
        self,
        client_id: Optional[Union[str, UUID]] = None,
        status: Optional[AgentStatus] = None,
        knowledge_base_id: Optional[Union[str, UUID]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Agent]:
        """Lista agentes com filtros opcionais.
        
        Args:
            client_id: ID do cliente para filtrar (opcional).
            status: Status dos agentes para filtrar (opcional).
            knowledge_base_id: ID da base de conhecimento para filtrar (opcional).
            limit: Número máximo de agentes a serem retornados.
            offset: Número de agentes a serem pulados.
            
        Returns:
            Lista de agentes que correspondem aos filtros.
        """
        try:
            if knowledge_base_id:
                return await agent_repository.get_by_knowledge_base(knowledge_base_id, client_id, limit, offset)
            elif status:
                return await agent_repository.get_by_status(status, client_id, limit, offset)
            elif client_id:
                return await agent_repository.get_by_client_id(client_id, limit, offset)
            else:
                filters = {}
                return await agent_repository.list(filters, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar agentes: {str(e)}")
            raise
    
    async def update_agent_status(
        self,
        agent_id: Union[str, UUID],
        status: AgentStatus,
        updated_by: Optional[Union[str, UUID]] = None
    ) -> Agent:
        """Atualiza o status de um agente.
        
        Args:
            agent_id: ID do agente.
            status: Novo status do agente.
            updated_by: ID do usuário que está atualizando o status (opcional).
            
        Returns:
            O agente atualizado.
        """
        try:
            return await agent_repository.update_status(agent_id, status, updated_by)
        except Exception as e:
            logger.error(f"Erro ao atualizar status do agente: {str(e)}")
            raise
    
    async def execute_agent(
        self,
        agent_id: Union[str, UUID],
        user_id: Union[str, UUID],
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentExecution:
        """Inicia a execução de um agente.
        
        Args:
            agent_id: ID do agente a ser executado.
            user_id: ID do usuário que está iniciando a execução.
            input_data: Dados de entrada para a execução.
            metadata: Metadados adicionais da execução (opcional).
            
        Returns:
            A execução criada.
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
                input=input_data,
                metadata=metadata or {}
            )
            
            # Salvar no repositório
            execution = await agent_execution_repository.create(execution)
            
            # Iniciar execução via API da Suna
            # Isso será feito pelo endpoint de proxy para evitar bloqueio
            # Aqui apenas atualizamos o status para PENDING
            
            return execution
        except Exception as e:
            logger.error(f"Erro ao executar agente: {str(e)}")
            raise
    
    async def get_execution(self, execution_id: Union[str, UUID]) -> Optional[AgentExecution]:
        """Recupera uma execução pelo ID.
        
        Args:
            execution_id: ID da execução.
            
        Returns:
            A execução encontrada ou None se não existir.
        """
        try:
            return await agent_execution_repository.get_by_id(execution_id)
        except Exception as e:
            logger.error(f"Erro ao recuperar execução: {str(e)}")
            raise
    
    async def list_executions(
        self,
        agent_id: Optional[Union[str, UUID]] = None,
        user_id: Optional[Union[str, UUID]] = None,
        client_id: Optional[Union[str, UUID]] = None,
        status: Optional[AgentExecutionStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentExecution]:
        """Lista execuções com filtros opcionais.
        
        Args:
            agent_id: ID do agente para filtrar (opcional).
            user_id: ID do usuário para filtrar (opcional).
            client_id: ID do cliente para filtrar (opcional).
            status: Status das execuções para filtrar (opcional).
            limit: Número máximo de execuções a serem retornadas.
            offset: Número de execuções a serem puladas.
            
        Returns:
            Lista de execuções que correspondem aos filtros.
        """
        try:
            if agent_id:
                return await agent_execution_repository.get_by_agent_id(agent_id, limit, offset)
            elif user_id:
                return await agent_execution_repository.get_by_user_id(user_id, limit, offset)
            elif client_id and status:
                return await agent_execution_repository.get_by_status(status, client_id, limit, offset)
            elif client_id:
                return await agent_execution_repository.get_by_client_id(client_id, limit, offset)
            elif status:
                return await agent_execution_repository.get_by_status(status, None, limit, offset)
            else:
                filters = {}
                return await agent_execution_repository.list(filters, limit, offset)
        except Exception as e:
            logger.error(f"Erro ao listar execuções: {str(e)}")
            raise
    
    async def update_execution_status(
        self,
        execution_id: Union[str, UUID],
        status: AgentExecutionStatus,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None
    ) -> AgentExecution:
        """Atualiza o status de uma execução.
        
        Args:
            execution_id: ID da execução.
            status: Novo status da execução.
            output: Saída da execução (opcional).
            error: Mensagem de erro (opcional).
            tokens_used: Número de tokens utilizados (opcional).
            
        Returns:
            A execução atualizada.
        """
        try:
            return await agent_execution_repository.update_status(execution_id, status, output, error, tokens_used)
        except Exception as e:
            logger.error(f"Erro ao atualizar status da execução: {str(e)}")
            raise
    
    async def cancel_execution(self, execution_id: Union[str, UUID]) -> AgentExecution:
        """Cancela uma execução em andamento.
        
        Args:
            execution_id: ID da execução a ser cancelada.
            
        Returns:
            A execução atualizada.
        """
        try:
            # Recuperar execução
            execution = await agent_execution_repository.get_by_id(execution_id)
            if not execution:
                raise ValueError(f"Execução com ID {execution_id} não encontrada")
            
            # Verificar se a execução pode ser cancelada
            if execution.status not in [AgentExecutionStatus.PENDING, AgentExecutionStatus.RUNNING]:
                raise ValueError(f"Execução com ID {execution_id} não pode ser cancelada (status atual: {execution.status})")
            
            # Aqui você pode implementar a lógica para cancelar a execução do agente
            # Por exemplo, enviando um sinal para o worker ou removendo da fila
            
            # Atualizar status para CANCELLED
            return await agent_execution_repository.update_status(
                execution_id,
                AgentExecutionStatus.CANCELLED,
                None,
                "Execução cancelada pelo usuário"
            )
        except Exception as e:
            logger.error(f"Erro ao cancelar execução: {str(e)}")
            raise
    
    def _validate_agent_configuration(self, configuration: Dict[str, Any]) -> None:
        """Valida a configuração de um agente.
        
        Args:
            configuration: Configuração do agente a ser validada.
            
        Raises:
            ValueError: Se a configuração for inválida.
        """
        # Verificar campos obrigatórios
        required_fields = ["model", "tools"]
        for field in required_fields:
            if field not in configuration:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado na configuração do agente")
        
        # Verificar modelo
        model = configuration.get("model")
        if not isinstance(model, str) or not model:
            raise ValueError("O campo 'model' deve ser uma string não vazia")
        
        # Verificar ferramentas
        tools = configuration.get("tools")
        if not isinstance(tools, list):
            raise ValueError("O campo 'tools' deve ser uma lista")
        
        # Verificar cada ferramenta
        for tool in tools:
            if not isinstance(tool, dict):
                raise ValueError("Cada ferramenta deve ser um objeto")
            
            if "name" not in tool:
                raise ValueError("Cada ferramenta deve ter um campo 'name'")
            
            if "description" not in tool:
                raise ValueError("Cada ferramenta deve ter um campo 'description'")


# Instância global do serviço de agentes
agent_service = AgentService.get_instance()
"""