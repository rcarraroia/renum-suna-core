# Formulário de Criação de Equipe

## Visão Geral

O formulário de criação de equipe permite aos usuários configurar uma nova equipe de agentes, definindo suas informações básicas, selecionando os agentes que farão parte da equipe e configurando o workflow de execução.

## Componentes Implementados

### Página Principal (`new.tsx`)

- **Formulário de Criação**: Formulário completo com validação
- **Gerenciamento de Estado**: Estado local para dados do formulário e erros
- **Validação**: Validação de todos os campos antes do envio
- **Feedback de Erro**: Exibição de mensagens de erro para cada campo
- **Integração com API**: Uso do hook `useCreateTeam` para enviar os dados

### Componentes de Formulário

- **TextField**: Campo de texto com suporte para validação e mensagens de erro
- **FormField**: Wrapper para campos de formulário com label e mensagem de erro
- **SelectField**: Campo de seleção com opções e integração com FormField

### Componentes Específicos

- **AgentSelector**: Componente para seleção de múltiplos agentes
- **WorkflowConfigurator**: Componente para configuração do workflow

### Utilitários

- **validation-utils.ts**: Funções para validação de dados de equipe e workflow

## Funcionalidades

1. **Informações Básicas**
   - Nome da equipe (obrigatório, mínimo 3 caracteres)
   - Descrição da equipe (obrigatório)

2. **Seleção de Agentes**
   - Lista de agentes disponíveis
   - Busca de agentes por nome ou ID
   - Seleção de múltiplos agentes (até 10)
   - Contador de agentes selecionados

3. **Configuração de Workflow**
   - Seleção do tipo de workflow (Sequencial, Paralelo, Condicional)
   - Configuração específica para cada tipo de workflow
   - Atribuição de papéis aos agentes
   - Definição de ordem de execução (para workflow sequencial)

4. **Validação**
   - Validação de todos os campos obrigatórios
   - Validação de regras específicas para cada tipo de workflow
   - Exibição de mensagens de erro para cada campo

5. **Integração com API**
   - Envio dos dados para a API
   - Feedback de sucesso ou erro
   - Redirecionamento para a página de detalhes da equipe após criação

## Fluxo de Uso

1. O usuário preenche as informações básicas da equipe
2. O usuário seleciona os agentes que farão parte da equipe
3. O usuário configura o workflow de execução
4. O usuário submete o formulário
5. O sistema valida os dados e exibe mensagens de erro, se houver
6. Se os dados forem válidos, o sistema envia para a API
7. Após a criação bem-sucedida, o usuário é redirecionado para a página de detalhes da equipe

## Validações Implementadas

1. **Nome da Equipe**
   - Obrigatório
   - Mínimo de 3 caracteres
   - Máximo de 100 caracteres

2. **Descrição da Equipe**
   - Obrigatória
   - Máximo de 500 caracteres

3. **Agentes**
   - Pelo menos um agente deve ser selecionado
   - Máximo de 10 agentes

4. **Workflow**
   - Tipo de workflow obrigatório
   - Para workflow sequencial:
     - Todos os agentes devem ter ordem de execução
     - Não pode haver ordens de execução duplicadas

## Próximos Passos

1. **Implementar Editor de Membros da Equipe** (T029)
   - Drag & drop para reordenar agentes
   - Configuração de roles e dependências
   - Preview da ordem de execução

2. **Implementar Página de Edição de Equipe**
   - Reutilizar componentes do formulário de criação
   - Carregar dados existentes da equipe
   - Validar e enviar atualizações