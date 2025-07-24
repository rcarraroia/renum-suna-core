# Documentação da API do Sistema de Equipes de Agentes

Esta documentação descreve os endpoints da API do sistema de orquestração de equipes de agentes.

## Base URL

```
http://localhost:9000/api/v1
```

## Autenticação

Todos os endpoints requerem autenticação. A autenticação é feita através do cabeçalho `Authorization` com um token JWT:

```
Authorization: Bearer YOUR_TOKEN
```

## Endpoints

### Equipes

#### Criar uma Equipe

```
POST /teams
```

**Descrição**: Cria uma nova equipe de agentes.

**Corpo da Requisição**:
```json
{
  "name": "Equipe de Análise de Dados",
  "description": "Equipe para análise de dados financeiros",
  "agent_ids": ["agent-123", "agent-456", "agent-789"],
  "workflow_definition": {
    "type": "sequential",
    "agents": [
      {
        "agent_id": "agent-123",
        "role": "leader",
        "execution_order": 1,
        "input": {
          "source": "initial_prompt"
        }
      },
      {
        "agent_id": "agent-456",
        "role": "member",
        "execution_order": 2,
        "input": {
          "source": "agent_result",
          "agent_id": "agent-123"
        }
      },
      {
        "agent_id": "agent-789",
        "role": "member",
        "execution_order": 3,
        "input": {
          "source": "combined",
          "sources": [
            {"type": "agent_result", "agent_id": "agent-123"},
            {"type": "agent_result", "agent_id": "agent-456"}
          ]
        }
      }
    ]
  },
  "user_api_keys": {
    "openai": "encrypted-api-key-1",
    "anthropic": "encrypted-api-key-2"
  },
  "team_config": {
    "max_tokens": 4000,
    "temperature": 0.7
  }
}
```

**Resposta**:
```json
{
  "team_id": "00000000-0000-0000-0000-000000000001",
  "user_id": "00000000-0000-0000-0000-000000000002",
  "name": "Equipe de Análise de Dados",
  "description": "Equipe para análise de dados financeiros",
  "agent_ids": ["agent-123", "agent-456", "agent-789"],
  "workflow_definition": {
    "type": "sequential",
    "agents": [
      {
        "agent_id": "agent-123",
        "role": "leader",
        "execution_order": 1,
        "input": {
          "source": "initial_prompt"
        }
      },
      {
        "agent_id": "agent-456",
        "role": "member",
        "execution_order": 2,
        "input": {
          "source": "agent_result",
          "agent_id": "agent-123"
        }
      },
      {
        "agent_id": "agent-789",
        "role": "member",
        "execution_order": 3,
        "input": {
          "source": "combined",
          "sources": [
            {"type": "agent_result", "agent_id": "agent-123"},
            {"type": "agent_result", "agent_id": "agent-456"}
          ]
        }
      }
    ]
  },
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### Listar Equipes

```
GET /teams
```

**Descrição**: Lista todas as equipes do usuário.

**Parâmetros de Consulta**:
- `page` (opcional): Número da página (padrão: 1)
- `limit` (opcional): Limite de resultados por página (padrão: 10)
- `name_filter` (opcional): Filtro por nome
- `active_only` (opcional): Incluir apenas equipes ativas (padrão: true)

**Resposta**:
```json
{
  "items": [
    {
      "team_id": "00000000-0000-0000-0000-000000000001",
      "user_id": "00000000-0000-0000-0000-000000000002",
      "name": "Equipe de Análise de Dados",
      "description": "Equipe para análise de dados financeiros",
      "agent_ids": ["agent-123", "agent-456", "agent-789"],
      "workflow_definition": {
        "type": "sequential",
        "agents": [...]
      },
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10,
  "pages": 1
}
```

#### Obter uma Equipe

```
GET /teams/{team_id}
```

**Descrição**: Obtém os detalhes de uma equipe específica.

**Parâmetros de Path**:
- `team_id`: ID da equipe

**Resposta**:
```json
{
  "team_id": "00000000-0000-0000-0000-000000000001",
  "user_id": "00000000-0000-0000-0000-000000000002",
  "name": "Equipe de Análise de Dados",
  "description": "Equipe para análise de dados financeiros",
  "agent_ids": ["agent-123", "agent-456", "agent-789"],
  "workflow_definition": {
    "type": "sequential",
    "agents": [...]
  },
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### Atualizar uma Equipe

```
PUT /teams/{team_id}
```

**Descrição**: Atualiza os detalhes de uma equipe específica.

**Parâmetros de Path**:
- `team_id`: ID da equipe

**Corpo da Requisição**:
```json
{
  "name": "Equipe de Análise de Dados Atualizada",
  "description": "Descrição atualizada",
  "agent_ids": ["agent-123", "agent-456", "agent-789", "agent-101"],
  "workflow_definition": {
    "type": "sequential",
    "agents": [...]
  },
  "is_active": true
}
```

**Resposta**:
```json
{
  "team_id": "00000000-0000-0000-0000-000000000001",
  "user_id": "00000000-0000-0000-0000-000000000002",
  "name": "Equipe de Análise de Dados Atualizada",
  "description": "Descrição atualizada",
  "agent_ids": ["agent-123", "agent-456", "agent-789", "agent-101"],
  "workflow_definition": {
    "type": "sequential",
    "agents": [...]
  },
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:01:00Z"
}
```

#### Excluir uma Equipe

```
DELETE /teams/{team_id}
```

**Descrição**: Exclui uma equipe específica.

**Parâmetros de Path**:
- `team_id`: ID da equipe

**Resposta**:
```json
{
  "status": "success",
  "message": "Team 00000000-0000-0000-0000-000000000001 deleted"
}
```

### Execuções

#### Executar uma Equipe

```
POST /teams/{team_id}/execute
```

**Descrição**: Inicia a execução de uma equipe.

**Parâmetros de Path**:
- `team_id`: ID da equipe

**Corpo da Requisição**:
```json
{
  "team_id": "00000000-0000-0000-0000-000000000001",
  "initial_prompt": "Analise os dados financeiros da empresa XYZ e prepare um relatório."
}
```

**Resposta**:
```json
{
  "execution_id": "00000000-0000-0000-0000-000000000003",
  "team_id": "00000000-0000-0000-0000-000000000001",
  "status": "pending",
  "initial_prompt": "Analise os dados financeiros da empresa XYZ e prepare um relatório.",
  "created_at": "2023-01-01T00:00:00Z"
}
```

#### Listar Execuções

```
GET /executions
```

**Descrição**: Lista todas as execuções do usuário.

**Parâmetros de Consulta**:
- `team_id` (opcional): Filtrar por equipe
- `limit` (opcional): Limite de resultados (padrão: 10)
- `offset` (opcional): Deslocamento para paginação (padrão: 0)

**Resposta**:
```json
[
  {
    "execution_id": "00000000-0000-0000-0000-000000000003",
    "team_id": "00000000-0000-0000-0000-000000000001",
    "status": "completed",
    "initial_prompt": "Analise os dados financeiros da empresa XYZ e prepare um relatório.",
    "final_result": {
      "summary": "Relatório financeiro da empresa XYZ",
      "details": "..."
    },
    "started_at": "2023-01-01T00:00:00Z",
    "completed_at": "2023-01-01T00:05:00Z",
    "created_at": "2023-01-01T00:00:00Z"
  }
]
```

#### Obter Status da Execução

```
GET /executions/{execution_id}/status
```

**Descrição**: Obtém o status atual de uma execução.

**Parâmetros de Path**:
- `execution_id`: ID da execução

**Resposta**:
```json
{
  "execution_id": "00000000-0000-0000-0000-000000000003",
  "team_id": "00000000-0000-0000-0000-000000000001",
  "status": "running",
  "progress": 50.0,
  "current_step": 2,
  "total_steps": 3,
  "active_agents": ["agent-456"],
  "completed_agents": ["agent-123"],
  "failed_agents": [],
  "started_at": "2023-01-01T00:00:00Z",
  "estimated_completion": "2023-01-01T00:05:00Z",
  "last_updated": "2023-01-01T00:02:30Z"
}
```

#### Obter Resultado da Execução

```
GET /executions/{execution_id}/result
```

**Descrição**: Obtém o resultado de uma execução concluída.

**Parâmetros de Path**:
- `execution_id`: ID da execução

**Resposta**:
```json
{
  "execution_id": "00000000-0000-0000-0000-000000000003",
  "team_id": "00000000-0000-0000-0000-000000000001",
  "status": "completed",
  "final_result": {
    "summary": "Relatório financeiro da empresa XYZ",
    "details": "..."
  },
  "agent_results": {
    "agent-123": {
      "result": "Dados financeiros analisados"
    },
    "agent-456": {
      "result": "Gráficos gerados"
    },
    "agent-789": {
      "result": "Relatório final compilado"
    }
  },
  "cost_metrics": {
    "total_cost_usd": 0.15,
    "agent_costs": {
      "agent-123": 0.05,
      "agent-456": 0.05,
      "agent-789": 0.05
    }
  },
  "usage_metrics": {
    "total_tokens": 5000,
    "agent_tokens": {
      "agent-123": 1500,
      "agent-456": 1500,
      "agent-789": 2000
    }
  },
  "started_at": "2023-01-01T00:00:00Z",
  "completed_at": "2023-01-01T00:05:00Z",
  "execution_duration": 300
}
```

#### Parar uma Execução

```
POST /executions/{execution_id}/stop
```

**Descrição**: Para uma execução em andamento.

**Parâmetros de Path**:
- `execution_id`: ID da execução

**Resposta**:
```json
{
  "status": "success",
  "message": "Execution 00000000-0000-0000-0000-000000000003 stopped"
}
```

#### Obter Logs da Execução

```
GET /executions/{execution_id}/logs
```

**Descrição**: Obtém os logs detalhados de uma execução.

**Parâmetros de Path**:
- `execution_id`: ID da execução

**Parâmetros de Consulta**:
- `limit` (opcional): Limite de resultados (padrão: 100)
- `offset` (opcional): Deslocamento para paginação (padrão: 0)
- `log_types` (opcional): Tipos de log a serem incluídos
- `agent_id` (opcional): Filtrar por agente específico

**Resposta**:
```json
[
  {
    "timestamp": "2023-01-01T00:00:00Z",
    "level": "info",
    "agent_id": "agent-123",
    "message": "Agent execution started",
    "details": {
      "step_order": 1,
      "suna_agent_run_id": "00000000-0000-0000-0000-000000000004"
    }
  },
  {
    "timestamp": "2023-01-01T00:01:00Z",
    "level": "info",
    "agent_id": "agent-123",
    "message": "Agent execution completed successfully",
    "details": {
      "step_order": 1,
      "execution_time": 60
    }
  }
]
```

### WebSocket para Monitoramento em Tempo Real

```
WebSocket /ws/executions/{execution_id}/monitor?token=YOUR_TOKEN
```

**Descrição**: WebSocket para monitoramento em tempo real da execução.

**Parâmetros de Path**:
- `execution_id`: ID da execução

**Parâmetros de Consulta**:
- `token`: Token de autenticação

**Mensagens Recebidas**:

1. Atualização de Status:
```json
{
  "type": "status_update",
  "data": {
    "execution_id": "00000000-0000-0000-0000-000000000003",
    "team_id": "00000000-0000-0000-0000-000000000001",
    "status": "running",
    "progress": 50.0,
    "current_step": 2,
    "total_steps": 3,
    "active_agents": ["agent-456"],
    "completed_agents": ["agent-123"],
    "failed_agents": [],
    "last_updated": "2023-01-01T00:02:30Z"
  },
  "timestamp": "2023-01-01T00:02:30Z"
}
```

2. Atualização de Status de Agente:
```json
{
  "type": "agent_status_update",
  "data": {
    "agent_id": "agent-456",
    "status": "running",
    "step_order": 2,
    "started_at": "2023-01-01T00:01:00Z"
  },
  "timestamp": "2023-01-01T00:01:00Z"
}
```

3. Atualização de Progresso:
```json
{
  "type": "progress_update",
  "data": {
    "execution_id": "00000000-0000-0000-0000-000000000003",
    "progress": 75.0,
    "current_step": 3,
    "total_steps": 4,
    "estimated_completion": "2023-01-01T00:05:00Z"
  },
  "timestamp": "2023-01-01T00:03:00Z"
}
```

4. Atualização de Resultado:
```json
{
  "type": "result_update",
  "data": {
    "execution_id": "00000000-0000-0000-0000-000000000003",
    "agent_id": "agent-456",
    "result": {
      "summary": "Análise de dados concluída",
      "details": "..."
    }
  },
  "timestamp": "2023-01-01T00:03:30Z"
}
```

5. Atualização de Erro:
```json
{
  "type": "error_update",
  "data": {
    "execution_id": "00000000-0000-0000-0000-000000000003",
    "agent_id": "agent-789",
    "error_message": "Falha ao processar dados",
    "error_details": {
      "code": "data_processing_error",
      "stack_trace": "..."
    }
  },
  "timestamp": "2023-01-01T00:04:00Z"
}
```

### API Keys

#### Criar uma API Key

```
POST /api-keys
```

**Descrição**: Cria uma nova API key para o usuário.

**Corpo da Requisição**:
```json
{
  "service_name": "openai",
  "api_key": "sk-your-api-key"
}
```

**Resposta**:
```json
{
  "key_id": "00000000-0000-0000-0000-000000000005",
  "user_id": "00000000-0000-0000-0000-000000000002",
  "service_name": "openai",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

#### Listar API Keys

```
GET /api-keys
```

**Descrição**: Lista todas as API keys do usuário.

**Resposta**:
```json
[
  {
    "key_id": "00000000-0000-0000-0000-000000000005",
    "user_id": "00000000-0000-0000-0000-000000000002",
    "service_name": "openai",
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  {
    "key_id": "00000000-0000-0000-0000-000000000006",
    "user_id": "00000000-0000-0000-0000-000000000002",
    "service_name": "anthropic",
    "is_active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

#### Excluir uma API Key

```
DELETE /api-keys/{service_name}
```

**Descrição**: Remove uma API key do usuário.

**Parâmetros de Path**:
- `service_name`: Nome do serviço

**Resposta**:
```json
{
  "status": "success",
  "message": "API key for service openai deleted"
}
```

## Códigos de Status

- `200 OK`: Requisição bem-sucedida
- `400 Bad Request`: Requisição inválida
- `401 Unauthorized`: Autenticação necessária
- `403 Forbidden`: Acesso negado
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

## Modelos de Dados

### TeamCreate

```json
{
  "name": "string",
  "description": "string",
  "agent_ids": ["string"],
  "workflow_definition": {
    "type": "sequential | parallel | pipeline | conditional",
    "agents": [
      {
        "agent_id": "string",
        "role": "leader | member | coordinator",
        "execution_order": 0,
        "input": {
          "source": "initial_prompt | agent_result | combined",
          "agent_id": "string",
          "sources": [
            {
              "type": "agent_result",
              "agent_id": "string"
            }
          ]
        },
        "conditions": {},
        "config": {}
      }
    ]
  },
  "user_api_keys": {},
  "team_config": {}
}
```

### TeamResponse

```json
{
  "team_id": "string (UUID)",
  "user_id": "string (UUID)",
  "name": "string",
  "description": "string",
  "agent_ids": ["string"],
  "workflow_definition": {},
  "is_active": true,
  "created_at": "string (datetime)",
  "updated_at": "string (datetime)"
}
```

### TeamExecutionCreate

```json
{
  "team_id": "string (UUID)",
  "initial_prompt": "string"
}
```

### TeamExecutionResponse

```json
{
  "execution_id": "string (UUID)",
  "team_id": "string (UUID)",
  "status": "pending | running | completed | failed | cancelled",
  "initial_prompt": "string",
  "final_result": {},
  "error_message": "string",
  "started_at": "string (datetime)",
  "completed_at": "string (datetime)",
  "created_at": "string (datetime)"
}
```

### TeamExecutionStatus

```json
{
  "execution_id": "string (UUID)",
  "team_id": "string (UUID)",
  "status": "pending | running | completed | failed | cancelled",
  "progress": 0.0,
  "current_step": 0,
  "total_steps": 0,
  "active_agents": ["string"],
  "completed_agents": ["string"],
  "failed_agents": ["string"],
  "started_at": "string (datetime)",
  "estimated_completion": "string (datetime)",
  "error_message": "string",
  "last_updated": "string (datetime)"
}
```

### TeamExecutionResult

```json
{
  "execution_id": "string (UUID)",
  "team_id": "string (UUID)",
  "status": "completed | failed | cancelled",
  "final_result": {},
  "agent_results": {},
  "cost_metrics": {
    "total_cost_usd": 0.0,
    "agent_costs": {}
  },
  "usage_metrics": {
    "total_tokens": 0,
    "agent_tokens": {}
  },
  "started_at": "string (datetime)",
  "completed_at": "string (datetime)",
  "execution_duration": 0
}
```

### ExecutionLogEntry

```json
{
  "timestamp": "string (datetime)",
  "level": "info | warning | error",
  "agent_id": "string",
  "message": "string",
  "details": {}
}
```

### UserApiKeyCreate

```json
{
  "service_name": "string",
  "api_key": "string"
}
```

### UserApiKeyResponse

```json
{
  "key_id": "string (UUID)",
  "user_id": "string (UUID)",
  "service_name": "string",
  "is_active": true,
  "created_at": "string (datetime)",
  "updated_at": "string (datetime)"
}
```