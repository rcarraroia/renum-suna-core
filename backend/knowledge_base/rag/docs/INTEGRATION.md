# Integração do Módulo RAG com a Plataforma Renum

## Visão Geral

Este documento descreve a integração do módulo RAG (Retrieval-Augmented Generation) com a plataforma Renum, permitindo que os agentes acessem conhecimento armazenado em bases de conhecimento para enriquecer suas respostas.

## Componentes Implementados

1. **Endpoint de Integração de Agentes**
   - Arquivo: `backend/knowledge_base/agent_rag_integration.py`
   - Endpoint: `POST /api/knowledge-base/agent-rag/query`
   - Funcionalidade: Recebe consultas de agentes, recupera informações relevantes e enriquece prompts

2. **Funções SQL para Integração**
   - Arquivo: `backend/knowledge_base/rag/utils/agent_integration_sql.py`
   - Funções:
     - `get_client_knowledge_bases`: Recupera bases de conhecimento para um cliente
     - `get_collections_for_knowledge_bases`: Recupera coleções para bases de conhecimento
     - `search_embeddings`: Busca embeddings relevantes para uma consulta
     - `filter_chunks`: Filtra chunks por metadados
     - `track_chunk_usage`: Rastreia o uso de chunks

3. **Inicialização do Banco de Dados**
   - Arquivo: `backend/knowledge_base/rag/utils/db_init.py`
   - Funcionalidade: Inicializa o banco de dados com tabelas, funções e políticas necessárias

4. **Documentação**
   - Arquivo: `backend/knowledge_base/rag/docs/agent_integration.md`
   - Conteúdo: Documentação detalhada sobre como usar a integração de agentes com o RAG

5. **Exemplos de Uso**
   - Arquivo: `backend/knowledge_base/rag/examples/agent_integration_example.py`
   - Funcionalidade: Demonstra como usar o endpoint de integração de agentes

6. **Testes**
   - Arquivo: `backend/knowledge_base/rag/tests/test_agent_integration.py`
   - Funcionalidade: Testes unitários para o endpoint de integração de agentes

## Fluxo de Integração

1. O agente recebe uma consulta do usuário
2. O agente envia a consulta para o endpoint `/api/knowledge-base/agent-rag/query`
3. O sistema identifica as bases de conhecimento relevantes para o cliente
4. O sistema recupera chunks relevantes com base na consulta
5. O sistema enriquece o prompt original com o contexto recuperado
6. O agente recebe o prompt enriquecido e o utiliza para gerar uma resposta
7. Opcionalmente, o agente pode enviar feedback sobre a relevância dos chunks

## Configuração

Para habilitar a integração do RAG com a plataforma Renum:

1. Certifique-se de que o módulo RAG esteja inicializado:
   ```python
   from knowledge_base.rag.utils.db_init import initialize_database
   
   await initialize_database()
   ```

2. Habilite o recurso RAG nas flags de recursos:
   ```sql
   INSERT INTO feature_flags (flag_name, enabled, description)
   VALUES ('rag_module', true, 'Enable RAG module functionality');
   ```

3. Certifique-se de que o router do RAG esteja incluído na API principal:
   ```python
   # Em backend/knowledge_base/api.py
   from knowledge_base.agent_rag_integration import router as agent_rag_router
   router.include_router(agent_rag_router)
   ```

## Uso pelos Agentes

Os agentes podem usar o endpoint de integração RAG da seguinte forma:

```python
async def enrich_prompt_with_knowledge(query, original_prompt):
    response = await api_client.post(
        "/api/knowledge-base/agent-rag/query",
        json={
            "query": query,
            "client_id": client_id,
            "agent_id": agent_id,
            "original_prompt": original_prompt,
            "max_tokens": 4000,
            "top_k": 5
        }
    )
    
    result = response.json()
    return result["enriched_prompt"]
```

## Próximos Passos

1. **Integração com o Fluxo de Agentes**
   - Modificar o fluxo de execução de agentes para usar automaticamente o RAG quando apropriado

2. **Interface de Usuário para Gerenciamento**
   - Desenvolver interfaces para gerenciar bases de conhecimento, coleções e documentos

3. **Análise de Uso**
   - Implementar dashboards para analisar o uso do RAG pelos agentes

4. **Aprendizado Contínuo**
   - Implementar mecanismos para melhorar a recuperação com base no feedback

5. **Otimização de Desempenho**
   - Implementar cache e otimizações para consultas frequentes