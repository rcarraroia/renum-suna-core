**Plataforma Renum: Projeto de Desenvolvimento Completo**

**Este documento apresenta um plano de projeto detalhado para a construção da Plataforma Renum, dividindo-o em fases estratégicas e especificando os componentes técnicos e as melhores práticas para o desenvolvimento, com foco na integração da Suna e na utilização de ferramentas de IA como o Kilocode.**

**1. Visão Geral do Projeto**

**A Plataforma Renum visa ser um Builder abrangente e uma Plataforma de Oferta de Agentes de IA Inteligentes para Diversos Fins. Ela permitirá que clientes criem e gerenciem seus próprios agentes de IA, enquanto internamente, agentes de IA especializados em programação (arquitetura, codificação, debug) acelerarão o desenvolvimento. A Suna by Kortix será o "cérebro" executor dos agentes, e a Plataforma Renum atuará como o orquestrador e a interface do usuário.**

**2. Ferramentas e Tecnologias Chave**

- **UI/UX Design: Lovable**
- **Frontend: Next.js (com React), Tailwind CSS**
- **Backend: Python (FastAPI)**
- **Banco de Dados: Supabase (PostgreSQL)**
- **Orquestração de Contêineres: Docker (para instâncias Suna)**
- **Ambiente de Desenvolvimento: VS Code com extensão Kilocode**
- **Modelos de IA para Desenvolvimento (Kilocode): Claude Sonnet 3.5 ou Gemini 1.5 Pro**

**3. Fase 1: Instalação e Configuração Inicial da Suna**

**Esta fase foca em estabelecer a base operacional da Suna, sem customizações iniciais, preparando-a para ser consumida como um serviço.**

**3.1. Objetivos**

- **Instalar e configurar uma instância funcional do sistema Suna original em um ambiente de servidor dedicado (VPS).**
- **Validar o funcionamento básico da Suna e suas APIs.**
- **Identificar os pontos de conexão iniciais para o futuro Backend da Plataforma Renum.**

**3.2. Tarefas Detalhadas**

1. **Provisionamento do Servidor:**
   1. **Contratar um servidor dedicado/VPS com as especificações mínimas recomendadas para rodar a Suna (CPU, RAM, armazenamento).**
   1. **Instalar um sistema operacional Linux (ex: Ubuntu Server).**
1. **Instalação do Docker e Docker Compose:**
   1. **Instalar o Docker Engine e o Docker Compose no servidor.**
   1. **Dica para AI (Kilocode):**
      1. **Prompt: "Forneça os comandos exatos para instalar Docker e Docker Compose em um servidor Ubuntu 22.04 LTS."**
1. **Clone do Repositório Suna:**
   1. **Clonar o repositório https://github.com/kortix-ai/suna.git para o servidor.**
1. **Configuração Inicial da Suna:**
   1. **Navegar para o diretório da Suna.**
   1. **Configurar as variáveis de ambiente necessárias para a Suna (Supabase URL, Supabase Anon Key, API Keys para LLMs como Anthropic/OpenAI/Google Gemini, Tavily, Firecrawl, etc.). Use variáveis de ambiente seguras.**
   1. **Dica para AI (Kilocode):**
      1. **Prompt: "Com base na documentação da Suna, liste as variáveis de ambiente essenciais para a configuração inicial do backend da Suna e seus valores de exemplo."**
1. **Execução da Suna:**
   1. **Executar a Suna usando Docker Compose.**
   1. **docker-compose up -d**
   1. **Dica para AI (Kilocode):**
      1. **Prompt: "Se a Suna não iniciar corretamente via Docker Compose, quais são os primeiros passos de depuração que devo seguir? Forneça comandos para verificar logs e status dos contêineres."**
1. **Verificação de Funcionalidade Básica:**
   1. **Acessar o frontend da Suna (se houver) para verificar se está online.**
   1. **Testar a criação e execução de um agente simples na Suna para garantir que o LLM e as ferramentas básicas (Tavily, Firecrawl) funcionem com as chaves de API da Renum.**
1. **Identificação de Endpoints da Suna:**
   1. **Documentar os endpoints da API da Suna que serão usados pelo Backend da Plataforma Renum para criar, executar e monitorar agentes.**

**3.3. Resultados Esperados**

- **Instância da Suna em execução e acessível.**
- **Conhecimento dos endpoints da Suna para integração futura.**
- **Ambiente pronto para a Fase 2.**

**4. Fase 2: Desenvolvimento Completo da Plataforma Renum**

**Esta fase é o core da construção do seu produto, onde a Plataforma Renum será desenvolvida como um sistema independente que orquestra a Suna e as ferramentas externas.**

**4.1. Objetivos**

- **Desenvolver o Frontend do Builder Renum (baseado na inspiração do Lovable).**
- **Construir o Backend da Plataforma Renum para gerenciar clientes, credenciais, orquestração de agentes Suna e proxy de ferramentas.**
- **Implementar a gestão de credenciais por cliente para ferramentas externas.**
- **Estabelecer a base para o futuro Agente Assistente de Criação.**

**4.2. Arquitetura de Alto Nível (Relembrando)**

**graph TD**

`    `**User[Usuário/Cliente Renum] <--> Frontend\_Renum[Frontend do Builder Renum (Next.js/React)]**

`    `**Frontend\_Renum <--> |REST API / WebSockets| Backend\_Renum[Backend da Plataforma Renum (Python/FastAPI)]**

`    `**subgraph Backend da Plataforma Renum**

`        `**DB\_Supabase(Supabase PostgreSQL)**

`        `**Auth\_Module(Módulo de Autenticação)**

`        `**Credential\_Manager(Gerenciador de Credenciais Seguras)**

`        `**Agent\_Orchestrator(Orquestrador de Agentes Suna)**

`        `**Tool\_Proxy\_Wrappers(Proxy/Wrappers de Ferramentas)**

`        `**Usage\_Tracker(Rastreador de Uso)**

`        `**Backend\_Renum --- DB\_Supabase**

`        `**Backend\_Renum --- Auth\_Module**

`        `**Backend\_Renum --- Credential\_Manager**

`        `**Backend\_Renum --- Agent\_Orchestrator**

`        `**Backend\_Renum --- Tool\_Proxy\_Wrappers**

`        `**Backend\_Renum --- Usage\_Tracker**

`        `**Agent\_Orchestrator --> |Docker API| Suna\_Instances[Instâncias de Agente Suna (Contêineres Docker)]**

`    `**end**

`    `**Suna\_Instances --> External\_Tools[Serviços Externos (Tavily, Firecrawl, WhatsApp, CRMs, etc.)]**

`    `**Suna\_Instances --> LLMs[Provedores de LLM (Anthropic, OpenAI, Google Gemini)]**

**4.3. Módulos e Componentes Principais**

**A. Frontend do Builder Renum (Next.js/React)**

- **UI/UX Design (Lovable):**
  - **Tarefa: Criar mockups e protótipos de alta fidelidade no Lovable para todas as telas identificadas: Dashboard, Builder de Agentes (criar/editar), Meus Projetos, Execuções e Testes (com detalhes de log em tempo real), Configurações (Perfil, APIs & Integrações, GitHub, Segurança, Notificações).**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Gere um wireframe detalhado para a tela 'APIs & Integrações' do dashboard Renum, mostrando campos para chaves de API de LLMs (OpenAI, Gemini, Anthropic) e uma seção para 'Outras Integrações' com opções de adicionar Tavily, Firecrawl e WhatsApp, incluindo um botão 'Testar Conexão' para cada."**
- **Desenvolvimento Frontend:**
  - **Configuração do Projeto: Inicializar projeto Next.js, configurar Tailwind CSS.**
  - **Autenticação/Autorização UI: Telas de login, registro, recuperação de senha.**
  - **Componentes Reutilizáveis: Desenvolver componentes React para inputs, botões, cards, tabelas, modais, etc., seguindo os designs do Lovable.**
  - **Navegação e Layout: Implementar a estrutura de navegação lateral e o layout geral do dashboard.**
  - **Páginas Principais:**
    - **Dashboard: Exibir métricas, feed de atividades, ações rápidas.**
    - **Builder de Agentes: Formulário de criação/edição de agentes com campos para nome, descrição, persona, diretrizes, e uma seção para seleção e configuração de ferramentas/credenciais.**
    - **Meus Projetos: Listagem e gerenciamento de projetos.**
    - **Execuções e Testes: Dashboard de execuções, histórico, e visualização de logs em tempo real (via WebSockets/SSE).**
    - **Configurações: Perfil do usuário, gerenciamento de API Keys (LLMs e Outras Ferramentas), integração GitHub, segurança, notificações.**
  - **Integração com Backend Renum: Utilizar Axios ou Fetch API para todas as comunicações REST.**
  - **Comunicação em Tempo Real: Implementar conexão WebSocket/SSE para receber logs de execução e atualizações de status do Backend da Renum.**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Crie um componente React (Next.js) para a seção 'Criação/Edição de Agente'. Inclua campos para 'Nome do Agente', 'Descrição', 'Persona', 'Diretrizes de Comportamento' e uma seção expansível para 'Ferramentas & Integrações'. Use Tailwind CSS para estilização e inclua validação de formulário."**
    - **Prompt: "Desenvolva um hook React personalizado para gerenciar o estado de um formulário com múltiplos campos, incluindo validação e submissão assíncrona."**

**B. Backend da Plataforma Renum (Python/FastAPI)**

- **Configuração do Projeto: Inicializar projeto FastAPI, configurar ambiente virtual, dependências.**
- **Conexão com Supabase (PostgreSQL):**
  - **Tarefa: Configurar a conexão com o banco de dados PostgreSQL do Supabase.**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Gere o código Python (FastAPI) para configurar a conexão com um banco de dados PostgreSQL no Supabase, incluindo exemplos de uso de um ORM como SQLAlchemy ou SQLModel."**
- **Módulo de Autenticação e Autorização:**
  - **Tarefa: Implementar registro de usuário, login (JWT), gerenciamento de sessões, e controle de acesso baseado em roles (cliente vs. interno).**
- **Módulo de Gerenciamento de Clientes/Usuários:**
  - **Tarefa: APIs para CRUD de usuários e perfis de clientes.**
  - **Esquema de DB (Supabase): Tabela users (id, email, password\_hash, role, etc.).**
- **Módulo de Gerenciamento de Credenciais Seguras:**
  - **Tarefa: Armazenar chaves de API de LLMs e outras ferramentas (Tavily, Firecrawl, WhatsApp, etc.) de forma criptografada no banco de dados, associadas a client\_id e tool\_type.**
  - **Criptografia: Utilizar bibliotecas de criptografia Python e planejar a integração com um KMS (Key Management Service) para chaves de criptografia.**
  - **APIs: Endpoints para o Frontend gerenciar essas credenciais.**
  - **Esquema de DB (Supabase): Tabela client\_credentials (id, client\_id, tool\_type, encrypted\_api\_key, created\_at, updated\_at).**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Crie um esquema de banco de dados PostgreSQL para armazenar credenciais de API de clientes. As credenciais devem ser criptografadas. Inclua campos para client\_id, tool\_type (ex: 'tavily', 'whatsapp'), encrypted\_api\_key e encryption\_metadata."**
    - **Prompt: "Gere um exemplo de função Python (FastAPI) para criptografar e descriptografar uma string usando AES-256, com uma chave de criptografia armazenada de forma segura (ex: variável de ambiente)."**
- **Módulo de Gerenciamento de Agentes:**
  - **Tarefa: APIs para criar, ler, atualizar e excluir metadados de agentes (nome, descrição, persona, diretrizes, LLM preferido, ferramentas habilitadas e suas credenciais associadas).**
  - **Esquema de DB (Supabase): Tabela agents (id, client\_id, name, description, persona, directives, llm\_config, enabled\_tools\_config, created\_at, updated\_at).**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Defina o modelo de dados em Python (usando Pydantic para FastAPI) para a criação de um agente, incluindo campos para nome, descrição, persona, e uma lista de ferramentas habilitadas, onde cada ferramenta pode ter uma credential\_id associada."**
- **Módulo de Orquestração de Agentes Suna:**
  - **Tarefa: Lógica para interagir com a API do Docker (ou Kubernetes, se escalar) para provisionar e desprovisionar instâncias Suna.**
  - **Configuração de Instâncias Suna: Injetar variáveis de ambiente nos contêineres Suna que apontam para os endpoints de proxy de ferramentas do Backend da Plataforma Renum (ex: TOOL\_TAVILY\_URL: "http://backend-renum:8000/api/client/{{client\_id}}/tools/tavily\_search").**
  - **APIs: Endpoints para iniciar/parar/reiniciar agentes.**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Gere um snippet de código Python usando o Docker SDK para iniciar um novo contêiner Docker da Suna, injetando variáveis de ambiente como TOOL\_TAVILY\_URL e LLM\_API\_KEY."**
- **Módulo de Proxy/Wrappers de Ferramentas:**
  - **Tarefa: Para cada ferramenta externa (Tavily, Firecrawl, WhatsApp, CRM, etc.), criar um endpoint de proxy no Backend da Renum.**
  - **Lógica:**
    - **Recebe a requisição da instância Suna (via client\_id no URL ou token).**
    - **Descriptografa a chave de API da ferramenta do cliente específico.**
    - **Faz a chamada real para a API externa usando essa chave.**
    - **Trata erros, rate limiting e retries.**
    - **Retorna a resposta para a Suna.**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Desenvolva um endpoint FastAPI POST /api/client/{client\_id}/tools/firecrawl\_scrape que recebe uma URL, recupera a chave Firecrawl do cliente do banco de dados (assumindo uma função get\_client\_api\_key(client\_id, 'firecrawl')), faz a requisição para a API Firecrawl e retorna a resposta. Inclua tratamento de erros para chaves inválidas ou falhas de rede."**
- **Módulo de Rastreamento de Uso e Faturamento:**
  - **Tarefa: Registrar cada chamada de ferramenta e uso de token de LLM (se o LLM for gerenciado pela Renum) por cliente e por agente.**
  - **Esquema de DB (Supabase): Tabela usage\_logs (id, client\_id, agent\_id, tool\_name, timestamp, tokens\_used, cost\_estimate, status).**
- **Módulo de Comunicação em Tempo Real (WebSockets/SSE):**
  - **Tarefa: Implementar endpoints WebSocket ou Server-Sent Events para transmitir logs de execução e status de agentes do Backend da Renum para o Frontend.**
  - **Dica para AI (Kilocode):**
    - **Prompt: "Gere um exemplo de endpoint WebSocket em FastAPI que possa receber logs de uma instância Suna e transmiti-los para um cliente frontend conectado."**

**C. Agentes de Programação Internos (Desenvolvimento Futuro)**

- **Tarefa: Utilizar o próprio Builder da Renum (com a interface interna) para criar e gerenciar os agentes de Arquitetura, Codificação e Debug.**
- **Ferramentas: Esses agentes terão acesso a APIs como GitHub, GitLab, ferramentas de CI/CD, e LLMs fine-tuned para código.**
- **Dica para AI (Kilocode):**
  - **Prompt: "Crie uma descrição de persona detalhada para um 'Agente de Codificação' que será usado internamente, focando em sua capacidade de gerar código Python, criar testes unitários e interagir com um sistema de arquivos."**

**4.4. Resultados Esperados**

- **Plataforma Renum completa, com frontend e backend operacionais.**
- **Gerenciamento seguro de clientes e credenciais.**
- **Capacidade de criar e orquestrar agentes Suna para clientes.**
- **Integração com ferramentas externas via proxy de credenciais do cliente.**
- **Base para o Agente Assistente de Criação e agentes de programação internos.**

**5. Melhores Práticas para Interação com Modelos de IA (Kilocode/Claude/Gemini)**

**Ao utilizar os modelos de IA via Kilocode para auxiliar no desenvolvimento, siga estas diretrizes para obter os melhores resultados:**

- **Clareza e Especificidade nos Prompts: Seja o mais claro e específico possível sobre o que você precisa. Evite ambiguidades.**
  - ***Ruim:* "Faça um código para o frontend."**
  - ***Bom:* "Gere um componente React funcional para o dashboard principal, usando Tailwind CSS para o layout de 3 colunas para métricas e uma seção de feed de atividades. Inclua placeholders para os dados."**
- **Contexto e Exemplos: Forneça contexto suficiente (linguagem, framework, bibliotecas, trechos de código existentes) e, se possível, exemplos do formato de saída desejado.**
  - **Prompt: "Com base no seguinte esquema de banco de dados PostgreSQL para agents [coloque o esquema aqui], gere o modelo de dados Pydantic correspondente para FastAPI."**
- **Iteração e Refinamento: Comece com um prompt mais amplo e refine-o em interações subsequentes. Peça por partes menores se a tarefa for muito complexa.**
  - **Prompt 1: "Crie a estrutura básica de um endpoint FastAPI para criar um agente."**
  - **Prompt 2: "Agora, adicione validação de entrada usando Pydantic e um exemplo de como interagir com o banco de dados Supabase para salvar o agente."**
- **Formato de Saída Desejado: Especifique o formato em que você quer a resposta (código Python, JSON, Markdown, etc.).**
  - **Prompt: "Retorne o código Python completo para o wrapper do Tavily, incluindo imports e tratamento de erros, em um bloco de código Markdown."**
- **Função de Agente de Programação: Lembre-se que o modelo de IA é seu assistente. Ele pode:**
  - **Gerar Código: Funções, classes, componentes, endpoints.**
  - **Refatorar: Melhorar a legibilidade, performance ou seguir padrões.**
  - **Depurar: Analisar erros e sugerir correções.**
  - **Projetar: Propor esquemas de banco de dados, estruturas de API.**
  - **Documentar: Gerar comentários, explicações para o código.**

**6. Considerações Finais**

- **Segurança: Priorize a segurança em todas as camadas, especialmente no gerenciamento de credenciais.**
- **Monitoramento e Observabilidade: Implemente desde o início um sistema robusto de logs e métricas para todas as partes da plataforma (frontend, backend, instâncias Suna, ferramentas externas).**
- **MLOps: Para o futuro, à medida que seus agentes internos de programação evoluem, pense em pipelines de MLOps para automatizar o treinamento, fine-tuning e deployment de novos modelos de IA.**
- **Iteração Contínua: Este é um projeto ambicioso. Divida-o em pequenas iterações, entregando valor incremental e coletando feedback para refinar o produto.**

**Este projeto detalhado deve servir como um guia sólido para a construção da Plataforma Renum. Boa sorte!**

