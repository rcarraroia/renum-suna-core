# Plano Estruturado para o Desenvolvimento da Plataforma Renum

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

- **Mono-repositório com Deploy Separado**:
  - Estrutura: `/suna-backend`, `/renum-backend`, `/renum-frontend`, `/renum-admin` (opcional), `/dock`
  - VPS atual: Exclusivo para Suna Core (já provisionada e funcional em 157.180.39.41)
  - Nova VPS: Para Backend e Frontend da Renum
  - Frontend da Renum: Deploy na Vercel
  - Banco de dados: Compartilhado no Supabase (multi-tenant)
  - Redis: Compartilhado ou isolado (via RedisCloud)
  - Comunicação entre sistemas: HTTP API + tokens + rotas privadas

### Separação de Responsabilidades

- **Suna Core**: 
  - Executor de agente (recebe prompt, raciocina, usa ferramentas)
  - Ambiente isolado em Docker
  - Agnóstico quanto ao cliente final ou credenciais específicas

- **Backend da Plataforma Renum**: 
  - Gerenciamento de usuários e clientes
  - Armazenamento seguro de credenciais de API de cada cliente
  - Orquestração do ciclo de vida das instâncias Suna
  - Rastreamento de uso e faturamento
  - APIs para o frontend do Builder
  - Proxy para chamadas de ferramentas externas
  - Módulo RAG para memória e contexto

- **Frontend do Builder Renum**: 
  - Interface para clientes criarem e gerenciarem agentes
  - Visualização de logs e execuções
  - Gerenciamento de credenciais e integrações
  - Interface para upload e gestão de bases de conhecimento (RAG)
  - Incorporação de todas as funcionalidades do frontend da Suna

- **Painel Administrativo Separado**: 
  - Interface dedicada para administradores
  - Gerenciamento de clientes e agentes globais
  - Configurações da plataforma
  - Monitoramento e métricas

## Plano de Desenvolvimento por Fases

### Fase 1: Fundação e MVP (Serviço Gerenciado)

**Objetivo Principal**: Estabelecer a base técnica e validar o modelo de negócio com os primeiros clientes através de um serviço gerenciado.

#### Componentes a Serem Criados:

1. **Integração com a Suna Core Existente**
   - Documentação dos endpoints da API da Suna já instalada na VPS
   - Desenvolvimento de cliente API para comunicação com a Suna
   - Testes de integração com a instância existente

2. **Módulo RAG (Retrieval-Augmented Generation)**
   - Implementação das tabelas no Supabase:
     - `conversation_history`
     - `knowledge_bases`
     - `document_chunks`
   - Integração com banco vetorial (Supabase Vector ou alternativa como Chroma)
   - Serviço de chunking, embedding e montagem de contexto personalizado
   - Integração com a execução dos agentes via Suna

3. **Backend da Plataforma Renum (Básico)**
   - Configuração do projeto FastAPI
   - Conexão com Supabase (PostgreSQL)
   - Módulo de autenticação e autorização
   - Módulo de gerenciamento de clientes/usuários
   - Módulo de gerenciamento de credenciais seguras (criptografado)
   - Módulo básico de orquestração de agentes Suna
   - Endpoints de proxy para ferramentas externas (Tavily, Firecrawl)
   - Validação das rotas de API para garantir consistência

4. **Frontend do Builder Renum (Básico)**
   - Configuração do projeto Next.js com Tailwind CSS
   - Telas de autenticação (login, registro)
   - Dashboard básico com métricas
   - Interface para visualização de agentes
   - Formulário para configuração de agentes
   - Interface para upload e gestão de bases de conhecimento (RAG)
   - Migração das funcionalidades essenciais do frontend da Suna

5. **Painel Administrativo Separado (Básico)**
   - Configuração do projeto Next.js separado
   - Autenticação para administradores
   - Dashboard para monitoramento de clientes e agentes
   - Interface para gerenciamento de usuários

#### Recursos e Tecnologias:
- Python/FastAPI para o backend
- Next.js/React/Tailwind para o frontend
- Supabase para banco de dados, autenticação e vetores
- Docker para orquestração de contêineres Suna
- Redis para cache
- LiteLLM para integração com LLMs (Anthropic, OpenAI, etc.)

#### Integrações:
- Supabase (banco de dados, autenticação e vetores)
- Suna Core (via API existente)
- LLMs (via LiteLLM)
- Tavily (pesquisa)
- Firecrawl (web scraping)

#### Automações e Testes:
- Testes unitários para componentes críticos
- Testes de integração para fluxos principais
- CI/CD básico para deploy contínuo
- Monitoramento básico de logs e erros

#### Entregáveis:
- Backend da Renum com funcionalidades básicas e módulo RAG
- Frontend do Builder com interface para gestão de agentes e bases de conhecimento
- Painel Administrativo básico
- Documentação de APIs e fluxos de trabalho
- Integração completa com a instância Suna existente

### Fase 2: Builder Assistido por IA

**Objetivo Principal**: Evoluir para um modelo onde os clientes têm mais autonomia, mas com forte suporte de IA.

#### Componentes a Serem Criados:

1. **Agente Assistente de Criação**
   - Desenvolvimento do agente especializado em guiar o cliente
   - Interface conversacional para criação de agentes
   - Lógica para recomendação de ferramentas e configurações
   - Integração com o backend para configuração automática

2. **Templates de Agentes**
   - Criação de templates pré-configurados para casos de uso comuns
   - Interface para seleção e personalização de templates
   - Sistema de versionamento de templates

3. **Backend da Plataforma Renum (Avançado)**
   - Módulo de rastreamento de uso e faturamento
   - Módulo de comunicação em tempo real (WebSockets/SSE)
   - Expansão dos wrappers de ferramentas externas
   - Melhorias na orquestração de agentes Suna
   - Aprimoramento do módulo RAG com recursos avançados

4. **Frontend do Builder Renum (Avançado)**
   - Interface completa para criação/edição de agentes
   - Visualização detalhada de logs e execuções
   - Gerenciamento de credenciais e integrações
   - Documentação e tutoriais integrados
   - Interface avançada para gestão de bases de conhecimento

5. **Agentes Internos de Desenvolvimento (Básico)**
   - Configuração inicial dos agentes de Arquitetura, Codificação e Debug
   - Interface administrativa para gerenciamento desses agentes
   - Integração com repositórios de código (GitHub/GitLab)

#### Recursos e Tecnologias:
- WebSockets/SSE para comunicação em tempo real
- Criptografia avançada para credenciais
- Integração com sistemas de versionamento de código
- Lovable para design de UI/UX

#### Integrações:
- Expansão para mais ferramentas externas (WhatsApp, CRMs, etc.)
- GitHub/GitLab para agentes de desenvolvimento
- Sistemas de monitoramento e observabilidade

#### Automações e Testes:
- Testes automatizados para UI
- Testes de carga para verificar escalabilidade
- Monitoramento avançado com alertas
- Backup automatizado de dados críticos

#### Entregáveis:
- Agente Assistente de Criação funcional
- Biblioteca de templates de agentes
- Backend com funcionalidades avançadas
- Frontend com interface completa
- Agentes internos de desenvolvimento em versão inicial
- Documentação expandida e tutoriais

### Fase 3: Plataforma Self-Service Completa

**Objetivo Principal**: Atingir escalabilidade máxima com uma plataforma onde os clientes têm autonomia completa.

#### Componentes a Serem Criados:

1. **Marketplace de Ferramentas e Integrações**
   - Interface para descoberta e ativação de ferramentas
   - Sistema de gerenciamento de credenciais para múltiplas ferramentas
   - Documentação detalhada para cada ferramenta

2. **Sistema de Compartilhamento de Templates**
   - Funcionalidade para clientes compartilharem templates
   - Sistema de avaliação e comentários
   - Curadoria de templates populares

3. **Backend da Plataforma Renum (Completo)**
   - Escalabilidade horizontal para suportar muitos clientes
   - Sistema avançado de faturamento e cobrança
   - APIs públicas para integrações de terceiros
   - Otimização de performance e recursos

4. **Frontend do Builder Renum (Completo)**
   - Interface totalmente self-service
   - Análises avançadas de uso e performance
   - Personalização avançada da experiência
   - Suporte a múltiplos idiomas

5. **Agentes Internos de Desenvolvimento (Avançado)**
   - Refinamento contínuo baseado em dados de uso
   - Capacidade de gerar código complexo e otimizado
   - Integração com sistemas de CI/CD
   - Automação de testes e depuração

#### Recursos e Tecnologias:
- Kubernetes para orquestração avançada de contêineres
- Sistemas de análise de dados para insights
- Infraestrutura escalável automaticamente
- Sistemas avançados de monitoramento e alerta

#### Integrações:
- RapidAPI para acesso a milhares de APIs externas
- Sistemas de pagamento e faturamento
- Plataformas de análise de dados
- Sistemas empresariais (ERP, CRM, etc.)

#### Automações e Testes:
- Testes A/B para otimização de UX
- Monitoramento preditivo para prevenção de problemas
- Escalabilidade automática baseada em demanda
- Análise contínua de segurança e vulnerabilidades

#### Entregáveis:
- Marketplace completo de ferramentas e integrações
- Sistema de compartilhamento de templates
- Backend com escalabilidade horizontal
- Frontend totalmente self-service
- Agentes internos de desenvolvimento avançados
- Documentação completa e recursos de aprendizado

## Módulo RAG (Retrieval-Augmented Generation)

### Visão Geral
O módulo RAG é um componente essencial da Plataforma Renum que permite aos agentes acessar e utilizar bases de conhecimento personalizadas. Este módulo enriquece as capacidades dos agentes, permitindo-lhes responder com base em documentos, links e outros materiais fornecidos pelos usuários.

### Componentes do Módulo RAG

1. **Armazenamento de Dados**:
   - Tabela `knowledge_bases`: Armazena metadados sobre as bases de conhecimento (nome, descrição, proprietário, etc.)
   - Tabela `document_chunks`: Armazena fragmentos de documentos processados
   - Tabela `conversation_history`: Armazena histórico de conversas para contexto
   - Banco vetorial: Armazena embeddings para recuperação semântica

2. **Processamento de Documentos**:
   - Serviço de chunking: Divide documentos em fragmentos gerenciáveis
   - Serviço de embedding: Converte fragmentos de texto em vetores
   - Indexação: Organiza vetores para recuperação eficiente

3. **Recuperação Contextual**:
   - Busca semântica: Encontra fragmentos relevantes com base na consulta
   - Montagem de contexto: Combina fragmentos recuperados em um contexto coerente
   - Injeção de contexto: Adiciona contexto relevante ao prompt do LLM

4. **Interface de Usuário**:
   - Upload de documentos: Interface para carregar arquivos, URLs e texto
   - Gerenciamento de bases de conhecimento: Criar, editar, excluir bases
   - Visualização de uso: Ver como as bases de conhecimento são utilizadas pelos agentes

### Fluxo de Trabalho RAG

1. **Criação da Base de Conhecimento**:
   - Usuário faz upload de documentos, URLs ou texto via frontend
   - Backend processa os documentos (chunking, embedding)
   - Vetores são armazenados no banco vetorial

2. **Execução do Agente com RAG**:
   - Usuário envia prompt ao agente
   - Backend recupera fragmentos relevantes da base de conhecimento
   - Contexto recuperado é adicionado ao prompt enviado ao LLM
   - Agente responde com base no conhecimento enriquecido

3. **Feedback e Refinamento**:
   - Usuário fornece feedback sobre a qualidade das respostas
   - Sistema ajusta parâmetros de recuperação com base no feedback
   - Base de conhecimento pode ser atualizada ou expandida

## Modelo de Versionamento e Controle de Qualidade

### Estratégia de Versionamento
1. **Mono-repositório com Git**:
   - Estrutura de pastas separadas para cada componente
   - Branches de feature para desenvolvimento isolado
   - Pull requests com revisão de código obrigatória
   - Versionamento semântico para releases

2. **CI/CD Pipeline**:
   - Testes automatizados em cada commit
   - Build e deploy automático para ambientes de desenvolvimento
   - Deploy manual para produção após aprovação
   - Rollback automatizado em caso de falhas

3. **Ambientes**:
   - Desenvolvimento: Para trabalho ativo
   - Staging: Para testes de integração
   - Produção: Para clientes reais

### Controle de Qualidade
1. **Testes Automatizados**:
   - Testes unitários para componentes isolados
   - Testes de integração para fluxos completos
   - Testes de UI para interfaces de usuário
   - Testes de carga para verificar escalabilidade

2. **Revisão de Código**:
   - Revisão por pares obrigatória
   - Análise estática de código
   - Verificação de segurança automatizada
   - Padrões de codificação consistentes

3. **Monitoramento**:
   - Logs centralizados com ELK Stack ou similar
   - Métricas de performance com Prometheus + Grafana
   - Rastreamento de erros com Sentry
   - Alertas para problemas críticos

## Treinamento e Utilização dos Agentes Internos

### Agente de Arquitetura
- **Fase 1**: Treinado com documentação de arquitetura de software, padrões de design e melhores práticas
- **Fase 2**: Refinado com feedback de projetos reais e exemplos de arquiteturas bem-sucedidas
- **Fase 3**: Otimizado para gerar arquiteturas completas e escaláveis automaticamente

### Agente de Codificação
- **Fase 1**: Treinado com exemplos de código Python/FastAPI e Next.js/React
- **Fase 2**: Refinado com base em revisões de código e padrões específicos do projeto
- **Fase 3**: Capaz de gerar componentes completos e otimizados com testes incluídos

### Agente de Debug
- **Fase 1**: Treinado com exemplos comuns de erros e soluções
- **Fase 2**: Refinado com logs reais de erros e soluções aplicadas
- **Fase 3**: Capaz de diagnosticar problemas complexos e sugerir correções precisas

### Utilização em Cada Fase
- **Fase 1**: Principalmente como assistentes para a equipe de desenvolvimento
- **Fase 2**: Participação ativa no desenvolvimento de novos componentes e templates
- **Fase 3**: Automação significativa do processo de desenvolvimento, com supervisão humana

## Fluxo de Trabalho da Plataforma

1. **Cliente (via Frontend do Builder Renum)**:
   - Cria/configura um agente
   - Insere suas próprias chaves de API (ex: Tavily, WhatsApp)
   - Faz upload de documentos para a base de conhecimento (RAG)
   - O Frontend envia essas informações para o Backend da Plataforma Renum

2. **Backend da Plataforma Renum**:
   - Armazena as chaves de API do cliente de forma segura e criptografada
   - Processa documentos para o módulo RAG (chunking, embedding)
   - Quando um agente é ativado, orquestra o lançamento de uma instância Suna
   - Configura a instância Suna para chamar endpoints proxy do Backend da Renum

3. **Suna Core (Agente)**:
   - Recebe o prompt do usuário
   - O Backend da Renum enriquece o prompt com contexto do RAG
   - O LLM raciocina e decide usar uma ferramenta
   - Envia a requisição da ferramenta para o Backend da Renum

4. **Backend da Plataforma Renum (Proxy)**:
   - Recebe a requisição da ferramenta da instância Suna
   - Identifica qual cliente e agente estão fazendo a requisição
   - Descriptografa a chave de API do cliente
   - Faz a chamada real para a API externa usando a chave do cliente
   - Rastreia o uso para fins de faturamento
   - Retorna a resposta para a instância Suna

5. **Suna Core (Agente)**:
   - Recebe a resposta da ferramenta
   - Continua seu processo de raciocínio e gera a resposta final

## Próximos Passos Imediatos

1. **Estrutura do Mono-repositório**:
   - Definir a estrutura de pastas e arquivos
   - Configurar .gitignore e outros arquivos de configuração

2. **Integração com a Suna Core Existente**:
   - Documentar os endpoints disponíveis na instância Suna já instalada
   - Desenvolver cliente API para comunicação com a Suna
   - Validar as rotas de API para garantir consistência

3. **Implementação do Módulo RAG**:
   - Criar as tabelas necessárias no Supabase
   - Implementar serviços de processamento de documentos
   - Desenvolver componentes de recuperação contextual

4. **Protótipo do Backend da Renum**:
   - Inicializar projeto FastAPI
   - Implementar módulos básicos (autenticação, gerenciamento de clientes)
   - Desenvolver endpoints de proxy para ferramentas externas

5. **Protótipo do Frontend do Builder**:
   - Inicializar projeto Next.js
   - Implementar componentes básicos (dashboard, formulário de agente)
   - Desenvolver interface para upload e gestão de bases de conhecimento

6. **Plano Detalhado de Implementação da Fase 1**:
   - Definir cronograma
   - Alocar recursos
   - Estabelecer marcos e entregáveis

---

Este plano estruturado foi atualizado com base nas novas informações fornecidas pela equipe Renum, incluindo a incorporação do módulo RAG, a integração com a instância Suna já existente, e a descontinuação do frontend da Suna em favor do frontend da Renum.