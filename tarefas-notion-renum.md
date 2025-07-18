# Tarefas do Projeto Renum para o Notion

## Fase 1: Fundação e MVP (Serviço Gerenciado)

### Módulo RAG - Backend

#### Estrutura e Configuração
- [x] Criar estrutura de diretórios para o módulo RAG
- [x] Configurar conexão com banco de dados
- [x] Implementar sistema de logging

#### Modelos e Repositórios
- [x] Implementar modelos de entidades (KnowledgeBase, Collection, Document, etc.)
- [x] Implementar modelos de API (requests e responses)
- [x] Implementar KnowledgeBaseRepository
- [x] Implementar CollectionRepository
- [x] Implementar DocumentRepository
- [x] Implementar ProcessingJobRepository

#### Serviços
- [x] Implementar ChunkingService
- [x] Implementar EmbeddingService
- [x] Implementar IngestionService
- [x] Implementar RetrievalService
- [x] Implementar LLMIntegrationService

#### Endpoints de Integração
- [x] Implementar endpoint /api/rag/query para enriquecimento de prompts
- [x] Implementar endpoint /api/rag/feedback para feedback de relevância

#### Endpoints REST para CRUD
- [x] Implementar endpoint GET /api/rag/bases para listar bases de conhecimento
- [x] Implementar endpoint POST /api/rag/bases para criar base de conhecimento
- [x] Implementar endpoint GET /api/rag/bases/{id} para obter detalhes de uma base
- [x] Implementar endpoint PUT /api/rag/bases/{id} para atualizar base de conhecimento
- [x] Implementar endpoint DELETE /api/rag/bases/{id} para excluir base de conhecimento
- [x] Implementar endpoint GET /api/rag/bases/{id}/collections para listar coleções
- [x] Implementar endpoint POST /api/rag/collections para criar coleção
- [x] Implementar endpoint GET /api/rag/collections/{id} para obter detalhes de uma coleção
- [x] Implementar endpoint PUT /api/rag/collections/{id} para atualizar coleção
- [x] Implementar endpoint DELETE /api/rag/collections/{id} para excluir coleção
- [x] Implementar endpoint GET /api/rag/collections/{id}/documents para listar documentos
- [x] Implementar endpoint POST /api/rag/documents/file para upload de arquivo
- [x] Implementar endpoint POST /api/rag/documents/url para adicionar URL
- [x] Implementar endpoint POST /api/rag/documents/text para adicionar texto
- [x] Implementar endpoint GET /api/rag/documents/{id} para obter detalhes de um documento
- [x] Implementar endpoint DELETE /api/rag/documents/{id} para excluir documento
- [x] Implementar endpoint GET /api/rag/documents/{id}/chunks para listar chunks
- [x] Implementar endpoint GET /api/rag/jobs/{id} para verificar status de processamento

#### Banco de Dados
- [ ] Criar tabelas do módulo RAG no Supabase
- [ ] Configurar extensão de vetores no Supabase
- [ ] Implementar funções SQL para consultas e operações

#### Testes
- [x] Criar testes unitários para endpoints de bases de conhecimento
- [x] Criar testes unitários para endpoints de coleções
- [ ] Criar testes unitários para endpoints de documentos
- [ ] Criar testes de integração para o módulo RAG

### Integração Suna Core - RAG

- [ ] Desenvolver cliente para comunicação entre Suna Core e Renum Backend
- [ ] Implementar endpoint para enriquecimento de prompts no Suna Core
- [ ] Configurar autenticação entre Suna Core e Renum Backend
- [ ] Implementar cache de consultas frequentes para otimização
- [ ] Criar testes de integração entre Suna Core e Renum Backend

### Módulo RAG - Frontend

- [ ] Criar página de listagem de bases de conhecimento
- [ ] Criar formulário de criação/edição de base de conhecimento
- [ ] Criar página de detalhes de base de conhecimento
- [ ] Criar página de listagem de coleções
- [ ] Criar formulário de criação/edição de coleção
- [ ] Criar página de detalhes de coleção
- [ ] Criar página de listagem de documentos
- [ ] Criar componente de upload de arquivos
- [ ] Criar componente de adição de URL
- [ ] Criar componente de adição de texto
- [ ] Criar página de detalhes de documento
- [ ] Criar visualizador de chunks
- [ ] Implementar busca e filtragem de documentos
- [ ] Criar indicadores de progresso para processamento de documentos
- [ ] Implementar feedback visual para ações do usuário

### Backend da Plataforma Renum (Básico)

- [x] Configuração do projeto FastAPI
- [x] Conexão com Supabase (PostgreSQL)
- [ ] Módulo de autenticação e autorização
- [ ] Módulo de gerenciamento de clientes/usuários
- [ ] Módulo de gerenciamento de credenciais seguras (criptografado)
- [ ] Módulo básico de orquestração de agentes Suna
- [ ] Endpoints de proxy para ferramentas externas (Tavily, Firecrawl)
- [ ] Validação das rotas de API para garantir consistência

### Frontend do Builder Renum (Básico)

- [ ] Configuração do projeto Next.js com Tailwind CSS
- [ ] Telas de autenticação (login, registro)
- [ ] Dashboard básico com métricas
- [ ] Interface para visualização de agentes
- [ ] Formulário para configuração de agentes
- [ ] Interface para upload e gestão de bases de conhecimento (RAG)
- [ ] Migração das funcionalidades essenciais do frontend da Suna

### Painel Administrativo Separado (Básico)

- [ ] Configuração do projeto Next.js separado
- [ ] Autenticação para administradores
- [ ] Dashboard para monitoramento de clientes e agentes
- [ ] Interface para gerenciamento de usuários

### Infraestrutura e DevOps

- [ ] Configurar VPS para Backend e Frontend da Renum
- [ ] Configurar deploy na Vercel para o Frontend
- [ ] Configurar Redis para cache
- [ ] Implementar CI/CD básico para deploy contínuo
- [ ] Configurar monitoramento básico de logs e erros

## Fase 2: Builder Assistido por IA

### Agente Assistente de Criação

- [ ] Desenvolvimento do agente especializado em guiar o cliente
- [ ] Interface conversacional para criação de agentes
- [ ] Lógica para recomendação de ferramentas e configurações
- [ ] Integração com o backend para configuração automática

### Templates de Agentes

- [ ] Criação de templates pré-configurados para casos de uso comuns
- [ ] Interface para seleção e personalização de templates
- [ ] Sistema de versionamento de templates

### Backend da Plataforma Renum (Avançado)

- [ ] Módulo de rastreamento de uso e faturamento
- [ ] Módulo de comunicação em tempo real (WebSockets/SSE)
- [ ] Expansão dos wrappers de ferramentas externas
- [ ] Melhorias na orquestração de agentes Suna
- [ ] Aprimoramento do módulo RAG com recursos avançados

### Frontend do Builder Renum (Avançado)

- [ ] Interface completa para criação/edição de agentes
- [ ] Visualização detalhada de logs e execuções
- [ ] Gerenciamento de credenciais e integrações
- [ ] Documentação e tutoriais integrados
- [ ] Interface avançada para gestão de bases de conhecimento

### Agentes Internos de Desenvolvimento (Básico)

- [ ] Configuração inicial dos agentes de Arquitetura, Codificação e Debug
- [ ] Interface administrativa para gerenciamento desses agentes
- [ ] Integração com repositórios de código (GitHub/GitLab)

## Fase 3: Plataforma Self-Service Completa

### Marketplace de Ferramentas e Integrações

- [ ] Interface para descoberta e ativação de ferramentas
- [ ] Sistema de gerenciamento de credenciais para múltiplas ferramentas
- [ ] Documentação detalhada para cada ferramenta

### Sistema de Compartilhamento de Templates

- [ ] Funcionalidade para clientes compartilharem templates
- [ ] Sistema de avaliação e comentários
- [ ] Curadoria de templates populares

### Backend da Plataforma Renum (Completo)

- [ ] Escalabilidade horizontal para suportar muitos clientes
- [ ] Sistema avançado de faturamento e cobrança
- [ ] APIs públicas para integrações de terceiros
- [ ] Otimização de performance e recursos

### Frontend do Builder Renum (Completo)

- [ ] Interface totalmente self-service
- [ ] Análises avançadas de uso e performance
- [ ] Personalização avançada da experiência
- [ ] Suporte a múltiplos idiomas

### Agentes Internos de Desenvolvimento (Avançado)

- [ ] Refinamento contínuo baseado em dados de uso
- [ ] Capacidade de gerar código complexo e otimizado
- [ ] Integração com sistemas de CI/CD
- [ ] Automação de testes e depuração