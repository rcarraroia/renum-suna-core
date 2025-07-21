# Problemas Conhecidos e Soluções

Este documento lista problemas comuns encontrados durante a instalação e uso das dependências do projeto Suna/Renum, junto com suas soluções.

## Problemas de Instalação

### Erro: No module named 'mcp'

**Problema:**
```
ModuleNotFoundError: No module named 'mcp'
```

**Causa:**
A biblioteca MCP não está instalada ou não está acessível no ambiente Python.

**Solução:**
1. Execute o script de instalação do MCP:
   ```bash
   install_mcp_deps.bat
   ```
2. Verifique se a instalação foi bem-sucedida:
   ```python
   import mcp
   print(mcp.__version__)
   ```
3. Se o problema persistir, tente instalar manualmente:
   ```bash
   pip install mcp
   ```

### Erro: Incompatibilidade de Versão do Python

**Problema:**
```
AttributeError: module 'logging' has no attribute 'getLevelNamesMapping'
```

**Causa:**
Este erro ocorre quando você está usando uma versão do Python anterior à 3.11, que não possui o método `getLevelNamesMapping` no módulo `logging`.

**Solução:**
1. Verifique a versão do Python:
   ```bash
   python --version
   ```
2. Certifique-se de estar usando Python 3.11 ou superior.
3. Se necessário, crie um novo ambiente virtual com Python 3.11:
   ```bash
   python3.11 -m venv backend/venv311
   ```
4. Ative o ambiente virtual correto:
   ```bash
   call backend\venv311\Scripts\activate.bat
   ```

### Erro: Conflito de Versões do Pydantic

**Problema:**
```
ImportError: cannot import name 'BaseSettings' from 'pydantic'
```

**Causa:**
Este erro ocorre quando você está usando uma versão do Pydantic incompatível (geralmente v2.x) enquanto o código espera a v1.x.

**Solução:**
1. Instale a versão específica do Pydantic requerida:
   ```bash
   pip install pydantic==1.10.8
   ```
2. Verifique se a instalação foi bem-sucedida:
   ```python
   import pydantic
   print(pydantic.__version__)
   ```

### Erro: Falha ao Instalar Pacotes com Extensões C

**Problema:**
```
error: Microsoft Visual C++ 14.0 or greater is required.
```

**Causa:**
Alguns pacotes Python requerem um compilador C++ para instalar.

**Solução:**
1. Instale o Microsoft Visual C++ Build Tools:
   - Baixe e instale as "Build Tools for Visual Studio" do site da Microsoft
   - Certifique-se de selecionar "C++ build tools" durante a instalação
2. Reinicie o terminal e tente instalar novamente.
3. Alternativamente, procure por versões pré-compiladas (wheels) dos pacotes.

## Problemas de Execução

### Erro: Falha ao Conectar ao Redis

**Problema:**
```
ConnectionError: Error 111 connecting to redis:6379. Connection refused.
```

**Causa:**
O serviço Redis não está em execução ou não está acessível.

**Solução:**
1. Verifique se o Redis está em execução:
   ```bash
   docker ps | findstr redis
   ```
2. Se não estiver, inicie o serviço:
   ```bash
   docker compose up redis -d
   ```
3. Verifique as configurações de conexão no arquivo `.env`.

### Erro: Falha ao Conectar ao RabbitMQ

**Problema:**
```
ConnectionError: [Errno 111] Connection refused
```

**Causa:**
O serviço RabbitMQ não está em execução ou não está acessível.

**Solução:**
1. Verifique se o RabbitMQ está em execução:
   ```bash
   docker ps | findstr rabbitmq
   ```
2. Se não estiver, inicie o serviço:
   ```bash
   docker compose up rabbitmq -d
   ```
3. Verifique as configurações de conexão no arquivo `.env`.

### Erro: Falha ao Iniciar o Worker Dramatiq

**Problema:**
```
dramatiq.errors.BrokerError: No broker specified
```

**Causa:**
O broker (RabbitMQ) não foi configurado corretamente para o Dramatiq.

**Solução:**
1. Certifique-se de que o RabbitMQ está em execução.
2. Verifique se o broker está configurado corretamente no código:
   ```python
   import dramatiq
   from dramatiq.brokers.rabbitmq import RabbitMQBroker
   
   rabbitmq_broker = RabbitMQBroker(host="localhost", port=5672)
   dramatiq.set_broker(rabbitmq_broker)
   ```

### Erro: Falha ao Conectar ao Supabase

**Problema:**
```
HTTPError: 401 Client Error: Unauthorized for url
```

**Causa:**
As credenciais do Supabase estão incorretas ou expiradas.

**Solução:**
1. Verifique se as variáveis de ambiente do Supabase estão configuradas corretamente no arquivo `.env`.
2. Verifique se o projeto Supabase está ativo e acessível.
3. Gere novas chaves de API se necessário.

## Problemas de Dependências

### Erro: Versões Incompatíveis

**Problema:**
```
ImportError: cannot import name 'X' from 'Y'
```

**Causa:**
Versões incompatíveis de pacotes estão instaladas.

**Solução:**
1. Execute o script de verificação de compatibilidade:
   ```bash
   check_version_compatibility.bat
   ```
2. Siga as recomendações para atualizar ou fazer downgrade de pacotes.
3. Se necessário, crie um novo ambiente virtual limpo e instale todas as dependências novamente.

### Erro: Dependências Faltantes

**Problema:**
```
ModuleNotFoundError: No module named 'X'
```

**Causa:**
Uma dependência necessária não está instalada.

**Solução:**
1. Execute o script de verificação de dependências faltantes:
   ```bash
   check_missing_dependencies.bat
   ```
2. Instale as dependências faltantes conforme recomendado.

## Problemas de Ambiente

### Erro: Variáveis de Ambiente Não Definidas

**Problema:**
```
KeyError: 'SOME_ENV_VAR'
```

**Causa:**
Uma variável de ambiente necessária não está definida.

**Solução:**
1. Verifique se o arquivo `.env` existe e contém todas as variáveis necessárias.
2. Execute o script de verificação de variáveis de ambiente:
   ```bash
   check_env_vars.bat
   ```
3. Adicione as variáveis faltantes ao arquivo `.env`.

### Erro: Ambiente Virtual Não Encontrado

**Problema:**
```
'venv311' não é reconhecido como um comando interno ou externo
```

**Causa:**
O ambiente virtual não existe ou não está no caminho esperado.

**Solução:**
1. Verifique se o diretório do ambiente virtual existe:
   ```bash
   dir backend\venv311
   ```
2. Se não existir, crie um novo ambiente virtual:
   ```bash
   python -m venv backend\venv311
   ```
3. Ative o ambiente virtual:
   ```bash
   call backend\venv311\Scripts\activate.bat
   ```

## Problemas Específicos do MCP

### Erro: Falha ao Inicializar o MCP

**Problema:**
```
AttributeError: 'NoneType' object has no attribute 'X'
```

**Causa:**
O MCP não foi inicializado corretamente ou está faltando configuração.

**Solução:**
1. Verifique se o arquivo de configuração do MCP existe:
   ```bash
   dir .kiro\settings\mcp.json
   ```
2. Certifique-se de que a variável de ambiente `MCP_CREDENTIAL_ENCRYPTION_KEY` está definida.
3. Reinstale o MCP e suas dependências:
   ```bash
   install_mcp_deps.bat
   install_mcp_related_deps.bat
   ```

### Erro: Falha na Comunicação com o Servidor MCP

**Problema:**
```
ConnectionError: Cannot connect to host X:Y
```

**Causa:**
O servidor MCP não está acessível ou não está em execução.

**Solução:**
1. Verifique se o comando `uvx` está instalado e disponível no PATH.
2. Verifique se o servidor MCP está configurado corretamente no arquivo `.kiro/settings/mcp.json`.
3. Reinicie o servidor MCP.

## Recursos Adicionais

- [Documentação do MCP](https://docs.example.com/mcp)
- [Documentação do FastAPI](https://fastapi.tiangolo.com/)
- [Documentação do Dramatiq](https://dramatiq.io/)
- [Documentação do Supabase](https://supabase.io/docs)
- [Documentação do Redis](https://redis.io/documentation)
- [Documentação do RabbitMQ](https://www.rabbitmq.com/documentation.html)

## Contato para Suporte

Se você encontrar problemas que não estão documentados aqui, entre em contato com a equipe de suporte:

- Email: suporte@exemplo.com
- Canal do Slack: #suporte-tecnico