# Pontos de Integração entre o Backend do Suna e o Renum

Este documento identifica os principais pontos de integração entre o backend do Suna e o Renum, que precisam ser preservados durante o processo de sincronização.

## 1. Módulo RAG (Retrieval-Augmented Generation)

O módulo RAG é um componente crítico que foi adaptado para a plataforma Renum. Os seguintes arquivos contêm referências específicas ao Renum:

### 1.1. Arquivos Principais

- `backend/knowledge_base/rag/__init__.py`
  - Contém a descrição do módulo como parte da "Renum Platform"
  - Versão: 0.1.0

- `backend/knowledge_base/agent_rag_integration.py`
  - Implementa a integração entre agentes e o módulo RAG para a plataforma Renum
  - Fornece endpoints para agentes acessarem conhecimento armazenado no módulo RAG

### 1.2. Estrutura do Módulo RAG

O módulo RAG tem a seguinte estrutura que precisa ser preservada:

```
backend/knowledge_base/rag/
├── docs/
├── examples/
├── models/
├── repositories/
├── services/
├── tests/
├── utils/
├── __init__.py
├── api.py
└── README.md
```

## 2. Integração com o Banco de Dados

O Renum utiliza tabelas específicas no banco de dados Supabase, todas com o prefixo "renum_":

- `renum_agent_shares`
- `renum_settings`
- `renum_metrics`
- `renum_audit_logs`
- `renum_admins`
- `renum_admin_credentials`
- `renum_system_settings`
- `renum_knowledge_bases`
- `renum_knowledge_collections`
- `renum_documents`
- `renum_document_chunks`
- `renum_document_versions`

## 3. APIs e Endpoints

O backend do Suna expõe endpoints específicos que são utilizados pelo Renum:

- `/agent-rag/query`: Endpoint para enriquecimento de prompts com conhecimento relevante
- `/agent-rag/feedback`: Endpoint para submeter feedback sobre a relevância dos chunks recuperados

## 4. Serviços e Utilitários

Os seguintes serviços e utilitários são utilizados pela integração:

- `RetrievalService`: Serviço para recuperação de chunks relevantes
- `LLMIntegrationService`: Serviço para integração com modelos de linguagem
- Utilitários de autenticação e conexão com o banco de dados

## 5. Configurações

O arquivo `.env.example` contém configurações que são utilizadas tanto pelo Suna quanto pelo Renum. Qualquer alteração neste arquivo pode afetar a integração.

## Observações para Sincronização

Durante o processo de sincronização, é importante:

1. Preservar todas as referências ao Renum nos arquivos mencionados
2. Manter a estrutura do módulo RAG intacta
3. Verificar se novas dependências ou configurações não afetam a integração
4. Testar todos os endpoints e serviços após a sincronização
5. Garantir que as tabelas com prefixo "renum_" continuem funcionando corretamente