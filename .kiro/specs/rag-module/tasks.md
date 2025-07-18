# Plano de Implementação do Módulo RAG

Este documento apresenta as tarefas de implementação para o módulo RAG (Retrieval-Augmented Generation) da Plataforma Renum, organizadas em uma sequência lógica e incremental.

## Tarefas de Implementação

- [-] 1. Configuração do ambiente e estrutura do projeto

  - [ ] 1.1 Criar estrutura de diretórios para o módulo RAG no backend
    - Criar diretórios para serviços, modelos, utilitários e testes
    - Configurar arquivos __init__.py para organização de módulos
    - _Requisitos: N/A_
  
  - [ ] 1.2 Configurar dependências e bibliotecas necessárias
    - Adicionar dependências ao pyproject.toml (PyPDF2, python-docx, BeautifulSoup, etc.)
    - Configurar ambiente virtual para desenvolvimento
    - _Requisitos: N/A_
  
  - [ ] 1.3 Configurar integração com Supabase para o módulo RAG
    - Criar cliente Supabase específico para o módulo RAG
    - Configurar acesso ao banco de dados vetorial do Supabase
    - _Requisitos: 6.1, 8.3_

- [ ] 2. Implementação do modelo de dados
  - [ ] 2.1 Criar esquemas e modelos Pydantic para as entidades do RAG
    - Implementar modelos para KnowledgeBase, Collection, Document, Chunk
    - Implementar modelos para requisições e respostas das APIs
    - _Requisitos: 1.1, 2.1, 3.1, 5.1_
  
  - [ ] 2.2 Criar tabelas no Supabase
    - Implementar script de migração para criar tabelas knowledge_bases, knowledge_collections, documents, document_chunks
    - Implementar script para tabelas document_versions, retrieval_feedback, document_usage_stats
    - Configurar Row Level Security (RLS) para isolamento de dados por cliente
    - _Requisitos: 3.1, 5.5, 8.1, 8.3_
  
  - [ ] 2.3 Implementar repositórios para acesso aos dados
    - Criar classes de repositório para cada entidade (KnowledgeBaseRepository, DocumentRepository, etc.)
    - Implementar métodos CRUD para cada repositório
    - Adicionar testes unitários para os repositórios
    - _Requisitos: 1.1, 2.1, 3.1, 5.1_

- [ ] 3. Implementação do serviço de ingestão de documentos
  - [ ] 3.1 Implementar processadores de documentos por formato
    - Criar processador para arquivos PDF usando PyPDF2
    - Criar processador para arquivos DOCX usando python-docx
    - Criar processador para arquivos de texto plano e Markdown
    - Implementar fábrica de processadores baseada no tipo de arquivo
    - _Requisitos: 1.2, 1.3_
  
  - [ ] 3.2 Implementar processador de URLs com Firecrawl
    - Criar cliente para a API do Firecrawl
    - Implementar extração e limpeza de conteúdo de páginas web
    - Adicionar tratamento de erros para URLs inacessíveis
    - _Requisitos: 2.1, 2.2, 2.3_
  
  - [ ] 3.3 Implementar serviço de chunking de texto
    - Criar algoritmo de chunking por tamanho fixo com sobreposição
    - Implementar chunking por parágrafos para preservar contexto
    - Adicionar metadados aos chunks (posição no documento, título da seção, etc.)
    - _Requisitos: 1.4, 1.5_
  
  - [ ] 3.4 Implementar sistema de processamento assíncrono
    - Criar fila de tarefas para processamento de documentos
    - Implementar workers para processar documentos em segundo plano
    - Adicionar sistema de notificação de conclusão de processamento
    - _Requisitos: 1.6, 2.5_

- [ ] 4. Implementação do serviço de embeddings
  - [ ] 4.1 Implementar cliente para modelo de embeddings
    - Criar wrapper para OpenAI Ada 2 (opção padrão)
    - Implementar alternativa com Sentence Transformers (opção self-hosted)
    - Criar fábrica de modelos de embedding baseada na configuração
    - _Requisitos: 1.5, 6.1_
  
  - [ ] 4.2 Implementar serviço de armazenamento de embeddings
    - Criar cliente para Supabase Vector
    - Implementar métodos para armazenar, atualizar e excluir embeddings
    - Adicionar índices para busca eficiente
    - _Requisitos: 1.5, 6.1, 6.2_
  
  - [ ] 4.3 Implementar gerenciamento do ciclo de vida dos embeddings
    - Criar métodos para atualizar embeddings quando documentos são modificados
    - Implementar versionamento de embeddings
    - Adicionar limpeza periódica de embeddings obsoletos
    - _Requisitos: 5.2, 5.3, 5.4_

- [ ] 5. Implementação do serviço de recuperação
  - [ ] 5.1 Implementar algoritmos de busca por similaridade
    - Criar função de busca por similaridade de cosseno
    - Implementar filtragem por metadados (coleção, tipo de documento, etc.)
    - Adicionar parâmetros de configuração (top_k, threshold de similaridade)
    - _Requisitos: 4.2, 6.2_
  
  - [ ] 5.2 Implementar sistema de caching
    - Criar cache para consultas frequentes
    - Implementar estratégia de invalidação de cache
    - Adicionar métricas de hit/miss do cache
    - _Requisitos: 6.3_
  
  - [ ] 5.3 Implementar rastreamento de uso de documentos
    - Criar sistema para registrar quais documentos são utilizados em cada consulta
    - Implementar atualização de estatísticas de uso
    - Adicionar endpoints para visualizar estatísticas de uso
    - _Requisitos: 7.2, 7.3, 7.4_

- [ ] 6. Implementação do serviço de integração com LLM
  - [ ] 6.1 Implementar formatação de prompts com contexto
    - Criar templates de prompts para diferentes modelos de LLM
    - Implementar lógica para incorporar chunks relevantes no prompt
    - Adicionar sistema de priorização de chunks por relevância
    - _Requisitos: 4.3, 4.6_
  
  - [ ] 6.2 Implementar processamento de respostas com fontes
    - Criar parser para extrair fontes utilizadas das respostas do LLM
    - Implementar formatação de respostas com citações
    - Adicionar metadados de fontes às respostas
    - _Requisitos: 4.4_
  
  - [ ] 6.3 Implementar integração com o Suna Core
    - Criar cliente para a API do Suna Core
    - Implementar middleware para enriquecer prompts antes de enviar ao Suna
    - Adicionar processamento de respostas do Suna
    - _Requisitos: 4.1, 4.3, 4.6_

- [ ] 7. Implementação das APIs REST
  - [ ] 7.1 Implementar endpoints para gerenciamento de bases de conhecimento
    - Criar endpoints CRUD para bases de conhecimento
    - Implementar endpoints para gerenciar coleções
    - Adicionar validação de entrada e tratamento de erros
    - _Requisitos: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 7.2 Implementar endpoints para upload e gerenciamento de documentos
    - Criar endpoint para upload de documentos
    - Implementar endpoints para adicionar URLs
    - Adicionar endpoints para editar, atualizar e excluir documentos
    - _Requisitos: 1.1, 2.1, 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 7.3 Implementar endpoints para consulta e feedback
    - Criar endpoint para consulta direta à base de conhecimento
    - Implementar endpoint para feedback de relevância
    - Adicionar endpoint para visualizar estatísticas de uso
    - _Requisitos: 4.1, 4.2, 7.1, 7.3_
  
  - [ ] 7.4 Implementar middleware de controle de acesso e limites
    - Criar middleware para verificar permissões de acesso
    - Implementar verificação de limites de uso por plano
    - Adicionar logging de acesso para auditoria
    - _Requisitos: 8.1, 8.2, 8.3_

- [ ] 8. Implementação da interface de usuário no frontend
  - [ ] 8.1 Implementar componentes para upload e gerenciamento de documentos
    - Criar componente de upload de arquivos com drag-and-drop
    - Implementar formulário para adicionar URLs
    - Adicionar visualização de progresso de processamento
    - _Requisitos: 1.1, 2.1, 5.1_
  
  - [ ] 8.2 Implementar interface de gerenciamento de coleções
    - Criar componentes para criar e editar coleções
    - Implementar visualização em árvore de coleções e documentos
    - Adicionar funcionalidade de arrastar e soltar para organizar documentos
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 8.3 Implementar visualização de documentos e histórico
    - Criar visualizador de documentos com highlighting
    - Implementar interface para visualizar e restaurar versões anteriores
    - Adicionar funcionalidade de edição inline
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 8.4 Implementar dashboard de métricas e uso
    - Criar visualizações gráficas de estatísticas de uso
    - Implementar tabelas de documentos mais utilizados
    - Adicionar filtros por período e tipo de documento
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 8.5 Implementar integração com a interface de chat
    - Criar componente para exibir fontes nas respostas do chat
    - Implementar botões de feedback de relevância
    - Adicionar opção para explorar documentos relacionados
    - _Requisitos: 4.3, 4.4, 4.5, 4.6_

- [ ] 9. Testes e otimização
  - [ ] 9.1 Implementar testes unitários abrangentes
    - Criar testes para cada componente do módulo RAG
    - Implementar mocks para serviços externos
    - Adicionar testes de casos de borda e tratamento de erros
    - _Requisitos: Todos_
  
  - [ ] 9.2 Implementar testes de integração
    - Criar testes end-to-end para fluxos completos
    - Implementar testes de integração com Supabase e Suna
    - Adicionar testes de performance para identificar gargalos
    - _Requisitos: Todos_
  
  - [ ] 9.3 Otimizar performance e escalabilidade
    - Identificar e resolver gargalos de performance
    - Implementar estratégias de caching adicionais
    - Otimizar consultas ao banco de dados
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 9.4 Implementar monitoramento e logging
    - Criar sistema de logging detalhado
    - Implementar métricas de performance e uso
    - Adicionar alertas para erros e degradação de performance
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 10. Documentação e implantação
  - [ ] 10.1 Criar documentação técnica
    - Documentar arquitetura e componentes
    - Implementar documentação de API com Swagger/OpenAPI
    - Adicionar guias de desenvolvimento e contribuição
    - _Requisitos: Todos_
  
  - [ ] 10.2 Criar documentação de usuário
    - Documentar fluxos de uso para usuários finais
    - Implementar tutoriais e exemplos
    - Adicionar FAQ e troubleshooting
    - _Requisitos: Todos_
  
  - [ ] 10.3 Preparar para implantação em produção
    - Criar scripts de migração de banco de dados
    - Implementar configuração para diferentes ambientes
    - Adicionar scripts de backup e recuperação
    - _Requisitos: Todos_