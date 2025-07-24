# WebSocket Manager

## Visão Geral

O WebSocket Manager é um componente responsável por gerenciar conexões WebSocket para monitoramento em tempo real de execuções de equipes de agentes. Ele permite que clientes se conectem a execuções específicas e recebam atualizações em tempo real sobre o progresso, status e resultados da execução.

## Funcionalidades

- **Gerenciamento de Conexões**: Conecta e desconecta clientes WebSocket
- **Broadcast de Mensagens**: Envia mensagens para todos os clientes conectados a uma execução
- **Tratamento de Erros**: Lida com erros de conexão e desconexões inesperadas

## Uso

### Conectar um Cliente

```python
await websocket_manager.connect(websocket, execution_id)
```

### Desconectar um Cliente

```python
websocket_manager.disconnect(websocket, execution_id)
```

### Enviar uma Mensagem

```python
await websocket_manager.broadcast(
    execution_id,
    {
        "type": "status_update",
        "data": {
            "status": "running",
            "progress": 50.0
        }
    }
)
```

## Tipos de Mensagens

### Status Update

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
    "failed_agents": []
  },
  "timestamp": "2023-01-01T00:02:30Z"
}
```

### Agent Status Update

```json
{
  "type": "agent_status_update",
  "data": {
    "agent_id": "agent-456",
    "status": "running",
    "step_order": 2
  },
  "timestamp": "2023-01-01T00:01:00Z"
}
```

### Progress Update

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

### Result Update

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

### Error Update

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

## Implementação

O WebSocket Manager é implementado como uma classe singleton que mantém um dicionário de conexões ativas por execution_id. Quando um cliente se conecta, ele é adicionado à lista de conexões para a execução correspondente. Quando um cliente se desconecta, ele é removido da lista.

O método `broadcast` envia uma mensagem para todos os clientes conectados a uma execução específica. Se ocorrer um erro ao enviar a mensagem para um cliente, ele é removido da lista de conexões.

## Considerações de Segurança

- **Autenticação**: Todos os clientes WebSocket devem ser autenticados antes de se conectarem
- **Validação de Execução**: Verificar se a execução existe e pertence ao usuário antes de permitir a conexão
- **Limite de Conexões**: Limitar o número de conexões por usuário para evitar sobrecarga do servidor

## Considerações de Performance

- **Eficiência de Broadcast**: O broadcast é otimizado para enviar mensagens apenas para clientes interessados em uma execução específica
- **Limpeza de Conexões**: Conexões inativas são removidas automaticamente para liberar recursos
- **Serialização de Mensagens**: As mensagens são serializadas como JSON para eficiência de transmissão