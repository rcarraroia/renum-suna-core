# Página de Listagem de Equipes

## Visão Geral

A página de listagem de equipes permite aos usuários visualizar, buscar e gerenciar suas equipes de agentes. Ela exibe as equipes em um formato de cards, com informações resumidas e ações rápidas para cada equipe.

## Componentes Implementados

### Página Principal (`index.tsx`)

- **Listagem de Equipes**: Exibe as equipes em um grid responsivo de cards
- **Paginação**: Permite navegar entre páginas de resultados
- **Busca**: Permite filtrar equipes por nome ou descrição
- **Estado Vazio**: Exibe uma mensagem quando não há equipes para mostrar
- **Estado de Carregamento**: Exibe um indicador de carregamento durante a busca
- **Estado de Erro**: Exibe uma mensagem de erro quando a busca falha

### Componente de Card (`TeamCard.tsx`)

- **Informações da Equipe**: Exibe nome, descrição, tipo de workflow e número de agentes
- **Badge de Tipo**: Exibe o tipo de workflow com cor correspondente
- **Ações Rápidas**: Botões para executar, editar e excluir a equipe
- **Link para Detalhes**: O nome da equipe é um link para a página de detalhes

### Componentes Comuns

- **PageHeader**: Cabeçalho de página com título, descrição e ações
- **SearchFilter**: Campo de busca com debounce para filtrar resultados
- **EmptyState**: Componente para exibir mensagem quando não há dados

### Utilitários

- **string-utils.ts**: Funções para manipulação de strings (truncamento, formatação de data, etc.)
- **workflow-utils.ts**: Funções para manipulação de workflows (nomes amigáveis, cores, validação, etc.)

## Funcionalidades

1. **Visualização de Equipes**
   - Lista todas as equipes do usuário
   - Exibe informações resumidas em cards
   - Paginação para navegar entre resultados

2. **Busca e Filtros**
   - Campo de busca para filtrar equipes por nome ou descrição
   - Debounce para evitar muitas requisições durante a digitação

3. **Ações Rápidas**
   - Botão para criar nova equipe
   - Botões para executar, editar e excluir equipes existentes

4. **Estados da Interface**
   - Estado de carregamento com spinner
   - Estado vazio com mensagem e ação
   - Estado de erro com mensagem e opção de tentar novamente

## Integração com API

A página utiliza os hooks do React Query para buscar dados da API:

- `useTeams`: Hook para buscar a lista de equipes com paginação e busca
- Parâmetros de busca: página, limite e termo de busca
- Tratamento de estados: carregando, erro e sucesso

## Próximos Passos

1. **Implementar Formulário de Criação de Equipe** (T028)
   - Formulário com validação
   - Seletor de agentes disponíveis
   - Configuração de estratégia de execução

2. **Implementar Editor de Membros da Equipe** (T029)
   - Drag & drop para reordenar agentes
   - Configuração de roles e dependências
   - Preview da ordem de execução