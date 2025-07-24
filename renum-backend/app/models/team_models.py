"""
Modelos Pydantic para o sistema de Equipes de Agentes.

Este módulo contém todos os modelos de dados utilizados pelo sistema de Equipes de Agentes,
incluindo configurações de equipe, definições de workflow, planos de execução e métricas.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class WorkflowType(str, Enum):
    """Tipos de workflow suportados pelo sistema."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"


class AgentRole(str, Enum):
    """Papéis que um agente pode ter em uma equipe."""
    LEADER = "leader"
    MEMBER = "member"
    COORDINATOR = "coordinator"


class ExecutionStatus(str, Enum):
    """Status possíveis para uma execução."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class InputSource(BaseModel):
    """Fonte de entrada para um agente no workflow."""
    source: str = Field(..., description="Tipo de fonte de entrada (initial_prompt, agent_result, combined)")
    agent_id: Optional[str] = Field(None, description="ID do agente de origem, se aplicável")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de fontes para combinação")


class AgentCondition(BaseModel):
    """Condição para execução de um agente em workflow condicional."""
    field: str = Field(..., description="Campo a ser avaliado")
    operator: str = Field(..., description="Operador de comparação (equals, not_equals, contains, etc.)")
    value: Any = Field(..., description="Valor para comparação")


class WorkflowAgent(BaseModel):
    """Configuração de um agente dentro de um workflow."""
    agent_id: str = Field(..., description="ID do agente no Suna Core")
    role: AgentRole = Field(default=AgentRole.MEMBER, description="Papel do agente na equipe")
    input: InputSource = Field(..., description="Configuração de entrada para o agente")
    conditions: Optional[List[AgentCondition]] = Field(None, description="Condições para execução (workflow condicional)")
    execution_order: Optional[int] = Field(None, description="Ordem de execução (workflow sequencial)")
    timeout: Optional[int] = Field(None, description="Timeout em segundos para execução do agente")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Configuração de retry para falhas")


class WorkflowDefinition(BaseModel):
    """Definição completa de um workflow de equipe."""
    type: WorkflowType = Field(..., description="Tipo de workflow")
    agents: List[WorkflowAgent] = Field(..., description="Lista de agentes no workflow")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configurações adicionais do workflow")

    @validator('agents')
    def validate_agents(cls, v, values):
        """Valida a configuração dos agentes de acordo com o tipo de workflow."""
        if not v:
            raise ValueError("A lista de agentes não pode estar vazia")
        
        workflow_type = values.get('type')
        
        if workflow_type == WorkflowType.SEQUENTIAL:
            # Verifica se todos os agentes têm execution_order definido
            for agent in v:
                if agent.execution_order is None:
                    raise ValueError(f"Agente {agent.agent_id} não tem execution_order definido em workflow sequencial")
        
        elif workflow_type == WorkflowType.CONDITIONAL:
            # Verifica se todos os agentes (exceto o primeiro) têm conditions definidas
            if len(v) > 1 and not all(a.conditions for a in v[1:]):
                raise ValueError("Todos os agentes (exceto o primeiro) devem ter conditions definidas em workflow condicional")
        
        elif workflow_type == WorkflowType.PIPELINE:
            # Verifica se a entrada de cada agente (exceto o primeiro) vem do agente anterior
            for i in range(1, len(v)):
                if v[i].input.source != "agent_result" or v[i].input.agent_id != v[i-1].agent_id:
                    raise ValueError(f"Agente {v[i].agent_id} deve receber entrada do agente anterior em workflow pipeline")
        
        return v


class TeamConfig(BaseModel):
    """Configuração completa de uma equipe de agentes."""
    name: str = Field(..., description="Nome da equipe")
    description: Optional[str] = Field(None, description="Descrição da equipe")
    workflow_definition: WorkflowDefinition = Field(..., description="Definição do workflow da equipe")
    user_api_keys: Optional[Dict[str, str]] = Field(default_factory=dict, description="API keys personalizadas do usuário")
    team_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configurações adicionais da equipe")
    is_active: bool = Field(default=True, description="Indica se a equipe está ativa")


class TeamCreate(BaseModel):
    """Modelo para criação de uma nova equipe."""
    name: str = Field(..., description="Nome da equipe")
    description: Optional[str] = Field(None, description="Descrição da equipe")
    agent_ids: List[str] = Field(..., description="Lista de IDs dos agentes que compõem a equipe")
    workflow_definition: WorkflowDefinition = Field(..., description="Definição do workflow da equipe")
    user_api_keys: Optional[Dict[str, str]] = Field(default_factory=dict, description="API keys personalizadas do usuário")
    team_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configurações adicionais da equipe")


class TeamUpdate(BaseModel):
    """Modelo para atualização de uma equipe existente."""
    name: Optional[str] = Field(None, description="Nome da equipe")
    description: Optional[str] = Field(None, description="Descrição da equipe")
    agent_ids: Optional[List[str]] = Field(None, description="Lista de IDs dos agentes que compõem a equipe")
    workflow_definition: Optional[WorkflowDefinition] = Field(None, description="Definição do workflow da equipe")
    user_api_keys: Optional[Dict[str, str]] = Field(None, description="API keys personalizadas do usuário")
    team_config: Optional[Dict[str, Any]] = Field(None, description="Configurações adicionais da equipe")
    is_active: Optional[bool] = Field(None, description="Indica se a equipe está ativa")


class TeamDB(BaseModel):
    """Modelo para representação de uma equipe no banco de dados."""
    team_id: UUID = Field(default_factory=uuid4, description="ID único da equipe")
    user_id: UUID = Field(..., description="ID do usuário proprietário da equipe")
    name: str = Field(..., description="Nome da equipe")
    description: Optional[str] = Field(None, description="Descrição da equipe")
    agent_ids: List[str] = Field(..., description="Lista de IDs dos agentes que compõem a equipe")
    workflow_definition: Dict[str, Any] = Field(..., description="Definição do workflow da equipe")
    user_api_keys: Dict[str, str] = Field(default_factory=dict, description="API keys personalizadas do usuário")
    team_config: Dict[str, Any] = Field(default_factory=dict, description="Configurações adicionais da equipe")
    is_active: bool = Field(default=True, description="Indica se a equipe está ativa")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação da equipe")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data da última atualização da equipe")
    created_by: Optional[UUID] = Field(None, description="ID do usuário que criou a equipe")


class TeamResponse(BaseModel):
    """Modelo para resposta de API com dados de uma equipe."""
    team_id: UUID = Field(..., description="ID único da equipe")
    user_id: UUID = Field(..., description="ID do usuário proprietário da equipe")
    name: str = Field(..., description="Nome da equipe")
    description: Optional[str] = Field(None, description="Descrição da equipe")
    agent_ids: List[str] = Field(..., description="Lista de IDs dos agentes que compõem a equipe")
    workflow_definition: WorkflowDefinition = Field(..., description="Definição do workflow da equipe")
    is_active: bool = Field(..., description="Indica se a equipe está ativa")
    created_at: datetime = Field(..., description="Data de criação da equipe")
    updated_at: datetime = Field(..., description="Data da última atualização da equipe")


class ExecutionStep(BaseModel):
    """Etapa de execução em um plano de execução."""
    step_id: str = Field(default_factory=lambda: str(uuid4()), description="ID único da etapa")
    agent_id: str = Field(..., description="ID do agente a ser executado")
    action: str = Field(default="execute", description="Ação a ser executada")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Dados de entrada para o agente")
    dependencies: List[str] = Field(default_factory=list, description="IDs das etapas que devem ser concluídas antes")
    timeout: Optional[int] = Field(None, description="Timeout em segundos")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Configuração de retry")


class ResourceRequirements(BaseModel):
    """Requisitos de recursos para execução."""
    memory_mb: Optional[int] = Field(None, description="Memória necessária em MB")
    cpu_units: Optional[int] = Field(None, description="Unidades de CPU necessárias")
    max_tokens: Optional[int] = Field(None, description="Máximo de tokens para modelos LLM")
    estimated_cost: Optional[float] = Field(None, description="Custo estimado em USD")


class ExecutionPlan(BaseModel):
    """Plano detalhado de execução de uma equipe."""
    execution_id: UUID = Field(default_factory=uuid4, description="ID único da execução")
    team_id: UUID = Field(..., description="ID da equipe")
    strategy: WorkflowType = Field(..., description="Estratégia de execução")
    steps: List[ExecutionStep] = Field(..., description="Etapas de execução")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Mapa de dependências entre etapas")
    estimated_duration: Optional[int] = Field(None, description="Duração estimada em segundos")
    resource_requirements: Optional[ResourceRequirements] = Field(None, description="Requisitos de recursos")


class TeamContext(BaseModel):
    """Contexto compartilhado entre agentes de uma equipe."""
    execution_id: UUID = Field(..., description="ID da execução")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Variáveis do contexto")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados do contexto")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação do contexto")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data da última atualização do contexto")
    version: int = Field(default=1, description="Versão do contexto")


class ContextChange(BaseModel):
    """Mudança em uma variável do contexto compartilhado."""
    key: str = Field(..., description="Chave da variável alterada")
    value: Any = Field(..., description="Novo valor da variável")
    previous_value: Optional[Any] = Field(None, description="Valor anterior da variável")
    changed_by: str = Field(..., description="ID do agente que fez a alteração")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da alteração")


class TeamMessage(BaseModel):
    """Mensagem entre agentes de uma equipe."""
    message_id: UUID = Field(default_factory=uuid4, description="ID único da mensagem")
    execution_id: UUID = Field(..., description="ID da execução")
    from_agent: str = Field(..., description="ID do agente remetente")
    to_agent: Optional[str] = Field(None, description="ID do agente destinatário (None para broadcast)")
    message_type: str = Field(..., description="Tipo da mensagem (info, request, response, error, context_update)")
    content: Dict[str, Any] = Field(..., description="Conteúdo da mensagem")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da mensagem")
    requires_response: bool = Field(default=False, description="Indica se a mensagem requer resposta")
    response_timeout: Optional[int] = Field(None, description="Timeout para resposta em segundos")


class UsageMetrics(BaseModel):
    """Métricas de uso de recursos por um agente."""
    model_provider: str = Field(..., description="Provedor do modelo (openai, anthropic, etc.)")
    model_name: str = Field(..., description="Nome do modelo utilizado")
    api_key_type: str = Field(..., description="Tipo de API key (user_provided, renum_native)")
    tokens_input: int = Field(default=0, description="Tokens de entrada consumidos")
    tokens_output: int = Field(default=0, description="Tokens de saída gerados")
    request_count: int = Field(default=1, description="Número de requisições feitas")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Dados da requisição para auditoria")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Dados da resposta para auditoria")


class CostMetrics(BaseModel):
    """Métricas de custo para um agente ou equipe."""
    cost_usd: float = Field(default=0.0, description="Custo total em USD")
    cost_breakdown: Dict[str, float] = Field(default_factory=dict, description="Detalhamento do custo por modelo/serviço")
    pricing_version: str = Field(default="v1", description="Versão da tabela de preços utilizada")


class ExecutionResult(BaseModel):
    """Resultado da execução de um agente ou equipe."""
    success: bool = Field(..., description="Indica se a execução foi bem-sucedida")
    output: Optional[Dict[str, Any]] = Field(None, description="Saída da execução")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    execution_time: float = Field(..., description="Tempo de execução em segundos")
    usage_metrics: Optional[UsageMetrics] = Field(None, description="Métricas de uso")
    cost_metrics: Optional[CostMetrics] = Field(None, description="Métricas de custo")


class TeamExecutionCreate(BaseModel):
    """Modelo para iniciar uma execução de equipe."""
    team_id: UUID = Field(..., description="ID da equipe")
    initial_prompt: str = Field(..., description="Prompt inicial para a equipe")
    user_api_keys: Optional[Dict[str, str]] = Field(None, description="API keys personalizadas para esta execução")
    execution_config: Optional[Dict[str, Any]] = Field(None, description="Configurações específicas para esta execução")


class TeamExecutionDB(BaseModel):
    """Modelo para representação de uma execução de equipe no banco de dados."""
    execution_id: UUID = Field(default_factory=uuid4, description="ID único da execução")
    team_id: UUID = Field(..., description="ID da equipe")
    user_id: UUID = Field(..., description="ID do usuário que iniciou a execução")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Status da execução")
    execution_plan: Optional[Dict[str, Any]] = Field(None, description="Plano de execução")
    shared_context: Dict[str, Any] = Field(default_factory=dict, description="Contexto compartilhado")
    initial_prompt: str = Field(..., description="Prompt inicial")
    final_result: Optional[Dict[str, Any]] = Field(None, description="Resultado final da execução")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    cost_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de custo")
    usage_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de uso")
    api_keys_used: Dict[str, str] = Field(default_factory=dict, description="API keys utilizadas")
    started_at: Optional[datetime] = Field(None, description="Data/hora de início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data/hora de conclusão da execução")
    created_at: datetime = Field(default_factory=datetime.now, description="Data/hora de criação do registro")


class TeamExecutionResponse(BaseModel):
    """Modelo para resposta de API com dados de uma execução de equipe."""
    execution_id: UUID = Field(..., description="ID único da execução")
    team_id: UUID = Field(..., description="ID da equipe")
    status: ExecutionStatus = Field(..., description="Status da execução")
    initial_prompt: str = Field(..., description="Prompt inicial")
    final_result: Optional[Dict[str, Any]] = Field(None, description="Resultado final da execução")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    started_at: Optional[datetime] = Field(None, description="Data/hora de início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data/hora de conclusão da execução")
    created_at: datetime = Field(..., description="Data/hora de criação do registro")


class TeamAgentExecutionDB(BaseModel):
    """Modelo para representação da execução de um agente em uma equipe no banco de dados."""
    execution_id: UUID = Field(..., description="ID da execução da equipe")
    agent_id: str = Field(..., description="ID do agente")
    suna_agent_run_id: Optional[UUID] = Field(None, description="ID da execução no Suna Core")
    step_order: int = Field(..., description="Ordem da etapa na execução")
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING, description="Status da execução do agente")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Dados de entrada para o agente")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Dados de saída do agente")
    context_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Snapshot do contexto")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    individual_cost_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de custo")
    individual_usage_metrics: Dict[str, Any] = Field(default_factory=dict, description="Métricas de uso")
    api_keys_snapshot: Dict[str, str] = Field(default_factory=dict, description="API keys utilizadas")
    started_at: Optional[datetime] = Field(None, description="Data/hora de início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data/hora de conclusão da execução")


class TeamAgentExecutionResponse(BaseModel):
    """Modelo para resposta de API com dados da execução de um agente em uma equipe."""
    execution_id: UUID = Field(..., description="ID da execução da equipe")
    agent_id: str = Field(..., description="ID do agente")
    suna_agent_run_id: Optional[UUID] = Field(None, description="ID da execução no Suna Core")
    step_order: int = Field(..., description="Ordem da etapa na execução")
    status: ExecutionStatus = Field(..., description="Status da execução do agente")
    input_data: Dict[str, Any] = Field(..., description="Dados de entrada para o agente")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Dados de saída do agente")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    started_at: Optional[datetime] = Field(None, description="Data/hora de início da execução")
    completed_at: Optional[datetime] = Field(None, description="Data/hora de conclusão da execução")


class TeamMessageDB(BaseModel):
    """Modelo para representação de uma mensagem entre agentes no banco de dados."""
    message_id: UUID = Field(default_factory=uuid4, description="ID único da mensagem")
    execution_id: UUID = Field(..., description="ID da execução")
    from_agent_id: str = Field(..., description="ID do agente remetente")
    to_agent_id: Optional[str] = Field(None, description="ID do agente destinatário (None para broadcast)")
    message_type: str = Field(..., description="Tipo da mensagem")
    content: Dict[str, Any] = Field(..., description="Conteúdo da mensagem")
    requires_response: bool = Field(default=False, description="Indica se a mensagem requer resposta")
    response_timeout: Optional[int] = Field(None, description="Timeout para resposta em segundos")
    response_message_id: Optional[UUID] = Field(None, description="ID da mensagem de resposta")
    created_at: datetime = Field(default_factory=datetime.now, description="Data/hora de criação da mensagem")


class TeamMessageResponse(BaseModel):
    """Modelo para resposta de API com dados de uma mensagem entre agentes."""
    message_id: UUID = Field(..., description="ID único da mensagem")
    execution_id: UUID = Field(..., description="ID da execução")
    from_agent_id: str = Field(..., description="ID do agente remetente")
    to_agent_id: Optional[str] = Field(None, description="ID do agente destinatário (None para broadcast)")
    message_type: str = Field(..., description="Tipo da mensagem")
    content: Dict[str, Any] = Field(..., description="Conteúdo da mensagem")
    requires_response: bool = Field(..., description="Indica se a mensagem requer resposta")
    response_message_id: Optional[UUID] = Field(None, description="ID da mensagem de resposta")
    created_at: datetime = Field(..., description="Data/hora de criação da mensagem")


class TeamContextSnapshotDB(BaseModel):
    """Modelo para representação de um snapshot de contexto no banco de dados."""
    execution_id: UUID = Field(..., description="ID da execução")
    snapshot_at: datetime = Field(default_factory=datetime.now, description="Data/hora do snapshot")
    context_data: Dict[str, Any] = Field(..., description="Dados do contexto")
    version: int = Field(default=1, description="Versão do contexto")
    created_by_agent: Optional[str] = Field(None, description="ID do agente que criou o snapshot")


class AIUsageLogDB(BaseModel):
    """Modelo para representação de um log de uso de IA no banco de dados."""
    log_id: UUID = Field(default_factory=uuid4, description="ID único do log")
    user_id: UUID = Field(..., description="ID do usuário")
    execution_id: Optional[UUID] = Field(None, description="ID da execução")
    agent_id: Optional[str] = Field(None, description="ID do agente")
    model_provider: str = Field(..., description="Provedor do modelo")
    model_name: str = Field(..., description="Nome do modelo")
    api_key_type: str = Field(..., description="Tipo de API key")
    tokens_input: int = Field(default=0, description="Tokens de entrada")
    tokens_output: int = Field(default=0, description="Tokens de saída")
    cost_usd: float = Field(default=0.0, description="Custo em USD")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Dados da requisição")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Dados da resposta")
    created_at: datetime = Field(default_factory=datetime.now, description="Data/hora de criação do log")


class UserAPIKeyDB(BaseModel):
    """Modelo para representação de uma API key de usuário no banco de dados."""
    key_id: UUID = Field(default_factory=uuid4, description="ID único da chave")
    user_id: UUID = Field(..., description="ID do usuário")
    service_name: str = Field(..., description="Nome do serviço (openai, anthropic, etc.)")
    encrypted_key: str = Field(..., description="Chave criptografada")
    is_active: bool = Field(default=True, description="Indica se a chave está ativa")
    created_at: datetime = Field(default_factory=datetime.now, description="Data/hora de criação da chave")
    updated_at: datetime = Field(default_factory=datetime.now, description="Data/hora da última atualização da chave")


class UserAPIKeyCreate(BaseModel):
    """Modelo para criação de uma API key de usuário."""
    service_name: str = Field(..., description="Nome do serviço (openai, anthropic, etc.)")
    api_key: str = Field(..., description="Chave de API")


class UserAPIKeyResponse(BaseModel):
    """Modelo para resposta de API com dados de uma API key de usuário."""
    key_id: UUID = Field(..., description="ID único da chave")
    user_id: UUID = Field(..., description="ID do usuário")
    service_name: str = Field(..., description="Nome do serviço")
    is_active: bool = Field(..., description="Indica se a chave está ativa")
    created_at: datetime = Field(..., description="Data/hora de criação da chave")
    updated_at: datetime = Field(..., description="Data/hora da última atualização da chave")


class PaginationParams(BaseModel):
    """Parâmetros de paginação para listagens."""
    page: int = Field(default=1, description="Número da página")
    limit: int = Field(default=10, description="Limite de itens por página")


class PaginatedResponse(BaseModel):
    """Resposta paginada genérica."""
    items: List[Any] = Field(..., description="Lista de itens")
    total: int = Field(..., description="Total de itens")
    page: int = Field(..., description="Página atual")
    limit: int = Field(..., description="Limite de itens por página")
    pages: int = Field(..., description="Total de páginas")


class PaginatedTeamResponse(BaseModel):
    """Resposta paginada específica para equipes."""
    items: List[TeamResponse] = Field(..., description="Lista de equipes")
    total: int = Field(..., description="Total de equipes")
    page: int = Field(default=1, description="Página atual")
    limit: int = Field(default=10, description="Limite de itens por página")
    pages: int = Field(..., description="Total de páginas")


class TeamExecutionStatusUpdate(BaseModel):
    """Modelo para atualização de status de uma execução de equipe."""
    status: ExecutionStatus = Field(..., description="Novo status da execução")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")


class TeamAgentExecutionStatusUpdate(BaseModel):
    """Modelo para atualização de status da execução de um agente em uma equipe."""
    status: ExecutionStatus = Field(..., description="Novo status da execução")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Dados de saída do agente")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")


class ExecutionStatusResponse(BaseModel):
    """Resposta com status detalhado de uma execução."""
    execution_id: UUID = Field(..., description="ID da execução")
    team_id: UUID = Field(..., description="ID da equipe")
    status: ExecutionStatus = Field(..., description="Status geral da execução")
    agent_statuses: Dict[str, ExecutionStatus] = Field(..., description="Status de cada agente")
    progress: float = Field(..., description="Progresso da execução (0-100%)")
    current_step: Optional[int] = Field(None, description="Etapa atual")
    total_steps: int = Field(..., description="Total de etapas")
    started_at: Optional[datetime] = Field(None, description="Data/hora de início")
    estimated_completion: Optional[datetime] = Field(None, description="Estimativa de conclusão")
    error_message: Optional[str] = Field(None, description="Mensagem de erro, se houver")
    last_updated: datetime = Field(..., description="Data/hora da última atualização")


class ExecutionLogEntry(BaseModel):
    """Entrada de log de uma execução."""
    timestamp: datetime = Field(..., description="Data/hora do evento")
    level: str = Field(..., description="Nível do log (info, warning, error)")
    agent_id: Optional[str] = Field(None, description="ID do agente relacionado")
    message: str = Field(..., description="Mensagem do log")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")