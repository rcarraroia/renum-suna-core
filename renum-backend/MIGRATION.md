# Migração do Módulo RAG

Este documento descreve a migração do módulo RAG (Retrieval-Augmented Generation) do Suna Core para a Plataforma Renum, conforme o plano de desenvolvimento aprovado.

## Visão Geral

De acordo com o plano de desenvolvimento da Plataforma Renum, o módulo RAG é responsabilidade da Plataforma Renum, não do Suna Core. O Suna Core deve ser mantido como um "cérebro executor" dos agentes, enquanto a Plataforma Renum atua como orquestradora, gerenciando bases de conhecimento, chunking, embeddings, busca vetorial e permissões multi-cliente.

## Estrutura Migrada

O módulo RAG foi migrado para a seguinte estrutura:

```
renum-backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── logger.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── README.md
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── api.py
│   │   │   └── entities.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── knowledge_base_repository.py
│   │   │   ├── collection_repository.py
│   │   │   ├── document_repository.py
│   │   │   └── processing_job_repository.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── chunking_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── llm_integration_service.py
│   │   │   └── retrieval_service.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── agent_integration_sql.py
│   │   │   ├── db_init.py
│   │   │   └── sql_scripts.py
│   │   └── tests/
│   │       └── __init__.py
│   ├── __init__.py
│   └── main.py
```

## Principais Alterações

1. **Estrutura de Diretórios**: O módulo RAG foi movido do diretório `backend/knowledge_base/rag` para `renum-backend/app/rag`.

2. **Namespace**: As importações foram atualizadas para refletir a nova estrutura de diretórios, por exemplo:
   - De: `from knowledge_base.rag.services.retrieval_service import RetrievalService`
   - Para: `from app.rag.services.retrieval_service import RetrievalService`

3. **Dependências**: As dependências foram atualizadas para usar os módulos core da Plataforma Renum:
   - De: `from utils.auth_utils import get_current_user_id_from_jwt`
   - Para: `from app.core.auth import get_current_user_id`

4. **Endpoints**: Os endpoints foram atualizados para refletir a nova estrutura:
   - De: `/api/knowledge-base/agent-rag/query`
   - Para: `/api/rag/query`

5. **Configuração**: Foi criado um módulo de configuração específico para a Plataforma Renum.

6. **Banco de Dados**: Foi criado um módulo de banco de dados específico para a Plataforma Renum.

## Componentes Implementados

1. **Modelos**:
   - Modelos de entidades para bases de conhecimento, coleções, documentos e chunks
   - Modelos de API para requisições e respostas

2. **Repositórios**:
   - Repositório de bases de conhecimento
   - Repositório de coleções
   - Repositório de documentos
   - Repositório de jobs de processamento

3. **Serviços**:
   - Serviço de chunking para dividir documentos em fragmentos
   - Serviço de embedding para gerar embeddings para chunks
   - Serviço de ingestão para processar documentos de diferentes fontes
   - Serviço de recuperação para buscar chunks relevantes
   - Serviço de integração com LLMs para enriquecer prompts

4. **Utilitários**:
   - Scripts SQL para criar tabelas e funções no banco de dados
   - Funções SQL para integração com agentes
   - Inicialização do banco de dados

5. **API**:
   - Endpoints para integração com agentes

## Status da Implementação

### Concluído
- ✅ Estrutura de diretórios e arquivos
- ✅ Modelos de dados
- ✅ Repositórios para acesso a dados
- ✅ Serviços de processamento de documentos
- ✅ Serviços de recuperação e enriquecimento de prompts
- ✅ Endpoints de integração com agentes
- ✅ Scripts SQL para criação de tabelas e funções

### Em Andamento
- 🔄 Endpoints REST para CRUD completo
- 🔄 Integração com o Suna Core para enriquecimento de prompts
- 🔄 Interface de usuário para gestão de bases de conhecimento

## Próximos Passos

1. **Implementar Endpoints REST Adicionais**:
   - Endpoints para gerenciamento de bases de conhecimento
   - Endpoints para gerenciamento de coleções
   - Endpoints para gerenciamento de documentos

2. **Integração com Suna Core**:
   - Implementar a integração com o Suna Core para enriquecimento de prompts
   - Configurar a comunicação entre os sistemas

3. **Interface de Usuário**:
   - Desenvolver a interface de usuário para gerenciamento de bases de conhecimento
   - Implementar a visualização de documentos e chunks
   - Implementar a busca e recuperação de informações

## Conclusão

A migração do módulo RAG do Suna Core para a Plataforma Renum foi concluída com sucesso. A nova estrutura segue o plano de desenvolvimento aprovado, mantendo a separação de responsabilidades entre o Suna Core (execução) e a Plataforma Renum (orquestração). Os componentes principais foram implementados e estão prontos para uso, com alguns itens ainda em desenvolvimento.