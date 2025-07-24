# Instruções de Execução do Sistema de Equipes de Agentes

Este documento fornece instruções para configurar e executar o sistema de orquestração de equipes de agentes.

## Pré-requisitos

- Python 3.9+
- Redis 6.0+
- Supabase (PostgreSQL 13+)
- Acesso ao Suna Core API

## Configuração do Ambiente

### 1. Clone o Repositório

```bash
git clone https://github.com/renum/renum-backend.git
cd renum-backend
```

### 2. Crie e Ative um Ambiente Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
pip install -e .
```

### 4. Configure as Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```
# Ambiente
ENV=development
DEBUG=true

# API
API_PREFIX=/api/v1
PROJECT_NAME="Renum Backend"
VERSION=0.1.0

# Segurança
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS
CORS_ORIGINS=["*"]
CORS_METHODS=["*"]
CORS_HEADERS=["*"]

# Banco de dados
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key-here

# Redis
REDIS_URL=redis://localhost:6379/0

# Suna Core
SUNA_API_URL=http://localhost:8000/api
SUNA_API_KEY=your-suna-api-key-here

# Limites
MAX_CONCURRENT_EXECUTIONS=5
MAX_AGENTS_PER_TEAM=10

# Criptografia
API_KEY_ENCRYPTION_KEY=your-encryption-key-here
```

### 5. Aplique o Schema do Banco de Dados

Execute o script para criar as tabelas no banco de dados:

```bash
python scripts/apply_team_tables.py
```

## Execução do Sistema

### Usando Docker

```bash
# Inicie os contêineres
docker-compose up -d
```

### Execução Local

```bash
# Inicie o Redis (se não estiver usando Docker)
redis-server

# Inicie o servidor
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

## Testando o Sistema

### Executando Testes Unitários

```bash
# Execute todos os testes
pytest

# Execute testes específicos
pytest tests/test_team_repository.py
pytest tests/test_team_orchestrator.py
pytest tests/test_execution_engine.py
pytest tests/test_suna_api_client.py
pytest tests/test_api.py
```

### Testando a API

Você pode usar o script de teste da API para verificar se tudo está funcionando corretamente:

```bash
# Configure a variável de ambiente AUTH_TOKEN
export AUTH_TOKEN=your-auth-token

# Execute o script de teste
python scripts/test_team_api.py
```

## Usando a API

### Documentação da API

A documentação da API está disponível em:

- Swagger UI: http://localhost:9000/docs
- OpenAPI JSON: http://localhost:9000/api/v1/openapi.json

### Exemplos de Uso

#### Criar uma Equipe

```bash
curl -X POST http://localhost:9000/api/v1/teams \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
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
    }
  }'
```

#### Executar uma Equipe

```bash
curl -X POST http://localhost:9000/api/v1/teams/TEAM_ID/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "team_id": "TEAM_ID",
    "initial_prompt": "Analise os dados financeiros da empresa XYZ e prepare um relatório."
  }'
```

#### Obter Status da Execução

```bash
curl -X GET http://localhost:9000/api/v1/executions/EXECUTION_ID/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Parar uma Execução

```bash
curl -X POST http://localhost:9000/api/v1/executions/EXECUTION_ID/stop \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoramento em Tempo Real

Para monitorar uma execução em tempo real, você pode usar o WebSocket:

```javascript
// Exemplo em JavaScript
const socket = new WebSocket(`ws://localhost:9000/api/v1/ws/executions/EXECUTION_ID/monitor?token=YOUR_TOKEN`);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Atualização da execução:', data);
};

socket.onclose = (event) => {
  console.log('Conexão fechada:', event.code, event.reason);
};

socket.onerror = (error) => {
  console.error('Erro na conexão:', error);
};
```

## Solução de Problemas

### Problemas de Conexão com o Banco de Dados

- Verifique se as credenciais do Supabase estão corretas no arquivo `.env`
- Verifique se as políticas RLS estão configuradas corretamente

### Problemas de Conexão com o Redis

- Verifique se o Redis está em execução
- Verifique se a URL do Redis está correta no arquivo `.env`

### Problemas de Comunicação com o Suna Core

- Verifique se o Suna Core está em execução
- Verifique se a URL e a API key do Suna Core estão corretas no arquivo `.env`
- Verifique os logs para erros de comunicação

## Logs

Os logs são gerados no console e podem ser configurados para serem salvos em um arquivo. O nível de log pode ser configurado no arquivo `.env` através da variável `DEBUG`.

## Suporte

Para obter suporte, entre em contato com a equipe de desenvolvimento ou abra uma issue no repositório do projeto.