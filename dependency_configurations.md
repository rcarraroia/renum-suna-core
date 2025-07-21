# Configurações Especiais de Dependências

Este documento detalha as configurações especiais necessárias para algumas dependências do projeto Suna/Renum. Siga estas instruções para garantir o funcionamento adequado de cada componente.

## MCP (Model Context Protocol)

### Configuração Básica

O MCP requer configurações específicas para funcionar corretamente:

1. **Arquivo de Configuração**:
   
   Crie um arquivo `.kiro/settings/mcp.json` com o seguinte conteúdo:

   ```json
   {
     "mcpServers": {
       "aws-docs": {
         "command": "uvx",
         "args": ["awslabs.aws-documentation-mcp-server@latest"],
         "env": {
           "FASTMCP_LOG_LEVEL": "ERROR"
         },
         "disabled": false,
         "autoApprove": []
       }
     }
   }
   ```

2. **Variáveis de Ambiente**:
   
   Certifique-se de que a seguinte variável esteja definida no arquivo `.env`:

   ```
   MCP_CREDENTIAL_ENCRYPTION_KEY="bPMwnHIrSKwQ5/yJVWop3aE7dSXsJD7lqnRw8GCfGbg="
   ```

3. **Dependências Relacionadas**:
   
   O MCP depende de `pydantic-core`, `typing-extensions`, `aiohttp` e `websockets`. Certifique-se de que estas dependências estejam instaladas com as versões corretas.

### Solução de Problemas

- Se o MCP não estiver funcionando, verifique se o comando `uvx` está instalado e disponível no PATH.
- Verifique se o Python 3.11+ está sendo usado, pois versões anteriores podem causar problemas de compatibilidade.

## Supabase

### Configuração Básica

O Supabase requer as seguintes configurações:

1. **Variáveis de Ambiente**:
   
   Certifique-se de que as seguintes variáveis estejam definidas no arquivo `.env`:

   ```
   SUPABASE_URL=https://uxxvoicxhkakpguvavba.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_PROJECT_ID=uxxvoicxhkakpguvavba
   SUPABASE_DB_PASSWORD="caStmTcNr7o5Yhsw"
   ```

2. **Inicialização**:
   
   Para inicializar o cliente Supabase no código:

   ```python
   from supabase import create_client
   import os

   supabase_url = os.environ.get("SUPABASE_URL")
   supabase_key = os.environ.get("SUPABASE_ANON_KEY")
   supabase = create_client(supabase_url, supabase_key)
   ```

### Solução de Problemas

- Se ocorrerem erros de conexão, verifique se as credenciais estão corretas e se o projeto Supabase está ativo.
- Para problemas de SSL, certifique-se de que os certificados CA estão atualizados.

## Redis e RabbitMQ

### Configuração Básica

Redis e RabbitMQ são usados para cache e filas de mensagens:

1. **Variáveis de Ambiente**:
   
   Certifique-se de que as seguintes variáveis estejam definidas no arquivo `.env`:

   ```
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_PASSWORD=
   REDIS_SSL=false

   RABBITMQ_HOST=rabbitmq
   RABBITMQ_PORT=5672
   ```

2. **Docker Compose**:
   
   Certifique-se de que os serviços Redis e RabbitMQ estejam definidos no arquivo `docker-compose.yaml`:

   ```yaml
   services:
     redis:
       image: redis:alpine
       ports:
         - "6379:6379"
       volumes:
         - redis-data:/data

     rabbitmq:
       image: rabbitmq:3-management
       ports:
         - "5672:5672"
         - "15672:15672"
       volumes:
         - rabbitmq-data:/var/lib/rabbitmq
   ```

3. **Inicialização**:
   
   Para inicializar o cliente Redis no código:

   ```python
   import redis
   import os

   redis_client = redis.Redis(
       host=os.environ.get("REDIS_HOST", "localhost"),
       port=int(os.environ.get("REDIS_PORT", 6379)),
       password=os.environ.get("REDIS_PASSWORD", ""),
       ssl=os.environ.get("REDIS_SSL", "false").lower() == "true"
   )
   ```

### Solução de Problemas

- Se os serviços não estiverem disponíveis, execute `docker compose up redis rabbitmq -d` para iniciá-los.
- Verifique se as portas não estão sendo usadas por outros serviços.

## Dramatiq

### Configuração Básica

Dramatiq é usado para processamento de tarefas em background:

1. **Configuração**:
   
   Configure o Dramatiq para usar o RabbitMQ como broker:

   ```python
   import dramatiq
   from dramatiq.brokers.rabbitmq import RabbitMQBroker
   import os

   rabbitmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
   rabbitmq_port = int(os.environ.get("RABBITMQ_PORT", 5672))
   
   rabbitmq_broker = RabbitMQBroker(
       host=rabbitmq_host,
       port=rabbitmq_port,
       heartbeat=5
   )
   
   dramatiq.set_broker(rabbitmq_broker)
   ```

2. **Execução do Worker**:
   
   Para executar o worker Dramatiq:

   ```bash
   python -m dramatiq run_agent_background
   ```

### Solução de Problemas

- Se o worker não iniciar, verifique se o RabbitMQ está em execução e acessível.
- Verifique os logs para mensagens de erro específicas.

## Tavily

### Configuração Básica

Tavily é usado para busca na web:

1. **Variáveis de Ambiente**:
   
   Certifique-se de que a seguinte variável esteja definida no arquivo `.env`:

   ```
   TAVILY_API_KEY="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"
   ```

2. **Inicialização**:
   
   Para inicializar o cliente Tavily no código:

   ```python
   from tavily import TavilyClient
   import os

   tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
   ```

### Solução de Problemas

- Se ocorrerem erros de autenticação, verifique se a chave API está correta e ativa.
- Para problemas de limite de taxa, implemente estratégias de recuo exponencial.

## Daytona

### Configuração Básica

Daytona é usado para execução de agentes:

1. **Variáveis de Ambiente**:
   
   Certifique-se de que as seguintes variáveis estejam definidas no arquivo `.env`:

   ```
   DAYTONA_API_KEY="dtn_935e4890c83b26edc7d3bf2d4a3635d6a4a16feca88c3cd6af10cb78f904db6d"
   DAYTONA_SERVER_URL=https://app.daytona.io/api
   DAYTONA_TARGET=us
   ```

2. **Inicialização**:
   
   Para inicializar o cliente Daytona no código:

   ```python
   from daytona_sdk import Daytona
   import os

   daytona_client = Daytona(
       api_key=os.environ.get("DAYTONA_API_KEY"),
       server_url=os.environ.get("DAYTONA_SERVER_URL")
   )
   ```

### Solução de Problemas

- Se ocorrerem erros de autenticação, verifique se a chave API está correta e ativa.
- Verifique se o servidor Daytona está acessível a partir do seu ambiente.

## QStash

### Configuração Básica

QStash é usado para agendamento de tarefas:

1. **Variáveis de Ambiente**:
   
   Certifique-se de que as seguintes variáveis estejam definidas no arquivo `.env`:

   ```
   QSTASH_URL=https://qstash.upstash.io
   QSTASH_TOKEN=dc45389c-95c6-4eef-a453-df52c48b8982
   QSTASH_CURRENT_SIGNING_KEY=sig_6zbn5hffr7eQGCQRL5DdEX43qysG
   QSTASH_NEXT_SIGNING_KEY=sig_6UXawsJmD8fbHvmaEzc9sXrocxSF
   ```

### Solução de Problemas

- Se ocorrerem erros de autenticação, verifique se o token está correto e ativo.
- Para problemas de agendamento, verifique se as chaves de assinatura estão atualizadas.

## Sentry

### Configuração Básica

Sentry é usado para monitoramento de erros:

1. **Inicialização**:
   
   Para inicializar o Sentry no código:

   ```python
   import sentry_sdk
   
   sentry_sdk.init(
       dsn="https://your-sentry-dsn@sentry.io/project-id",
       traces_sample_rate=0.1,
       environment="development"  # ou "production"
   )
   ```

### Solução de Problemas

- Se os erros não estiverem sendo reportados, verifique se o DSN está correto.
- Verifique se o ambiente está configurado corretamente.

## Considerações Finais

- Sempre mantenha as variáveis de ambiente em um arquivo `.env` seguro e não o inclua no controle de versão.
- Use ambientes virtuais para isolar as dependências do projeto.
- Mantenha as versões das dependências atualizadas, mas teste cuidadosamente antes de atualizar em produção.
- Documente quaisquer alterações nas configurações para referência futura.