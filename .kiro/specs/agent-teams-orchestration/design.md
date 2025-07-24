# Design Técnico: Sistema de Equipes de Agentes

## Arquitetura Geral

### Visão de Alto Nível - Arquitetura Renum-Suna Integrada

```
┌─────────────────────────────────────────────────────────────────┐
│                Frontend Renum (React/TypeScript)                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Team Builder  │  │ Execution Monitor│  │   Team Manager  │ │
│  │   (/teams/new)  │  │  (Real-time UI)  │  │ (/teams/[id])   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/WebSocket
┌─────────────────────────────▼───────────────────────────────────┐
│                    Backend Renum (FastAPI)                      │
│                        "CÉREBRO DA EQUIPE"                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Team API      │  │ Orchestrator API│  │  Monitoring API │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │Team Orchestrator│  │ Workflow Engine │  │ Metrics Collector│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Delegação de Tarefas
                              │ (API Calls)
┌─────────────────────────────▼───────────────────────────────────┐
│                    Backend Suna (FastAPI)                       │
│                   "EXECUÇÃO DE AGENTES INDIVIDUAIS"             │
│                        (INALTERADO)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Agent API     │  │  Thread Manager │  │   Tool Registry │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    Infrastructure Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     Redis       │  │    Supabase     │  │   LLMs/APIs     │ │
│  │(Context+Message)│  │  (Persistence)  │  │(User API Keys)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Princípios Arquiteturais Fundamentais

1. **Separação de Responsabilidades**:
   - **Backend Renum**: Orquestração, workflow, contexto compartilhado
   - **Backend Suna**: Execução individual de agentes (inalterado)

2. **Comunicação Inter-Backends**:
   - Backend Renum faz chamadas API para Backend Suna
   - Cada agente individual é executado pelo Suna Core
   - Resultados são consolidados pelo Renum

3. **Preservação do Suna Core**:
   - Zero modificações no código do Suna
   - Compatibilidade total com atualizações futuras
   - Funcionalidade individual de agentes mantida

## Componentes Principais - Backend Renum

### 1. Team Orchestrator (Backend Renum)

**Responsabilidade**: Coordenação central de todas as execuções de equipe - "CÉREBRO DA EQUIPE"

```python
class RenumTeamOrchestrator:
    def __init__(self, db_connection, redis_client, suna_api_client):
        self.db = db_connection  # Banco Renum
        self.redis = redis_client  # Redis compartilhado
        self.suna_api = suna_api_client  # Cliente para Backend Suna
        self.workflow_engine = WorkflowEngine()
        self.context_manager = RenumContextManager(redis_client)
        self.message_bus = RenumMessageBus(redis_client)
        self.metrics_collector = RenumMetricsCollector(db_connection)
        self.cost_tracker = RenumCostTracker(db_connection)
    
    async def execute_team(
        self, 
        team_id: str, 
        initial_prompt: str,
        user_id: str
    ) -> str:
        """
        Inicia execução de uma equipe de agentes
        - Carrega workflow_definition da equipe
        - Delega execuções individuais para Backend Suna
        - Consolida resultados
        
        Returns:
            execution_id: ID único da execução
        """
        
    async def get_execution_status(self, execution_id: str) -> ExecutionStatus:
        """Retorna status atual da execução"""
        
    async def stop_execution(self, execution_id: str) -> bool:
        """Para execução em andamento"""
        
    async def get_execution_logs(self, execution_id: str) -> List[ExecutionLog]:
        """Retorna logs detalhados da execução"""
```

### 2. Workflow Engine (Backend Renum)

**Responsabilidade**: Interpretação e execução do workflow_definition

```python
class WorkflowEngine:
    def __init__(self, suna_api_client):
        self.suna_api = suna_api_client
        self.strategies = {
            'sequential': SequentialWorkflowStrategy(),
            'parallel': ParallelWorkflowStrategy(),
            'pipeline': PipelineWorkflowStrategy(),
            'conditional': ConditionalWorkflowStrategy()
        }
    
    async def create_execution_plan(
        self, 
        workflow_definition: dict,
        agent_ids: List[str],
        user_api_keys: dict
    ) -> ExecutionPlan:
        """Cria plano de execução baseado no workflow_definition da equipe"""
        
    async def execute_plan(
        self, 
        plan: ExecutionPlan, 
        context: RenumTeamContext
    ) -> ExecutionResult:
        """
        Executa o plano de execução
        - Delega cada agente individual para Backend Suna
        - Gerencia context object entre execuções
        - Coleta métricas de custo por agente
        """

class ExecutionPlan:
    execution_id: str
    team_id: str
    strategy: str
    steps: List[ExecutionStep]
    dependencies: Dict[str, List[str]]
    estimated_duration: int
    resource_requirements: ResourceRequirements

class ExecutionStep:
    step_id: str
    agent_id: str
    action: str
    input_data: Dict[str, Any]
    dependencies: List[str]
    timeout: int
    retry_config: RetryConfig
```

### 3. Renum Context Manager (Backend Renum)

**Responsabilidade**: Gerenciamento do context object e memory compartilhado

```python
class RenumContextManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def create_context(
        self, 
        execution_id: str, 
        user_api_keys: dict
    ) -> RenumTeamContext:
        """Cria novo context object e memory compartilhado para execução de equipe"""
        
    async def update_context_object(
        self, 
        execution_id: str, 
        updated_context: dict, 
        agent_id: str
    ):
        """Atualiza context object após execução de um agente"""
        
    async def set_shared_memory(
        self, 
        execution_id: str, 
        key: str, 
        value: Any, 
        agent_id: str
    ):
        """Define variável no memory compartilhado da equipe"""
        
    async def get_variable(self, execution_id: str, key: str) -> Any:
        """Obtém variável do contexto compartilhado"""
        
    async def get_all_variables(self, execution_id: str) -> Dict[str, Any]:
        """Retorna todas as variáveis do contexto"""
        
    async def subscribe_to_changes(
        self, 
        execution_id: str, 
        agent_id: str
    ) -> AsyncIterator[ContextChange]:
        """Inscreve agente para mudanças no contexto"""

class RenumTeamContext:
    execution_id: str
    context_object: Dict[str, Any]  # Context object passado entre agentes
    shared_memory: Dict[str, Any]   # Memory compartilhado da equipe
    workflow_state: Dict[str, Any]  # Estado atual do workflow
    user_api_keys: Dict[str, str]   # API keys do usuário
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int
```

### 4. Team Message Bus

**Responsabilidade**: Sistema de mensagens entre agentes

```python
class TeamMessageBus:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def send_message(
        self, 
        execution_id: str,
        from_agent: str,
        to_agent: str,
        message: TeamMessage
    ):
        """Envia mensagem para agente específico"""
        
    async def broadcast_message(
        self, 
        execution_id: str,
        from_agent: str,
        message: TeamMessage,
        exclude_agents: List[str] = None
    ):
        """Envia mensagem para todos os agentes da equipe"""
        
    async def request_response(
        self, 
        execution_id: str,
        from_agent: str,
        to_agent: str,
        request: TeamMessage,
        timeout: int = 30
    ) -> TeamMessage:
        """Solicita resposta de agente específico"""
        
    async def subscribe_to_messages(
        self, 
        execution_id: str, 
        agent_id: str
    ) -> AsyncIterator[TeamMessage]:
        """Inscreve agente para receber mensagens"""

class TeamMessage:
    message_id: str
    execution_id: str
    from_agent: str
    to_agent: Optional[str]  # None para broadcast
    message_type: str  # 'info', 'request', 'response', 'error'
    content: Dict[str, Any]
    timestamp: datetime
    requires_response: bool = False
    response_timeout: Optional[int] = None
```

### 5. Renum Metrics Collector (Backend Renum)

**Responsabilidade**: Coleta de métricas e custos por agente individual

```python
class RenumMetricsCollector:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def track_agent_execution_start(
        self, 
        execution_id: str, 
        agent_id: str, 
        suna_agent_run_id: str
    ):
        """Inicia tracking de execução de agente individual"""
        
    async def track_ai_usage(
        self, 
        execution_id: str,
        agent_id: str,
        model_provider: str,
        model_name: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float,
        api_key_type: str
    ):
        """Registra uso de modelo IA por agente específico"""
        
    async def calculate_team_total_cost(self, execution_id: str) -> float:
        """Calcula custo total da execução da equipe"""
        
    async def generate_cost_breakdown(self, execution_id: str) -> Dict[str, float]:
        """Gera breakdown de custos por agente"""

### 6. Renum Cost Tracker (Backend Renum)

**Responsabilidade**: Rastreamento de custos para billing futuro

```python
class RenumCostTracker:
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def track_user_api_key_usage(
        self, 
        user_id: str,
        execution_id: str,
        api_key_hash: str,
        usage_data: dict
    ):
        """Rastreia uso de API keys do usuário"""
        
    async def prepare_for_native_billing(
        self, 
        user_id: str,
        usage_period: str
    ) -> Dict[str, Any]:
        """Prepara dados para futuro modelo de billing nativo"""

### 7. Suna API Client (Backend Renum)

**Responsabilidade**: Comunicação com Backend Suna para execução de agentes

```python
class SunaAPIClient:
    def __init__(self, suna_base_url: str, api_key: str):
        self.base_url = suna_base_url
        self.api_key = api_key
        self.session = aiohttp.ClientSession()
    
    async def execute_individual_agent(
        self, 
        agent_id: str,
        prompt: str,
        context: dict,
        user_api_keys: dict
    ) -> dict:
        """
        Executa agente individual no Backend Suna
        - Mantém Suna Core inalterado
        - Passa context object como input
        - Retorna resultado para consolidação
        """
        
    async def get_agent_run_status(self, agent_run_id: str) -> dict:
        """Obtém status de execução de agente no Suna"""
        
    async def stop_agent_run(self, agent_run_id: str) -> bool:
        """Para execução de agente no Suna"""

### 8. Strategy Engine

**Responsabilidade**: Implementação das diferentes estratégias de workflow

```python
class WorkflowStrategy(ABC):
    def __init__(self, suna_api_client: SunaAPIClient):
        self.suna_api = suna_api_client
    
    @abstractmethod
    async def execute(
        self, 
        agent_ids: List[str], 
        context: RenumTeamContext,
        workflow_definition: dict
    ) -> ExecutionResult:
        pass

class SequentialWorkflowStrategy(WorkflowStrategy):
    """Execução sequencial - um agente por vez, context object passado adiante"""
    
    async def execute(self, agent_ids, context, workflow_definition):
        results = []
        current_context = context.context_object.copy()
        
        for agent_id in agent_ids:
            # Executa agente individual no Backend Suna
            result = await self.suna_api.execute_individual_agent(
                agent_id=agent_id,
                prompt=self._build_agent_prompt(agent_id, workflow_definition),
                context=current_context,
                user_api_keys=context.user_api_keys
            )
            results.append(result)
            
            # Atualiza context object com resultado do agente
            current_context = self._merge_context(current_context, result.get('output_context', {}))
            
            # Atualiza context no Redis
            await context.update_context_object(current_context, agent_id)
            
        return ExecutionResult(success=True, results=results, final_context=current_context)

class ParallelWorkflowStrategy(WorkflowStrategy):
    """Execução paralela - todos os agentes simultaneamente com mesmo context"""
    
    async def execute(self, agent_ids, context, workflow_definition):
        # Cria tasks para todos os agentes com mesmo context object
        tasks = [
            self.suna_api.execute_individual_agent(
                agent_id=agent_id,
                prompt=self._build_agent_prompt(agent_id, workflow_definition),
                context=context.context_object,
                user_api_keys=context.user_api_keys
            )
            for agent_id in agent_ids
        ]
        
        # Executa todos simultaneamente no Backend Suna
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolida resultados no context object
        consolidated_context = self._consolidate_parallel_results(
            context.context_object, results
        )
        
        return ExecutionResult(
            success=all(not isinstance(r, Exception) for r in results),
            results=results,
            final_context=consolidated_context
        )

class PipelineStrategy(ExecutionStrategy):
    """Execução em pipeline - saída de um é entrada do próximo"""
    
    async def execute(self, agents, context, message_bus):
        pipeline_data = context.get_variable("initial_input")
        results = []
        
        for agent in sorted(agents, key=lambda a: a.execution_order):
            # Usa saída do agente anterior como entrada
            agent_input = pipeline_data if results == [] else results[-1].output
            
            result = await self._execute_agent(
                agent, context, message_bus, input_data=agent_input
            )
            results.append(result)
            pipeline_data = result.output
            
        return ExecutionResult(success=True, results=results, final_output=pipeline_data)

class ConditionalStrategy(ExecutionStrategy):
    """Execução condicional - baseada em resultados e condições"""
    
    async def execute(self, agents, context, message_bus):
        executed_agents = set()
        results = []
        
        while len(executed_agents) < len(agents):
            # Encontra próximos agentes elegíveis
            eligible_agents = [
                agent for agent in agents 
                if agent.id not in executed_agents 
                and self._check_conditions(agent, context, results)
            ]
            
            if not eligible_agents:
                break  # Nenhum agente elegível, para execução
                
            # Executa agentes elegíveis em paralelo
            tasks = [
                self._execute_agent(agent, context, message_bus) 
                for agent in eligible_agents
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            executed_agents.update(agent.id for agent in eligible_agents)
            
        return ExecutionResult(success=True, results=results)
```

## Modelo de Dados

### Estrutura do Banco de Dados - Backend Renum

```sql
-- Tabela principal de equipes (Backend Renum)
CREATE TABLE renum_agent_teams (
    team_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_ids JSONB NOT NULL, -- Array de agent_ids que compõem a equipe
    workflow_definition JSONB NOT NULL, -- JSON/DSL que descreve a orquestração
    user_api_keys JSONB DEFAULT '{}', -- API keys personalizadas do usuário
    team_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Membros da equipe
CREATE TABLE team_members (
    team_id UUID REFERENCES agent_teams(team_id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(agent_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- 'leader', 'member', 'coordinator'
    execution_order INTEGER DEFAULT 0,
    dependencies JSONB DEFAULT '[]', -- Array de agent_ids que devem executar antes
    conditions JSONB DEFAULT '{}', -- Condições para execução (para estratégia condicional)
    agent_config JSONB DEFAULT '{}', -- Configurações específicas do agente na equipe
    is_active BOOLEAN DEFAULT true,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (team_id, agent_id)
);

-- Execuções de equipe (Backend Renum)
CREATE TABLE renum_team_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES renum_agent_teams(team_id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    execution_plan JSONB, -- Plano de execução gerado pelo workflow_definition
    shared_context JSONB DEFAULT '{}', -- Context object compartilhado
    initial_prompt TEXT,
    final_result JSONB,
    error_message TEXT,
    cost_metrics JSONB DEFAULT '{}', -- Métricas de custo por agente individual
    usage_metrics JSONB DEFAULT '{}', -- Consumo de modelos IA por agente
    api_keys_used JSONB DEFAULT '{}', -- Registro das API keys utilizadas
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Log de execução de agentes individuais na equipe (Backend Renum)
CREATE TABLE renum_team_agent_executions (
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    agent_id VARCHAR(255) NOT NULL, -- ID do agente no Suna Core
    suna_agent_run_id UUID, -- ID da execução no Backend Suna
    step_order INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    input_data JSONB,
    output_data JSONB,
    context_snapshot JSONB, -- Snapshot do contexto no momento da execução
    error_message TEXT,
    individual_cost_metrics JSONB DEFAULT '{}', -- Custo específico deste agente
    individual_usage_metrics JSONB DEFAULT '{}', -- Uso específico deste agente
    api_keys_snapshot JSONB DEFAULT '{}', -- API keys usadas por este agente
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (execution_id, agent_id)
);

-- Log de mensagens entre agentes (Backend Renum)
CREATE TABLE renum_team_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    from_agent_id VARCHAR(255), -- ID do agente no Suna Core
    to_agent_id VARCHAR(255), -- NULL para broadcast
    message_type VARCHAR(50) NOT NULL, -- 'info', 'request', 'response', 'error', 'context_update'
    content JSONB NOT NULL,
    requires_response BOOLEAN DEFAULT false,
    response_timeout INTEGER,
    response_message_id UUID REFERENCES renum_team_messages(message_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Contexto compartilhado (backup/auditoria - dados principais no Redis)
CREATE TABLE renum_team_context_snapshots (
    execution_id UUID REFERENCES renum_team_executions(execution_id) ON DELETE CASCADE,
    snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context_data JSONB NOT NULL, -- Context object completo
    version INTEGER DEFAULT 1,
    created_by_agent VARCHAR(255), -- ID do agente no Suna Core
    PRIMARY KEY (execution_id, snapshot_at)
);

-- Tabela para logging de uso de modelos IA (preparação para billing nativo)
CREATE TABLE renum_ai_usage_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    execution_id UUID REFERENCES renum_team_executions(execution_id),
    agent_id VARCHAR(255), -- ID do agente no Suna Core
    model_provider VARCHAR(100), -- 'openai', 'anthropic', 'custom', etc.
    model_name VARCHAR(100),
    api_key_type VARCHAR(50), -- 'user_provided', 'renum_native' (futuro)
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0,
    request_data JSONB, -- Dados da requisição para auditoria
    response_data JSONB, -- Dados da resposta para auditoria
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Estruturas Redis - Gerenciadas pelo Backend Renum

```python
# Estruturas Redis para performance e comunicação em tempo real
# Todas gerenciadas pelo Backend Renum como "memory" compartilhado

# Context object da equipe (atualizado por cada agente)
renum_team_context:{execution_id} = {
    "context_object": {...}, # Context object passado entre agentes
    "shared_memory": {...}, # Memory compartilhado da equipe
    "workflow_state": {...}, # Estado atual do workflow
    "user_api_keys": {...}, # API keys do usuário para esta execução
    "version": 1,
    "last_updated": "2024-01-01T00:00:00Z",
    "last_updated_by": "agent_id"
}

# Canal de mensagens da equipe (Backend Renum)
renum_team_messages:{execution_id} = [
    {
        "message_id": "uuid",
        "from_agent": "agent_id", # ID do agente no Suna Core
        "to_agent": "agent_id", # ou null para broadcast
        "type": "context_update", # 'info', 'request', 'response', 'context_update'
        "content": {...},
        "suna_thread_id": "uuid", # Thread ID no Suna Core
        "timestamp": "2024-01-01T00:00:00Z"
    }
]

# Status da execução em tempo real (Backend Renum)
renum_execution_status:{execution_id} = {
    "status": "running",
    "current_step": 2,
    "total_steps": 5,
    "workflow_definition": {...}, # Workflow sendo executado
    "active_agents": ["agent1", "agent2"],
    "completed_agents": ["agent0"],
    "failed_agents": [],
    "suna_agent_runs": {"agent1": "run_id_1", "agent2": "run_id_2"}, # Mapeamento para execuções no Suna
    "cost_tracking": {"agent1": 0.05, "agent2": 0.03}, # Custo por agente
    "last_updated": "2024-01-01T00:00:00Z"
}

# Fila de tarefas por agente
agent_task_queue:{execution_id}:{agent_id} = [
    {
        "task_id": "uuid",
        "type": "execute",
        "data": {...},
        "priority": 1,
        "created_at": "2024-01-01T00:00:00Z"
    }
]

# Lock para coordenação
team_execution_lock:{execution_id} = {
    "locked_by": "orchestrator_instance_id",
    "locked_at": "2024-01-01T00:00:00Z",
    "ttl": 300
}
```

## APIs e Endpoints

### Team Management API

```python
# Endpoints para gerenciamento de equipes

@router.post("/teams")
async def create_team(team_data: TeamCreateRequest, user_id: str = Depends(get_current_user_id)):
    """Cria nova equipe de agentes"""

@router.get("/teams")
async def list_teams(user_id: str = Depends(get_current_user_id)) -> List[TeamResponse]:
    """Lista equipes do usuário"""

@router.get("/teams/{team_id}")
async def get_team(team_id: str, user_id: str = Depends(get_current_user_id)) -> TeamResponse:
    """Obtém detalhes de uma equipe"""

@router.put("/teams/{team_id}")
async def update_team(team_id: str, team_data: TeamUpdateRequest, user_id: str = Depends(get_current_user_id)):
    """Atualiza configuração da equipe"""

@router.delete("/teams/{team_id}")
async def delete_team(team_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove equipe"""

@router.post("/teams/{team_id}/members")
async def add_team_member(team_id: str, member_data: TeamMemberRequest, user_id: str = Depends(get_current_user_id)):
    """Adiciona agente à equipe"""

@router.delete("/teams/{team_id}/members/{agent_id}")
async def remove_team_member(team_id: str, agent_id: str, user_id: str = Depends(get_current_user_id)):
    """Remove agente da equipe"""
```

### Team Execution API

```python
# Endpoints para execução de equipes

@router.post("/teams/{team_id}/execute")
async def execute_team(
    team_id: str, 
    execution_request: TeamExecutionRequest, 
    user_id: str = Depends(get_current_user_id)
) -> TeamExecutionResponse:
    """Inicia execução de uma equipe"""

@router.get("/executions/{execution_id}")
async def get_execution_status(
    execution_id: str, 
    user_id: str = Depends(get_current_user_id)
) -> ExecutionStatusResponse:
    """Obtém status da execução"""

@router.post("/executions/{execution_id}/stop")
async def stop_execution(
    execution_id: str, 
    user_id: str = Depends(get_current_user_id)
):
    """Para execução em andamento"""

@router.get("/executions/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str, 
    user_id: str = Depends(get_current_user_id)
) -> List[ExecutionLogEntry]:
    """Obtém logs detalhados da execução"""

@router.get("/executions/{execution_id}/context")
async def get_shared_context(
    execution_id: str, 
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Obtém contexto compartilhado atual"""

@router.get("/executions/{execution_id}/messages")
async def get_team_messages(
    execution_id: str, 
    user_id: str = Depends(get_current_user_id)
) -> List[TeamMessageResponse]:
    """Obtém mensagens trocadas entre agentes"""
```

### WebSocket para Monitoramento em Tempo Real

```python
@router.websocket("/executions/{execution_id}/monitor")
async def monitor_execution(websocket: WebSocket, execution_id: str):
    """WebSocket para monitoramento em tempo real da execução"""
    await websocket.accept()
    
    try:
        # Inscreve para updates da execução
        async for update in team_orchestrator.subscribe_to_execution_updates(execution_id):
            await websocket.send_json({
                "type": "execution_update",
                "data": update
            })
    except WebSocketDisconnect:
        pass
    finally:
        # Cleanup subscription
        await team_orchestrator.unsubscribe_from_execution_updates(execution_id)
```

## Integração com Sistema Existente

### Extensão do ThreadManager

```python
# Modificações no ThreadManager existente para suportar contexto de equipe

class ThreadManager:
    def __init__(self, trace=None, team_context=None, team_message_bus=None):
        # ... código existente ...
        self.team_context = team_context
        self.team_message_bus = team_message_bus
    
    async def add_message(self, thread_id, type, content, **kwargs):
        # ... código existente ...
        
        # Se faz parte de uma equipe, também adiciona ao contexto da equipe
        if self.team_context:
            await self.team_context.add_message_to_context(
                thread_id, type, content, **kwargs
            )
```

### Extensão do Agent Runner

```python
# Modificações no sistema de execução de agentes

async def run_agent_in_team_context(
    agent_config: dict,
    thread_id: str,
    team_context: TeamContext,
    message_bus: TeamMessageBus,
    **kwargs
):
    """Executa agente com contexto de equipe"""
    
    # Cria ThreadManager com contexto de equipe
    thread_manager = ThreadManager(
        team_context=team_context,
        team_message_bus=message_bus
    )
    
    # Adiciona ferramentas específicas de equipe
    thread_manager.add_tool(TeamContextTool, team_context=team_context)
    thread_manager.add_tool(TeamMessageTool, message_bus=message_bus)
    
    # Executa agente normalmente
    return await run_agent(
        thread_id=thread_id,
        thread_manager=thread_manager,
        agent_config=agent_config,
        **kwargs
    )
```

### Novas Ferramentas para Agentes

```python
class TeamContextTool(Tool):
    """Ferramenta para agentes acessarem contexto compartilhado"""
    
    def __init__(self, team_context: TeamContext):
        self.team_context = team_context
    
    async def set_shared_variable(self, key: str, value: Any):
        """Define variável no contexto compartilhado da equipe"""
        await self.team_context.set_variable(key, value, self.agent_id)
    
    async def get_shared_variable(self, key: str) -> Any:
        """Obtém variável do contexto compartilhado da equipe"""
        return await self.team_context.get_variable(key)
    
    async def get_all_shared_variables(self) -> Dict[str, Any]:
        """Obtém todas as variáveis compartilhadas"""
        return await self.team_context.get_all_variables()

class TeamMessageTool(Tool):
    """Ferramenta para agentes se comunicarem entre si"""
    
    def __init__(self, message_bus: TeamMessageBus):
        self.message_bus = message_bus
    
    async def send_message_to_agent(self, target_agent: str, message: str, message_type: str = "info"):
        """Envia mensagem para agente específico da equipe"""
        await self.message_bus.send_message(
            self.execution_id, self.agent_id, target_agent,
            TeamMessage(content={"text": message}, message_type=message_type)
        )
    
    async def broadcast_to_team(self, message: str, message_type: str = "info"):
        """Envia mensagem para todos os agentes da equipe"""
        await self.message_bus.broadcast_message(
            self.execution_id, self.agent_id,
            TeamMessage(content={"text": message}, message_type=message_type)
        )
    
    async def request_from_agent(self, target_agent: str, request: str, timeout: int = 30) -> str:
        """Solicita resposta de agente específico"""
        response = await self.message_bus.request_response(
            self.execution_id, self.agent_id, target_agent,
            TeamMessage(content={"text": request}, message_type="request"),
            timeout=timeout
        )
        return response.content.get("text", "")
```

## Considerações de Performance

### Otimizações Redis

```python
# Pipeline Redis para operações em lote
async def batch_context_updates(self, updates: List[ContextUpdate]):
    """Atualiza múltiplas variáveis de contexto em uma operação"""
    pipe = self.redis.pipeline()
    for update in updates:
        pipe.hset(f"team_context:{update.execution_id}", update.key, update.value)
    await pipe.execute()

# Pub/Sub para notificações em tempo real
async def subscribe_to_context_changes(self, execution_id: str):
    """Inscreve para mudanças no contexto em tempo real"""
    pubsub = self.redis.pubsub()
    await pubsub.subscribe(f"team_context_changes:{execution_id}")
    
    async for message in pubsub.listen():
        if message['type'] == 'message':
            yield json.loads(message['data'])
```

### Pool de Conexões

```python
# Pool de conexões para agentes
class AgentConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections = {}
    
    async def get_agent_connection(self, agent_id: str):
        """Obtém conexão reutilizável para agente"""
        if agent_id in self.active_connections:
            return self.active_connections[agent_id]
        
        connection = await self.pool.get()
        self.active_connections[agent_id] = connection
        return connection
    
    async def release_agent_connection(self, agent_id: str):
        """Libera conexão do agente"""
        if agent_id in self.active_connections:
            connection = self.active_connections.pop(agent_id)
            await self.pool.put(connection)
```

## Monitoramento e Observabilidade

### Métricas Coletadas

```python
class TeamMetricsCollector:
    def __init__(self):
        self.metrics = {
            'execution_duration': [],
            'agent_execution_times': {},
            'message_count': 0,
            'context_updates': 0,
            'error_count': 0,
            'success_rate': 0.0
        }
    
    async def track_execution_start(self, execution_id: str):
        """Inicia tracking de uma execução"""
        
    async def track_agent_execution(self, agent_id: str, duration: float):
        """Registra tempo de execução de um agente"""
        
    async def track_message_sent(self, from_agent: str, to_agent: str):
        """Registra mensagem enviada"""
        
    async def track_context_update(self, key: str, agent_id: str):
        """Registra atualização no contexto"""
        
    async def generate_execution_report(self, execution_id: str) -> ExecutionReport:
        """Gera relatório completo da execução"""
```

### Dashboard de Monitoramento

```python
# Endpoints para dashboard de monitoramento
@router.get("/teams/{team_id}/metrics")
async def get_team_metrics(team_id: str, period: str = "7d"):
    """Obtém métricas da equipe por período"""
    
@router.get("/executions/{execution_id}/performance")
async def get_execution_performance(execution_id: str):
    """Obtém métricas de performance de uma execução específica"""
    
@router.get("/teams/analytics")
async def get_teams_analytics(user_id: str = Depends(get_current_user_id)):
    """Obtém analytics agregadas de todas as equipes do usuário"""
```

## Segurança e Isolamento

### Row Level Security (RLS)

```sql
-- Políticas RLS para isolamento de dados

-- Equipes só podem ser acessadas pelo proprietário
CREATE POLICY team_access_policy ON agent_teams
    FOR ALL USING (account_id = auth.uid());

-- Membros da equipe só podem ser gerenciados pelo proprietário da equipe
CREATE POLICY team_members_policy ON team_members
    FOR ALL USING (
        team_id IN (
            SELECT team_id FROM agent_teams WHERE account_id = auth.uid()
        )
    );

-- Execuções só podem ser acessadas por quem iniciou ou é proprietário da equipe
CREATE POLICY team_executions_policy ON team_executions
    FOR ALL USING (
        initiated_by = auth.uid() OR
        team_id IN (
            SELECT team_id FROM agent_teams WHERE account_id = auth.uid()
        )
    );
```

### Validação de Permissões

```python
async def validate_team_access(team_id: str, user_id: str) -> bool:
    """Valida se usuário tem acesso à equipe"""
    client = await db.client
    result = await client.table('agent_teams').select('account_id').eq('team_id', team_id).execute()
    
    if not result.data:
        return False
    
    return result.data[0]['account_id'] == user_id

async def validate_agent_ownership(agent_id: str, user_id: str) -> bool:
    """Valida se usuário é proprietário do agente"""
    client = await db.client
    result = await client.table('agents').select('account_id').eq('agent_id', agent_id).execute()
    
    if not result.data:
        return False
    
    return result.data[0]['account_id'] == user_id
```

## Tratamento de Erros e Recuperação

### Estratégias de Retry

```python
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_delay: int = 60
    retry_on_exceptions: List[Type[Exception]] = [ConnectionError, TimeoutError]

async def execute_with_retry(func, retry_config: RetryConfig, *args, **kwargs):
    """Executa função com retry automático"""
    last_exception = None
    
    for attempt in range(retry_config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if type(e) not in retry_config.retry_on_exceptions:
                raise
            
            last_exception = e
            if attempt < retry_config.max_attempts - 1:
                delay = min(
                    retry_config.backoff_factor ** attempt,
                    retry_config.max_delay
                )
                await asyncio.sleep(delay)
    
    raise last_exception
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Executa função com circuit breaker"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise
```

## Próximos Passos

1. **Validação do Design**: Review técnico com a equipe
2. **Prototipagem**: Implementar MVP da orquestração básica
3. **Testes de Carga**: Validar performance com múltiplos agentes
4. **Implementação Incremental**: Desenvolver por componentes
5. **Integração e Testes**: Validar integração com sistema existente