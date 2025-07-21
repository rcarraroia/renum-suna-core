# Plano Estruturado para o Desenvolvimento da Plataforma Renum (Atualizado)

## Sumário Executivo

A Plataforma Renum é um sistema de criação e orquestração de agentes de IA personalizados que utiliza o Suna como "cérebro executor" dos agentes. Este documento apresenta um plano estruturado para o desenvolvimento completo da plataforma, dividido em fases estratégicas alinhadas com o modelo de negócio híbrido e faseado.

## Principais Objetivos do Projeto

1. Criar uma plataforma de construção e orquestração de agentes de IA personalizados (Builder)
2. Utilizar o Suna como "cérebro executor" dos agentes, enquanto a Plataforma Renum atua como orquestradora
3. Implementar uma estratégia híbrida e faseada de negócio (serviço gerenciado → builder assistido → self-service)
4. Desenvolver agentes internos especializados em programação (arquitetura, codificação e debug)
5. Garantir segurança e isolamento de dados por cliente através de uma arquitetura robusta
6. Oferecer uma experiência de usuário intuitiva para criação e gerenciamento de agentes
7. Implementar um sistema de memória e contexto (RAG) para enriquecer as capacidades dos agentes

## Arquitetura Técnica

### Estrutura de Repositório e Deploy

- **Mono-repositório com Deploy Separado**: ✅
  - Estrutura: `/backend`, `/renum-backend`, `/Suna frontend`, `/renum-admin` (opcional), `/dock` ✅
  - VPS atual: Exclusivo para Suna Core (já provisionada e funcional em 157.180.39.41) ✅
  - Nova VPS: Para Backend e Frontend da Renum 🔄
  - Frontend da Renum: Deploy na Vercel 🔄
  - Banco de dados: Compartilhado no Supabase (multi-tenant) ✅
  - Redis: Compartilhado ou isolado (via RedisCloud) 🔄
  - Comunicação entre sistemas: HTTP API + tokens + rotas privadas 🔄

### Separação de Responsabilidades

- **Suna Core**: ✅
  - Executor de agente (recebe prompt, raciocina, usa ferramentas) ✅
  - Ambiente isolado em Docker ✅
  - Agnóstico quanto ao cliente final ou credenciais específicas ✅

- **Backend da Plataforma Renum**: 🔄
  - Gerenciamento de usuários e clientes 🔄
  - Armazenamento seguro de credenciais de API de cada cliente 🔄
  - Orquestração do ciclo de vida das instâncias Suna 🔄
  - Rastreamento de uso e faturamento 🔄
  - APIs para o frontend do Builder 🔄
  - Proxy para chamadas de ferramentas externas 🔄
  - Módulo RAG para memória e contexto ✅

- **Frontend do Builder Renum**: 🔄
  - Interface para clientes criarem e gerenciarem agentes 🔄
  - Visualização de logs e execuções 🔄
  - Gerenciamento de credenciais e integrações 🔄
  - Interface para upload e gestão de bases de conhecimento (RAG) 🔄
  - Incorporação de todas as funcionalidades do frontend da Suna 🔄

- **Painel Administrativo Separado**: 🔄
  - Interface dedicada para administradores 🔄
  - Gerenciamento de clientes e agentes globais 🔄
  - Configurações da plataforma 🔄
  - Monitoramento e métricas 🔄

## Plano de Desenvolvimento por Fases

### Fase 1: Fundação e MVP (Serviço Gerenciado)

**Objetivo Principal**: Estabelecer a base técnica e validar o modelo de negócio com os primeiros clientes através de um serviço gerenciado.

#### Componentes a Serem Criados:

1. **Integração com a Suna Core Existente** 🔄
   - Documentação dos endpoints da API da Suna já instalada na VPS 🔄
   - Desenvolvimento de cliente API para comunicação com a Suna 🔄
   - Testes de integração com a instância existente 🔄

2. **Módulo RAG (Retrieval-Augmented Generation)** ✅
   - Implementação das tabelas no Supabase: ✅
     - `knowledge_bases` ✅
     - `knowledge_collections` ✅
     - `documents` ✅
     - `document_chunks` ✅
     - `document_versions` ✅
     - `document_usage_stats` ✅
     - `retrieval_feedback` ✅
     - `processing_jobs` ✅
   - Integração com banco vetorial (Supabase Vector) ✅
   - Serviço de chunking, embedding e montagem de contexto personalizado ✅
   - Endpoints REST para CRUD completo ✅
   - Integração com a execução dos agentes via Suna ✅

3. **Backend da Plataforma Renum (Básico)** 🔄
   - Configuração do projeto FastAPI ✅
   - Conexão com Supabase (PostgreSQL) ✅
   - Cliente Supabase centralizado com retry e SSL ✅
   - Configuração SSL e opções de conexão segura ✅
   - Módulo de autenticação e autorização 🔄
     - Integração com Supabase Auth 🔄
     - Gerenciamento de usuários 🔄
     - Gerenciamento de sessões 🔄
   - Módulo de gerenciamento de clientes/usuários 🔄
   - Módulo de gerenciamento de credenciais seguras (criptografado) 🔄
   - Módulo básico de orquestração de agentes Suna 🔄
   - Endpoints de proxy para ferramentas externas (Tavily, Firecrawl) ✅
   - Validação das rotas de API para garantir consistência 🔄

4. **Frontend do Builder Renum (Básico)** 🔄
   - Configuração do projeto Next.js com Tailwind CSS 🔄
   - Telas de autenticação (login, registro) 🔄
   - Dashboard básico com métricas 🔄
   - Interface para visualização de agentes 🔄
   - Formulário para configuração de agentes 🔄
   - Interface para upload e gestão de bases de conhecimento (RAG) 🔄
   - Migração das funcionalidades essenciais do frontend da Suna 🔄

5. **Painel Administrativo Separado (Básico)** 🔄
   - Configuração do projeto Next.js separado 🔄
   - Autenticação para administradores 🔄
   - Dashboard para monitoramento de clientes e agentes 🔄
   - Interface para gerenciamento de usuários 🔄

#### Recursos e Tecnologias:
- Python/FastAPI para o backend ✅
- Next.js/React/Tailwind para o frontend 🔄
- Supabase para banco de dados, autenticação e vetores ✅
- Docker para orquestração de contêineres Suna ✅
- Redis para cache 🔄
- LiteLLM para integração com LLMs (Anthropic, OpenAI, etc.) 🔄

#### Integrações:
- Supabase (banco de dados, autenticação e vetores) ✅
- Suna Core (via API existente) 🔄
- LLMs (via LiteLLM) 🔄
- Tavily (pesquisa) 🔄
- Firecrawl (web scraping) ✅

#### Automações e Testes:
- Testes unitários para componentes críticos 🔄
- Testes de integração para fluxos principais 🔄
- CI/CD básico para deploy contínuo 🔄
- Monitoramento básico de logs e erros 🔄

#### Entregáveis:
- Backend da Renum com funcionalidades básicas e módulo RAG 🔄
- Frontend do Builder com interface para gestão de agentes e bases de conhecimento 🔄
- Painel Administrativo básico 🔄
- Documentação de APIs e fluxos de trabalho 🔄
- Integração completa com a instância Suna existente 🔄

### Fase 2: Builder Assistido por IA

**Objetivo Principal**: Evoluir para um modelo onde os clientes têm mais autonomia, mas com forte suporte de IA.

#### Componentes a Serem Criados:

1. **Agente Assistente de Criação** 🔄
   - Desenvolvimento do agente especializado em guiar o cliente 🔄
   - Interface conversacional para criação de agentes 🔄
   - Lógica para recomendação de ferramentas e configurações 🔄
   - Integração com o backend para configuração automática 🔄

2. **Templates de Agentes** 🔄
   - Criação de templates pré-configurados para casos de uso comuns 🔄
   - Interface para seleção e personalização de templates 🔄
   - Sistema de versionamento de templates 🔄

3. **Backend da Plataforma Renum (Avançado)** 🔄
   - Módulo de rastreamento de uso e faturamento 🔄
   - Módulo de comunicação em tempo real (WebSockets/SSE) 🔄
   - Expansão dos wrappers de ferramentas externas 🔄
   - Melhorias na orquestração de agentes Suna 🔄
   - Aprimoramento do módulo RAG com recursos avançados 🔄

4. **Frontend do Builder Renum (Avançado)** 🔄
   - Interface completa para criação/edição de agentes 🔄
   - Visualização detalhada de logs e execuções 🔄
   - Gerenciamento de credenciais e integrações 🔄
   - Documentação e tutoriais integrados 🔄
   - Interface avançada para gestão de bases de conhecimento 🔄

5. **Agentes Internos de Desenvolvimento (Básico)** 🔄
   - Configuração inicial dos agentes de Arquitetura, Codificação e Debug 🔄
   - Interface administrativa para gerenciamento desses agentes 🔄
   - Integração com repositórios de código (GitHub/GitLab) 🔄

### Fase 3: Plataforma Self-Service Completa

**Objetivo Principal**: Atingir escalabilidade máxima com uma plataforma onde os clientes têm autonomia completa.

#### Componentes a Serem Criados:

1. **Marketplace de Ferramentas e Integrações** 🔄
   - Interface para descoberta e ativação de ferramentas 🔄
   - Sistema de gerenciamento de credenciais para múltiplas ferramentas 🔄
   - Documentação detalhada para cada ferramenta 🔄

2. **Sistema de Compartilhamento de Templates** 🔄
   - Funcionalidade para clientes compartilharem templates 🔄
   - Sistema de avaliação e comentários 🔄
   - Curadoria de templates populares 🔄

3. **Backend da Plataforma Renum (Completo)** 🔄
   - Escalabilidade horizontal para suportar muitos clientes 🔄
   - Sistema avançado de faturamento e cobrança 🔄
   - APIs públicas para integrações de terceiros 🔄
   - Otimização de performance e recursos 🔄

4. **Frontend do Builder Renum (Completo)** 🔄
   - Interface totalmente self-service 🔄
   - Análises avançadas de uso e performance 🔄
   - Personalização avançada da experiência 🔄
   - Suporte a múltiplos idiomas 🔄

5. **Agentes Internos de Desenvolvimento (Avançado)** 🔄
   - Refinamento contínuo baseado em dados de uso 🔄
   - Capacidade de gerar código complexo e otimizado 🔄
   - Integração com sistemas de CI/CD 🔄
   - Automação de testes e depuração 🔄

## Módulo RAG (Retrieval-Augmented Generation)

### Visão Geral
O módulo RAG é um componente essencial da Plataforma Renum que permite aos agentes acessar e utilizar bases de conhecimento personalizadas. Este módulo enriquece as capacidades dos agentes, permitindo-lhes responder com base em documentos, links e outros materiais fornecidos pelos usuários.

### Componentes do Módulo RAG

1. **Armazenamento de Dados**: ✅
   - Tabela `knowledge_bases`: Armazena metadados sobre as bases de conhecimento ✅
   - Tabela `knowledge_collections`: Armazena coleções dentro das bases de conhecimento ✅
   - Tabela `documents`: Armazena metadados dos documentos ✅
   - Tabela `document_chunks`: Armazena fragmentos de documentos processados ✅
   - Tabela `document_versions`: Armazena histórico de versões de documentos ✅
   - Tabela `document_usage_stats`: Armazena estatísticas de uso ✅
   - Tabela `retrieval_feedback`: Armazena feedback sobre relevância ✅
   - Tabela `processing_jobs`: Armazena jobs de processamento ✅
   - Banco vetorial: Armazena embeddings para recuperação semântica ✅

2. **Processamento de Documentos**: ✅
   - Serviço de chunking: Divide documentos em fragmentos gerenciáveis ✅
   - Serviço de embedding: Converte fragmentos de texto em vetores ✅
   - Serviço de ingestão: Processa documentos de diferentes fontes ✅
   - Indexação: Organiza vetores para recuperação eficiente ✅

3. **Recuperação Contextual**: ✅
   - Busca semântica: Encontra fragmentos relevantes com base na consulta ✅
   - Montagem de contexto: Combina fragmentos recuperados em um contexto coerente ✅
   - Injeção de contexto: Adiciona contexto relevante ao prompt do LLM ✅

4. **Interface de Usuário**: 🔄
   - Upload de documentos: Interface para carregar arquivos, URLs e texto 🔄
   - Gerenciamento de bases de conhecimento: Criar, editar, excluir bases 🔄
   - Visualização de uso: Ver como as bases de conhecimento são utilizadas pelos agentes 🔄

### Próximos Passos do Módulo RAG

1. **Implementar Endpoints REST Adicionais**: ✅
   - Endpoints para gerenciamento de bases de conhecimento ✅
   - Endpoints para gerenciamento de coleções ✅
   - Endpoints para gerenciamento de documentos ✅

2. **Integração com Suna Core**: ✅
   - Implementar a integração com o Suna Core para enriquecimento de prompts ✅
   - Configurar a comunicação entre os sistemas ✅

3. **Interface de Usuário**: 🔄
   - Desenvolver a interface de usuário para gerenciamento de bases de conhecimento 🔄
   - Implementar a visualização de documentos e chunks 🔄
   - Implementar a busca e recuperação de informações 🔄

## Fluxo de Trabalho da Plataforma

1. **Cliente (via Frontend do Builder Renum)**: 🔄
   - Cria/configura um agente 🔄
   - Insere suas próprias chaves de API (ex: Tavily, WhatsApp) 🔄
   - Faz upload de documentos para a base de conhecimento (RAG) 🔄
   - O Frontend envia essas informações para o Backend da Plataforma Renum 🔄

2. **Backend da Plataforma Renum**: 🔄
   - Armazena as chaves de API do cliente de forma segura e criptografada 🔄
   - Processa documentos para o módulo RAG (chunking, embedding) ✅
   - Quando um agente é ativado, orquestra o lançamento de uma instância Suna 🔄
   - Configura a instância Suna para chamar endpoints proxy do Backend da Renum 🔄

3. **Suna Core (Agente)**: 🔄
   - Recebe o prompt do usuário ✅
   - O Backend da Renum enriquece o prompt com contexto do RAG 🔄
   - O LLM raciocina e decide usar uma ferramenta ✅
   - Envia a requisição da ferramenta para o Backend da Renum 🔄

4. **Backend da Plataforma Renum (Proxy)**: 🔄
   - Recebe a requisição da ferramenta da instância Suna 🔄
   - Identifica qual cliente e agente estão fazendo a requisição 🔄
   - Descriptografa a chave de API do cliente 🔄
   - Faz a chamada real para a API externa usando a chave do cliente 🔄
   - Rastreia o uso para fins de faturamento 🔄
   - Retorna a resposta para a instância Suna 🔄

5. **Suna Core (Agente)**: ✅
   - Recebe a resposta da ferramenta ✅
   - Continua seu processo de raciocínio e gera a resposta final ✅

## Próximos Passos Imediatos

1. **Estrutura do Mono-repositório**: ✅
   - Definir a estrutura de pastas e arquivos ✅
   - Configurar .gitignore e outros arquivos de configuração ✅

2. **Integração com a Suna Core Existente**: 🔄
   - Documentar os endpoints disponíveis na instância Suna já instalada 🔄
   - Desenvolver cliente API para comunicação com a Suna 🔄
   - Validar as rotas de API para garantir consistência 🔄

3. **Implementação do Módulo RAG**: ✅
   - Criar as tabelas necessárias no Supabase ✅
   - Implementar serviços de processamento de documentos ✅
   - Desenvolver componentes de recuperação contextual ✅
   - Implementar sistema de rastreamento de uso ✅
   - Implementar endpoints REST para CRUD completo ✅
   - Integrar com o Suna Core para enriquecimento de prompts ✅

4. **Protótipo do Backend da Renum**: 🔄
   - Inicializar projeto FastAPI ✅
   - Implementar cliente Supabase centralizado com retry e SSL ✅
   - Implementar camada de acesso a dados ✅
     - Criar interfaces base de repositório ✅
     - Implementar pool de conexões para PostgreSQL ✅
     - Implementar repositórios base para entidades principais ✅
   - Implementar módulo RAG ✅
     - Criar funções SQL para operações vetoriais ✅
     - Implementar serviço de embeddings ✅
     - Implementar serviço de busca semântica ✅
   - Módulo de autenticação e autorização ✅
     - Integração com Supabase Auth ✅
     - Gerenciamento de usuários ✅
     - Gerenciamento de sessões ✅
   - Sistema de gerenciamento de credenciais seguras ✅
     - Criptografia de dados sensíveis ✅
     - Armazenamento seguro de chaves de API ✅
     - Gerenciamento de ciclo de vida de credenciais ✅
   - Sistema de gerenciamento de agentes ✅
     - Modelos de dados para agentes e execuções ✅
     - Repositórios para agentes e execuções ✅
     - Serviço de gerenciamento de agentes ✅
     - API REST para gerenciamento de agentes ✅
   - Desenvolver endpoints de proxy para ferramentas externas ✅

5. **Protótipo do Frontend do Builder**: 🔄
   - Inicializar projeto Next.js 🔄
   - Implementar componentes básicos (dashboard, formulário de agente) 🔄
   - Desenvolver interface para upload e gestão de bases de conhecimento 🔄

6. **Plano Detalhado de Implementação da Fase 1**: ✅
   - Definir cronograma ✅
   - Alocar recursos ✅
   - Estabelecer marcos e entregáveis ✅
   - Documentação de requisitos e design para integração Supabase-Renum ✅

---

Este plano estruturado foi atualizado para refletir o progresso atual do desenvolvimento da Plataforma Renum, com foco especial no módulo RAG que já foi implementado com sucesso.