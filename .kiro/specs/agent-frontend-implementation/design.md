# Design Document

## Visão Geral

Este documento descreve o design para a implementação do frontend de criação e teste de agentes na plataforma Renum. A implementação será baseada em Next.js com React, utilizando TailwindCSS para estilização e integrando-se com o backend através de APIs RESTful.

## Arquitetura

A implementação seguirá uma arquitetura de componentes React com gerenciamento de estado local e global, utilizando o padrão de páginas do Next.js. A comunicação com o backend será feita através de chamadas HTTP para as APIs implementadas no backend Renum, que por sua vez se integra com o Suna Core.

### Fluxo de Dados

1. **Autenticação**: O usuário se autentica na plataforma, recebendo um token JWT.
2. **Criação de Agentes**: O usuário preenche o formulário de criação de agente, que é enviado para a API de criação de agentes.
3. **Listagem de Agentes**: O frontend solicita a lista de agentes do usuário autenticado.
4. **Execução de Agentes**: O usuário inicia uma conversa com um agente, enviando mensagens que são processadas pelo backend.
5. **Feedback**: O sistema exibe as respostas do agente e informações sobre o processamento.

## Componentes e Interfaces

### Páginas

1. **Dashboard** (`/dashboard`)
   - Visão geral dos agentes do usuário
   - Métricas de uso
   - Links para criação e gerenciamento de agentes

2. **Criação de Agente** (`/agents/new`)
   - Formulário para configuração de um novo agente
   - Seleção de modelo, ferramentas e bases de conhecimento
   - Configuração de prompt do sistema

3. **Detalhes do Agente** (`/agents/[id]`)
   - Informações detalhadas sobre o agente
   - Métricas de uso
   - Opções para editar ou excluir o agente

4. **Chat com Agente** (`/agents/[id]/chat`)
   - Interface de conversação
   - Exibição de mensagens do usuário e do agente
   - Indicadores de processamento e uso de ferramentas

### Componentes Reutilizáveis

1. **Sidebar**
   - Navegação principal
   - Logo da plataforma
   - Links para as principais seções

2. **AgentCard**
   - Exibição resumida de informações do agente
   - Status visual
   - Links para detalhes e chat

3. **ChatInterface**
   - Campo de entrada de mensagem
   - Exibição de histórico de mensagens
   - Indicadores de digitação e processamento

4. **ToolUsageDisplay**
   - Exibição de informações sobre ferramentas utilizadas pelo agente
   - Resultados de pesquisas, web scraping, etc.

5. **KnowledgeBaseSelector**
   - Seleção de bases de conhecimento para associar ao agente
   - Visualização de bases selecionadas

## Modelos de Dados

### Agent

```typescript
interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'draft' | 'inactive' | 'archived';
  created_at: string;
  updated_at: string;
  user_id: string;
  configuration: {
    model: string;
    system_prompt: string;
    tools: Tool[];
  };
  knowledge_base_ids: string[];
}
```

### Tool

```typescript
interface Tool {
  id: string;
  name: string;
  description: string;
  parameters?: Record<string, any>;
}
```

### KnowledgeBase

```typescript
interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
}
```

### Message

```typescript
interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  tool_calls?: ToolCall[];
}
```

### ToolCall

```typescript
interface ToolCall {
  id: string;
  tool: string;
  input: Record<string, any>;
  output?: Record<string, any>;
  status: 'pending' | 'completed' | 'failed';
}
```

## Tratamento de Erros

1. **Erros de Validação**
   - Exibição de mensagens de erro próximas aos campos com problemas
   - Destaque visual de campos inválidos

2. **Erros de API**
   - Exibição de mensagens de erro em componentes de alerta
   - Opções para tentar novamente ou voltar

3. **Erros de Autenticação**
   - Redirecionamento para página de login
   - Mensagens informativas sobre a necessidade de autenticação

## Estratégia de Testes

1. **Testes de Componentes**
   - Testes unitários para componentes reutilizáveis
   - Verificação de renderização e comportamento

2. **Testes de Integração**
   - Testes de fluxos completos (criação de agente, chat, etc.)
   - Verificação de integração entre componentes

3. **Testes de Responsividade**
   - Verificação de comportamento em diferentes tamanhos de tela
   - Testes em dispositivos móveis e desktop

## Considerações de UX/UI

1. **Identidade Visual**
   - Utilização da logo da Renum (localizada em `E:\PROJETOS SITE\repositorios\renum-suna-core\Arquivos Renum\Imagens Modelo\Logo renum.png`)
   - Paleta de cores consistente com a identidade da marca

2. **Responsividade**
   - Design mobile-first
   - Adaptação de layouts para diferentes tamanhos de tela

3. **Feedback Visual**
   - Indicadores de carregamento para operações assíncronas
   - Mensagens de sucesso e erro claras e contextuais

4. **Acessibilidade**
   - Contraste adequado entre texto e fundo
   - Textos alternativos para imagens
   - Navegação por teclado