# Integração de Agentes com o Módulo RAG

Este documento descreve como integrar agentes da plataforma Renum com o módulo RAG (Retrieval-Augmented Generation) para enriquecer prompts com conhecimento contextual.

## Visão Geral

A integração de agentes com o módulo RAG permite que os agentes da plataforma Renum acessem conhecimento armazenado em bases de conhecimento para enriquecer suas respostas. O fluxo básico é:

1. O agente recebe uma consulta do usuário
2. O agente envia a consulta para o endpoint de integração RAG
3. O sistema identifica as bases de conhecimento relevantes para o cliente
4. O sistema recupera chunks relevantes com base na consulta
5. O sistema enriquece o prompt original com o contexto recuperado
6. O agente recebe o prompt enriquecido e o utiliza para gerar uma resposta

## Endpoints de API

### Enriquecer Prompt com RAG

**Endpoint:** `POST /api/knowledge-base/agent-rag/query`

**Descrição:** Processa uma consulta de agente e enriquece o prompt com conhecimento relevante.

**Requisição:**

```json
{
  "query": "Quais são os recursos principais do nosso produto?",
  "client_id": "client-123",
  "agent_id": "agent-456",
  "original_prompt": "Você é um assistente útil. Por favor, responda à pergunta do usuário.",
  "max_tokens": 4000,
  "top_k": 5
}
```

**Resposta:**

```json
{
  "enriched_prompt": "Vou fornecer algumas informações relevantes para ajudar a responder à pergunta do usuário.\n\nInformações Relevantes:\n[Fonte: Documentação do Produto]\nOs recursos principais do nosso produto incluem: análise de dados em tempo real, integração com APIs externas, painel de controle personalizável, relatórios automatizados e suporte a múltiplos idiomas.\n\nVocê é um assistente útil. Por favor, responda à pergunta do usuário.",
  "used_sources": [
    {
      "chunk_id": "chunk-123",
      "document_id": "doc-456",
      "document_name": "Documentação do Produto",
      "collection_id": "col-789",
      "collection_name": "Documentação Técnica",
      "similarity": 0.92,
      "content_preview": "Os recursos principais do nosso produto incluem: análise de dados em tempo real, integração com APIs externas..."
    }
  ],
  "metadata": {
    "knowledge_bases_found": 2,
    "collections_found": 5,
    "chunks_retrieved": 10,
    "chunks_used": 1
  }
}
```

### Enviar Feedback de Relevância

**Endpoint:** `POST /api/knowledge-base/agent-rag/feedback`

**Descrição:** Envia feedback sobre a relevância de um chunk recuperado.

**Requisição:**

```json
{
  "message_id": "message-789",
  "chunk_id": "chunk-123",
  "relevance_score": 5,
  "feedback_text": "Esta informação era exatamente o que eu precisava."
}
```

**Resposta:**

```json
{
  "success": true,
  "message": "Feedback enviado com sucesso"
}
```

## Exemplo de Uso

Veja o arquivo `backend/knowledge_base/rag/examples/agent_integration_example.py` para um exemplo completo de como usar a integração de agentes com o módulo RAG.

## Considerações de Implementação

### Autenticação

Todos os endpoints requerem autenticação usando um token JWT válido. O token deve ser incluído no cabeçalho `Authorization` como `Bearer {token}`.

### Limites e Cotas

- O número máximo de tokens para o contexto pode ser configurado (padrão: 4000)
- O número máximo de chunks recuperados pode ser configurado (padrão: 5)
- Considere os limites de uso do cliente ao recuperar e processar chunks

### Monitoramento e Feedback

- Use o endpoint de feedback para melhorar a qualidade da recuperação ao longo do tempo
- Monitore o uso de chunks para identificar quais documentos são mais úteis
- Analise os padrões de consulta para melhorar a organização das bases de conhecimento

## Fluxo de Integração

```
┌─────────┐         ┌──────────────┐         ┌───────────────┐         ┌─────────┐
│         │         │              │         │               │         │         │
│ Cliente ├────────►│ Agente Renum ├────────►│ Endpoint RAG  ├────────►│   LLM   │
│         │         │              │         │               │         │         │
└─────────┘         └──────────────┘         └───────┬───────┘         └────┬────┘
                                                     │                      │
                                                     ▼                      ▼
                                            ┌───────────────┐      ┌─────────────────┐
                                            │               │      │                 │
                                            │ Base de       │      │ Resposta        │
                                            │ Conhecimento  │      │ Enriquecida     │
                                            │               │      │                 │
                                            └───────────────┘      └─────────────────┘
```

## Próximos Passos

1. Implementar cache de consultas frequentes para melhorar o desempenho
2. Adicionar suporte para filtragem avançada de chunks por metadados
3. Implementar mecanismos de aprendizado para melhorar a relevância da recuperação
4. Adicionar suporte para múltiplos modelos de embedding