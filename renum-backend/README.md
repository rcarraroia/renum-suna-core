# Renum Backend

Backend para a Plataforma Renum Suna, incluindo o sistema de Equipes de Agentes.

## Visão Geral

O Renum Backend é responsável por gerenciar equipes de agentes de IA, permitindo que usuários criem, configurem e executem equipes coordenadas para resolver tarefas complexas que requerem múltiplas especialidades.

## Status do Projeto

O sistema de orquestração de equipes de agentes foi implementado com sucesso, incluindo todos os componentes principais necessários para o funcionamento do backend. A implementação seguiu a arquitetura definida no documento de design, com separação clara de responsabilidades entre os diferentes componentes.

Para mais detalhes sobre o estado atual da implementação, consulte os seguintes documentos:
- [Resumo da Implementação](./IMPLEMENTATION_SUMMARY.md)
- [Instruções de Execução](./EXECUTION_INSTRUCTIONS.md)
- [Documentação da API](./API_DOCUMENTATION.md)
- [Conclusão](./CONCLUSAO.md)

## Funcionalidades

- Criação e gerenciamento de equipes de agentes
- Execução de equipes com diferentes estratégias (sequencial, paralelo, condicional, pipeline)
- Monitoramento em tempo real de execuções
- Gerenciamento de contexto compartilhado entre agentes
- Sistema de mensagens entre agentes
- Gerenciamento seguro de API keys
- Integração com o Suna Core para execução de agentes individuais

## Requisitos

- Python 3.9+
- Redis 6.0+
- Supabase (PostgreSQL 13+)
- Acesso ao Suna Core API

## Instalação

### Usando Docker

```bash
# Clone o repositório
git clone https://github.com/renum/renum-backend.git
cd renum-backend

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Inicie os contêineres
docker-compose up -d
```

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/renum/renum-backend.git
cd renum-backend

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\\Scripts\\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
pip install -e .

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Aplique o schema do banco de dados
python scripts/apply_team_tables.py

# Teste a instalação
python scripts/test_installation.py

# Inicie o servidor
python scripts/run_server.py
# ou
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

## Uso

### API

A API está disponível em `http://localhost:9000/api/v1`.

A documentação da API está disponível em `http://localhost:9000/docs`.

### Exemplos

#### Criar uma equipe

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

#### Executar uma equipe

```bash
curl -X POST http://localhost:9000/api/v1/teams/TEAM_ID/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "team_id": "TEAM_ID",
    "initial_prompt": "Analise os dados financeiros da empresa XYZ e prepare um relatório."
  }'
```

## Desenvolvimento

### Estrutura do Projeto

```
renum-backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── teams.py
│   │   │   └── team_executions.py
│   ├── core/
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── logger.py
│   ├── db/
│   │   └── database.py
│   ├── models/
│   │   └── team_models.py
│   ├── repositories/
│   │   ├── team_repository.py
│   │   └── team_execution_repository.py
│   ├── services/
│   │   ├── api_key_manager.py
│   │   ├── execution_engine.py
│   │   ├── suna_api_client.py
│   │   ├── team_context_manager.py
│   │   ├── team_message_bus.py
│   │   └── team_orchestrator.py
│   └── main.py
├── scripts/
│   ├── apply_team_tables.py
│   ├── create_team_tables.sql
│   ├── run_server.py
│   ├── test_installation.py
│   └── test_team_api.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_execution_engine.py
│   ├── test_suna_api_client.py
│   ├── test_team_orchestrator.py
│   └── test_team_repository.py
├── .env.example
├── .gitignore
├── API_DOCUMENTATION.md
├── CONCLUSAO.md
├── docker-compose.yml
├── Dockerfile
├── EXECUTION_INSTRUCTIONS.md
├── IMPLEMENTATION_SUMMARY.md
├── pyproject.toml
├── README.md
└── requirements.txt
```

### Testes

```bash
# Execute os testes
pytest

# Execute os testes com cobertura
pytest --cov=app

# Execute testes específicos
pytest tests/test_team_repository.py
pytest tests/test_team_orchestrator.py
pytest tests/test_execution_engine.py
pytest tests/test_suna_api_client.py
pytest tests/test_api.py
```

### Próximos Passos

1. **Testes de Integração**: Implementar testes end-to-end das estratégias e fluxos completos.
2. **Frontend**: Desenvolver a interface para gerenciamento de equipes, visualizador de fluxo e dashboard de monitoramento.
3. **Otimizações de Performance**: Implementar otimizações para melhorar a performance do sistema.
4. **Recursos Avançados**: Implementar recursos avançados como sistema de aprovações, ferramentas para agentes e templates de equipe.

## Licença

Proprietary - Todos os direitos reservados.