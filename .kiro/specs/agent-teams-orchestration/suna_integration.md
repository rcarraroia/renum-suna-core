# Integração Renum-Suna para Equipes de Agentes

Este documento detalha a arquitetura de integração entre o Backend Renum e o Suna Core para implementação do sistema de "Equipes de Agentes", conforme os requisitos específicos.

## Princípios Fundamentais

1. **Backend Renum como Orquestrador Central**
   - O Backend Renum atua como o "cérebro" da equipe
   - Gerencia o workflow, contexto compartilhado e comunicação
   - Delega a execução de agentes individuais para o Suna Core

2. **Suna Core Inalterado**
   - Zero modificações no código do Suna Core
   - Compatibilidade total com atualizações futuras
   - Funcionalidade individual de agentes mantida intacta

3. **Comunicação via API**
   - Backend Renum faz chamadas API para o Suna Core
   - Resultados são consolidados pelo Backend Renum
   - Redis utilizado para estado compartilhado

## Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Renum (FastAPI)                      │
│                        "CÉREBRO DA EQUIPE"                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │Team Orchestrator│  │ Workflow Engine │  │ Metrics Collector│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Suna (FastAPI)                       │
│                   "EXECUÇÃO DE AGENTES INDIVIDUAIS"             │
│                        (INALTERADO)                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Agent API     │  │  Thread Manager │  │   Tool Registry │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Cliente de API Suna

```python
class SunaApiClient:
    """Cliente para comunicação com o Suna Core API."""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )
    
    async def execute_agent(self, agent_id: str, thread_id: str, prompt: str, 
                           user_api_keys: Dict[str, str] = None) -> str:
        """Executa um agente individual no Suna Core.
        
        Args:
            agent_id: ID do agente no Suna Core
            thread_id: ID da thread para execução
            prompt: Prompt inicial para o agente
            user_api_keys: API keys personalizadas do usuário
            
        Returns:
            agent_run_id: ID da execução do agente
        """
        headers = {}
        if user_api_keys:
            # Adiciona headers para API keys personalizadas
            for key_name, key_value in user_api_keys.items():
                headers[f"X-API-Key-{key_name}"] = key_value
        
        url = f"{self.base_url}/api/thread/{thread_id}/agent/start"
        payload = {
            "agent_id": agent_id,
            "initial_prompt": prompt
        }
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise SunaApiError(f"Failed to execute agent: {error_text}")
            
            result = await response.json()
            return result["agent_run_id"]
    
    async def get_agent_run_status(self, agent_run_id: str) -> Dict[str, Any]:
        """Obtém o status de uma execução de agente."""
        url = f"{self.base_url}/api/agent-run/{agent_run_id}"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                error_text = await response.text()
                raise SunaApiError(f"Failed to get agent run status: {error_text}")
            
            return await response.json()
    
    async def get_agent_run_results(self, agent_run_id: str) -> Dict[str, Any]:
        """Obtém os resultados de uma execução de agente."""
        url = f"{self.base_url}/api/agent-run/{agent_run_id}/results"
        
        async with self.session.get(url) as response:
            if response.status != 200:
                error_text = await response.text()
                raise SunaApiError(f"Failed to get agent run results: {error_text}")
            
            return await response.json()
    
    async def stop_agent_run(self, agent_run_id: str) -> bool:
        """Para uma execução de agente em andamento."""
        url = f"{self.base_url}/api/agent-run/{agent_run_id}/stop"
        
        async with self.session.post(url) as response:
            if response.status != 200:
                error_text = await response.text()
                raise SunaApiError(f"Failed to stop agent run: {error_text}")
            
            return True
    
    async def close(self):
        """Fecha a sessão HTTP."""
        await self.session.close()
```

## Orquestrador de Equipes

```python
class TeamOrchestrator:
    """Orquestrador central para equipes de agentes."""
    
    def __init__(self, db_connection, redis_client, suna_api_client: SunaApiClient):
        self.db = db_connection
        self.redis = redis_client
        self.suna_api_client = suna_api_client
        self.execution_engine = ExecutionEngine()
        self.context_manager = TeamContextManager(redis_client)
        self.message_bus = TeamMessageBus(redis_client)
        self.metrics_collector = TeamMetricsCollector(db_connection)
        self.api_key_manager = ApiKeyManager(db_connection)
    
    async def execute_team(self, team_id: str, initial_prompt: str, user_id: str) -> str:
        """Inicia a execução de uma equipe de agentes.
        
        Args:
            team_id: ID da equipe
            initial_prompt: Prompt inicial
            user_id: ID do usuário
            
        Returns:
            execution_id: ID da execução
        """
        # 1. Carregar configuração da equipe
        team_config = await self._load_team_config(team_id, user_id)
        
        # 2. Criar plano de execução baseado no workflow_definition
        execution_plan = await self.execution_engine.create_execution_plan(team_config)
        
        # 3. Criar registro de execução
        execution_id = await self._create_execution_record(team_id, user_id, execution_plan, initial_prompt)
        
        # 4. Inicializar contexto compartilhado
        await self.context_manager.create_context(execution_id, {"initial_prompt": initial_prompt})
        
        # 5. Iniciar execução assíncrona
        asyncio.create_task(self._execute_workflow(execution_id, execution_plan, team_config))
        
        return execution_id
    
    async def _execute_workflow(self, execution_id: str, execution_plan: Dict, team_config: Dict):
        """Executa o workflow da equipe conforme o plano de execução."""
        try:
            # 1. Atualizar status para 'running'
            await self._update_execution_status(execution_id, "running")
            
            # 2. Obter API keys personalizadas do usuário
            user_api_keys = await self.api_key_manager.get_user_api_keys(team_config["user_id"])
            
            # 3. Executar o workflow conforme a estratégia definida
            workflow_type = team_config.get("workflow_definition", {}).get("type", "sequential")
            
            if workflow_type == "sequential":
                await self._execute_sequential_workflow(execution_id, execution_plan, user_api_keys)
            elif workflow_type == "parallel":
                await self._execute_parallel_workflow(execution_id, execution_plan, user_api_keys)
            elif workflow_type == "conditional":
                await self._execute_conditional_workflow(execution_id, execution_plan, user_api_keys)
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")
            
            # 4. Finalizar execução
            await self._update_execution_status(execution_id, "completed")
            
            # 5. Coletar métricas finais
            await self.metrics_collector.collect_final_metrics(execution_id)
            
        except Exception as e:
            # Registrar erro e atualizar status
            await self._update_execution_status(execution_id, "failed", str(e))
            logger.error(f"Team execution failed: {str(e)}")
    
    async def _execute_sequential_workflow(self, execution_id: str, execution_plan: Dict, user_api_keys: Dict):
        """Executa agentes sequencialmente, um após o outro."""
        context = await self.context_manager.get_context(execution_id)
        
        for step in execution_plan["steps"]:
            agent_id = step["agent_id"]
            
            # 1. Preparar prompt para o agente com contexto atual
            prompt = self._prepare_agent_prompt(step, context)
            
            # 2. Criar thread para este agente no Suna Core
            thread_id = await self._create_thread_in_suna()
            
            # 3. Executar agente no Suna Core
            agent_run_id = await self.suna_api_client.execute_agent(
                agent_id, thread_id, prompt, user_api_keys
            )
            
            # 4. Registrar início da execução do agente
            await self._register_agent_execution_start(execution_id, agent_id, agent_run_id)
            
            # 5. Aguardar conclusão do agente
            agent_result = await self._wait_for_agent_completion(agent_run_id)
            
            # 6. Atualizar contexto compartilhado com resultado
            await self.context_manager.update_context(
                execution_id, 
                {f"agent_{agent_id}_result": agent_result}
            )
            
            # 7. Registrar conclusão da execução do agente
            await self._register_agent_execution_complete(
                execution_id, agent_id, agent_result
            )
            
            # 8. Coletar métricas de uso
            await self.metrics_collector.collect_agent_metrics(
                execution_id, agent_id, agent_run_id
            )
    
    async def _execute_parallel_workflow(self, execution_id: str, execution_plan: Dict, user_api_keys: Dict):
        """Executa todos os agentes simultaneamente."""
        context = await self.context_manager.get_context(execution_id)
        tasks = []
        
        for step in execution_plan["steps"]:
            # Criar task para cada agente
            task = asyncio.create_task(
                self._execute_single_agent(execution_id, step, context, user_api_keys)
            )
            tasks.append(task)
        
        # Aguardar conclusão de todos os agentes
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados e erros
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Agent execution failed: {str(result)}")
                # Registrar erro para este agente específico
                await self._register_agent_execution_error(
                    execution_id, 
                    execution_plan["steps"][i]["agent_id"], 
                    str(result)
                )
    
    async def _execute_conditional_workflow(self, execution_id: str, execution_plan: Dict, user_api_keys: Dict):
        """Executa agentes com base em condições."""
        context = await self.context_manager.get_context(execution_id)
        executed_agents = set()
        
        while len(executed_agents) < len(execution_plan["steps"]):
            # Encontrar próximos agentes elegíveis
            eligible_steps = [
                step for step in execution_plan["steps"]
                if step["agent_id"] not in executed_agents
                and self._evaluate_conditions(step, context)
            ]
            
            if not eligible_steps:
                break  # Nenhum agente elegível, encerra execução
            
            # Executar agentes elegíveis em paralelo
            tasks = [
                asyncio.create_task(
                    self._execute_single_agent(execution_id, step, context, user_api_keys)
                )
                for step in eligible_steps
            ]
            
            # Aguardar conclusão dos agentes elegíveis
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Atualizar lista de agentes executados
            for step in eligible_steps:
                executed_agents.add(step["agent_id"])
            
            # Atualizar contexto para próxima iteração
            context = await self.context_manager.get_context(execution_id)
    
    async def _execute_single_agent(self, execution_id: str, step: Dict, context: Dict, user_api_keys: Dict):
        """Executa um único agente e processa seu resultado."""
        agent_id = step["agent_id"]
        
        try:
            # 1. Preparar prompt para o agente com contexto atual
            prompt = self._prepare_agent_prompt(step, context)
            
            # 2. Criar thread para este agente no Suna Core
            thread_id = await self._create_thread_in_suna()
            
            # 3. Executar agente no Suna Core
            agent_run_id = await self.suna_api_client.execute_agent(
                agent_id, thread_id, prompt, user_api_keys
            )
            
            # 4. Registrar início da execução do agente
            await self._register_agent_execution_start(execution_id, agent_id, agent_run_id)
            
            # 5. Aguardar conclusão do agente
            agent_result = await self._wait_for_agent_completion(agent_run_id)
            
            # 6. Atualizar contexto compartilhado com resultado
            await self.context_manager.update_context(
                execution_id, 
                {f"agent_{agent_id}_result": agent_result}
            )
            
            # 7. Registrar conclusão da execução do agente
            await self._register_agent_execution_complete(
                execution_id, agent_id, agent_result
            )
            
            # 8. Coletar métricas de uso
            await self.metrics_collector.collect_agent_metrics(
                execution_id, agent_id, agent_run_id
            )
            
            return agent_result
            
        except Exception as e:
            # Registrar erro para este agente
            await self._register_agent_execution_error(execution_id, agent_id, str(e))
            raise
```

## Gerenciador de API Keys

```python
class ApiKeyManager:
    """Gerencia API keys personalizadas dos usuários."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_user_api_keys(self, user_id: str) -> Dict[str, str]:
        """Obtém as API keys personalizadas do usuário."""
        client = await self.db.client
        result = await client.table('user_api_keys').select('*').eq('user_id', user_id).execute()
        
        if not result.data:
            return {}
        
        # Descriptografar as chaves antes de retornar
        api_keys = {}
        for key_data in result.data:
            api_keys[key_data['service_name']] = self._decrypt_api_key(key_data['encrypted_key'])
        
        return api_keys
    
    async def set_user_api_key(self, user_id: str, service_name: str, api_key: str) -> bool:
        """Define uma API key personalizada para o usuário."""
        client = await self.db.client
        
        # Criptografar a chave antes de armazenar
        encrypted_key = self._encrypt_api_key(api_key)
        
        # Inserir ou atualizar a chave
        await client.table('user_api_keys').upsert({
            'user_id': user_id,
            'service_name': service_name,
            'encrypted_key': encrypted_key,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        
        return True
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """Criptografa uma API key."""
        # Implementação de criptografia segura
        # ...
        return encrypted_key
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Descriptografa uma API key."""
        # Implementação de descriptografia segura
        # ...
        return decrypted_key
```

## Coletor de Métricas

```python
class TeamMetricsCollector:
    """Coleta métricas de uso e custo para equipes de agentes."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def collect_agent_metrics(self, execution_id: str, agent_id: str, agent_run_id: str):
        """Coleta métricas de uso e custo para um agente específico."""
        client = await self.db.client
        
        # 1. Obter dados de uso do Suna Core
        agent_run_data = await self._get_agent_run_data(agent_run_id)
        
        # 2. Calcular métricas de uso
        usage_metrics = self._calculate_usage_metrics(agent_run_data)
        
        # 3. Calcular métricas de custo
        cost_metrics = self._calculate_cost_metrics(usage_metrics)
        
        # 4. Registrar métricas no banco de dados
        await client.table('renum_ai_usage_logs').insert({
            'execution_id': execution_id,
            'agent_id': agent_id,
            'model_provider': usage_metrics.get('model_provider'),
            'model_name': usage_metrics.get('model_name'),
            'api_key_type': usage_metrics.get('api_key_type'),
            'tokens_input': usage_metrics.get('tokens_input', 0),
            'tokens_output': usage_metrics.get('tokens_output', 0),
            'cost_usd': cost_metrics.get('cost_usd', 0),
            'request_data': usage_metrics.get('request_data'),
            'response_data': usage_metrics.get('response_data')
        }).execute()
        
        # 5. Atualizar métricas na execução do agente
        await client.table('renum_team_agent_executions').update({
            'individual_usage_metrics': usage_metrics,
            'individual_cost_metrics': cost_metrics
        }).eq('execution_id', execution_id).eq('agent_id', agent_id).execute()
    
    async def collect_final_metrics(self, execution_id: str):
        """Coleta métricas finais para toda a execução da equipe."""
        client = await self.db.client
        
        # 1. Obter todas as métricas de agentes individuais
        result = await client.table('renum_team_agent_executions').select(
            'individual_usage_metrics', 'individual_cost_metrics'
        ).eq('execution_id', execution_id).execute()
        
        # 2. Agregar métricas
        total_usage = self._aggregate_usage_metrics([r['individual_usage_metrics'] for r in result.data])
        total_cost = self._aggregate_cost_metrics([r['individual_cost_metrics'] for r in result.data])
        
        # 3. Atualizar métricas na execução da equipe
        await client.table('renum_team_executions').update({
            'usage_metrics': total_usage,
            'cost_metrics': total_cost
        }).eq('execution_id', execution_id).execute()
    
    async def _get_agent_run_data(self, agent_run_id: str) -> Dict[str, Any]:
        """Obtém dados de uso do Suna Core para um agent_run_id."""
        # Implementação para obter dados do Suna Core
        # ...
        return agent_run_data
    
    def _calculate_usage_metrics(self, agent_run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de uso com base nos dados do agente."""
        # Implementação para calcular tokens, chamadas de API, etc.
        # ...
        return usage_metrics
    
    def _calculate_cost_metrics(self, usage_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula métricas de custo com base nas métricas de uso."""
        # Implementação para calcular custos baseados em preços de modelos
        # ...
        return cost_metrics
    
    def _aggregate_usage_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrega métricas de uso de múltiplos agentes."""
        # Implementação para somar tokens, chamadas, etc.
        # ...
        return aggregated_metrics
    
    def _aggregate_cost_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrega métricas de custo de múltiplos agentes."""
        # Implementação para somar custos
        # ...
        return aggregated_metrics
```

## Workflow DSL

O sistema utiliza uma DSL (Domain Specific Language) em formato JSON para definir o workflow de execução da equipe:

```json
{
  "type": "sequential",
  "agents": [
    {
      "agent_id": "agent-123",
      "role": "researcher",
      "input": {
        "source": "initial_prompt"
      }
    },
    {
      "agent_id": "agent-456",
      "role": "analyst",
      "input": {
        "source": "agent_result",
        "agent_id": "agent-123"
      }
    },
    {
      "agent_id": "agent-789",
      "role": "writer",
      "input": {
        "source": "combined",
        "sources": [
          {"type": "agent_result", "agent_id": "agent-123"},
          {"type": "agent_result", "agent_id": "agent-456"}
        ]
      }
    }
  ]
}
```

Para workflows condicionais:

```json
{
  "type": "conditional",
  "agents": [
    {
      "agent_id": "agent-123",
      "role": "classifier",
      "input": {
        "source": "initial_prompt"
      }
    },
    {
      "agent_id": "agent-456",
      "role": "technical_support",
      "conditions": [
        {
          "field": "agent_agent-123_result.category",
          "operator": "equals",
          "value": "technical"
        }
      ],
      "input": {
        "source": "agent_result",
        "agent_id": "agent-123"
      }
    },
    {
      "agent_id": "agent-789",
      "role": "billing_support",
      "conditions": [
        {
          "field": "agent_agent-123_result.category",
          "operator": "equals",
          "value": "billing"
        }
      ],
      "input": {
        "source": "agent_result",
        "agent_id": "agent-123"
      }
    }
  ]
}
```

## Considerações de Implementação

1. **Isolamento do Suna Core**
   - Toda comunicação com o Suna Core é feita via API
   - Nenhuma modificação direta no código do Suna Core
   - Compatibilidade garantida com atualizações futuras

2. **Gerenciamento de API Keys**
   - API keys dos usuários são armazenadas criptografadas
   - Passadas para o Suna Core apenas durante execução
   - Suporte para futuro modelo de billing nativo

3. **Métricas e Billing**
   - Registro detalhado de uso por agente individual
   - Atribuição correta de custos ao user_id da equipe
   - Preparação para futuro modelo de billing nativo

4. **Contexto Compartilhado**
   - Context object atualizado por cada agente
   - Gerenciado via Redis para performance
   - Snapshots periódicos para auditoria e recuperação